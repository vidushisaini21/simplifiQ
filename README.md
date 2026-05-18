# SimpliFiQ — AI-Powered Web Audit Tool

An automated lead audit pipeline: submit a company website → AI-generated PDF report → emailed to the lead automatically.

---

## How It Works

```
[React Form]
    │
    ▼ POST /api/leads  (202 Accepted — instant)
[FastAPI Background Task]
    │
    ├─ 1. Scrape website  (httpx → Playwright fallback)
    ├─ 2. AI analysis     (Google Gemini 1.5 Flash)
    ├─ 3. Generate PDF    (Playwright headless Chrome)
    ├─ 4. Google Drive    (Upload PDF + set shareable link)
    ├─ 5. Google Sheets   (Log lead data + Drive link)
    └─ 6. Send email      (Resend → Gmail SMTP → log fallback)

[Frontend polls /api/report-status every 5s]
    │
    └─ Shows PDF preview + Download button when done
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 19 (Vite), Vanilla CSS, React Hook Form, Axios |
| **Backend** | Python FastAPI, Uvicorn |
| **Scraping** | httpx, BeautifulSoup4, Playwright Chromium |
| **AI** | Google Gemini 1.5 Flash |
| **PDF** | Playwright (HTML → PDF via headless Chrome) |
| **Google APIs** | Drive API (v3), Sheets API (v4) via Service Account |
| **Email** | Resend API / Gmail SMTP fallback |

---

## Quick Start

### 1. Configure Environment Variables

Create `backend/.env` (copy from `backend/.env.example`):

```env
GEMINI_API_KEY=your_key_from_aistudio.google.com
RESEND_API_KEY=your_key_from_resend.com
RESEND_FROM_EMAIL=you@yourverifieddomain.com

# OR use Gmail instead of Resend:
GMAIL_USER=your_gmail@gmail.com
GMAIL_APP_PASSWORD=your_16char_app_password

# ── Google Integrations (Drive & Sheets) ──
GOOGLE_SERVICE_ACCOUNT_JSON=google-credentials.json
GOOGLE_SHEET_ID=your_google_sheet_id
GOOGLE_DRIVE_FOLDER_ID=your_google_drive_folder_id
```

### 2. Start the Backend

```bash
cd backend
pip install -r requirements.txt
playwright install chromium
python main.py
# Runs on http://localhost:8000
```

### 3. Start the Frontend

```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:5173
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Health check |
| POST | `/api/leads` | Submit lead → start workflow |
| GET | `/api/report-status?email=...` | Poll for completion |
| GET | `/reports/{filename}` | Download generated PDF |
| GET | `/docs` | Swagger UI (auto-generated) |

---

## Key Design Decisions

- **Async background tasks** — heavy work (scraping, AI, PDF) runs after 202 response; client polls for status
- **Two-layer scraping** — httpx for speed, Playwright for JS-rendered sites 
- **Three-tier email fallback** — Resend → Gmail SMTP → local log; never crashes
- **AI fallback** — rule-based scoring when Gemini is unavailable; report always generates
- **HTML-to-PDF** — uses Chrome's print engine for pixel-perfect branded reports

---

> See **`PROJECT_EXPLANATION.md`** for a complete, interview-ready breakdown of every component, technology choice, and design decision.
