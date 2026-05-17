# SimpliFiQ — Complete Project Explanation
### Everything You Need to Explain This in an Interview

---

## 1. What Is This Project?

**SimpliFiQ** is a full-stack, AI-powered web audit tool. A user submits a form with their name, email, company name, and website URL. The system:

1. **Scrapes** the company's website to extract real data (title, headings, technologies, social media links, contact info, etc.)
2. **Sends** that data to **Google Gemini AI** to generate a professional, personalised business analysis
3. **Generates** a beautiful, branded **PDF report** (cover page + 2 content pages)
4. **Emails** the PDF to the user automatically (via Resend API or Gmail SMTP)
5. **Displays** the PDF in-browser and lets the user **download** it or **start another audit**

The whole pipeline runs **asynchronously** — the frontend immediately gets a "202 Accepted" response and then polls for status every 5 seconds while the heavy work happens in the background.

---

## 2. Project Structure

```
Assignment/
├── backend/                  ← Python FastAPI server
│   ├── main.py               ← API routes, background workflow orchestrator
│   ├── requirements.txt      ← Python dependencies
│   ├── start.ps1             ← PowerShell startup script for Windows
│   ├── .env                  ← Secret keys (gitignored)
│   ├── .env.example          ← Template showing what keys are needed
│   ├── reports/              ← Generated PDFs stored here
│   └── services/
│       ├── enrichment.py     ← Website scraper (httpx + BeautifulSoup + Playwright)
│       ├── ai_service.py     ← Google Gemini AI integration
│       ├── report.py         ← HTML-to-PDF generator using Playwright
│       └── email_service.py  ← Email sending (Resend → Gmail → log fallback)
│
├── frontend/                 ← React + Vite app
│   ├── index.html            ← Single HTML shell
│   ├── package.json          ← Node dependencies
│   ├── vite.config.js        ← Vite bundler config
│   └── src/
│       ├── main.jsx          ← React root mount
│       ├── App.jsx           ← Entire frontend application (form + polling + result)
│       └── index.css         ← All custom CSS (glassmorphism dark theme)
│
├── .gitignore                ← Excludes .env, node_modules, __pycache__, PDFs
├── README.md                 ← Quick start guide
└── PROJECT_EXPLANATION.md    ← This file
```

---

## 3. Technology Stack — Why Each Was Chosen

| Layer | Technology | Why |
|---|---|---|
| **Frontend Framework** | React 19 (via Vite) | Component-based UI, fast HMR dev experience |
| **Form Handling** | React Hook Form | Zero re-renders on typing, easy validation |
| **HTTP Client** | Axios | Cleaner API than fetch, automatic JSON parsing |
| **Styling** | Vanilla CSS (no Tailwind in use) | Full control, glassmorphism effects, custom animations |
| **Backend Framework** | FastAPI (Python) | Async-first, auto-generates docs at /docs, fast |
| **Website Scraping** | httpx + BeautifulSoup4 | httpx handles async HTTP, BS4 parses HTML |
| **JS-heavy site fallback** | Playwright Chromium | Renders JavaScript before scraping (headless browser) |
| **AI Engine** | Google Gemini 1.5 Flash | Fast, cheap, great at structured JSON output |
| **PDF Generation** | Playwright (headless Chrome) | Renders full HTML/CSS to pixel-perfect PDF |
| **Email — Primary** | Resend API | Reliable transactional email with attachment support |
| **Email — Fallback** | Gmail SMTP + App Password | Works when no Resend key is set |
| **Email — Last Resort** | Local `email_log.txt` | Never crashes, always logs |
| **Environment Config** | python-dotenv | Loads .env file into os.getenv() |

---

## 4. The Complete Data Flow (Step by Step)

