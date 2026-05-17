from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from services.enrichment import enrich_company
from services.ai_service import generate_ai_insights
from services.report import generate_pdf_report
from services.email_service import send_audit_email
from services.google_integration import append_to_sheet, upload_to_drive

app = FastAPI(title="SimpliFiQ Audit API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)
app.mount("/reports", StaticFiles(directory=str(REPORTS_DIR)), name="reports")

# In-memory lead status store
lead_status: dict = {}


class LeadInput(BaseModel):
    name: str
    email: str
    companyName: str
    website: str


@app.get("/")
async def root():
    return {"status": "SimpliFiQ Audit API running ✅"}


@app.post("/api/leads", status_code=202)
async def submit_lead(lead: LeadInput, background_tasks: BackgroundTasks):
    lead_status[lead.email] = {"status": "processing", "file_name": None, "error": None}
    background_tasks.add_task(process_lead_workflow, lead.model_dump())
    return {"message": "Lead received, processing started"}


@app.get("/api/report-status")
async def report_status(email: str):
    entry = lead_status.get(email)
    if not entry:
        return {"status": "not_found"}
    pdf_url = f"http://localhost:8000/reports/{entry['file_name']}" if entry["file_name"] else None
    return {"status": entry["status"], "pdfUrl": pdf_url, "error": entry.get("error")}


async def process_lead_workflow(lead_dict: dict):
    email = lead_dict["email"]
    try:
        print(f"\n🚀 Starting workflow for {email}")

        # 1. Scrape
        print("🔍 Scraping website data...")
        enriched = await enrich_company(lead_dict["website"])

        # 2. AI Insights
        print("🤖 Calling Gemini for AI insights...")
        ai_insights = await generate_ai_insights(lead_dict, enriched)

        # 3. Generate PDF
        print("📄 Generating PDF with Playwright...")
        file_name = await generate_pdf_report(lead_dict, enriched, ai_insights)

        # 4. Save to Google Drive
        print("☁️ Archiving PDF to Google Drive...")
        pdf_full_path = str(REPORTS_DIR / file_name)
        upload_to_drive(file_name, pdf_full_path)

        # 5. Send Email (non-critical)
        print("📧 Sending email via Resend...")
        try:
            await send_audit_email(lead_dict, file_name)
        except Exception as e:
            print(f"⚠️  Email failed (non-critical): {e}")

        # 6. Log to Google Sheets
        print("📊 Logging to Google Sheets...")
        append_to_sheet(lead_dict, "Completed")

        lead_status[email] = {"status": "done", "file_name": file_name, "error": None}
        print(f"✅ Workflow complete for {email}. File: {file_name}")

    except Exception as e:
        import traceback
        print(f"❌ Workflow error for {email}: {e}")
        traceback.print_exc()
        lead_status[email] = {"status": "error", "file_name": None, "error": str(e)}
        # Log failure to Google Sheets
        append_to_sheet(lead_dict, f"Failed: {str(e)[:100]}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
