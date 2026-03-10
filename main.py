from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import httpx
import xml.etree.ElementTree as ET
from datetime import datetime
import asyncio
import re
import os

app = FastAPI(title="Afghanistan Incident Monitor")

# Allow all origins so your colleagues can access from any browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Sources ────────────────────────────────────────────────────────────────────
SOURCES = [
    # English – Afghan outlets
    {"id": "tolonews",    "name": "TOLOnews",       "lang": "English", "flag": "🇦🇫", "color": "#e85d04", "intl": False,
     "url": "https://tolonews.com/rss.xml"},
    {"id": "pajhwok",     "name": "Pajhwok",         "lang": "English", "flag": "🇦🇫", "color": "#f77f00", "intl": False,
     "url": "https://pajhwok.com/feed"},
    {"id": "khaama",      "name": "Khaama Press",    "lang": "English", "flag": "🇦🇫", "color": "#d62828", "intl": False,
     "url": "https://khaama.com/feed"},
    {"id": "ariana",      "name": "Ariana News",     "lang": "English", "flag": "🇦🇫", "color": "#fcbf49", "intl": False,
     "url": "https://ariananews.af/feed"},
    {"id": "zantimes",    "name": "Zan Times",       "lang": "English", "flag": "🇦🇫", "color": "#7b2d8b", "intl": False,
     "url": "https://zantimes.com/feed"},
    {"id": "aan",         "name": "Afghan Analysts", "lang": "English", "flag": "🇦🇫", "color": "#023e8a", "intl": False,
     "url": "https://www.afghanistan-analysts.org/en/feed/"},
    # English – Afghan outlets (continued)
    {"id": "roshana",     "name": "Roshana",             "lang": "English", "flag": "🇦🇫", "color": "#0ea5e9", "intl": False,
     "url": "https://roshana.af/feed"},
    {"id": "afintl_en",   "name": "AF International",    "lang": "English", "flag": "🇦🇫", "color": "#6366f1", "intl": False,
     "url": "https://www.afintl.com/en/feed"},
    # Farsi/Dari – Afghan outlets (continued)
    {"id": "afintl_fa",   "name": "افغانستان اینترنشنال","lang": "Farsi",   "flag": "🇦🇫", "color": "#6366f1", "intl": False,
     "url": "https://www.afintl.com/feed"},
    # English – International
    {"id": "reuters",     "name": "Reuters",         "lang": "English", "flag": "🌐", "color": "#ff6b35", "intl": True,
     "url": "https://feeds.reuters.com/reuters/topNews"},
    {"id": "bbc",         "name": "BBC World",       "lang": "English", "flag": "🌐", "color": "#bb0000", "intl": True,
     "url": "https://feeds.bbci.co.uk/news/world/rss.xml"},
    # Farsi/Dari
    {"id": "tolonews_fa", "name": "TOLOnews دری",    "lang": "Farsi",   "flag": "🇦🇫", "color": "#e85d04", "intl": False,
     "url": "https://tolonews.com/fa/rss.xml"},
    {"id": "pajhwok_fa",  "name": "Pajhwok دری",     "lang": "Farsi",   "flag": "🇦🇫", "color": "#f77f00", "intl": False,
     "url": "https://dari.pajhwok.com/feed"},
    {"id": "bbcfarsi",    "name": "BBC فارسی",       "lang": "Farsi",   "flag": "🌐", "color": "#bb0000", "intl": True,
     "url": "https://feeds.bbci.co.uk/persian/rss.xml"},
    {"id": "rferl_fa",    "name": "رادیو آزادی",    "lang": "Farsi",   "flag": "🌐", "color": "#1565c0", "intl": True,
     "url": "https://www.rferl.org/api/zptiqmouuq/articles.rss"},
    # Pashto
    {"id": "tolonews_ps", "name": "TOLOnews پښتو",  "lang": "Pashto",  "flag": "🇦🇫", "color": "#e85d04", "intl": False,
     "url": "https://tolonews.com/ps/rss.xml"},
    {"id": "pajhwok_ps",  "name": "Pajhwok پښتو",   "lang": "Pashto",  "flag": "🇦🇫", "color": "#f77f00", "intl": False,
     "url": "https://pashto.pajhwok.com/feed"},
    {"id": "rferl_ps",    "name": "رادیو آزادي",   "lang": "Pashto",  "flag": "🌐", "color": "#1565c0", "intl": True,
     "url": "https://www.rferl.org/api/zyvurqiuq/articles.rss"},
]

