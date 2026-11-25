# 🎓 Academic Intelligence Dashboard

A full-stack web application that automates scraping student exam results from the **Government Arts College (Autonomous), Salem-7** [SLMGACCOE eCampus portal](https://slmgaccoe.edecampus.com/student/index.php). Upload a spreadsheet, scrape results in bulk, view an interactive analytics dashboard, and chat with an AI assistant to query class performance — all from one sleek collegiate-themed interface.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **📤 Bulk Upload** | Upload .xlsx or .csv files containing student register numbers and dates of birth |
| **🤖 Headless Scraping** | Chrome runs invisibly in the background — no manual browser needed |
| **🔄 Smart Retry** | Each student is retried up to 3 times on portal timeout or failure |
| **📊 Live Progress** | Real-time progress bar + per-student success/failure status as scraping runs |
| **📋 Consolidated Export** | All results merged into a single `student_results.xlsx` with dynamic subject columns |
| **📈 Visual Dashboard** | Auto-generated interactive HTML report with charts, class insights, and statistics |
| **💬 Ask AI (Chat)** | Natural-language chat interface powered by local Ollama (`qwen3.5:4b`) |
| **🏛️ Collegiate Light Theme** | Clean UI styled after the official GAC Salem-7 collegiate palette |
| **📝 Live Logs** | In-browser scrolling log panel showing scraper events in real time |

---

## 📋 Requirements

- **Python 3.10+**
- **Google Chrome** (installed on your system; ChromeDriver is auto-managed)

### Python Dependencies

| Package | Purpose |
|---------|---------|
| `fastapi>=0.110.0` | Web framework for the backend REST API |
| `uvicorn[standard]>=0.28.0` | ASGI server to serve FastAPI |
| `selenium>=4.18.1` | Browser automation for scraping the eCampus portal |
| `webdriver-manager>=4.0.1` | Auto-downloads the correct ChromeDriver version |
| `beautifulsoup4>=4.12.3` | Parses student result HTML tables |
| `pandas>=2.2.1` | Data manipulation and DataFrame construction |
| `openpyxl>=3.1.2` | Reading `.xlsx` input and writing the output Excel file |
| `python-multipart>=0.0.9` | Handles multipart file uploads in FastAPI |
| `jinja2>=3.1.2` | Renders the HTML analytics dashboard report |
| `httpx>=0.27.0` | Async HTTP client to call the local Ollama LLM endpoint |
| `python-dotenv>=1.0.0` | Loads environment variables from `.env` |

---

## 🚀 How to Run

### 1. Clone the repository

```bash
git clone https://github.com/balafromtn/GACSLM-Result-Analysis-System.git
cd GACSLM-Result-Analysis-System
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the environment

Create (or edit) `backend/.env` (copy from `backend/.env.example`):

```env
LLM_PROVIDER=ollama
LLM_API_BASE=http://localhost:11434/v1
LLM_MODEL=qwen3.5:4b
LLM_API_KEY=ollama
LLM_TIMEOUT=180.0
```

### 5. Start the backend server

```bash
cd backend
python -m uvicorn main:app --reload
```

### 6. Open the app in your browser

Navigate to: [http://127.0.0.1:8000](http://127.0.0.1:8000)

> The frontend is served automatically as static files by FastAPI — no separate frontend server is needed.

---

## 🤖 AI Chat Setup (Local Ollama)

The **Ask AI** feature connects directly to locally hosted Ollama for natural language queries over the scraped student exam dataset.

1. Install [Ollama](https://ollama.com/) on your local machine.
2. Pull the recommended model:
   ```bash
   ollama pull qwen3.5:4b
   ```
3. Start Ollama (if not already running as a system service):
   ```bash
   ollama serve
   ```
4. Verify the model is available:
   ```bash
   ollama list
   ```
5. Ensure your `backend/.env` has the local Ollama configuration:
   ```env
   LLM_PROVIDER=ollama
   LLM_API_BASE=http://localhost:11434/v1
   LLM_MODEL=qwen3.5:4b
   LLM_API_KEY=ollama
   ```
   No Google Colab instance or Cloudflare Tunnel is required.

---

## 📄 Input File Format

The uploaded file must be `.xlsx` or `.csv` with **at least three required columns**:

| Column | Header | Format | Example |
|--------|--------|--------|---------|
| 1 | `reg_no` | Year + Dept code + Roll number | `24UCS250904` |
| 2 | `dob` | Date of birth — **mm/dd/yyyy** recommended | `10/20/2006` |
| 3 | `gender` | `Male` or `Female` (used for stats) | `Male` |

An optional **`community`** column is also supported and included in the analytics report.

### Example

| reg_no | dob | gender | community |
|--------|-----|--------|-----------|
| 24UCS250904 | 10/20/2006 | Male | OBC |
| 24UCS250905 | 11/28/2006 | Female | BC |
| 24UCS250906 | 03/15/2006 | Male | OC |

> **Notes:**
> - Column headers are **case-insensitive**.
> - Supported DOB formats: `mm/dd/yyyy`, `dd/mm/yyyy`, `yyyy-mm-dd`, `dd-mm-yyyy`.
> - CSV files must be UTF-8 encoded.

---

## 🌐 Web App Sections

### 📤 Upload Panel
- Drag-and-drop or browse to select your `.xlsx`/`.csv` file
- Displays a preview table of parsed students with register numbers and DOBs

### 🚀 Scraping Controls
- **Start Scraping** button kicks off the background scraping task
- A progress bar tracks completion percentage in real time
- Per-student status cards show ✅ (success) or ❌ (failed) results as they arrive

### 📝 Live Logs
- Scrollable log panel streams timestamped scraper events
- Color-coded by log level: INFO, WARNING, ERROR

### 📊 Visual Dashboard
- After scraping, opens a generated HTML report in a new tab
- Includes: class summary stats, subject-wise pass/fail charts, gender and community breakdowns, topper list

### 📥 Export
- **Download Excel** button fetches `student_results.xlsx` containing all scraped results in a unified sheet with dynamic subject columns

### 💬 Ask AI
- Chat interface powered by **qwen3.5:4b** running locally via **Ollama**
- Example queries:
  - *"How many students failed more than 2 subjects?"*
  - *"What is the class average for subject 24UCS101?"*
  - *"List the top 5 students by total marks."*

---

## 🔄 How It Works

```
┌─────────────────────────────────────────────────────────────┐
│  1. UPLOAD                                                  │
│     POST /upload — validates columns, parses DOB formats    │
│     → Stores student list in-memory                         │
├─────────────────────────────────────────────────────────────┤
│  2. SCRAPE (background thread)                              │
│     POST /scrape — spawns a daemon thread                   │
│     → Headless Chrome logs into slmgaccoe.edecampus.com     │
│     → For each student: fills reg_no + dob, submits form,   │
│       navigates to ResultPrint.php, extracts marks table    │
│     → Retries up to 3x on failure                          │
├─────────────────────────────────────────────────────────────┤
│  3. PARSE                                                   │
│     BeautifulSoup extracts per-student:                     │
│     → Name, Register No, Degree/Branch, Exam Month/Year     │
│     → Subject codes, marks, grades (dynamically discovered) │
├─────────────────────────────────────────────────────────────┤
│  4. EXPORT & REPORT                                         │
│     GET /download → student_results.xlsx                    │
│     GET /report   → Interactive HTML analytics dashboard    │
├─────────────────────────────────────────────────────────────┤
│  5. ASK AI                                                  │
│     POST /ask-ai → sends question + scraped data to local   │
│     Ollama endpoint → returns LLM answer                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🗂️ API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/upload` | Upload `.xlsx`/`.csv`; returns parsed student list |
| `POST` | `/scrape` | Start background scraping job |
| `GET` | `/status` | Live scraping progress, success/fail lists, and log buffer |
| `GET` | `/logs` | Recent log entries (last 200) |
| `GET` | `/download` | Download `student_results.xlsx` |
| `GET` | `/report` | Fetch the generated HTML analytics dashboard |
| `POST` | `/ask-ai` | Send a question; answered by local Ollama |

---

## 📁 Project Structure

```
academic-intelligence-system/
├── requirements.txt          # Python dependencies
├── backend/
│   ├── .env                  # Environment config (LLM_API_BASE, LLM_MODEL)
│   ├── .env.example          # Sample environment configuration
│   ├── __init__.py
│   ├── main.py               # FastAPI app, API endpoints, state management
│   ├── scraper.py            # Selenium headless Chrome automation
│   ├── parser.py             # BeautifulSoup result table parser
│   ├── exporter.py           # Pandas DataFrame + Excel export
│   ├── report_generator.py   # Jinja2 HTML analytics dashboard generator
│   ├── analytics.py          # Deterministic analytics helper functions
│   ├── intelligence/         # Generic Hybrid Academic Data Intelligence Engine
│   │   ├── __init__.py
│   │   ├── schema.py         # Dynamic schema discovery & subject alias resolution
│   │   ├── engine.py         # Deterministic query execution engine (Pandas/Python)
│   │   ├── planner.py        # Schema-aware query planner & intent classifier
│   │   ├── memory.py         # Bounded conversation memory & follow-up resolver
│   │   └── dispatcher.py     # Dual-path execution orchestrator (Path A / Path B)
│   └── templates/            # Jinja2 HTML templates for the report
├── frontend/
│   ├── index.html            # Single-page app structure
│   ├── style.css             # GAC Salem-7 collegiate light theme CSS
│   └── app.js                # Upload, scraping, live status, chat logic
├── tests/
│   └── test_hybrid_engine.py # Automated test suite for intelligence engine
├── logs/
│   └── scraper.log           # Persistent scraper log file
├── .gitignore
└── README.md
```

---

## 🧠 Hybrid Academic Data Intelligence Engine

The application features a **Dual-Path Hybrid Academic Intelligence Engine** designed to answer natural language questions about student exam results accurately and instantaneously:

### 1. Dual-Path Architecture
- **Path A: Direct Analytical Execution (< 2ms, 0 LLM Tokens)**:
  - High-frequency factual queries (*class toppers, top/bottom ranks, overall pass rates, failure lists, student lookups, subject stats, gender comparisons, performance distributions*) are resolved deterministically using Python & Pandas.
  - Zero LLM tokens consumed and zero inference wait time.
- **Path B: LLM-Assisted Synthesis (Compact Verified Context)**:
  - Open-ended, pedagogical, or multi-metric evaluation questions (*"How can we improve results?", "What are the department's weak areas?"*) pass a strictly bounded list of verified facts (~50-150 tokens) to locally hosted Ollama (`qwen3.5:4b`).
  - Strict system prompt prevents hallucinations, recalculations, or internal chain-of-thought exposure.

### 2. Conversation Awareness & Memory
- Bounded conversation state tracks referenced entities, subjects, and analytical intents.
- Resolves anaphoric follow-up queries:
  - *User*: "Who is the class topper?"
  - *User*: "What about the girls?" → *Auto-resolves to female topper*
  - *User*: "Compare their marks" → *Auto-compares male vs female topper*

### 3. Running Automated Tests
Run the comprehensive test suite covering schema discovery, rankings, tied toppers, multi-condition filtering, comparisons, distributions, and follow-ups:

```bash
python tests/test_hybrid_engine.py
```
```

---

## 🎨 UI Theme

The interface uses a clean **collegiate light theme** inspired by the **GAC Salem-7 official color palette**:

| Token | Light Theme | Description |
|-------|-------------|-------------|
| Background | `#f4f6fa` | Crisp light background |
| Header / Card | `#ffffff` | Clean elevated card surfaces |
| Accent / Gold | `#ffb606` | Official collegiate gold accent |
| Primary Blue | `#1565c0` | Department navy blue |
| Success | `#2e7d32` | Forest green for passes |
| Text | `#1e293b` | High-contrast slate text |

## 📝 License
This project is built only for educational purpose.