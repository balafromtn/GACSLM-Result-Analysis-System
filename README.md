# 🎓 Academic Intelligence Dashboard

A full-stack academic analytics platform that automates student data ingestion, retrieves examination results from the **SLMGACCOE eCampus portal**, and transforms the collected data into meaningful, interactive performance insights.

The system is designed to reduce manual result collection and provide administrators and faculty with a centralized dashboard for analyzing student and class-level academic performance.

---

## ✨ Features

### 📥 Automated Data Ingestion

* Upload student data through `.csv` or `.xlsx` files.
* Accepts student register numbers and other required identification details.
* Automatically initiates the result retrieval pipeline after upload.

### 🤖 Automated Result Scraping

* Uses **Selenium WebDriver** for browser automation.
* Runs the browser in **headless mode** for background execution.
* Navigates the SLMGACCOE eCampus result portal automatically.
* Retrieves raw academic result data without blocking the main API.

### 🧠 Intelligent HTML Parsing

* Uses **BeautifulSoup4** to process scraped HTML.
* Handles varying and complex result-table structures.
* Cleans and converts raw HTML data into structured JSON.
* Designed to accommodate changes in the portal's result-page structure.

### ⚡ Background Processing

* Academic result retrieval runs asynchronously.
* Prevents long-running scraping operations from blocking API requests.
* Supports background task coordination through Redis.

### 📊 Interactive Analytics Dashboard

Provides visual insights such as:

* Overall pass percentage
* Class average SGPA
* Student-level academic performance
* Subject-wise performance
* Result summaries
* Interactive charts and visual reports

### 🔐 Secure Architecture

* PostgreSQL database for persistent storage.
* Database credentials managed through environment variables.
* Dockerized infrastructure for consistent development and deployment.
* Sensitive configuration files excluded from version control.

---

# 🛠️ Tech Stack

## Frontend

| Technology          | Purpose                         |
| ------------------- | ------------------------------- |
| **Next.js**         | Frontend framework              |
| **React**           | UI development                  |
| **Tailwind CSS**    | Styling and responsive UI       |
| **Lucide React**    | Icons                           |
| **Chart.js**        | Data visualization              |
| **React-Chartjs-2** | Chart.js integration with React |

## Backend

| Technology            | Purpose                      |
| --------------------- | ---------------------------- |
| **FastAPI**           | REST API framework           |
| **Python**            | Backend and scraping logic   |
| **SQLAlchemy**        | ORM and database interaction |
| **Selenium**          | Browser automation           |
| **WebDriver Manager** | WebDriver management         |
| **BeautifulSoup4**    | HTML parsing                 |
| **Redis**             | Background task coordination |

## Infrastructure

| Technology         | Purpose                       |
| ------------------ | ----------------------------- |
| **PostgreSQL 15**  | Primary database              |
| **Docker**         | Containerization              |
| **Docker Compose** | Multi-container orchestration |
| **Adminer**        | Database administration       |

---

# 🏗️ System Architecture

```text
                    ┌─────────────────────┐
                    │      Frontend       │
                    │   Next.js + React   │
                    └──────────┬──────────┘
                               │
                               │ REST API
                               ▼
                    ┌─────────────────────┐
                    │       FastAPI       │
                    │      Backend        │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
       ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
       │ PostgreSQL  │  │    Redis    │  │   Services  │
       │  Database   │  │ Task Queue  │  │ Coordination│
       └─────────────┘  └─────────────┘  └──────┬──────┘
                                                │
                                                ▼
                                      ┌──────────────────┐
                                      │ Scraper Engine   │
                                      │    Selenium      │
                                      └────────┬─────────┘
                                               │
                                               ▼
                                      ┌──────────────────┐
                                      │ eCampus Portal   │
                                      └────────┬─────────┘
                                               │
                                               ▼
                                      ┌──────────────────┐
                                      │ BeautifulSoup    │
                                      │ HTML Parser      │
                                      └────────┬─────────┘
                                               │
                                               ▼
                                      Structured Result Data
```

---

# 📂 Project Structure

```text
academic-intelligence-system/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── # FastAPI route handlers
│   │   │      # Upload, analytics, etc.
│   │   │
│   │   ├── core/
│   │   │   └── # Database configuration
│   │   │      # Environment settings
│   │   │
│   │   ├── models/
│   │   │   └── # SQLAlchemy database models
│   │   │
│   │   ├── services/
│   │   │   └── # Background task coordination
│   │   │
│   │   └── main.py
│   │       # FastAPI application entry point
│   │
│   ├── scraper_engine/
│   │   ├── scraper.py
│   │   │   # Selenium browser automation
│   │   │
│   │   └── parser.py
│   │       # BeautifulSoup HTML extraction
│   │
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   └── # Next.js App Router
│   │   │
│   │   ├── components/
│   │   │   └── # Reusable UI components
│   │   │      # GradeChart, ClassReport, etc.
│   │   │
│   │   └── lib/
│   │       └── # API client and Axios configuration
│   │
│   ├── package.json
│   └── tailwind.config.ts
│
├── docker-compose.yml
├── .env
├── .gitignore
└── README.md
```

