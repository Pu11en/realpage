"""propertystack plugin -- the tools behind the query-propertystack skill.

At load time every CSV in $PS_DATA_DIR is loaded into a SQLite file (one table
per CSV). Queries then open that file read-only with an authorizer that only
allows reads, so nothing the model sends can change data.

Tools (toolset "propertystack"):
  ps_schema          tables, columns, row counts, and the citation name for each
  ps_sql             one read-only SELECT, max 200 rows
  ps_research_search keyword search over the research folders
  ps_research_read   read one research file
  ps_web_search      live web search (Jina Search), top results only
  ps_web_read        read one public web page as text (Jina Reader)

The two web tools only exist when JINA_API_KEY is set; they fetch through
Jina, so this container never connects to the target site itself.
"""
from __future__ import annotations

import csv
import json
import os
import re
import sqlite3
import time
import urllib.parse
import urllib.request
from pathlib import Path

DATA_DIR = Path(os.getenv("PS_DATA_DIR", "/opt/propertystack/data"))
RESEARCH_DIR = Path(os.getenv("PS_RESEARCH_DIR", "/opt/propertystack/research"))
# One SQLite file per process: the gateway and other hermes processes load this
# plugin at the same moment, and a shared file made them collide ("disk I/O
# error", "table already exists", root-owned read-only file).
DB_PATH = Path(os.getenv("PS_DB_PATH", f"/tmp/propertystack-{os.getpid()}.db"))
MAX_ROWS = 200
QUERY_SECONDS = 5

# built once at load: table, citation, row count, columns
SCHEMA: list[dict] = []


def _table_name(csv_name: str) -> str:
    stem = re.sub(r"^\d+-", "", Path(csv_name).stem)
    return re.sub(r"[^a-z0-9]+", "_", stem.lower()).strip("_")


# Scraped "emails" that aren't the building's: software vendors' accessibility inboxes, lead-routing
# robots, review sites, a web agency, and image filenames the scraper mistook for emails.
JUNK_EMAIL_DOMAINS = ("entrata.com", "apartments247.com", "birdeye.com", "leadmanaging.com",
                      "aptleasing.info", "assist.rent", "eliseai.com", "knck.io", "francemediainc.com")


def _usable_email(email):
    e = (email or "").strip().lower()
    if "@" not in e or e.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg")):
        return None
    local, domain = e.split("@", 1)
    if local.startswith(("accessibility", "webaccessibility", "profiles")):
        return None
    if any(domain == d or domain.endswith("." + d) for d in JUNK_EMAIL_DOMAINS):
        return None
    return email.strip()


# Plain names the agent lists under **Sources** (never the file name).
SOURCE_NAMES = {
    "apartments": "County property records",
    "websites": "Building websites",
    "software": "Software check (with proof link)",
    "sales": "County sales records",
    "upcoming": "City permits and news",
    "master": "County property records + software check",
    "leads": "CraneSignal lead ranking",
    "contacts": "Contact info from building websites",
    "state_leads": "CraneSignal lead ranking",
    "street_talk": "Reddit posts",
    "dallas_buildings": "Dallas-area building survey (county records)",
    "dallas_websites": "Dallas-area building survey (websites)",
    "dallas_software": "Dallas-area building survey (software check)",
    "dallas_sales": "Dallas-area building survey (county sales records)",
    "dallas_contacts": "Dallas-area building survey (contacts from websites)",
    "map_summary": "CraneSignal lead map (state and top-city totals)",
    "software_share": "Property software market share (Plano/Richardson only)",
    "building_extras": "Building owner, sale and lead detail (Plano/Richardson only)",
    "cranesignal_pipeline_steps": "CraneSignal build pipeline steps",
    "cranesignal_pipeline_runs": "CraneSignal build run history",
    "cranesignal_review_reasons": "CraneSignal review queue summary",
    "cranesignal_review_queue": "CraneSignal review queue",
    "cranesignal_accuracy_docs": "CraneSignal accuracy notes",
    "cranesignal_chat_stats": "CraneSignal chat speed measurements",
    "cranesignal_eval_checks": "CraneSignal eval checks",
    "cranesignal_eval_summary": "CraneSignal eval summary",
    "cranesignal_eval_failure_types": "CraneSignal eval failure types",
    "cranesignal_buildbot_summary": "CraneSignal AI build summary",
    "cranesignal_buildbot_examples": "CraneSignal AI build examples",
}