INCIDENT_KEYWORDS = [
    # Violence & attacks — English
    "attack", "attacked", "bomb", "bombing", "blast", "explosion", "ied",
    "suicide attack", "suicide bomber", "airstrike", "air strike",
    "killed", "killing", "dead", "death", "casualties", "casualty",
    "wounded", "injured", "gunfire", "shooting", "shot", "ambush",
    "clash", "clashes", "fighting", "offensive", "raid", "assault",
    "assassination", "assassinated", "execution", "executed",
    "kidnap", "kidnapped", "abducted", "hostage",
    "rocket", "mortar", "grenade", "landmine", "mine",
    "militant", "insurgent", "armed group", "armed attack",
    "massacre", "slaughter", "murder", "stabbing",
    # Flogging & punishment — English
    "flog", "flogging", "flogged", "whipped", "whipping", "lashed", "lashing",
    "stoned", "stoning", "public punishment", "public execution",
    "corporal punishment", "sentenced", "verdict", "hanged", "hanging",
    "amputat",
    # Violence — Farsi/Dari
    "حمله", "انفجار", "بمب", "کشته", "زخمی", "تیراندازی",
    "انتحاری", "درگیری", "اختطاف", "ترور", "موشک", "کمین",
    "اعدام", "جنگ", "خشونت", "قتل", "کشتار",
    # Flogging & punishment — Farsi/Dari
    "شلاق", "سنگسار", "مجازات", "حکم", "محکوم", "اعدام علنی",
    # Violence — Pashto
    "برید", "چاودنه", "وژل", "ټپي", "ډزې", "انتحاري",
    "ټکر", "اختطاف", "راکټ", "کمین", "وژنه", "وژل شو",
    # Flogging & punishment — Pashto
    "نیول", "سزا", "شلاقول", "اعدام", "حکم", "سنګسار",
]

AFGHANISTAN_GEO = [
    # English only — used to filter international outlets (BBC, Reuters, RFE/RL)
    "afghanistan", "afghan",
    # Major cities and provinces
    "kabul", "kandahar", "helmand", "kunduz", "herat", "mazar", "mazar-i-sharif",
    "jalalabad", "ghazni", "paktia", "nangarhar", "paktika", "logar", "wardak",
    "baghlan", "badakhshan", "faryab", "balkh", "zabul", "uruzgan", "farah",
    "nimroz", "ghor", "bamyan", "nuristan", "kunar", "laghman", "kapisa",
    "parwan", "khost", "panjshir", "samangan", "sar-e-pol", "takhar", "badghis",
    "jawzjan", "daykundi",
    # Key actors
    "taliban", "isis-k", "iskp", "haqqani",
]

def is_relevant(text: str, intl: bool) -> bool:
    lower = text.lower()
    # All outlets: must mention Afghanistan, an Afghan location, or Taliban
    if not any(kw in lower for kw in AFGHANISTAN_GEO):
        return False
    # All outlets: must also match at least one incident keyword
    return any(kw in lower for kw in INCIDENT_KEYWORDS)

def clean_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()

def parse_date(date_str: str) -> str:
    if not date_str:
        return ""
    for fmt in [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S GMT",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
    ]:
        try:
            return datetime.strptime(date_str.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return date_str[:10] if len(date_str) >= 10 else date_str

def parse_rss(xml_text: str, source: dict) -> list:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    # Handle both RSS and Atom
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    items = root.findall(".//item") or root.findall(".//atom:entry", ns)

    results = []
    for item in items:
        def text(tag):
            el = item.find(tag)
            return el.text or "" if el is not None else ""

        title = clean_html(text("title"))
        link  = text("link") or text("guid")
        desc  = clean_html(text("description") or text("summary"))[:400]
        date  = parse_date(text("pubDate") or text("published") or text("updated"))

        if not title:
            continue
        if not is_relevant(title + " " + desc, source["intl"]):
            continue

        results.append({
            "title": title,
            "link": link,
            "description": desc,
            "date": date,
            "source_id":   source["id"],
            "source_name": source["name"],
            "source_lang": source["lang"],
            "source_flag": source["flag"],
            "source_color": source["color"],
        })
    return results

async def fetch_source(client: httpx.AsyncClient, source: dict) -> dict:
    try:
        r = await client.get(
            source["url"],
            timeout=12,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; AfghanistanMonitor/1.0)"},
        )
        r.raise_for_status()
        items = parse_rss(r.text, source)
        return {"id": source["id"], "status": "ok", "count": len(items), "items": items}
    except Exception as e:
        return {"id": source["id"], "status": "error", "error": str(e)[:120], "items": []}


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/api/sources")
def get_sources():
    return SOURCES

@app.get("/api/feed")
async def get_feed(date_from: str = "", date_to: str = ""):
    async with httpx.AsyncClient() as client:
        tasks = [fetch_source(client, src) for src in SOURCES]
        results = await asyncio.gather(*tasks)

    all_items = []
    source_statuses = {}

    for r in results:
        source_statuses[r["id"]] = {"status": r["status"], "count": r.get("count", 0), "error": r.get("error", "")}
        all_items.extend(r["items"])

    # Date filtering
    if date_from or date_to:
        filtered = []
        for item in all_items:
            d = item.get("date", "")
            # If a date filter is active and the article has no parseable date, exclude it
            if not d:
                continue
            if date_from and d < date_from:
                continue
            if date_to and d > date_to:
                continue
            filtered.append(item)
        all_items = filtered

    # Deduplicate by title
    seen = set()
    deduped = []
    for item in all_items:
        key = item["title"][:60].lower().strip()
        if key and key not in seen:
            seen.add(key)
            deduped.append(item)

    # Sort newest first
    deduped.sort(key=lambda x: x.get("date", ""), reverse=True)

    return {"items": deduped, "sources": source_statuses, "total": len(deduped)}

@app.get("/health")
def health():
    return {"status": "ok"}

# Serve frontend (index.html) for all non-API routes
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(frontend_dir, "index.html"))
