import time
from pathlib import Path
from playwright.async_api import async_playwright

REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)

def _score_color(score: int) -> str:
    if score >= 8: return "#0ea5e9"   # Premium Blue/Cyan
    if score >= 6: return "#f59e0b"   # Amber
    return "#ef4444"                  # Red

def _build_html(lead: dict, enriched: dict, ai: dict) -> str:
    company = lead["companyName"]
    date_str = time.strftime("%B %d, %Y")
    score = ai.get("digital_maturity_score", 5)
    score_color = _score_color(score)

    def li_items(lst, bullet_color="#0ea5e9"):
        return "".join(f'<li style="position:relative; padding-left:24px; margin-bottom:12px; font-size:13px; color:#334155; line-height:1.6;"><span style="position:absolute; left:0; top:2px; color:{bullet_color}; font-size:16px;">✦</span>{item}</li>' for item in (lst or []) if item)

    def kv_row(label, value):
        if not value: return ""
        return f'<div style="display:flex; justify-content:space-between; padding:12px 0; border-bottom:1px solid #f1f5f9;"><span style="color:#64748b; font-size:13px; font-weight:600; width:35%;">{label}</span><span style="color:#0f172a; font-size:13px; font-weight:500; text-align:right; width:65%; word-break:break-word;">{value}</span></div>'

    tech_pills = "".join(
        f'<span style="background:linear-gradient(135deg, #f0f9ff, #e0f2fe); color:#0369a1; border:1px solid #bae6fd; font-size:11px; font-weight:700; padding:6px 14px; border-radius:24px; letter-spacing:0.5px; text-transform:uppercase; margin-right:8px; margin-bottom:8px; display:inline-block; box-shadow:0 2px 4px rgba(14,165,233,0.1);">{t}</span>' for t in (enriched.get("technologies") or [])
    ) or '<span style="color:#94a3b8; font-style:italic; font-size:13px;">No technologies auto-detected</span>'

    # Simplified Score Gauge using pure SVG
    gauge_svg = f"""
    <svg viewBox="0 0 36 36" style="width:140px; height:140px;">
      <path class="circle-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#f1f5f9" stroke-width="3" />
      <path class="circle" stroke-dasharray="{score * 10}, 100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="{score_color}" stroke-width="3" stroke-linecap="round" />
      <text x="18" y="20.5" font-family="Inter" font-weight="900" font-size="10" fill="#0f172a" text-anchor="middle">{score}<tspan font-size="4" font-weight="600" fill="#64748b" dy="-3">/10</tspan></text>
    </svg>
    """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Discovery Audit Report – {company}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&family=Inter:wght@400;500;600&display=swap');
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Inter', sans-serif; font-size: 14px; color: #334155; background: #ffffff; }}

  /* Cover Page */
  .cover {{
    height: 1122px; width: 794px; /* A4 */
    background: linear-gradient(135deg, #020617 0%, #0f172a 40%, #1e1b4b 100%);
    position: relative; overflow: hidden; page-break-after: always;
    display: flex; flex-direction: column; justify-content: center; padding: 100px;
  }}
  .cover::before {{ content:''; position:absolute; top:-150px; right:-100px; width:600px; height:600px; border-radius:50%; background:radial-gradient(circle, rgba(14,165,233,0.15) 0%, rgba(0,0,0,0) 70%); }}
  .cover::after {{ content:''; position:absolute; bottom:-100px; left:-100px; width:500px; height:500px; border-radius:50%; background:radial-gradient(circle, rgba(99,102,241,0.1) 0%, rgba(0,0,0,0) 70%); }}
  
  .badge {{ display:inline-block; border:1px solid rgba(255,255,255,0.1); background:rgba(255,255,255,0.05); backdrop-filter:blur(10px); color:#38bdf8; font-family:'Outfit'; font-size:12px; font-weight:700; letter-spacing:3px; text-transform:uppercase; padding:10px 24px; border-radius:30px; margin-bottom:40px; }}
  .cover h1 {{ font-family:'Outfit'; font-size:64px; font-weight:900; color:#ffffff; line-height:1.1; margin-bottom:24px; letter-spacing:-1px; }}
  .cover h2 {{ font-family:'Outfit'; font-size:28px; font-weight:400; color:#94a3b8; margin-bottom:60px; }}
  
  .meta-grid {{ display:grid; grid-template-columns:1fr; gap:20px; border-top:1px solid rgba(255,255,255,0.1); padding-top:40px; }}
  .meta-item {{ display:flex; flex-direction:column; }}
  .meta-label {{ font-size:11px; font-weight:700; color:#64748b; text-transform:uppercase; letter-spacing:1px; margin-bottom:4px; }}
  .meta-value {{ font-size:16px; font-weight:500; color:#f8fafc; }}

  /* Content Pages */
  .page {{ width:794px; min-height:1122px; padding:70px; position:relative; page-break-after:always; background:#ffffff; }}
  .page-header {{ display:flex; justify-content:space-between; align-items:flex-end; border-bottom:2px solid #0f172a; padding-bottom:24px; margin-bottom:40px; }}
  .page-header-title {{ font-family:'Outfit'; font-size:20px; font-weight:800; color:#0f172a; text-transform:uppercase; letter-spacing:1px; }}
  .page-header-company {{ font-size:13px; font-weight:500; color:#64748b; }}
  
  /* Sections */
  .section {{ margin-bottom:48px; }}
  .section-title {{ display:flex; align-items:center; gap:16px; font-family:'Outfit'; font-size:20px; font-weight:800; color:#0f172a; margin-bottom:24px; }}
  .section-num {{ width:32px; height:32px; background:#0f172a; color:#ffffff; border-radius:8px; display:flex; justify-content:center; align-items:center; font-size:14px; font-weight:800; }}
  
  /* Cards */
  .card {{ background:#f8fafc; border:1px solid #e2e8f0; border-radius:16px; padding:30px; box-shadow:0 4px 6px -1px rgba(0,0,0,0.02); }}
  
  /* Grid Layouts */
  .two-col {{ display:grid; grid-template-columns:1fr 1fr; gap:30px; }}
  
  /* Feature Box */
  .callout {{ background:linear-gradient(135deg, #f0fdf4, #dcfce7); border-left:4px solid #22c55e; padding:24px; border-radius:0 12px 12px 0; font-size:15px; color:#166534; line-height:1.7; font-weight:500; margin-bottom:30px; }}
  .alert-box {{ background:linear-gradient(135deg, #fffbeb, #fef3c7); border-left:4px solid #f59e0b; padding:24px; border-radius:0 12px 12px 0; font-size:15px; color:#92400e; line-height:1.7; font-weight:500; }}
  
  .footer {{ position:absolute; bottom:50px; left:70px; right:70px; display:flex; justify-content:space-between; align-items:center; font-size:11px; font-weight:600; color:#94a3b8; border-top:1px solid #e2e8f0; padding-top:20px; }}
</style>
</head>
<body>

<!-- Cover Page -->
<div class="cover">
  <div class="badge">SimpliFiQ Report</div>
  <h1>Discovery Audit<br/><span style="color:#38bdf8;">Analysis</span></h1>
  <h2>Prepared exclusively for {company}</h2>
  
  <div class="meta-grid" style="grid-template-columns: 1fr 1fr; margin-top: auto;">
    <div class="meta-item">
      <span class="meta-label">Prepared For</span>
      <span class="meta-value">{lead['name']} ({lead['email']})</span>
    </div>
    <div class="meta-item">
      <span class="meta-label">Web Ecosystem</span>
      <span class="meta-value">{enriched.get('url', lead['website'])}</span>
    </div>
    <div class="meta-item" style="margin-top:24px;">
      <span class="meta-label">Date Generated</span>
      <span class="meta-value">{date_str}</span>
    </div>
    <div class="meta-item" style="margin-top:24px;">
      <span class="meta-label">Industry Classification</span>
      <span class="meta-value">{ai.get('industry_vertical', 'Technology / Services')}</span>
    </div>
  </div>
</div>

<!-- Page 1: Overivew -->
<div class="page">
  <div class="page-header">
    <div class="page-header-title">Executive Summary</div>
    <div class="page-header-company">{company}</div>
  </div>
  
  <div class="section">
    <div class="section-title"><div class="section-num">1</div>AI Strategic Analysis</div>
    <div class="callout">"{ai.get('executive_summary', 'Detailed analysis of web presence and digital footprint.')}"</div>
    
    <div class="card" style="display:flex; align-items:center; gap:40px; margin-top:30px;">
      {gauge_svg}
      <div>
        <div style="font-family:'Outfit'; font-size:24px; font-weight:800; color:#0f172a; margin-bottom:8px;">{ai.get('digital_maturity_label', 'Developing')} Digital Presence</div>
        <p style="color:#475569; font-size:14px; line-height:1.7; margin-bottom:16px;">{ai.get('digital_maturity_reasoning', 'Scores are calculated based on UI/UX, technology, and SEO.')}</p>
        <p style="color:#64748b; font-size:13px; font-style:italic;"><strong>Competitive Context:</strong> {ai.get('competitor_landscape', '')}</p>
      </div>
    </div>
  </div>

  <div class="section">
    <div class="section-title"><div class="section-num">2</div>Website Engine & Architecture</div>
    <div class="card">
      <div style="margin-bottom:20px; font-family:'Outfit'; font-size:16px; font-weight:700; color:#0f172a;">Detected Technology Stack</div>
      <div>{tech_pills}</div>
    </div>
  </div>
  
  <div class="footer">
    <span>SimpliFiQ Automated Intelligence</span>
    <span>Page 1 / 2</span>
  </div>
</div>

<!-- Page 2: Recommendations -->
<div class="page">
  <div class="page-header">
    <div class="page-header-title">Audit Deep Dive</div>
    <div class="page-header-company">{company}</div>
  </div>

  <div class="two-col section">
    <div class="card" style="background:#f0fdf4; border-color:#bbf7d0;">
      <div style="font-family:'Outfit'; font-size:18px; font-weight:800; color:#166534; margin-bottom:20px; border-bottom:1px solid #dcfce7; padding-bottom:12px;">Key Strengths</div>
      <ul style="list-style:none; padding:0;">
        {li_items(ai.get("strengths") or [], "#22c55e")}
      </ul>
    </div>
    
    <div class="card" style="background:#fefce8; border-color:#fef08a;">
      <div style="font-family:'Outfit'; font-size:18px; font-weight:800; color:#854d0e; margin-bottom:20px; border-bottom:1px solid #fef08a; padding-bottom:12px;">Growth Opportunities</div>
      <ul style="list-style:none; padding:0;">
        {li_items(ai.get("opportunities") or [], "#eab308")}
      </ul>
    </div>
  </div>

  <div class="section">
    <div class="section-title"><div class="section-num">3</div>Structural Metadata</div>
    <div class="card">
      {kv_row("Primary SEO Title", enriched.get("title") or "Not configured properly.")}
      {kv_row("Meta Description", enriched.get("description") or "Not configured properly.")}
      {kv_row("H1 Headers", " • ".join(enriched.get("h1") or []) or "No H1 tags found.")}
      {kv_row("Navigation Assets", " • ".join(enriched.get("nav_links") or []) or "No primary nav detected.")}
    </div>
  </div>

  <div class="section">
    <div class="section-title"><div class="section-num">4</div>Primary Recommendation</div>
    <div class="alert-box">
      🔥 <strong>Immediate Action Required:</strong><br/><br/>
      {ai.get('key_recommendation', 'Establish a comprehensive digital strategy to improve your online brand identity and increase conversions.')}
    </div>
  </div>

  <div class="footer">
    <span>SimpliFiQ Automated Intelligence</span>
    <span>Page 2 / 2</span>
  </div>
</div>

</body>
</html>"""

async def generate_pdf_report(lead: dict, enriched: dict, ai: dict) -> str:
    html = _build_html(lead, enriched, ai)
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in lead["companyName"])
    file_name = f"AuditReport_{safe_name}_{int(time.time())}.pdf"
    output_path = REPORTS_DIR / file_name

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page()
        await page.set_content(html, wait_until="networkidle")
        await page.pdf(
            path=str(output_path),
            format="A4",
            print_background=True,
            margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
        )
        await browser.close()

    print(f"  ✅ Premium PDF saved: {file_name}")
    return file_name