```
USER fills form
    │
    ▼ POST /api/leads  (HTTP 202 Accepted — instant)
FASTAPI main.py
    │  Stores email → "processing" in memory dict
    │  Queues background task
    │
    ▼ Background Task: process_lead_workflow(lead)
    │
    ├─ STEP 1: enrichment.py → enrich_company(website)
    │     ├── Normalize URL (add https:// if missing)
    │     ├── Try httpx GET (fast, async)
    │     ├── If httpx fails → try Playwright (JS rendering)
    │     ├── Parse with BeautifulSoup:
    │     │     title, meta description, og:tags, keywords
    │     │     h1/h2/h3 headings, nav links, footer text
    │     │     body paragraph text
    │     ├── detect_technologies(): regex scan HTML for 19 tech patterns
    │     ├── extract_social_links(): find LinkedIn, Twitter, etc. hrefs
    │     ├── extract_contact_info(): regex for emails and phone numbers
    │     └── try_fetch_about(): tries /about, /about-us, /company pages
    │
    ├─ STEP 2: ai_service.py → generate_ai_insights(lead, enriched)
    │     ├── Build a rich context string from enriched data
    │     ├── Send prompt to Gemini 1.5 Flash asking for JSON back
    │     ├── Parse JSON response (strip any markdown code fences)
    │     └── If Gemini fails → _fallback_insights() (rule-based scoring)
    │         Returns: executive_summary, industry_vertical,
    │                  digital_maturity_score (1-10), digital_maturity_label,
    │                  strengths[], opportunities[], key_recommendation,
    │                  competitor_landscape
    │
    ├─ STEP 3: report.py → generate_pdf_report(lead, enriched, ai)
    │     ├── _build_html(): constructs full A4-sized HTML (cover + 2 pages)
    │     │     Cover: company name, date, industry, lead info
    │     │     Page 1: AI executive summary, SVG score gauge, tech stack pills
    │     │     Page 2: Strengths vs Opportunities grid, metadata table,
    │     │              key recommendation callout box
    │     ├── Launch Playwright headless Chromium
    │     ├── page.set_content(html, wait_until="networkidle")
    │     │    (waits for Google Fonts to load for beautiful typography)
    │     ├── page.pdf(format="A4", print_background=True)
    │     └── Save as AuditReport_{CompanyName}_{timestamp}.pdf
    │
    ├─ STEP 4: email_service.py → send_audit_email(lead, file_name)
    │     ├── Check RESEND_API_KEY → send via Resend with PDF attachment
    │     ├── else check GMAIL_USER + GMAIL_APP_PASSWORD → Gmail SMTP SSL
    │     └── else → log to email_log.txt (silent fallback, never crashes)
    │
    └─ UPDATE lead_status[email] = {status: "done", file_name: "..."}

FRONTEND polls GET /api/report-status?email=...  every 5 seconds
    │  Response: {status, pdfUrl, error}
    │
    ▼ When status === "done" && pdfUrl exists:
    ├── Stop polling
    ├── Show iframe with PDF preview
    ├── Show "Download PDF" button (anchor tag with download attr)
    └── Show "Make Another Audit" button (resets entire form state)
```

---

## 5. Backend Deep Dive — `main.py`

```python
app = FastAPI(title="SimpliFiQ Audit API")
```

**Key design decisions:**

- **CORS middleware with `allow_origins=["*"]`** — allows the React dev server (localhost:5173) to call the API (localhost:8000) without browser CORS errors. In production this should be restricted to your domain.

- **Static file mounting**: `app.mount("/reports", StaticFiles(...))` — this makes all PDFs in the `reports/` folder directly accessible at `http://localhost:8000/reports/filename.pdf`. No need for a separate file server.

- **In-memory status store**: `lead_status: dict = {}` — a simple Python dictionary keyed by email. In production this would be Redis or a database. For this demo it's sufficient and simple.

- **Background tasks**: `background_tasks.add_task(process_lead_workflow, lead.model_dump())` — FastAPI's built-in BackgroundTasks runs the heavy workflow *after* the HTTP response is sent. This is why the user gets instant feedback (202) while waiting for the 10-30 second processing.

- **Error isolation**: Email failure doesn't break the whole workflow (wrapped in its own try/except). Only scraping or PDF failure marks the lead as "error".

---

## 6. Scraping Deep Dive — `enrichment.py`

**Two-layer scraping strategy:**

1. **httpx (primary)**: Fast, async HTTP client. Uses a real browser User-Agent to avoid bot blocks. Works for most static sites.
2. **Playwright (fallback)**: Full headless Chromium browser. Executes JavaScript, waits 2 seconds for SPA content to render. Used for React/Vue/Angular sites that don't serve content in initial HTML.

**Technology Detection:**
```python
("WordPress", re.compile(r"wp-content|wp-includes|wordpress", re.I)),
("React",     re.compile(r"__react|React\.createElement", re.I)),
# ... 19 total patterns
```
Scans the raw HTML string for 19 known technology fingerprints. This is the same technique used by commercial tools like BuiltWith and Wappalyzer.

**About page enrichment**: The scraper also tries common "about" page slugs (`/about`, `/about-us`, `/company`, `/who-we-are`) to get richer company context for the AI analysis.

---

## 7. AI Deep Dive — `ai_service.py`

**The prompt engineering approach:**
The system builds a structured context string from all the scraped data and asks Gemini to return a **specific JSON schema**. Strict JSON output means no parsing guesswork.