def _research_source(rel: str) -> str:
    topic = re.sub(r"^\d+-", "", rel.split("/")[0]).replace("-", " ")
    return f"RealPage research notes ({topic})"


# Every URL a tool hands the agent is remembered, so the chat proxy's link
# guard (chatbot/linkfix.py) can drop any link the agent made up.
SEEN_URLS = Path(os.environ.get("HERMES_HOME", "/opt/data")) / "seen-urls.txt"
SEEN_MAX_BYTES = 4_000_000
_URL_RE = re.compile(r"https?://[^\s)\]>\"'`,]+")


def _remember_urls(*texts: str) -> None:
    urls = {u.rstrip(".;:!?") for t in texts if t for u in _URL_RE.findall(t)}
    if not urls:
        return
    try:
        SEEN_URLS.parent.mkdir(parents=True, exist_ok=True)
        if SEEN_URLS.exists() and SEEN_URLS.stat().st_size > SEEN_MAX_BYTES:
            keep = SEEN_URLS.read_text(errors="replace").splitlines()[-20000:]
            SEEN_URLS.write_text("\n".join(keep) + "\n")
        with open(SEEN_URLS, "a", encoding="utf-8") as f:
            f.write("".join(u + "\n" for u in sorted(urls)))
    except OSError:
        pass


def _build_db() -> None:
    SCHEMA.clear()
    tmp = DB_PATH.with_suffix(".building")
    tmp.unlink(missing_ok=True)
    con = sqlite3.connect(tmp)
    for path in sorted(DATA_DIR.glob("*.csv")):
        with open(path, newline="") as f:
            rows = list(csv.reader(f))
        if not rows:
            continue
        header, body = rows[0], rows[1:]
        _remember_urls(*(c for r in body for c in r if "http" in c))
        table = _table_name(path.name)
        if table == "contacts" and "email" in header:  # same junk filter as the site
            i = header.index("email")
            body = [r[:i] + [_usable_email(r[i]) or ""] + r[i + 1:] if len(r) > i else r for r in body]
        SCHEMA.append({"table": table, "source_name": SOURCE_NAMES.get(table, table), "rows": len(body), "columns": header})
        cols = ", ".join(f'"{c}"' for c in header)
        con.execute(f'CREATE TABLE "{table}" ({cols})')
        con.executemany(
            f'INSERT INTO "{table}" VALUES ({", ".join("?" * len(header))})',
            [(r + [""] * (len(header) - len(r)))[: len(header)] for r in body],
        )
    con.commit()
    con.close()
    tmp.replace(DB_PATH)


_READ_ACTIONS = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION}


def _authorizer(action, *_):
    return sqlite3.SQLITE_OK if action in _READ_ACTIONS else sqlite3.SQLITE_DENY


def _ro_connect() -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    con.set_authorizer(_authorizer)
    deadline = time.monotonic() + QUERY_SECONDS
    con.set_progress_handler(lambda: 1 if time.monotonic() > deadline else 0, 10000)
    return con


