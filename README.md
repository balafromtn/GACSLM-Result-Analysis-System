# 🎓 Academic Intelligence Dashboard

A full-stack, automated platform designed to ingest student data, asynchronously scrape academic results from the SLMGACCOE eCampus portal, and visualize the performance metrics on a modern, interactive dashboard.

## ✨ Features

* **Automated Data Ingestion:** Upload a `.csv` or `.xlsx` file containing student register numbers to initiate the pipeline.
* **Background Scraping Engine:** Utilizes Selenium WebDriver in headless mode to navigate the portal, bypass logins, and extract raw result tables without blocking the main application.
* **Intelligent HTML Parsing:** Uses BeautifulSoup to dynamically parse and clean complex, varying HTML table structures into structured JSON data.
* **Real-time Analytics Dashboard:** Visualizes overall pass percentages, class average SGPA, and detailed student-level performance with beautiful gradient UI components.
* **Secure Architecture:** Fully containerized PostgreSQL database with environment-variable-driven credentials.

## 🛠️ Tech Stack

**Frontend**
* Framework: Next.js (React)
* Styling: Tailwind CSS
* Icons: Lucide React
* Charts: Chart.js (via React-Chartjs-2)

**Backend**
* API Framework: FastAPI (Python)
* ORM: SQLAlchemy
* Scraping Engine: Selenium & WebDriver Manager
* HTML Parsing: BeautifulSoup4
* Task Processing: Background Tasks / Redis

**Infrastructure**
* Database: PostgreSQL 15
* Containerization: Docker & Docker Compose
* Database Management: Adminer

## 📂 Project Structure

```text
academic-intelligence-system/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI route handlers (upload, analytics)
│   │   ├── core/         # DB config, environment settings
│   │   ├── models/       # SQLAlchemy database schemas
│   │   ├── services/     # Background scraping task coordination
│   │   └── main.py       # FastAPI application entry point
│   ├── scraper_engine/
│   │   ├── scraper.py    # Selenium browser automation
│   │   └── parser.py     # BeautifulSoup HTML extraction
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/          # Next.js App Router (Dashboard UI)
│   │   ├── components/   # Reusable UI (GradeChart, ClassReport)
│   │   └── lib/          # API client and Axios configuration
│   ├── package.json
│   └── tailwind.config.ts
├── docker-compose.yml
└── .gitignore

```

🚀 Getting Started
1. Prerequisites
Ensure you have the following installed on your machine:

Docker Desktop

Node.js (v18+)

Python 3.10+

2. Environment Setup
Security Note: Never commit database credentials to version control.

Create a .env file in the root directory (alongside docker-compose.yml) and add your secure credentials:

Code snippet
# .env
POSTGRES_USER=admin
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=academic_intelligence
3. Start the Infrastructure
Spin up the PostgreSQL database, Redis, and Adminer containers:

Bash
docker-compose up -d
(You can access your database visually by navigating to http://localhost:8080 and logging into Adminer).

4. Start the Backend (FastAPI)
Open a new terminal, navigate to the backend directory, install the dependencies, and start the server:

Bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
The API will be available at http://localhost:8000.

5. Start the Frontend (Next.js)
Open a new terminal, navigate to the frontend directory, install packages, and run the development server:

Bash
cd frontend
npm install
npm run dev
The Dashboard will be available at http://localhost:3000.

🗺️ Roadmap (Upcoming Features)
[ ] Auto-Polling: Implement dynamic frontend polling to replace manual dashboard refreshing during active scraping jobs.

[ ] AI Chatbot Integration: Add a natural language interface to query class performance (e.g., "Who scored highest in Data Structures?").

[ ] Automated Reports: Backend generation of downloadable, formatted PDF class reports.

📝 License
This project is for educational and internal academic administrative use.


***

You can create a new file named `README.md` in the root of your project (right next to your `docker-compose.yml`) and paste this directly in.

Now that your repository is documented and secured, which feature from our roadmap should we tackle next?

<ElicitationsGroup message="What would you like to do next?">
<Elicitation label="Implement auto-polling for results" query="Implement auto-polling for results" query_intent="CLICKABLE_SUGGESTION" />
<Elicitation label="Build the AI chatbot interface" query="Build the AI chatbot interface" query_intent="CLICKABLE_SUGGESTION" />
<Elicitation label="Create backend PDF export" query="Create backend PDF export" query_intent="CLICKABLE_SUGGESTION" />
</ElicitationsGroup>