```
"Return ONLY a JSON object (no markdown, no extra text)"
```

The regex `re.sub(r"```json\s*|\s*```", "", text)` strips any markdown code fences Gemini might add despite instructions.

**Fallback scoring system**: When Gemini is unavailable, a rule-based scorer calculates a digital maturity score:
- Base score: 4
- +2 for social media presence
- +1 for Google Analytics
- +1 for contact info found
- +1 for About page content
- +1 for H1 headings found
- Capped at 10

This ensures the pipeline **never fails completely** — it always produces a report.

---

## 8. PDF Generation Deep Dive — `report.py`

**Why Playwright for PDF instead of a library like ReportLab?**

Playwright renders real HTML + CSS to PDF using Chrome's print engine. This means:
- Google Fonts load correctly (beautiful typography)
- CSS gradients, box shadows, flexbox all work perfectly
- The output looks **exactly** like a designed webpage
- No need to learn a separate PDF layout API

**The PDF structure:**
- **Cover page** (A4 height = 1122px): Dark gradient background, company name, date, industry classification, lead info
- **Page 1** — Executive Summary: AI analysis quote, SVG circular score gauge (pure SVG, no images), technology pills
- **Page 2** — Audit Deep Dive: Strengths/Opportunities 2-column grid, Structural Metadata table, Key Recommendation callout

**SVG Score Gauge** — this is a custom circle progress indicator built purely in SVG:
```svg
<!-- stroke-dasharray="70, 100" means 70% of the circle is filled = score 7/10 -->
<path stroke-dasharray="{score * 10}, 100" ... />
```

---

## 9. Email Service Deep Dive — `email_service.py`

**Three-tier fallback chain:**

| Priority | Method | When Used |
|---|---|---|
| 1st | **Resend API** | `RESEND_API_KEY` is set in .env |
| 2nd | **Gmail SMTP** | `GMAIL_USER` + `GMAIL_APP_PASSWORD` are set |
| 3rd | **Log to file** | Neither credential is configured |

**Gmail App Password** — not the regular Gmail password. You generate a 16-character App Password from Google Account → Security → 2-Step Verification → App Passwords. This is required because Google blocks direct login with regular passwords for SMTP.

**Resend** — a modern email API (similar to SendGrid/Mailgun). PDF is base64-encoded before sending as an attachment. The `from_email` must be a verified domain in Resend.

**HTML email template** — the email body is a full HTML email (table-based layout for email client compatibility) with the PDF attached. Includes: header, personalised greeting, checklist of what's in the report, CTA note, footer.

---

## 10. Frontend Deep Dive — `App.jsx`

**State machine approach:**
The app has 3 distinct visual states controlled by 4 pieces of state:

```
State 1: Form view
  - polling = false, pdfUrl = null
  - Shows the input form

State 2: Processing view  
  - polling = true, pdfUrl = null
  - Shows animated spinner + "Analyzing Digital Presence" message
  - Form is hidden

State 3: Success view
  - polling = false, pdfUrl = "http://localhost:8000/reports/..."
  - Shows PDF iframe + Download button + Make Another Audit button
```

**Polling mechanism:**
```javascript
useEffect(() => {
  let intervalId;
  if (polling && pollEmail) {
    intervalId = setInterval(async () => {
      const res = await axios.get(`/api/report-status?email=${email}`);
      if (data.status === "done" && data.pdfUrl) {
        setPolling(false);
        setPdfUrl(data.pdfUrl);  // ← pdfUrl comes from API, not file_name
      }
    }, 5000);  // poll every 5 seconds
  }
  return () => clearInterval(intervalId);  // cleanup on unmount
}, [polling, pollEmail]);
```

The `useEffect` cleanup function (`return () => clearInterval(intervalId)`) prevents memory leaks if the component unmounts while polling.

**Why React Hook Form?**
- `register()` connects inputs to the form without controlled state
- `handleSubmit()` only fires if validation passes
- `reset()` clears all fields when "Make Another Audit" is clicked
- Zero re-renders while user is typing (unlike `useState` + `onChange`)

**Download PDF button:**
```jsx
<a href={pdfUrl} download target="_blank" rel="noopener noreferrer">
  Download PDF Report
</a>
```
The `download` attribute on an anchor tag triggers a browser file download instead of navigation. `target="_blank"` opens in a new tab as fallback.

---

## 11. CSS Design System — `index.css`

**Design philosophy: Glassmorphism dark theme**

Key CSS techniques used:

