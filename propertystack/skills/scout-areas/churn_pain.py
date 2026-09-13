"""Scout S4: churn (recent apartment sales / management changes) + competitor pain (portal and
payment complaints naming Yardi/Entrata/RealPage) per metro.

News + complaint searches go through Jina (each counted by the run's SearchBudget). Reddit uses
tooling/reddit_search.py (read-only, free, not counted). Only items with a URL and a date inside
the last 24 months are kept (undated news pages are fetched once via crawl4ai to read their
publish date). Writes propertystack/data/scout/<date>/<slug>/evidence.json.
"""
import datetime, json, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "tooling"))

WINDOW_DAYS = 730      # last 24 months
NEWS_QUERIES = [
    "{city} {st} apartment complex sold",
    "{city} {st} apartment community acquired multifamily",
    "{city} {st} apartments new management company takes over",
    "{city} {st} multifamily sale units buyer",
]
PAIN_QUERIES = [
    "{city} {st} apartment resident portal complaints rent payment",
    "{city} apartments rentcafe yardi payment problem",
    "{city} apartments entrata resident portal fees",
    "{city} apartments realpage loft resident portal complaint",
]
# Searched inside the city's own subreddit (r/Tucson, r/SanAntonio ...), newest first.
REDDIT_QUERIES = ["rentcafe", "yardi", "entrata", "realpage", "rent portal fee"]
# Vendor-owned, app-store and video sites: marketing/help pages, never a local complaint or deal.
EXTRA_SKIP = ("yardi.com", "rentcafe.com", "rentcafe.co.uk", "entrata.com", "residentportal.com",
              "realpage.com", "loftliving.com", "apple.com", "play.google.com", "cityfeet.com",
              "realmo.com", "era.com", "loopnet.com", "crexi.com", "omnihomesinternational.com")

DEAL = re.compile(r"\b(sold|sells?|sale of|sale price|acquire[sd]?|acquisition|buys|bought|purchase[sd]?|"
                  r"new (?:property )?management|takes over management|management change|"
                  r"third-party management|assumes management)\b", re.I)
APTS = re.compile(r"\b(apartments?|multifamily|multi-family|units|residential community)\b", re.I)
VENDOR = re.compile(r"\b(yardi|rent ?cafe|entrata|realpage|real page|loft ?living|onesite|"
                    r"resident ?portal|activebuilding)\b", re.I)
PAIN = re.compile(r"\b(portal|pay(?:ing)? rent|payment|fees?|convenience fee|login|glitch|"
                  r"charged|autopay|app|website)\b", re.I)
VENDOR_NAME = {"yardi": "Yardi", "rentcafe": "Yardi", "entrata": "Entrata", "residentportal": "Entrata",
               "realpage": "RealPage", "loftliving": "RealPage", "onesite": "RealPage",
               "activebuilding": "RealPage"}

MONTHS = "jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec"
_URL_DATE = re.compile(r"/(20\d\d)[/-](\d{1,2})(?:[/-](\d{1,2}))?(?:/|-|$)")
_TXT_DATE = re.compile(rf"\b({MONTHS})[a-z]*\.? (\d{{1,2}}),? (20\d\d)\b", re.I)
_ISO_DATE = re.compile(r"\b(20\d\d)-(\d\d)-(\d\d)\b")
_REL = re.compile(r"\b(\d+) (day|week|month)s? ago\b", re.I)


def find_date(text, url="", today=None):
    """Best-effort publish date from the URL or text; None if nothing usable."""
    today = today or datetime.date.today()
    m = _URL_DATE.search(url)
    if m:
        y, mo, d = int(m[1]), int(m[2]), int(m[3] or 1)
        try:
            return datetime.date(y, mo, d)
        except ValueError:
            pass
    m = _ISO_DATE.search(text)
    if m:
        try:
            return datetime.date(int(m[1]), int(m[2]), int(m[3]))
        except ValueError:
            pass
    m = _TXT_DATE.search(text)
    if m:
        mo = MONTHS.split("|").index(m[1][:3].lower()) + 1
        try:
            return datetime.date(int(m[3]), mo, int(m[2]))
        except ValueError:
            pass
    m = _REL.search(text)
    if m:
        n = int(m[1]) * {"day": 1, "week": 7, "month": 30}[m[2].lower()]
        return today - datetime.timedelta(days=n)
    return None


_META_DATE = re.compile(r"(?:datePublished|publishDate|published_time|pubdate|publish[_-]?date|dateCreated)"
                        r"(?:\W|content){0,20}(20\d\d)-(\d\d)-(\d\d)", re.I)
_LABEL_DATE = re.compile(rf"(?:article-date|published|posted on|dateline)[^<>]{{0,60}}>?\s*"
                         rf"(({MONTHS})[a-z]*\.? \d{{1,2}},? 20\d\d)", re.I)


