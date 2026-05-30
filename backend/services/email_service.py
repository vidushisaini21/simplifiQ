import os
import base64
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

REPORTS_DIR = Path("reports")


async def send_audit_email(lead: dict, file_name: str):
    """
    Try Resend first (if key set), then fall back to Gmail REST API (if OAuth config set),
    then fall back to Gmail SMTP, and finally log to email_log.txt.
    """
    resend_key       = os.getenv("RESEND_API_KEY", "")
    gmail_client_id  = os.getenv("GMAIL_CLIENT_ID", "")
    gmail_client_sec = os.getenv("GMAIL_CLIENT_SECRET", "")
    gmail_refresh    = os.getenv("GMAIL_REFRESH_TOKEN", "")
    gmail_user       = os.getenv("GMAIL_USER", "")
    gmail_pass       = os.getenv("GMAIL_APP_PASSWORD", "")  # Gmail App Password (not account password)

    # ── 1. Resend API ──────────────────────────────────────────
    if resend_key and not resend_key.startswith("your_"):
        try:
            await _send_via_resend(lead, file_name, resend_key)
            return
        except Exception as e:
            print(f"  ⚠️  Resend failed: {e} — trying Gmail REST API...")

    # ── 2. Gmail REST API ──────────────────────────────────────
    if gmail_client_id and gmail_client_sec and gmail_refresh and gmail_user:
        try:
            await _send_via_gmail_api(lead, file_name, gmail_client_id, gmail_client_sec, gmail_refresh, gmail_user)
            return
        except Exception as e:
            print(f"  ⚠️  Gmail REST API failed: {e} — trying Gmail SMTP...")

    # ── 3. Gmail SMTP fallback ─────────────────────────────────
    if gmail_user and gmail_pass and not gmail_pass.startswith("your_"):
        try:
            _send_via_gmail(lead, file_name, gmail_user, gmail_pass)
            return
        except Exception as e:
            print(f"  ⚠️  Gmail SMTP failed: {e} — logging to file...")
            print("  💡 Tip: If you are deployed on Render's free tier, outbound SMTP ports (465/587) are blocked.")
            print("     To send emails, use Resend API with a verified custom domain, or upgrade Render to a paid plan.")

    # ── 4. Local log fallback ──────────────────────────────────
    _log_fallback(lead, file_name)
    has_credentials = (
        (resend_key and not resend_key.startswith("your_")) or
        (gmail_client_id and gmail_client_sec and gmail_refresh) or
        (gmail_user and gmail_pass and not gmail_pass.startswith("your_"))
    )
    if has_credentials:
        print("  📝 Email sending failed — logged details to email_log.txt")
    else:
        print("  📝 No email credentials set — logged details to email_log.txt")
        print("  👉 Set GMAIL_USER + GMAIL_APP_PASSWORD (or Gmail OAuth credentials) in .env to enable email")


async def _send_via_resend(lead: dict, file_name: str, api_key: str):
    import resend
    resend.api_key = api_key

    pdf_path = REPORTS_DIR / file_name
    with open(pdf_path, "rb") as f:
        pdf_b64 = base64.b64encode(f.read()).decode()

    from_email = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")

    params = {
        "from": f"SimpliFiQ Audit <{from_email}>",
        "to":   [lead["email"]],
        "subject": f"📊 Your Discovery Audit — {lead['companyName']}",
        "html": _build_email_html(lead),
        "attachments": [{"filename": file_name, "content": pdf_b64}],
    }
    resend.Emails.send(params)
    print(f"  ✅ Email sent via Resend to {lead['email']}")


def _send_via_gmail(lead: dict, file_name: str, gmail_user: str, gmail_pass: str):
    """Send email using Gmail SMTP with App Password."""
    to_email  = lead["email"]
    pdf_path  = REPORTS_DIR / file_name

    msg = MIMEMultipart("mixed")
    msg["From"]    = f"SimpliFiQ Audit <{gmail_user}>"
    msg["To"]      = to_email
    msg["Subject"] = f"📊 Your Discovery Audit Report — {lead['companyName']}"

    # HTML body
    body = MIMEText(_build_email_html(lead), "html")
    msg.attach(body)

    # PDF attachment
    with open(pdf_path, "rb") as f:
        pdf_data = f.read()
    attachment = MIMEBase("application", "octet-stream")
    attachment.set_payload(pdf_data)
    encoders.encode_base64(attachment)
    attachment.add_header("Content-Disposition", f'attachment; filename="{file_name}"')
    msg.attach(attachment)

    # Send via Gmail SMTP SSL
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
        server.login(gmail_user, gmail_pass)
        server.sendmail(gmail_user, to_email, msg.as_string())

    print(f"  ✅ Email sent via Gmail SMTP to {to_email}")