- **Glassmorphism card**: `backdrop-filter: blur(20px)` with `background: rgba(255,255,255,0.03)` creates the frosted glass effect
- **Animated background orbs**: `body::before` and `body::after` pseudo-elements with `border-radius: 50%` and `filter: blur(120px)` create the ambient glow
- **CSS custom properties** (`--accent`, `--card-bg`, etc.) allow consistent theming
- **Focus glow ring**: `box-shadow: 0 0 0 4px rgba(56,189,248,0.1)` on input focus
- **Gradient buttons**: `linear-gradient(135deg, #0284c7, #38bdf8)` with `transform: translateY(-2px)` hover lift
- **Spinner animation**: CSS `@keyframes spin` rotating a half-colored border

**Google Fonts used**: Outfit (headings, bold) + Inter (body text) loaded from CDN.

---

## 12. Environment Variables — What Each Does

```env
# .env (backend only, never committed to git)

GEMINI_API_KEY=...      # Google AI Studio key for Gemini 1.5 Flash
                        # Get free at: aistudio.google.com

RESEND_API_KEY=...      # Resend transactional email API key
RESEND_FROM_EMAIL=...   # Must be a verified domain sender in Resend

GMAIL_USER=...          # Your Gmail address (fallback email sender)
GMAIL_APP_PASSWORD=...  # 16-char App Password from Google Account settings
```

**Security**: `.env` is in `.gitignore` — it is never pushed to GitHub. The `.env.example` file shows what keys are needed without real values.

---

## 13. API Endpoints

| Method | Endpoint | What It Does |
|---|---|---|
| `GET` | `/` | Health check → `{"status": "SimpliFiQ Audit API running ✅"}` |
| `POST` | `/api/leads` | Accepts lead data, starts background workflow, returns 202 |
| `GET` | `/api/report-status?email=...` | Returns `{status, pdfUrl, error}` |
| `GET` | `/reports/{filename}` | Serves PDF file directly (static file mount) |
| `GET` | `/docs` | Auto-generated FastAPI Swagger UI |

---

## 14. Error Handling & Resilience

| Failure Scenario | How It's Handled |
|---|---|
| Website unreachable | httpx fails → Playwright fallback → returns empty enrichment, workflow continues |
| Gemini API error | Returns template-based fallback insights, workflow continues |
| Email sending fails | Logs to `email_log.txt`, workflow still marks as "done" |
| PDF generation fails | Marks lead as "error", frontend shows error message |
| User submits bad URL | React Hook Form regex validation blocks submission |
| Network timeout | httpx timeout=12s, Playwright timeout=20s, then graceful failure |

---

## 15. How to Run the Project

### Backend
```bash
cd backend
pip install -r requirements.txt
playwright install chromium        # downloads headless browser
# fill in backend/.env with your keys
python main.py                     # starts on http://localhost:8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev                        # starts on http://localhost:5173
```

### PowerShell shortcut (Windows)
```powershell
# In backend folder:
.\start.ps1
```

---

## 16. Git & Version Control

The project uses Git with the following ignored files:
- `node_modules/` — npm dependencies (reinstallable)
- `__pycache__/` — Python bytecode cache
- `.env` — secret keys
- `reports/*.pdf` — generated reports (ephemeral)
- `email_log.txt`, `leads_log.txt` — runtime logs
- `server_out.txt`, `server_err.txt` — server console logs

A `reports/.gitkeep` file ensures the empty `reports/` folder is tracked by Git (empty folders are ignored by Git by default).

---

## 17. Key Interview Talking Points

1. **"Why async/background tasks?"** — The AI + scraping pipeline takes 10-30 seconds. A synchronous request would timeout. Background tasks let us immediately respond with 202 and let the client poll for completion.

2. **"Why two scraping methods?"** — Many modern websites are SPAs (Single Page Applications) that render content via JavaScript. Plain HTTP requests just get empty HTML. Playwright solves this by running a full browser.

3. **"How does the PDF look so good?"** — Instead of using a PDF library with its own layout constraints, I built a full HTML/CSS page and used Chrome's print engine (via Playwright) to render it. This gives unlimited design freedom.

4. **"What if Gemini is down?"** — The fallback_insights() function calculates scores and generates insights using simple rules based on the scraped data. The report always gets generated.

5. **"How is this secure?"** — API keys are in .env (not in code), .gitignored. CORS is configured. In production, CORS would be locked to the specific frontend domain. The reports directory only serves files, not directory listings.

6. **"What would you improve in production?"** — 
   - Replace in-memory `lead_status` dict with Redis
   - Add a database to persist leads and reports
   - Add rate limiting (to prevent abuse)
   - Deploy backend on Railway/Render, frontend on Vercel
   - Add authentication so only verified users access their reports
   - Restrict CORS to the production domain
