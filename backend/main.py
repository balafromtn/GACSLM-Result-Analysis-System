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

load_dotenv()
COLAB_PANDASAI_URL = os.environ.get("COLAB_PANDASAI_URL")

from scraper import create_driver, scrape_student
from parser import parse_result_html
from exporter import build_dataframe, export_to_excel_bytes
from report_generator import generate_report_html

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

            raw_html = scrape_student(driver, reg, dob)

            if raw_html:
                parsed = parse_result_html(raw_html)
                if parsed:
                    # Inject additional fields for export
                    parsed["gender"] = student.get("gender", "UNKNOWN")
                    parsed["community"] = student.get("community", "UNKNOWN")
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
    """Answer questions based on the scraped results using Colab PandasAI."""
    if not COLAB_PANDASAI_URL:
        raise HTTPException(status_code=500, detail="Colab PandasAI URL not configured in .env")

    with state_lock:
        results = state["results"]

    if not results:
        raise HTTPException(status_code=400, detail="No data available. Please scrape results first.")

    payload = {
        "query": req.question,
        "data": results
    }

    try:
        # Use a longer timeout as PandasAI model inference might take a while
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(COLAB_PANDASAI_URL, json=payload)
            response.raise_for_status()
            
            # Assuming the Colab endpoint returns {"answer": "..."}
            data = response.json()
            answer = data.get("answer") or str(data)
            return {"answer": str(answer).strip()}
            
    except httpx.HTTPStatusError as e:
        logger.error(f"Colab API HTTP Error: {e.response.status_code} - {e.response.text}")
        raise HTTPException(status_code=502, detail=f"Colab API Error: {e.response.text}")
    except Exception as e:
        logger.error(f"Colab API Connection Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to connect to the Colab LLM. Ensure your notebook is running.")


# ── Serve frontend ──────────────────────────────────────────────────
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")