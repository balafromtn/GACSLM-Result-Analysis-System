"""
main.py — FastAPI backend for the SLMGACCOE Results Scraper.

Endpoints:
    POST /upload    — Accept .xlsx or .csv, parse it, return student list
    POST /scrape    — Start scraping in background thread
    GET  /status    — Return live scraping progress + log messages
    GET  /download  — Return the generated Excel file
    GET  /logs      — Return recent log entries for the UI

All results held IN MEMORY only — no database, no file persistence.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import threading
import logging
import os
import sys
import json
from io import BytesIO, StringIO
from datetime import datetime
from collections import deque
from pydantic import BaseModel
from dotenv import load_dotenv
import httpx

# Ensure backend directory is in sys.path so sibling imports work regardless of CWD
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

load_dotenv(os.path.join(BACKEND_DIR, ".env"))
load_dotenv()

# LLM Configuration (supports local Ollama OpenAI-compatible endpoint)
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "ollama")
LLM_API_BASE = os.environ.get("LLM_API_BASE", "http://localhost:11434/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "qwen3.5:4b")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "ollama")
LLM_TIMEOUT = float(os.environ.get("LLM_TIMEOUT", "180.0"))

from scraper import create_driver, scrape_student
from parser import parse_result_html
from exporter import build_dataframe, export_to_excel_bytes
from report_generator import generate_report_html
from analytics import (
    AcademicAnalytics,
    build_academic_context_and_intent,
    sanitize_llm_response,
)

# ── Logging setup (file + console + in-memory ring buffer) ───────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "scraper.log")

# In-memory log buffer for the UI (last 200 entries)
log_buffer: deque[dict] = deque(maxlen=200)
log_buffer_lock = threading.Lock()


class UILogHandler(logging.Handler):
    """Custom handler that pushes log records into an in-memory buffer for the UI."""

    def emit(self, record):
        entry = {
            "time": datetime.fromtimestamp(record.created).strftime("%H:%M:%S"),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        with log_buffer_lock:
            log_buffer.append(entry)


# Configure root logger directly (not via basicConfig, which can be
# silently ignored if the root logger already has handlers from uvicorn)
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

# Remove any existing handlers to avoid duplicates on reload
root_logger.handlers.clear()

file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8", mode="a")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
)
root_logger.addHandler(file_handler)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(
    logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
)
root_logger.addHandler(console_handler)

ui_handler = UILogHandler()
ui_handler.setLevel(logging.INFO)
root_logger.addHandler(ui_handler)

logger = logging.getLogger(__name__)
logger.info("Logging initialized — file: %s", LOG_FILE)

# ── FastAPI app ──────────────────────────────────────────────────────
app = FastAPI(
    title="SLMGACCOE Results Scraper",
    description="Automate scraping student exam results from the SLMGACCOE eCampus portal.",
    version="2.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory state ─────────────────────────────────────────────────
state = {
    "students": [],
    "total": 0,
    "done": 0,
    "current": "",
    "failed": [],
    "success": [],
    "results": [],
    "excel_bytes": None,
    "scraping": False,
    "completed": False,
}
state_lock = threading.Lock()


def reset_state():
    """Reset all scraping state."""
    with state_lock:
        state["students"] = []
        state["total"] = 0
        state["done"] = 0
        state["current"] = ""
        state["failed"] = []
        state["success"] = []
        state["results"] = []
        state["excel_bytes"] = None
        state["scraping"] = False
        state["completed"] = False

    with log_buffer_lock:
        log_buffer.clear()


# ── Endpoints ────────────────────────────────────────────────────────

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Accept an .xlsx or .csv file with columns: register_no, dob."""
    filename = file.filename.lower()
    if not (filename.endswith(".xlsx") or filename.endswith(".csv")):
        raise HTTPException(status_code=400, detail="Only .xlsx and .csv files are accepted.")

    try:
        contents = await file.read()

        if filename.endswith(".csv"):
            text = contents.decode("utf-8")
            df = pd.read_csv(StringIO(text))
            logger.info(f"Parsing CSV file: {file.filename}")
        else:
            df = pd.read_excel(BytesIO(contents), engine="openpyxl")
            logger.info(f"Parsing Excel file: {file.filename}")

        required_cols = {"reg_no", "dob", "gender"}
        actual_cols = set(df.columns.str.strip().str.lower())
        if not required_cols.issubset(actual_cols):
            raise HTTPException(
                status_code=400,
                detail=f"File must have columns: reg_no, dob, gender. Found: {list(df.columns)}",
            )

        df.columns = df.columns.str.strip().str.lower()

        students = []
        for idx, row in df.iterrows():
            reg = str(row["reg_no"]).strip()
            dob_raw = row["dob"]
            gender = str(row["gender"]).strip() if pd.notna(row["gender"]) else "UNKNOWN"
            community = str(row["community"]).strip() if "community" in row and pd.notna(row["community"]) else "UNKNOWN"

            if isinstance(dob_raw, str):
                dob_parsed = None
                for fmt in ["%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]:
                    try:
                        dob_parsed = datetime.strptime(dob_raw.strip(), fmt)
                        break
                    except ValueError:
                        continue
                if dob_parsed is None:
                    try:
                        dob_parsed = pd.to_datetime(dob_raw)
                    except Exception:
                        logger.error(f"Row {idx + 1}: Cannot parse DOB '{dob_raw}' for {reg}")
                        raise HTTPException(
                            status_code=400,
                            detail=f"Row {idx + 1}: Cannot parse DOB '{dob_raw}' for '{reg}'. Expected: mm/dd/yyyy",
                        )
            else:
                dob_parsed = pd.to_datetime(dob_raw)

            dob_str = dob_parsed.strftime("%Y-%m-%d")
            students.append({
                "reg_no": reg, 
                "dob": dob_str,
                "gender": gender,
                "community": community
            })

        reset_state()
        with state_lock:
            state["students"] = students
            state["total"] = len(students)

        logger.info(f"✅ Uploaded {len(students)} students from {file.filename}")

        return {
            "message": f"Uploaded {len(students)} students successfully.",
            "students": students,
            "total": len(students),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")


@app.post("/scrape")
async def start_scraping():
    """Start scraping in a background thread."""
    with state_lock:
        if state["scraping"]:
            raise HTTPException(status_code=409, detail="Scraping already in progress.")
        if not state["students"]:
            raise HTTPException(status_code=400, detail="No students uploaded. Upload a file first.")

        state["scraping"] = True
        state["completed"] = False
        state["done"] = 0
        state["current"] = ""
        state["failed"] = []
        state["success"] = []
        state["results"] = []
        state["excel_bytes"] = None
        state["report_html"] = None

    with log_buffer_lock:
        log_buffer.clear()

    thread = threading.Thread(target=_scrape_all, daemon=True)
    thread.start()

    logger.info(f"🚀 Scraping started for {state['total']} students")
    return {"message": "Scraping started.", "total": state["total"]}


def _scrape_all():
    """Background scraping function."""
    driver = None
    try:
        logger.info("Creating WebDriver (headless Chrome)...")
        driver = create_driver(headless=True)
        logger.info("✅ WebDriver created successfully.")

        students = state["students"]

        for i, student in enumerate(students, 1):
            reg = student["reg_no"]
            dob = student["dob"]

            with state_lock:
                state["current"] = reg

            logger.info(f"[{i}/{len(students)}] Scraping {reg}...")

            # Ensure driver is alive before scraping; recreate if it crashed
            try:
                _ = driver.current_url
            except Exception:
                logger.warning("WebDriver is unresponsive or disconnected. Recreating driver...")
                try:
                    driver.quit()
                except Exception:
                    pass
                driver = create_driver(headless=True)

            raw_html = None
            try:
                raw_html = scrape_student(driver, reg, dob)
            except Exception as e:
                logger.error(f"Scraper error for {reg}: {e}")
                try:
                    driver.quit()
                except Exception:
                    pass
                try:
                    driver = create_driver(headless=True)
                except Exception:
                    pass

            if raw_html:
                parsed = parse_result_html(raw_html)
                if parsed:
                    # Inject additional fields for export
                    parsed["gender"] = student.get("gender", "UNKNOWN")
                    parsed["community"] = student.get("community", "UNKNOWN")
                    parsed["register_no"] = reg
                    parsed["reg_no"] = reg

                    with state_lock:
                        state["results"].append(parsed)
                        state["success"].append(reg)
                        state["done"] += 1
                    logger.info(f"✅ {reg} — scraped successfully ({len(parsed.get('subjects', {}))} subjects)")
                else:
                    error_msg = "HTML parsed but no valid data extracted"
                    with state_lock:
                        state["failed"].append({"reg_no": reg, "error": error_msg})
                        state["done"] += 1
                    logger.error(f"❌ {reg} — {error_msg}")
            else:
                error_msg = "Failed after 3 retries (page may be down or data invalid)"
                with state_lock:
                    state["failed"].append({"reg_no": reg, "error": error_msg})
                    state["done"] += 1
                logger.error(f"❌ {reg} — {error_msg}")

        with state_lock:
            if state["results"]:
                df = build_dataframe(state["results"])
                state["excel_bytes"] = export_to_excel_bytes(df)
                state["report_html"] = generate_report_html(state["results"])
                logger.info(f"📊 Excel and Report generated — {len(state['results'])} students, {len(df.columns) - 3} subjects")
            else:
                logger.warning("⚠ No successful results to export")

            state["scraping"] = False
            state["completed"] = True
            state["current"] = ""

        logger.info(f"🏁 Scraping complete — {len(state['success'])} success, {len(state['failed'])} failed")

    except Exception as e:
        logger.error(f"🚫 Scraping thread crashed: {e}", exc_info=True)
        with state_lock:
            state["scraping"] = False
            state["completed"] = True
            state["current"] = ""
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("WebDriver closed.")
            except Exception:
                pass


@app.get("/status")
async def get_status():
    """Return live scraping progress + recent log entries."""
    with state_lock:
        status_data = {
            "total": state["total"],
            "done": state["done"],
            "current": state["current"],
            "failed": list(state["failed"]),
            "success": list(state["success"]),
            "scraping": state["scraping"],
            "completed": state["completed"],
            "results": state["results"] if state["completed"] else [],
        }

    with log_buffer_lock:
        status_data["logs"] = list(log_buffer)

    return status_data


@app.get("/logs")
async def get_logs():
    """Return recent log entries for the UI."""
    with log_buffer_lock:
        return {"logs": list(log_buffer)}


@app.get("/download")
async def download_excel():
    """Return the generated Excel file."""
    with state_lock:
        excel_bytes = state["excel_bytes"]

    if not excel_bytes:
        raise HTTPException(status_code=404, detail="No results available. Run scraping first.")

    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="student_results.xlsx"'}
    )


@app.get("/report")
async def download_report():
    """Return the generated HTML dashboard."""
    with state_lock:
        report_html = state["report_html"]

    if not report_html:
        raise HTTPException(status_code=404, detail="No report available. Run scraping first.")

    return Response(
        content=report_html,
        media_type="text/html",
    )


class ChatRequest(BaseModel):
    question: str


@app.post("/ask-ai")
async def ask_ai(req: ChatRequest):
    """Answer questions based on the scraped results using deterministic Python analytics + local Ollama."""
    with state_lock:
        results = state["results"]

    if not results:
        raise HTTPException(status_code=400, detail="No data available. Please scrape results first.")

    api_base = LLM_API_BASE.rstrip("/")
    if api_base.endswith("/chat/completions"):
        endpoint = api_base
    elif api_base.endswith("/v1"):
        endpoint = f"{api_base}/chat/completions"
    else:
        endpoint = f"{api_base}/v1/chat/completions"

    # Step 1: Compute verified academic metrics in Python (toppers, ranks, pass %, failed lists)
    analytics = AcademicAnalytics(results)
    verified_context, intent = build_academic_context_and_intent(req.question, analytics)

    # Step 2: Formulate prompt with verified conclusions, forbidding raw thinking output
    system_prompt = (
        "You are an academic analysis assistant for student examination results. "
        "You are provided with pre-calculated, verified academic facts and statistics.\n\n"
        "STRICT GUIDELINES:\n"
        "1. Answer the question directly, concisely, and accurately using ONLY the verified facts provided below.\n"
        "2. Do NOT show any 'Thinking Process:', chain of thought, or step-by-step calculations.\n"
        "3. Provide ONLY the final answer and a short natural-language explanation.\n"
        "4. Format your answer with clean Markdown:\n"
        "   - Separate paragraphs with a blank line.\n"
        "   - When listing student details or statistics, put EACH attribute or item on its own new line starting with '* ' or '- '.\n"
        "   - Never bunch multiple bullet points onto the same line.\n"
        "   - Use **bold** for key names, register numbers, ranks, and totals.\n"
        "5. If there is a tie, mention all tied students.\n"
        "6. Never guess, invent, or recalculate totals or statistics.\n\n"
        f"{verified_context}"
    )

    headers = {"Content-Type": "application/json"}
    if LLM_API_KEY:
        headers["Authorization"] = f"Bearer {LLM_API_KEY}"

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": req.question}
        ],
        "temperature": 0.1,
        "keep_alive": "15m"
    }

    try:
        async with httpx.AsyncClient(timeout=LLM_TIMEOUT) as client:
            response = await client.post(endpoint, json=payload, headers=headers)

            if response.status_code == 404:
                error_detail = response.text
                logger.error(f"Ollama model '{LLM_MODEL}' not found: {error_detail}")
                raise HTTPException(
                    status_code=404,
                    detail=f"Model '{LLM_MODEL}' not found in Ollama. Run 'ollama pull {LLM_MODEL}' in your terminal."
                )

            response.raise_for_status()
            data = response.json()

            # Extract answer from OpenAI-compatible choices
            raw_answer = ""
            choices = data.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                raw_answer = message.get("content") or ""
                # If content is empty but reasoning is present, use reasoning as source
                if not raw_answer and "reasoning" in message:
                    raw_answer = message.get("reasoning", "")
            else:
                raw_answer = data.get("answer") or str(data)

            # Sanitize response: strip any chain-of-thought or "Thinking Process:" artifacts
            final_answer = sanitize_llm_response(raw_answer)

            # Fallback if model output is blank or completely stripped of content
            if not final_answer or "Thinking Process:" in final_answer:
                clean_ctx = verified_context.replace("### Verified Academic Calculations: ", "")
                clean_ctx = clean_ctx.replace("### Verified Academic Dataset Summary", "Class Summary:")
                final_answer = clean_ctx.strip()

            return {"answer": final_answer}

    except httpx.ConnectError:
        logger.error(f"Failed to connect to Ollama at {endpoint}")
        raise HTTPException(
            status_code=503,
            detail=f"Could not connect to Ollama at {LLM_API_BASE}. Ensure Ollama is running locally (e.g., 'ollama serve')."
        )
    except httpx.TimeoutException:
        logger.error(f"Ollama inference timed out after {LLM_TIMEOUT}s")
        raise HTTPException(
            status_code=504,
            detail=f"Inference timed out after {int(LLM_TIMEOUT)} seconds. The model may still be loading or generating a response."
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"Ollama API HTTP Error: {e.response.status_code} - {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Ollama API Error: {e.response.text}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error querying Ollama: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process query with AI service.")


# ── Serve frontend ──────────────────────────────────────────────────
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")