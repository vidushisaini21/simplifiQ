import httpx
from bs4 import BeautifulSoup
import re
from typing import Optional

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def normalize_url(website: str) -> str:
    w = website.strip()
    if not w.startswith(("http://", "https://")):
        w = "https://" + w
    return w.rstrip("/")


async def fetch_html_httpx(url: str) -> Optional[str]:
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=12, headers=HEADERS) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.text
    except Exception as e:
        print(f"  httpx failed for {url}: {e}")
        return None


async def fetch_html_playwright(url: str) -> Optional[str]:
    """Fallback: use Playwright Chromium for JS-rendered pages."""
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            page = await browser.new_page()
            await page.set_extra_http_headers({"User-Agent": HEADERS["User-Agent"]})
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(2000)
            content = await page.content()
            await browser.close()
            return content
    except Exception as e:
        print(f"  Playwright also failed for {url}: {e}")
        return None


async def fetch_html(url: str) -> Optional[str]:
    html = await fetch_html_httpx(url)
    if not html:
        print(f"  Retrying with Playwright for {url}...")
        html = await fetch_html_playwright(url)
    return html


def extract_social_links(soup: BeautifulSoup) -> dict:
    patterns = {
        "LinkedIn":  re.compile(r"linkedin\.com/(?:company|in)/", re.I),
        "Twitter":   re.compile(r"(?:twitter|x)\.com/", re.I),
        "Facebook":  re.compile(r"facebook\.com/", re.I),
        "Instagram": re.compile(r"instagram\.com/", re.I),
        "YouTube":   re.compile(r"youtube\.com/", re.I),
        "GitHub":    re.compile(r"github\.com/", re.I),
    }
    found = {}
    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        for name, rx in patterns.items():
            if name not in found and rx.search(href):
                found[name] = href
    return found


def extract_contact_info(html: str) -> dict:
    email_rx = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
    phone_rx = re.compile(r"\+?[\d][\d\s\-().]{8,}\d")
    emails = list({
        e for e in email_rx.findall(html)
        if not re.search(r"\.(png|jpg|gif|svg|css|js|woff)$", e, re.I) and "example" not in e
    })[:3]
    phones = list({p.strip() for p in phone_rx.findall(html) if len(re.sub(r"\D", "", p)) >= 10})[:2]
    return {"emails": emails, "phones": phones}


def detect_technologies(html: str) -> list:
    checks = [
        ("WordPress",       re.compile(r"wp-content|wp-includes|wordpress", re.I)),
        ("Shopify",         re.compile(r"shopify", re.I)),
        ("React",           re.compile(r"__react|React\.createElement|react\.development", re.I)),
        ("Vue.js",          re.compile(r"Vue\.|__vue|vue\.min", re.I)),
        ("Angular",         re.compile(r"ng-version|angular\.min|angular\.js", re.I)),
        ("Next.js",         re.compile(r"__NEXT_DATA__|next-head", re.I)),
        ("jQuery",          re.compile(r"jquery", re.I)),
        ("Bootstrap",       re.compile(r"bootstrap\.min\.css|bootstrap\.bundle", re.I)),
        ("TailwindCSS",     re.compile(r"tailwind", re.I)),
        ("Google Analytics",re.compile(r"gtag\(|google-analytics|G-[A-Z0-9]+", re.I)),
        ("Google Tag Manager", re.compile(r"googletagmanager", re.I)),
        ("HubSpot",         re.compile(r"hubspot", re.I)),
        ("Intercom",        re.compile(r"intercom", re.I)),
        ("Hotjar",          re.compile(r"hotjar", re.I)),
        ("Salesforce",      re.compile(r"salesforce", re.I)),
        ("Stripe",          re.compile(r"stripe\.js|stripe\.com/v3", re.I)),
        ("Cloudflare",      re.compile(r"cloudflare", re.I)),
        ("Webflow",         re.compile(r"webflow", re.I)),
        ("Wix",             re.compile(r"wix\.com|wixstatic", re.I)),
        ("Squarespace",     re.compile(r"squarespace", re.I)),
    ]
    return [name for name, rx in checks if rx.search(html)]


async def try_fetch_about(base_url: str) -> str:
    slugs = ["/about", "/about-us", "/company", "/who-we-are", "/our-story"]
    for slug in slugs:
        html = await fetch_html(base_url + slug)
        if not html:
            continue
        soup = BeautifulSoup(html, "lxml")
        for sel in ["main", "article", ".about", "#about", "section"]:
            el = soup.select_one(sel)
            if el:
                text = re.sub(r"\s+", " ", el.get_text()).strip()
                if len(text) > 150:
                    return text[:700]
    return ""


async def enrich_company(website: str) -> dict:
    base_url = normalize_url(website)
    result = {
        "url": base_url, "title": "", "description": "",
        "og_title": "", "og_description": "", "keywords": [],
        "h1": [], "h2": [], "h3": [], "nav_links": [],
        "body_text": "", "about_text": "", "social_links": {},
        "contact": {"emails": [], "phones": []},
        "technologies": [], "footer_text": "",
    }

    html = await fetch_html(base_url)
    if not html:
        print(f"  ⚠️  Could not fetch {base_url} at all, returning empty enrichment")
        return result

    soup = BeautifulSoup(html, "lxml")

    # Meta tags
    result["title"] = (soup.title.string or "").strip()
    for attrs, key in [
        ({"name": "description"},        "description"),
        ({"property": "og:description"}, "og_description"),
        ({"property": "og:title"},        "og_title"),
    ]:
        tag = soup.find("meta", attrs=attrs)
        if tag:
            result[key] = (tag.get("content") or "").strip()
    if not result["description"]:
        result["description"] = result["og_description"]

    kw_tag = soup.find("meta", attrs={"name": "keywords"})
    if kw_tag:
        result["keywords"] = [k.strip() for k in (kw_tag.get("content") or "").split(",") if k.strip()][:12]

    def clean(tags):
        return [re.sub(r"\s+", " ", t.get_text()).strip() for t in tags]

    result["h1"] = [h for h in clean(soup.find_all("h1")) if h][:5]
    result["h2"] = [h for h in clean(soup.find_all("h2")) if h][:8]
    result["h3"] = [h for h in clean(soup.find_all("h3")) if h][:8]

    nav = soup.find("nav") or soup.find("header")
    if nav:
        result["nav_links"] = list({a.get_text().strip() for a in nav.find_all("a") if a.get_text().strip()})[:12]

    result["social_links"]  = extract_social_links(soup)
    result["contact"]       = extract_contact_info(html)
    result["technologies"]  = detect_technologies(html)

    footer = soup.find("footer")
    if footer:
        result["footer_text"] = re.sub(r"\s+", " ", footer.get_text()).strip()[:400]

    paragraphs = [re.sub(r"\s+", " ", p.get_text()).strip()
                  for p in soup.find_all("p") if len(p.get_text().strip()) > 60]
    result["body_text"] = " ".join(paragraphs[:5])[:600]

    # About page scrape
    result["about_text"] = await try_fetch_about(base_url)

    print(f"  ✅ Enrichment done: title='{result['title'][:40]}', h1={len(result['h1'])}, techs={len(result['technologies'])}")
    return result