def ps_schema(args: dict, **_) -> str:
    return json.dumps({
        "tables": SCHEMA,
        "notes": [
            "Query the table name (e.g. FROM software). List source_name once under **Sources** at the end; never show file, table or column names.",
            "All columns are TEXT; CAST(units AS INTEGER) for numbers.",
            "master = apartments + websites + software joined; one row per building (apt_id).",
            "software='unknown' means not identified; the reason is in unknown_reason.",
            "Software data covers Plano and Richardson only (software/master tables); other areas' "
            "software is blank. Vendor counts must say they cover Plano and Richardson only.",
            "contacts: phone/email only where the website scrape actually found them.",
            "leads.ref_id is an apt_id (signal=sold) or an upcoming project_id (signal=upcoming).",
            "state_leads: every tracked state's leads, one flat row per lead (no separate master/contacts). "
            "Texas (area='tx') already includes the 42 Plano/Richardson leads, so count states and regions "
            "(region='Dallas–Fort Worth') from state_leads alone -- never add the leads table on top. "
            "Filter with WHERE area='<slug>' from the area list below; stage is permitted/leasing/"
            "under_construction/sold/planned. permit_link/news_link/website_link/agenda_link/map_link "
            "are ready-made URLs for the deep-dive link row (map_link may be blank -- build it from address).",
            "street_talk: saved Texas Reddit/YouTube posts. part=rivals (RealPage vs Yardi/Entrata/AppFolio), "
            "buildings (talk about a lead building; building_id/building), unhappy (rival customers; warm_lead=1 "
            "sounds like a manager/owner). companies is ';'-joined -- filter with companies LIKE '%Yardi%'. "
            "sentiment is happy/angry/mixed/neutral. Quote briefly and always give each post's url as its link.",
            "dallas_buildings/dallas_websites/dallas_software/dallas_sales/dallas_contacts: a separate "
            "Dallas-area building survey (not leads) -- never add these buildings or units to any Texas or "
            "Dallas-Fort Worth lead count. dallas_software is almost entirely 'unknown' (not checked yet); "
            "don't count it toward vendor market share.",
            "map_summary: one row per state/top-city pair, matching the site's lead map exactly -- "
            "state_total is that state's total leads, city_count is that city's leads. Use this (not "
            "state_leads) to answer 'which state/city has the most leads' so the numbers match the map; "
            "group by state and sum/compare state_total (it repeats per city row, so don't sum it across "
            "a state's own rows).",
            "software_share: the site's vendor market-share chart, Plano and Richardson only (same scope "
            "as the software/master tables) -- pct_of_identified_properties is already computed, so use it "
            "directly rather than recomputing from properties/units; never present it as covering any other "
            "area.",
            "building_extras: one row per Plano/Richardson building (join to master on apt_id) with owner, "
            "website_confidence, unknown_reason (same values as master, handy without a join), plus "
            "sale_date/sale_new_owner/sale_previous_owner and lead_rank/lead_total_leads/lead_why -- all "
            "blank when that building has no sale or isn't a ranked lead, which is most of them.",
            "cranesignal_* tables: CraneSignal's own build, eval, speed, and AI-agent progress numbers "
            "from the Under the Hood page. Use them only for questions about CraneSignal itself (how it "
            "was built, checked, measured, or how accurate/fast it is), never as property/lead/software "
            "facts. eval/chat/buildbot rows have measured_at dates; state that date because those numbers "
            "may be old. cost_note says per-area dollars are a placeholder until run logs record dollars.",
        ],
    })


def ps_sql(args: dict, **_) -> str:
    query = (args.get("query") or "").strip().rstrip(";")
    if not re.match(r"(?is)^\s*(select|with)\b", query) or ";" in query:
        return json.dumps({"error": "Only a single SELECT (or WITH ... SELECT) statement is allowed."})
    try:
        con = _ro_connect()
        cur = con.execute(query)
        cols = [d[0] for d in cur.description or []]
        rows = cur.fetchmany(MAX_ROWS + 1)
        con.close()
    except sqlite3.Error as e:
        return json.dumps({"error": f"SQL error: {e}"})
    _remember_urls(*(str(c) for r in rows for c in r if c and "http" in str(c)))
    return json.dumps({
        "columns": cols,
        "rows": rows[:MAX_ROWS],
        "truncated": len(rows) > MAX_ROWS,
    })


def _research_files() -> list[Path]:
    return sorted(p for p in RESEARCH_DIR.rglob("*") if p.is_file() and p.suffix in (".md", ".txt", ".csv"))


def ps_research_search(args: dict, **_) -> str:
    terms = [t.lower() for t in re.findall(r"\w+", args.get("query") or "") if len(t) > 2]
    if not terms:
        return json.dumps({"error": "Give at least one search word (3+ letters)."})
    hits = []
    for path in _research_files():
        rel = str(path.relative_to(RESEARCH_DIR))
        for i, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
            low = line.lower()
            score = sum(t in low for t in terms)
            if score:
                hits.append((score, rel, i, line.strip()[:300]))
    hits.sort(key=lambda h: (-h[0], h[1], h[2]))
    return json.dumps({
        "files": [str(p.relative_to(RESEARCH_DIR)) for p in _research_files()],
        "hits": [{"file": rel, "source_name": _research_source(rel), "line": i, "text": t} for _, rel, i, t in hits[:40]],
    })


def ps_research_read(args: dict, **_) -> str:
    rel = (args.get("path") or "").strip().lstrip("/")
    target = (RESEARCH_DIR / rel).resolve()
    if RESEARCH_DIR.resolve() not in target.parents or not target.is_file():
        return json.dumps({"error": "Unknown file.", "files": [str(p.relative_to(RESEARCH_DIR)) for p in _research_files()]})
    text = target.read_text(errors="replace")
    _remember_urls(text[:20000])
    return json.dumps({"source_name": _research_source(rel), "text": text[:20000], "truncated": len(text) > 20000})