def page_date(html):
    """Publish date from a fetched page's metadata (JSON-LD / meta tags / labelled date); None if absent."""
    html = html or ""
    m = _META_DATE.search(html)
    if m:
        try:
            return datetime.date(int(m[1]), int(m[2]), int(m[3]))
        except ValueError:
            pass
    m = _LABEL_DATE.search(html)
    return find_date(m[1]) if m else None


def skipped(url):
    import sample
    host = sample.urlparse(url).netloc.lower().removeprefix("www.")
    return any(host == d or host.endswith("." + d) for d in sample.SKIP_DOMAINS + EXTRA_SKIP)


def in_window(date, today=None):
    today = today or datetime.date.today()
    return date is not None and 0 <= (today - date).days <= WINDOW_DAYS


def _subs(metro):
    city = metro["name"].split(",")[0].split("-")[0].strip()
    return {"city": city, "st": metro["state"]}


def _vendors(text):
    return sorted({VENDOR_NAME[re.sub(r"\s+", "", v.lower())] for v in VENDOR.findall(text)})


def _run_queries(queries, metro, budget, search):
    subs, seen = _subs(metro), {}
    for q in queries:
        budget.use()                          # raises CapReached before going over
        for r in search(q.format(**subs)):
            u = r.get("url", "")
            if u and u not in seen:
                seen[u] = r
    return list(seen.values()), subs["city"]


def churn_items(metro, budget, search, reader=None, today=None):
    """News items about apartment sales / management changes in this metro, dated, last 24 months."""
    results, city = _run_queries(NEWS_QUERIES, metro, budget, search)
    out = []
    for r in results:
        text = f"{r.get('title', '')} {r.get('description', '')}"
        if skipped(r["url"]) or not (DEAL.search(text) and APTS.search(text)
                                     and city.lower() in (text + r["url"]).lower()):
            continue
        date = find_date(text, r["url"], today)
        if date is None and reader:
            try:
                date = page_date(reader.get(r["url"]))
            except Exception:                 # crawl failure: stays undated, dropped
                pass
        if in_window(date, today):
            out.append({"url": r["url"], "title": r.get("title", ""), "date": date.isoformat()})
    return out


def pain_items(metro, budget, search, reddit=None, today=None):
    """Portal/payment complaints naming a vendor for this metro: web search + Reddit, last 24 months."""
    results, city = _run_queries(PAIN_QUERIES, metro, budget, search)
    out = []
    for r in results:
        text = f"{r.get('title', '')} {r.get('description', '')}"
        vendors = _vendors(text)
        date = find_date(text, r["url"], today)
        if (vendors and PAIN.search(text) and in_window(date, today) and not skipped(r["url"])
                and city.lower() in (text + r["url"]).lower()):
            out.append({"url": r["url"], "title": r.get("title", ""), "date": date.isoformat(),
                        "vendors": vendors, "source": "web"})
    sub = re.sub(r"[^A-Za-z]", "", city)
    for q in REDDIT_QUERIES if reddit else []:
        for p in reddit(q, sub):
            text = f"{p.get('title', '')} {p.get('body', '')}"
            date = datetime.datetime.fromtimestamp(p.get("createdUtc") or 0, datetime.timezone.utc).date()
            vendors = _vendors(text)
            if vendors and PAIN.search(text) and in_window(date, today) and p["url"] not in {x["url"] for x in out}:
                out.append({"url": p["url"], "title": p.get("title", ""), "date": date.isoformat(),
                            "vendors": vendors, "source": "reddit"})
    return out


def reddit_search():
    """Read-only Reddit search via tooling/reddit_search.py; returns None if no session cookie."""
    import reddit_search as rs
    try:
        cookie = rs.load_cookie("DSH_REDDIT_COOKIE")
    except SystemExit:
        return None

    def search(q, subreddit=None):
        try:
            payload = rs.get_json(rs.search_url(q, subreddit, "new", "all", 10), cookie)
        except SystemExit:                    # tool exits on HTTP/login errors; skip that query
            return []
        return [p for p in (rs.post_from(c) for c in rs.children(payload)) if p]
    return search


def write_evidence(slug, dest, churn, pain):
    (dest / slug).mkdir(parents=True, exist_ok=True)
    path = dest / slug / "evidence.json"
    path.write_text(json.dumps({"slug": slug, "window_days": WINDOW_DAYS,
                                "churn": churn, "complaints": pain}, indent=2))
    return path


def churn_pain_metro(metro, budget, search, reddit, dest, reader=None):
    """Full S4 step for one metro -> (churn count, complaint count, evidence links, json path)."""
    churn = churn_items(metro, budget, search, reader)
    pain = pain_items(metro, budget, search, reddit)
    path = write_evidence(metro["slug"], dest, churn, pain)
    return len(churn), len(pain), [x["url"] for x in churn[:3] + pain[:3]], path