async def _send_via_gmail_api(lead: dict, file_name: str, client_id: str, client_secret: str, refresh_token: str, gmail_user: str):
    """Send email using Gmail REST API via HTTPS."""
    import httpx
    
    # 1. Exchange refresh token for access token
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        res = await client.post(token_url, data=token_data)
        res.raise_for_status()
        access_token = res.json()["access_token"]
        
        # 2. Build MIME message
        to_email  = lead["email"]
        pdf_path  = REPORTS_DIR / file_name

        msg = MIMEMultipart("mixed")
        msg["From"]    = f"SimpliFiQ Audit <{gmail_user}>"
        msg["To"]      = to_email
        msg["Subject"] = f"📊 Your Discovery Audit Report — {lead['companyName']}"

        # HTML body
        body = MIMEText(_build_email_html(lead), "html")
        msg.attach(body)

        # PDF attachment
        with open(pdf_path, "rb") as f:
            pdf_data = f.read()
        attachment = MIMEBase("application", "octet-stream")
        attachment.set_payload(pdf_data)
        encoders.encode_base64(attachment)
        attachment.add_header("Content-Disposition", f'attachment; filename="{file_name}"')
        msg.attach(attachment)

        # 3. Base64url encode the message
        raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
        
        # 4. Post message to Gmail API
        gmail_send_url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        payload = {"raw": raw_message}
        
        res_send = await client.post(gmail_send_url, headers=headers, json=payload)
        res_send.raise_for_status()

    print(f"  ✅ Email sent via Gmail REST API to {to_email}")


def _log_fallback(lead: dict, file_name: str):
    with open("email_log.txt", "a", encoding="utf-8") as f:
        f.write(
            f"{datetime.now().isoformat()} | {lead['name']} | "
            f"{lead['email']} | {lead['companyName']} | {file_name}\n"
        )


def _build_email_html(lead: dict) -> str:
    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"/></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:'Helvetica Neue',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f3f4f6;padding:40px 20px;">
    <tr><td>
      <table width="580" align="center" cellpadding="0" cellspacing="0"
        style="background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.08);">

        <!-- Header -->
        <tr>
          <td style="background:linear-gradient(135deg,#312e81,#4f46e5,#7c3aed);padding:40px;text-align:center;">
            <p style="color:#c7d2fe;font-size:12px;letter-spacing:2px;text-transform:uppercase;margin:0 0 12px;">SimpliFiQ · AI Audit Pipeline</p>
            <h1 style="color:#fff;font-size:26px;margin:0 0 8px;font-weight:800;">📊 Your Audit Report is Ready</h1>
            <p style="color:#a5b4fc;font-size:16px;margin:0;">Personalized insights for <strong style="color:#fff;">{lead['companyName']}</strong></p>
          </td>
        </tr>

        <!-- Body -->
        <tr>
          <td style="padding:36px 40px;">
            <p style="color:#1f2937;font-size:16px;margin:0 0 20px;">Hi <strong>{lead['name']}</strong>,</p>
            <p style="color:#4b5563;font-size:14px;line-height:1.75;margin:0 0 16px;">
              Your AI-powered <strong>Discovery Audit Report</strong> for <strong>{lead['companyName']}</strong> has been
              generated and is <strong>attached to this email as a PDF</strong>.
            </p>
            <p style="color:#4b5563;font-size:14px;line-height:1.75;margin:0 0 24px;">
              The report includes:
            </p>
            <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:24px;">
              {"".join(f'''<tr><td style="padding:6px 0;">
                <span style="display:inline-block;width:24px;height:24px;background:#ede9fe;border-radius:6px;text-align:center;line-height:24px;margin-right:10px;font-size:14px;">✓</span>
                <span style="color:#374151;font-size:13px;">{item}</span>
              </td></tr>''' for item in [
                  "Website & meta content analysis",
                  "AI-generated executive summary",
                  "Digital maturity score (1–10)",
                  "Technology stack detection",
                  "Strengths & opportunities",
                  "Strategic recommendations",
              ])}
            </table>

            <!-- CTA note -->
            <div style="background:#f0fdf4;border:1px solid #a7f3d0;border-radius:10px;padding:16px 20px;margin-bottom:24px;">
              <p style="color:#065f46;font-size:13px;margin:0;">
                📎 <strong>Check your email attachments</strong> for the PDF report. If you don't see it, check your Spam folder.
              </p>
            </div>

            <p style="color:#9ca3af;font-size:13px;margin:0;">
              Reply to this email if you have any questions. We're happy to discuss the findings.
            </p>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="background:#f9fafb;border-top:1px solid #e5e7eb;padding:20px 40px;text-align:center;">
            <p style="color:#9ca3af;font-size:11px;margin:0;">
              🔒 Secure, automated process · Powered by SimpliFiQ<br/>
              This report was generated automatically using public web data.
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""
