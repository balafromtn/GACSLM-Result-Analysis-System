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
| **💬 Ask AI (Chat)** | Natural-language chat interface powered by Qwen3:4b via a Colab-hosted PandasAI server tunnelled through Cloudflare |
| **🌗 Light & Dark Theme** | Dual-theme UI styled after the GAC Salem-7 collegiate color palette |
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
| `httpx>=0.27.0` | Async HTTP client to call the Colab AI server |
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
cd backend
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

Create (or edit) `backend/.env`:

```env
COLAB_PANDASAI_URL=https://<your-cloudflare-tunnel-subdomain>.trycloudflare.com/ask
```

> The URL is generated each time you run the Colab notebook (`Academic_LLM_Server.ipynb`). Copy the tunnel URL printed in the notebook output and paste it here.

### 5. Start the backend server

Make sure you are inside the `backend/` directory:

```bash
cd backend
python -m uvicorn main:app --reload
```

### 6. Open the app in your browser

Navigate to: [http://127.0.0.1:8000](http://127.0.0.1:8000)

> The frontend is served automatically as static files by FastAPI — no separate frontend server is needed.

---

## 🤖 AI Chat Setup (Google Colab)

The **Ask AI** feature requires a separately running Google Colab notebook that hosts the LLM server.

1. Open `Academic_LLM_Server.ipynb` in Google Colab.
2. Run all cells — the notebook will:
   - Install `pandasai`, `ollama`, and `cloudflared`
   - Pull the **Qwen3:4b** model via Ollama
   - Start a Flask API server on port `5000`
   - Create a **Cloudflare Tunnel** and print a public HTTPS URL
3. Copy the printed tunnel URL (e.g. `https://xxxx.trycloudflare.com`) and set it in `backend/.env` as shown above.
4. The local FastAPI backend will proxy AI queries to this Colab endpoint via `POST /ask-ai`.

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
- Chat interface powered by **Qwen3:4b** running on Google Colab via **PandasAI**
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
│     POST /ask-ai → proxies question + scraped data to       │
│     Colab PandasAI endpoint → returns LLM answer            │
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
| `POST` | `/ask-ai` | Send a question; proxied to the Colab LLM server |

---

## 📁 Project Structure

```
academic-intelligence-system/
├── backend/
│   ├── .env                  # Environment config (COLAB_PANDASAI_URL)
│   ├── __init__.py
│   ├── main.py               # FastAPI app, all API endpoints, in-memory state
│   ├── scraper.py            # Selenium headless Chrome automation
│   ├── parser.py             # BeautifulSoup result table parser
│   ├── exporter.py           # Pandas DataFrame + Excel export
│   ├── report_generator.py   # Jinja2 HTML analytics dashboard generator
│   ├── requirements.txt      # Python dependencies
│   └── templates/            # Jinja2 HTML templates for the report
├── frontend/
│   ├── index.html            # Single-page app structure
│   ├── style.css             # GAC Salem-7 collegiate themed CSS (light + dark)
│   └── app.js                # Upload, scraping, live status, chat logic
├── logs/
│   └── scraper.log           # Persistent scraper log file
├── .gitignore
└── README.md
```

---

## 🎨 UI Theme

The interface uses a **dual-theme design** (light and dark) inspired by the **GAC Salem-7 collegiate color palette**:

| Token | Dark Theme | Light Theme |
|-------|-----------|-------------|
| Background | `#0a0e17` (midnight) | `#f0f4ff` |
| Header / Card | `#111827` | `#ffffff` |
| Accent / Gold | `#ffb606` | `#b8860b` |
| Primary Blue | `#2563eb` | `#1565c0` |
| Success | `#10b981` | `#2e7d32` |
| Text | `#e2e8f0` | `#1e293b` |

## 📝 License
This project is built only for educational purpose.