JINA_KEY = os.getenv("JINA_API_KEY", "").strip()
WEB_CHARS = 12000
WEB_SECONDS = 40


def _jina_get(url: str, headers: dict) -> str:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {JINA_KEY}", **headers})
    with urllib.request.urlopen(req, timeout=WEB_SECONDS) as r:
        return r.read().decode("utf-8", "replace")


def ps_web_search(args: dict, **_) -> str:
    query = (args.get("query") or "").strip()[:200]
    if not query:
        return json.dumps({"error": "Give a search query."})
    try:
        body = _jina_get("https://s.jina.ai/?" + urllib.parse.urlencode({"q": query}),
                         {"Accept": "application/json", "X-Respond-With": "no-content"})
        data = json.loads(body).get("data") or []
    except Exception as e:
        return json.dumps({"error": f"Web search failed: {type(e).__name__}"})
    _remember_urls(*(x.get("url", "") for x in data[:8]))
    return json.dumps({"results": [
        {"title": x.get("title", ""), "url": x.get("url", ""), "description": (x.get("description") or "")[:300]}
        for x in data[:8]
    ]})


def ps_web_read(args: dict, **_) -> str:
    url = (args.get("url") or "").strip()
    if not re.match(r"(?i)^https?://[^/\s]+\.[a-z]{2,}", url):
        return json.dumps({"error": "Give one full public http(s) URL."})
    try:
        text = _jina_get("https://r.jina.ai/" + url, {"X-Retain-Images": "none"})
    except Exception as e:
        return json.dumps({"error": f"Could not read that page: {type(e).__name__}"})
    _remember_urls(url, text[:WEB_CHARS])
    return json.dumps({"source_url": url, "text": text[:WEB_CHARS], "truncated": len(text) > WEB_CHARS})


def _schema(name: str, description: str, props: dict, required: list[str]) -> dict:
    return {
        "name": name,
        "description": description,
        "parameters": {"type": "object", "properties": props, "required": required},
    }


def register(ctx) -> None:
    _build_db()
    ctx.register_tool(
        name="ps_schema", toolset="propertystack",
        schema=_schema("ps_schema", "List CraneSignal tables, columns, row counts and the plain source_name for each. Call this first.", {}, []),
        handler=ps_schema, description="CraneSignal schema",
    )
    ctx.register_tool(
        name="ps_sql", toolset="propertystack",
        schema=_schema(
            "ps_sql",
            "Run ONE read-only SQLite SELECT over the CraneSignal CSV tables (max 200 rows). Writes are rejected.",
            {"query": {"type": "string", "description": "A single SELECT statement."}},
            ["query"],
        ),
        handler=ps_sql, description="CraneSignal read-only SQL",
    )
    ctx.register_tool(
        name="ps_research_search", toolset="propertystack",
        schema=_schema(
            "ps_research_search",
            "Keyword search over the RealPage research folders (company, products, reviews, reddit, social, news, competitors, voice of customer, AI visibility = how AIs rank RealPage). Returns file + line hits.",
            {"query": {"type": "string", "description": "Search words."}},
            ["query"],
        ),
        handler=ps_research_search, description="Research search",
    )
    ctx.register_tool(
        name="ps_research_read", toolset="propertystack",
        schema=_schema(
            "ps_research_read",
            "Read one research file by its relative path, e.g. 04-reddit/index.md.",
            {"path": {"type": "string", "description": "Relative path from ps_research_search."}},
            ["path"],
        ),
        handler=ps_research_read, description="Research read",
    )
    if JINA_KEY:
        ctx.register_tool(
            name="ps_web_search", toolset="propertystack",
            schema=_schema(
                "ps_web_search",
                "Live web search. Use to research ONE lead the user asked about (owner, management company, resident reviews, news). Returns titles, URLs, snippets.",
                {"query": {"type": "string", "description": "Search words, e.g. the building name + city + 'reviews'."}},
                ["query"],
            ),
            handler=ps_web_search, description="Web search (Jina)",
        )
        ctx.register_tool(
            name="ps_web_read", toolset="propertystack",
            schema=_schema(
                "ps_web_read",
                "Read one public web page (from ps_web_search or a source URL in the data) as text. Cite the URL.",
                {"url": {"type": "string", "description": "Full http(s) URL."}},
                ["url"],
            ),
            handler=ps_web_read, description="Web page read (Jina)",
        )
