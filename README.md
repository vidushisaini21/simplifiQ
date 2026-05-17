# SimpliFiQ — AI Software Developer Intern Assessment

A full-stack application that automates lead capture → website enrichment → PDF report generation → email delivery.

---

## Tech Stack
| Layer | Technology |
|---|---|
| **Frontend** | React (Vite), Vanilla CSS (glassmorphism), React Hook Form |
| **Backend** | Node.js, Express, Cheerio (scraping), PDFKit (PDF), Nodemailer (email) |
| **Bonus** | Google Sheets API logging (with graceful fallback) |

---

## ⚡ Quick Start

### Step 1 — Configure Email (REQUIRED to receive real emails)

Open `backend/.env` and fill in your Gmail credentials:

```env
SMTP_USER=your_gmail_address@gmail.com
SMTP_PASS=your_16_char_app_password
PORT=5000
```

> **How to get a Gmail App Password:**
> 1. Go to [myaccount.google.com/security](https://myaccount.google.com/security)
> 2. Enable **2-Step Verification** (required)
> 3. Search **"App Passwords"** → App: **Mail** → Generate
> 4. Copy the 16-character password (e.g. `abcd efgh ijkl mnop`)  
>    Paste it without spaces: `SMTP_PASS=abcdefghijklmnop`

---

### Step 2 — Run the Backend

```bash
cd backend
npm install
node server.js
```
Server starts on **http://localhost:5000**

---

### Step 3 — Run the Frontend

```bash
cd frontend
npm install
npm run dev
```
Opens on **http://localhost:5173**

---

## Workflow Architecture

```
[React Form] 
    │
    ▼ POST /api/leads
[Express Server] ─── 202 Accepted (instant response)
    │
    ▼ async workflow
[Enrichment] ── cheerio scrapes company website metadata
    │
    ▼
[PDF Generator] ── pdfkit creates branded audit report
    │
    ▼
[Email Service] ── nodemailer sends PDF to prospect's email
    │
    ▼
[Sheets Logger] ── logs to Google Sheets OR leads_log.txt fallback
```

## Fail-Safe Design
- **Website scraping** — wrapped in try/catch; uses fallback data if website is unreachable
- **Email delivery** — falls back to Ethereal test account if `.env` credentials are missing (prints preview URL to console)
- **Google Sheets** — falls back to `leads_log.txt` if no GCP credentials are configured
- **422 errors** — field validation on both frontend (React Hook Form) and backend

---

## Bonus Features
- ✅ **Google Sheets logging** — implemented in `backend/services/sheets.js`  
- ✅ **Local fallback logging** — `leads_log.txt` created automatically  
- ✅ **PDF archiving** — reports saved to `backend/reports/`