---

# 🚀 Getting Started

## 1. Prerequisites

Make sure the following software is installed:

* [Docker Desktop](https://www.docker.com/products/docker-desktop/)
* Node.js **18 or later**
* Python **3.10 or later**
* Git

Verify the installations:

```bash
docker --version
node --version
python --version
git --version
```

---

## 2. Clone the Repository

```bash
git clone <your-repository-url>
cd academic-intelligence-system
```

---

## 3. Configure Environment Variables

> ⚠️ **Security:** Never commit database credentials or other secrets to Git.

Create a `.env` file in the project root, next to `docker-compose.yml`:

```env
POSTGRES_USER=admin
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=academic_intelligence
```

Make sure `.env` is included in `.gitignore`:

```gitignore
.env
```

---

## 4. Start the Infrastructure

Start PostgreSQL, Redis, and Adminer using Docker Compose:

```bash
docker compose up -d
```

Check the running containers:

```bash
docker compose ps
```

### Adminer

Adminer can be accessed at:

```text
http://localhost:8080
```

Use the PostgreSQL credentials defined in your `.env` file.

---

# ⚙️ Backend Setup

## 5. Create a Python Virtual Environment

Open a new terminal:

```bash
cd backend
```

Create the virtual environment:

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 6. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 7. Start the FastAPI Server

```bash
uvicorn app.main:app --reload
```

The backend API will be available at:

```text
http://localhost:8000
```

FastAPI's interactive API documentation:

```text
http://localhost:8000/docs
```

---

# 🎨 Frontend Setup

## 8. Install Dependencies

Open another terminal:

```bash
cd frontend
npm install
```

---

## 9. Start the Development Server

```bash
npm run dev
```

The dashboard will be available at:

```text
http://localhost:3000
```

---

# 🔄 Application Workflow

The overall workflow follows this process:

```text
1. Upload CSV/XLSX
        │
        ▼
2. Validate Student Data
        │
        ▼
3. Create Scraping Job
        │
        ▼
4. Background Scraping
        │
        ▼
5. Access eCampus Portal
        │
        ▼
6. Retrieve Result HTML
        │
        ▼
7. Parse HTML with BeautifulSoup
        │
        ▼
8. Convert Results to Structured Data
        │
        ▼
9. Store Results in PostgreSQL
        │
        ▼
10. Generate Analytics
        │
        ▼
11. Display Results on Dashboard
```

---

# 📊 Dashboard

The dashboard provides a centralized view of academic performance.

### Key Analytics

* **Overall Pass Percentage**
* **Class Average SGPA**
* **Student Performance**
* **Subject-wise Results**
* **Performance Distribution**
* **Individual Student Results**

The frontend uses interactive charts and modern UI components to make academic data easier to understand and analyze.

---

# 🧪 Development

### Run Backend

```bash
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload
```

### Run Frontend

```bash
cd frontend
npm run dev
```

### Run Infrastructure

```bash
docker compose up -d
```

### Stop Infrastructure

```bash
docker compose down
```

---

# 🗺️ Roadmap

The following features are planned for future releases:

* [ ] **Auto-Polling**

  * Implement dynamic frontend polling for active scraping jobs.
  * Automatically update the dashboard when scraping is completed.

* [ ] **AI Chatbot Integration**

  * Add a natural-language interface for querying academic data.
  * Example:

    > "Who scored the highest in Data Structures?"

* [ ] **Automated Reports**

  * Generate downloadable PDF class reports.
  * Include student statistics, subject performance, and class-level analytics.

* [ ] **Advanced Analytics**

  * Semester-to-semester performance comparison.
  * Subject-wise trends.
  * Top-performing and at-risk student identification.

* [ ] **Job Monitoring**

  * Display scraping progress and job status.
  * Provide detailed failure and retry information.

---

# 🔒 Security Considerations

* Store credentials exclusively in environment variables.
* Never commit `.env` files to the repository.
* Avoid logging sensitive student information.
* Restrict database access to trusted services.
* Use HTTPS and secure authentication when deploying to production.
* Apply appropriate access controls before exposing academic data to users.

> **Important:** Student academic records may contain sensitive personal information. Ensure that any deployment complies with applicable institutional policies, privacy requirements, and data-protection regulations.

---

# 📝 License

This project is intended for **educational and internal academic administrative use**.

If you plan to deploy or distribute the system publicly, review the applicable institutional policies, portal terms of use, and data-protection requirements first.

---

## 👨‍💻 Project Status

**Status:** 🚧 Active Development

The core pipeline for student data ingestion, automated result retrieval, parsing, storage, and dashboard visualization is under active development.

---

<p align="center">
  Built for smarter academic data management 🎓
</p>
