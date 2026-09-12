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
        table = _table_name(path.name)
        SCHEMA.append({"table": table, "cite_as": f"[{path.name}]", "rows": len(body), "columns": header})
        cols = ", ".join(f'"{c}"' for c in header)
        con.execute(f'CREATE TABLE "{table}" ({cols})')
        con.executemany(
            f'INSERT INTO "{table}" VALUES ({", ".join("?" * len(header))})',
            [r + [""] * (len(header) - len(r)) for r in body],
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
            "Query the table name (e.g. FROM software), cite the cite_as file name.",
            "All columns are TEXT; CAST(units AS INTEGER) for numbers.",
            "master = apartments + websites + software joined; one row per building (apt_id).",
            "software='unknown' means not identified; the reason is in unknown_reason.",
            "contacts: phone/email only where the website scrape actually found them.",
            "leads.ref_id is an apt_id (signal=sold) or an upcoming project_id (signal=upcoming).",
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
        "hits": [{"cite_as": f"[{rel}]", "line": i, "text": t} for _, rel, i, t in hits[:40]],
    })


def ps_research_read(args: dict, **_) -> str:
    rel = (args.get("path") or "").strip().lstrip("/")
    target = (RESEARCH_DIR / rel).resolve()
    if RESEARCH_DIR.resolve() not in target.parents or not target.is_file():
        return json.dumps({"error": "Unknown file.", "files": [str(p.relative_to(RESEARCH_DIR)) for p in _research_files()]})
    text = target.read_text(errors="replace")
    return json.dumps({"cite_as": f"[{rel}]", "text": text[:20000], "truncated": len(text) > 20000})


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
    return json.dumps({"cite_as": url, "text": text[:WEB_CHARS], "truncated": len(text) > WEB_CHARS})


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
        schema=_schema("ps_schema", "List PropertyStack tables, columns, row counts and the [file.csv] citation for each. Call this first.", {}, []),
        handler=ps_schema, description="PropertyStack schema",
    )
    ctx.register_tool(
        name="ps_sql", toolset="propertystack",
        schema=_schema(
            "ps_sql",
            "Run ONE read-only SQLite SELECT over the PropertyStack CSV tables (max 200 rows). Writes are rejected.",
            {"query": {"type": "string", "description": "A single SELECT statement."}},
            ["query"],
        ),
        handler=ps_sql, description="PropertyStack read-only SQL",
    )
    ctx.register_tool(
        name="ps_research_search", toolset="propertystack",
        schema=_schema(
            "ps_research_search",
            "Keyword search over the RealPage research folders (company, products, reviews, reddit, social, news, competitors, voice of customer). Returns file + line hits.",
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
