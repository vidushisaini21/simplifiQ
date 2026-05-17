import os
import json
import re
from dotenv import load_dotenv

load_dotenv()


async def generate_ai_insights(lead: dict, enriched: dict) -> dict:
    """Generate business insights using Gemini 1.5 Flash."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        print("  ⚠️  GEMINI_API_KEY not set — using template fallback")
        return _fallback_insights(lead, enriched)

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        context = f"""
Company: {lead['companyName']}
Website: {lead['website']}
Page Title: {enriched.get('title') or 'N/A'}
Meta Description: {enriched.get('description') or 'N/A'}
H1 Headlines: {'; '.join(enriched.get('h1', [])) or 'None detected'}
H2 Topics: {'; '.join((enriched.get('h2') or [])[:6]) or 'None detected'}
Navigation Items: {'; '.join(enriched.get('nav_links', [])) or 'None detected'}
Technologies: {', '.join(enriched.get('technologies', [])) or 'None detected'}
Social Media: {', '.join(enriched.get('social_links', {}).keys()) or 'None found'}
Contact Emails Found: {', '.join(enriched.get('contact', {}).get('emails', [])) or 'None found'}
About / Body Text: {(enriched.get('about_text') or enriched.get('body_text') or 'Not available')[:400]}
"""

        prompt = f"""You are a senior business analyst specializing in digital strategy.
Analyze this company's public web presence and return ONLY a JSON object (no markdown, no extra text):

{context}

Return this exact JSON structure:
{{
  "executive_summary": "2-3 sentence professional analysis of the company and their digital presence",
  "industry_vertical": "The specific industry or sector this company operates in",
  "digital_maturity_score": 7,
  "digital_maturity_label": "Established",
  "digital_maturity_reasoning": "Short reason explaining the score out of 10",
  "strengths": ["strength 1", "strength 2", "strength 3", "strength 4"],
  "opportunities": ["opportunity 1", "opportunity 2", "opportunity 3", "opportunity 4"],
  "key_recommendation": "The single most impactful actionable recommendation",
  "competitor_landscape": "1-2 sentences on their competitive environment"
}}"""

        response = model.generate_content(prompt)
        text = re.sub(r"```json\s*|\s*```", "", response.text.strip())
        insights = json.loads(text)
        print("  ✅ Gemini insights generated successfully")
        return insights

    except Exception as e:
        print(f"  ⚠️  Gemini error: {e} — falling back to template")
        return _fallback_insights(lead, enriched)


def _fallback_insights(lead: dict, enriched: dict) -> dict:
    """Template-based insights when Gemini key is absent or fails."""
    company = lead["companyName"]
    has_social = bool(enriched.get("social_links"))
    has_analytics = "Google Analytics" in enriched.get("technologies", [])
    has_contact = bool(enriched.get("contact", {}).get("emails"))
    has_about = bool(enriched.get("about_text"))

    score = 4
    if has_social:    score += 2
    if has_analytics: score += 1
    if has_contact:   score += 1
    if has_about:     score += 1
    if enriched.get("h1"): score += 1
    score = min(score, 10)

    label = "Basic" if score < 5 else "Developing" if score < 7 else "Established" if score < 9 else "Advanced"

    return {
        "executive_summary": (
            f"{company} operates at {lead['website']} with an identifiable web presence. "
            f"Based on automated analysis of their public website, they show structured digital activity "
            f"with clear opportunities for strategic improvements to drive growth."
        ),
        "industry_vertical": "Business Services / Technology",
        "digital_maturity_score": score,
        "digital_maturity_label": label,
        "digital_maturity_reasoning": (
            f"Score based on: {'social media presence, ' if has_social else ''}"
            f"{'analytics integration, ' if has_analytics else ''}"
            f"{'accessible contact info, ' if has_contact else ''}"
            f"overall web structure and content depth."
        ),
        "strengths": [
            "Active web presence with structured content layout",
            "Clear brand identity and messaging",
            "Defined navigation to guide user journeys",
            "Identifiable service/product offering",
        ],
        "opportunities": [
            "Expand social media presence for broader audience reach" if not has_social else "Increase content posting frequency across social platforms",
            "Implement analytics for data-driven decision making" if not has_analytics else "Leverage analytics insights to optimize conversion funnels",
            "Add visible contact information to improve lead generation" if not has_contact else "Create dedicated landing pages for each service offering",
            "Build an 'About Us' page to establish trust and credibility" if not has_about else "Add client testimonials and case studies to build social proof",
        ],
        "key_recommendation": (
            f"Develop a consistent content marketing strategy for {company} that aligns with customer "
            f"acquisition goals, leveraging SEO and social media to drive qualified organic traffic."
        ),
        "competitor_landscape": (
            f"{company} operates in a competitive digital landscape where clear differentiation, "
            f"strong online presence, and fast response times are critical success factors."
        ),
    }
