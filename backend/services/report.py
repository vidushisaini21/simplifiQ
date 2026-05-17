import time
from pathlib import Path
from playwright.async_api import async_playwright


REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)


def _score_color(score: int) -> str:
    if score >= 8: return "#059669"   # green
    if score >= 6: return "#d97706"   # amber
    return "#dc2626"                   # red


def _score_arc(score: int) -> str:
    """SVG arc for the gauge."""
    pct = score / 10
    angle = pct * 180  # 0–180 degrees
    r = 54
    cx, cy = 70, 70
    import math
    rad = math.radians(180 - angle)
    x = cx + r * math.cos(rad)
    y = cy - r * math.sin(rad)
    large = 1 if angle > 180 else 0
    return f"M {cx - r} {cy} A {r} {r} 0 {large} 1 {x:.2f} {y:.2f}"


def _build_html(lead: dict, enriched: dict, ai: dict) -> str:
    company = lead["companyName"]
    date_str = time.strftime("%B %d, %Y")
    score = ai.get("digital_maturity_score", 5)
    score_color = _score_color(score)
    arc_path = _score_arc(score)

    def li_items(lst):
        return "".join(f'<li>{item}</li>' for item in (lst or []) if item)

    def kv_row(label, value):
        if not value: return ""
        return f'<tr><td class="kv-key">{label}</td><td class="kv-val">{value}</td></tr>'

    tech_pills = "".join(
        f'<span class="pill">{t}</span>' for t in (enriched.get("technologies") or [])
    ) or '<span class="muted">No technologies auto-detected</span>'

    social_rows = "".join(
        kv_row(k, f'<a href="{v}" style="color:#4f46e5">{v[:50]}</a>')
        for k, v in (enriched.get("social_links") or {}).items()
    ) or '<tr><td colspan="2" class="muted">No social media links detected on homepage</td></tr>'

    emails = enriched.get("contact", {}).get("emails", [])
    phones = enriched.get("contact", {}).get("phones", [])

    h1_items = li_items(enriched.get("h1") or [])
    h2_items = li_items((enriched.get("h2") or [])[:6])
    h3_items = li_items((enriched.get("h3") or [])[:5])
    nav_items = li_items(enriched.get("nav_links") or [])

    about_text = enriched.get("about_text") or enriched.get("body_text") or "Content not available from public pages."
    summary_text = ai.get("executive_summary", "")
    strengths = li_items(ai.get("strengths") or [])
    opportunities = li_items(ai.get("opportunities") or [])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Discovery Audit Report – {company}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Inter', Arial, sans-serif; font-size: 13px; color: #1f2937; background: #fff; }}

  /* ── Cover ── */
  .cover {{
    height: 100vh; min-height: 1122px;
    background: linear-gradient(135deg, #312e81 0%, #4f46e5 50%, #7c3aed 100%);
    display: flex; flex-direction: column; justify-content: center; align-items: flex-start;
    padding: 80px; position: relative; overflow: hidden; page-break-after: always;
  }}
  .cover::before {{
    content: ''; position: absolute; top: -120px; right: -120px;
    width: 500px; height: 500px; border-radius: 50%;
    background: rgba(255,255,255,0.06);
  }}
  .cover::after {{
    content: ''; position: absolute; bottom: -80px; left: 200px;
    width: 300px; height: 300px; border-radius: 50%;
    background: rgba(255,255,255,0.04);
  }}
  .cover-badge {{
    background: rgba(255,255,255,0.15); color: #c7d2fe;
    font-size: 10px; font-weight: 600; letter-spacing: 2px; text-transform: uppercase;
    padding: 6px 14px; border-radius: 20px; margin-bottom: 32px;
    border: 1px solid rgba(255,255,255,0.2);
  }}
  .cover h1 {{ color: #fff; font-size: 52px; font-weight: 900; line-height: 1.1; margin-bottom: 20px; }}
  .cover-subtitle {{ color: #a5b4fc; font-size: 20px; font-weight: 400; margin-bottom: 48px; }}
  .cover-divider {{ width: 60px; height: 3px; background: #818cf8; margin-bottom: 40px; border-radius: 2px; }}
  .cover-meta {{ color: rgba(255,255,255,0.7); font-size: 13px; line-height: 2; }}
  .cover-meta strong {{ color: #fff; }}
  .cover-footer {{
    position: absolute; bottom: 40px; left: 80px; right: 80px;
    display: flex; justify-content: space-between; align-items: center;
    border-top: 1px solid rgba(255,255,255,0.15); padding-top: 20px;
  }}
  .cover-footer span {{ color: rgba(255,255,255,0.5); font-size: 11px; }}

  /* ── Content pages ── */
  .page {{
    padding: 60px; min-height: 1122px; position: relative;
    page-break-after: always;
  }}
  .page-header {{
    display: flex; justify-content: space-between; align-items: center;
    border-bottom: 2px solid #4f46e5; padding-bottom: 16px; margin-bottom: 32px;
  }}
  .page-header-title {{ color: #4f46e5; font-size: 11px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; }}
  .page-header-company {{ color: #9ca3af; font-size: 11px; }}
  .page-footer {{
    position: absolute; bottom: 30px; left: 60px; right: 60px;
    display: flex; justify-content: space-between; align-items: center;
    border-top: 1px solid #e5e7eb; padding-top: 12px;
    color: #9ca3af; font-size: 10px;
  }}

  /* ── Section titles ── */
  .section {{ margin-bottom: 36px; }}
  .section-title {{
    font-size: 16px; font-weight: 800; color: #1e1b4b;
    margin-bottom: 14px; display: flex; align-items: center; gap: 10px;
  }}
  .section-num {{
    background: linear-gradient(135deg, #4f46e5, #7c3aed);
    color: white; width: 26px; height: 26px; border-radius: 6px;
    display: flex; align-items: center; justify-content: center;
    font-size: 12px; font-weight: 700; flex-shrink: 0;
  }}
  .section-divider {{ height: 1px; background: #e5e7eb; margin: 0 0 16px 0; }}

  /* ── Cards ── */
  .card {{
    background: #f9fafb; border: 1px solid #e5e7eb;
    border-radius: 12px; padding: 20px; margin-bottom: 16px;
  }}
  .card-purple {{ background: #f5f3ff; border-color: #c4b5fd; }}

  /* ── KV table ── */
  .kv-table {{ width: 100%; border-collapse: collapse; }}
  .kv-table tr {{ border-bottom: 1px solid #f3f4f6; }}
  .kv-table tr:last-child {{ border-bottom: none; }}
  .kv-key {{ color: #6b7280; font-weight: 600; font-size: 12px; padding: 8px 12px 8px 0; width: 160px; vertical-align: top; }}
  .kv-val {{ color: #1f2937; font-size: 12px; padding: 8px 0; }}

  /* ── Lists ── */
  .styled-list {{ list-style: none; padding: 0; }}
  .styled-list li {{
    padding: 7px 0 7px 20px; position: relative; color: #374151;
    font-size: 12.5px; border-bottom: 1px solid #f3f4f6; line-height: 1.5;
  }}
  .styled-list li:last-child {{ border-bottom: none; }}
  .styled-list li::before {{
    content: '▸'; position: absolute; left: 0; color: #4f46e5; font-size: 10px; top: 9px;
  }}
  .green-list li::before {{ color: #059669; }}
  .amber-list li::before {{ color: #d97706; }}

  /* ── Score gauge ── */
  .score-section {{
    display: flex; align-items: center; gap: 32px;
    background: linear-gradient(135deg, #f5f3ff, #ede9fe);
    border: 1px solid #c4b5fd; border-radius: 12px; padding: 24px;
  }}
  .gauge-wrap {{ text-align: center; flex-shrink: 0; }}
  .gauge-wrap svg {{ display: block; margin: 0 auto; }}
  .gauge-label {{ font-size: 11px; color: #6b7280; margin-top: 6px; }}
  .score-text {{ font-size: 11.5px; color: #374151; line-height: 1.7; }}
  .score-text strong {{ color: #4f46e5; }}
  .maturity-badge {{
    display: inline-block; padding: 4px 12px; border-radius: 20px;
    font-size: 11px; font-weight: 700; color: white;
    background: {score_color}; margin-bottom: 10px;
  }}

  /* ── Pills ── */
  .pill-wrap {{ display: flex; flex-wrap: wrap; gap: 8px; }}
  .pill {{
    background: #ede9fe; color: #4f46e5; font-size: 11px; font-weight: 600;
    padding: 5px 12px; border-radius: 20px; border: 1px solid #c4b5fd;
  }}

  /* ── Summary box ── */
  .summary-box {{
    background: linear-gradient(135deg, #f0fdf4, #dcfce7);
    border-left: 4px solid #059669; border-radius: 8px;
    padding: 16px 20px; font-size: 13px; color: #065f46; line-height: 1.7;
    font-style: italic;
  }}

  /* ── Rec box ── */
  .rec-box {{
    background: linear-gradient(135deg, #fffbeb, #fef3c7);
    border-left: 4px solid #d97706; border-radius: 8px;
    padding: 16px 20px; font-size: 13px; color: #92400e; line-height: 1.7;
  }}

  .muted {{ color: #9ca3af; font-style: italic; }}
  .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
</style>
</head>
<body>

<!-- ═══════════════ COVER ═══════════════ -->
<div class="cover">
  <div class="cover-badge">SimpliFiQ · AI Discovery Audit</div>
  <h1>Discovery<br/>Audit Report</h1>
  <p class="cover-subtitle">Prepared for {company}</p>
  <div class="cover-divider"></div>
  <div class="cover-meta">
    <div><strong>Contact Name:</strong> {lead['name']}</div>
    <div><strong>Email:</strong> {lead['email']}</div>
    <div><strong>Website Analyzed:</strong> {enriched.get('url', lead['website'])}</div>
    <div><strong>Report Date:</strong> {date_str}</div>
    <div><strong>Industry:</strong> {ai.get('industry_vertical', 'Business Services')}</div>
  </div>
  <div class="cover-footer">
    <span>Confidential · SimpliFiQ Automated Audit Pipeline</span>
    <span>AI-Powered · {date_str}</span>
  </div>
</div>

<!-- ═══════════════ PAGE 1: OVERVIEW + AI SUMMARY ═══════════════ -->
<div class="page">
  <div class="page-header">
    <span class="page-header-title">Prospect Information & AI Summary</span>
    <span class="page-header-company">{company} · {date_str}</span>
  </div>

  <!-- Prospect Info -->
  <div class="section">
    <div class="section-title"><div class="section-num">1</div>Prospect Information</div>
    <div class="section-divider"></div>
    <div class="card">
      <table class="kv-table">
        {kv_row("Full Name", lead.get("name"))}
        {kv_row("Email", lead.get("email"))}
        {kv_row("Company", lead.get("companyName"))}
        {kv_row("Website", lead.get("website"))}
        {kv_row("Industry", ai.get("industry_vertical", "Business Services"))}
      </table>
    </div>
  </div>

  <!-- AI Executive Summary -->
  <div class="section">
    <div class="section-title"><div class="section-num">2</div>AI Executive Summary</div>
    <div class="section-divider"></div>
    <div class="summary-box">{summary_text or 'AI summary not available.'}</div>
    <br/>
    <div class="score-section">
      <div class="gauge-wrap">
        <svg width="140" height="80" viewBox="0 0 140 80">
          <!-- Background arc -->
          <path d="M 16 70 A 54 54 0 0 1 124 70" fill="none" stroke="#e5e7eb" stroke-width="10" stroke-linecap="round"/>
          <!-- Score arc -->
          <path d="{arc_path}" fill="none" stroke="{score_color}" stroke-width="10" stroke-linecap="round"/>
          <!-- Score text -->
          <text x="70" y="65" text-anchor="middle" font-size="22" font-weight="900" fill="{score_color}" font-family="Inter,Arial">{score}</text>
          <text x="70" y="78" text-anchor="middle" font-size="9" fill="#9ca3af" font-family="Inter,Arial">out of 10</text>
        </svg>
        <div class="gauge-label">Digital Maturity Score</div>
      </div>
      <div class="score-text">
        <div class="maturity-badge">{ai.get('digital_maturity_label', 'Developing')}</div>
        <div>{ai.get('digital_maturity_reasoning', 'Score based on web presence evaluation.')}</div>
        <br/>
        <div><strong>Competitor Context:</strong> {ai.get('competitor_landscape', 'N/A')}</div>
      </div>
    </div>
  </div>

  <div class="page-footer">
    <span>SimpliFiQ Discovery Audit Report</span>
    <span>Page 1</span>
  </div>
</div>

<!-- ═══════════════ PAGE 2: SCRAPED WEBSITE DATA ═══════════════ -->
<div class="page">
  <div class="page-header">
    <span class="page-header-title">Website Content Analysis</span>
    <span class="page-header-company">{company} · {date_str}</span>
  </div>

  <!-- Meta -->
  <div class="section">
    <div class="section-title"><div class="section-num">3</div>Website Meta & Description</div>
    <div class="section-divider"></div>
    <div class="card">
      <table class="kv-table">
        {kv_row("Page Title", enriched.get("title") or "Not found")}
        {kv_row("Meta Description", enriched.get("description") or "Not found")}
        {kv_row("OG Title", enriched.get("og_title") or "Not set")}
        {kv_row("Meta Keywords", ', '.join(enriched.get('keywords') or []) or "Not set")}
      </table>
    </div>
  </div>

  <!-- Headings -->
  <div class="section">
    <div class="section-title"><div class="section-num">4</div>Page Headings & Structure</div>
    <div class="section-divider"></div>
    <div class="two-col">
      <div>
        <div style="font-weight:700;font-size:12px;color:#4f46e5;margin-bottom:8px;">H1 — Primary Headlines</div>
        <ul class="styled-list">
          {h1_items or '<li class="muted">None detected</li>'}
        </ul>
      </div>
      <div>
        <div style="font-weight:700;font-size:12px;color:#7c3aed;margin-bottom:8px;">H2 — Section Topics</div>
        <ul class="styled-list">
          {h2_items or '<li class="muted">None detected</li>'}
        </ul>
      </div>
    </div>
    {f'''<br/><div style="font-weight:700;font-size:12px;color:#6b7280;margin-bottom:8px;">H3 — Sub-topics</div>
    <ul class="styled-list">{h3_items}</ul>''' if h3_items else ''}
  </div>

  <!-- Navigation -->
  <div class="section">
    <div class="section-title"><div class="section-num">5</div>Site Navigation</div>
    <div class="section-divider"></div>
    <ul class="styled-list">
      {nav_items or '<li class="muted">No navigation items detected</li>'}
    </ul>
  </div>

  <!-- About -->
  {f'''<div class="section">
    <div class="section-title"><div class="section-num">6</div>Company Description (About Page)</div>
    <div class="section-divider"></div>
    <div class="card">{about_text}</div>
  </div>''' if about_text else ''}

  <div class="page-footer">
    <span>SimpliFiQ Discovery Audit Report</span>
    <span>Page 2</span>
  </div>
</div>

<!-- ═══════════════ PAGE 3: TECH + SOCIAL + CONTACT + AI INSIGHTS ═══════════════ -->
<div class="page">
  <div class="page-header">
    <span class="page-header-title">Technology, Social & AI Recommendations</span>
    <span class="page-header-company">{company} · {date_str}</span>
  </div>

  <!-- Technology Stack -->
  <div class="section">
    <div class="section-title"><div class="section-num">7</div>Detected Technology Stack</div>
    <div class="section-divider"></div>
    <div class="pill-wrap">{tech_pills}</div>
  </div>

  <!-- Social Media -->
  <div class="section">
    <div class="section-title"><div class="section-num">8</div>Social Media Presence</div>
    <div class="section-divider"></div>
    <div class="card">
      <table class="kv-table">{social_rows}</table>
    </div>
  </div>

  <!-- Contact -->
  <div class="section">
    <div class="section-title"><div class="section-num">9</div>Contact Information Found</div>
    <div class="section-divider"></div>
    <div class="card">
      <table class="kv-table">
        {kv_row("Email(s)", ', '.join(emails) if emails else "None found on public pages")}
        {kv_row("Phone(s)", ', '.join(phones) if phones else "None found on public pages")}
      </table>
    </div>
  </div>

  <!-- Strengths & Opportunities -->
  <div class="two-col">
    <div class="section">
      <div class="section-title"><div class="section-num">10</div>Strengths</div>
      <div class="section-divider"></div>
      <ul class="styled-list green-list">
        {strengths or '<li class="muted">Analysis pending</li>'}
      </ul>
    </div>
    <div class="section">
      <div class="section-title"><div class="section-num">11</div>Opportunities</div>
      <div class="section-divider"></div>
      <ul class="styled-list amber-list">
        {opportunities or '<li class="muted">Analysis pending</li>'}
      </ul>
    </div>
  </div>

  <!-- Key Recommendation -->
  <div class="section">
    <div class="section-title"><div class="section-num">12</div>Key Recommendation</div>
    <div class="section-divider"></div>
    <div class="rec-box">
      ⭐ <strong>Priority Action:</strong> {ai.get('key_recommendation', 'Develop a comprehensive digital strategy aligned with your business goals.')}
    </div>
  </div>

  <!-- Closing -->
  <div class="card card-purple" style="text-align:center;padding:24px;">
    <div style="font-size:15px;font-weight:700;color:#4f46e5;margin-bottom:8px;">Ready to Act on These Insights?</div>
    <div style="color:#6b7280;font-size:12px;line-height:1.7;">
      This report was automatically generated using publicly available data from {enriched.get('url', lead['website'])}.<br/>
      Reach out to discuss how SimpliFiQ can help <strong>{company}</strong> implement these recommendations<br/>
      and drive measurable growth.
    </div>
  </div>

  <div class="page-footer">
    <span>SimpliFiQ Discovery Audit Report · Confidential</span>
    <span>Page 3</span>
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

    print(f"  ✅ PDF saved: {file_name}")
    return file_name
