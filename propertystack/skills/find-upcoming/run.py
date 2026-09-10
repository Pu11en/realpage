"""Skill 6 — find-upcoming, GATHER phase only: pull raw candidate documents from public
sources about apartment projects in the pipeline (zoning filed through leasing), and write
one JSON object per source document to data/<area>/6-upcoming-candidates.jsonl.

This script does NOT decide what's a real project, merge duplicates, or write 6-upcoming.csv.
That's the EXTRACT step, done by the agent per SKILL.md (a cheap model reading this file).

Sources:
1. Plano Legistar Web API (free, no key) — https://webapi.legistar.com/v1/plano/matters
   P&Z body matters, last ~24 months, one candidate per matter (title is the "text").
2. TDLR TABS registrations via zabalist.com (Jina search + read) — TDLR's own site has no
   bulk export or reusable per-project page structure.
3. News search (Jina search + read) across Community Impact, Dallas Morning News,
   Dallas Business Journal, Candysdirt, and general web — a broad set of queries to maximize
   recall (see QUERIES below), including named-development queries for known Plano/Richardson
   pipeline projects.

Usage: python3 skills/find-upcoming/run.py --area plano-richardson
"""
import argparse, collections, datetime as dt, json, re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from lib.paths import area_dir
from lib.runlog import RunLog
from lib.jina import Jina
import httpx

TODAY = "2026-09-10"
LEGISTAR_BASE = "https://webapi.legistar.com/v1/plano/matters"
TRIM_CHARS = 4000

NEWS_QUERIES = [
    "site:communityimpact.com Plano apartments multifamily units 2025 2026",
    "site:communityimpact.com Richardson apartments multifamily units 2025 2026",
    "site:dallasnews.com Plano apartment development 2026",
    "site:bizjournals.com/dallas Richardson multifamily units 2026",
    "site:bizjournals.com/dallas Plano multifamily units 2026",
    "site:candysdirt.com Plano apartments multifamily",
    "site:candysdirt.com Richardson apartments multifamily",
    "Plano Planning and Zoning apartments",
    "Richardson City Council zoning apartments units",
    "Heritage Creekside Plano apartments",
    "CityLine Richardson apartments construction",
    "Spring Creek Parkway apartments Plano zoning",
    "communityimpact.com Plano apartment groundbreaking site plan 2026",
    "communityimpact.com Richardson apartment groundbreaking 2026",
    "Haggard Farm Plano apartments townhomes",
    "Collin Creek Multifamily Plano apartments",
    "JLB West CityLine Richardson apartments",
    "110 E Polk Street Richardson apartments",
    "StreetLights Residential Plano Legacy Drive apartments",
    "Preston Road Plano apartments zoning 2026",
    # added after review-weak-spots.md: Preston Road / Spring Creek projects were sourced
    # in research-01 from a content.civicplus.com city staff-report PDF this run's queries
    # never surfaced (a GATHER recall gap, not an extraction miss)
    "site:content.civicplus.com Plano apartments staff report",
    "Plano Spring Creek Parkway apartments 304 units site plan",
    "Preston Road Plano apartments 351 units site plan",
    # "The Glenville" (390 units, Central Expressway, approved Jan 2024) kept getting
    # crowded out by a same-word TDLR filing for a different, already-opened project
    # ("Glenville Independent Living", N Glenville Dr) — broaden past the exact TABS hit
    "The Glenville Richardson apartments 390 units Central Expressway",
    "Richardson City Council Glenville apartments approved",
]

TDLR_QUERIES = [
    "site:zabalist.com Plano multifamily",
    "site:zabalist.com Richardson multifamily",
    "site:zabalist.com Collin Creek Multifamily Plano",
    "site:zabalist.com JLB West Cityline Richardson",
    "site:zabalist.com Haggard Farm Plano",
    "site:zabalist.com Polk Street Richardson",
]


def fetch_legistar(log):
    """P&Z body matters, last ~24 months. One candidate document per matter (no filtering
    for residential relevance here -- that's an EXTRACT-step judgment call)."""
    since = (dt.date.fromisoformat(TODAY) - dt.timedelta(days=730)).isoformat()
    params = {"$filter": f"MatterIntroDate ge datetime'{since}'", "$top": 1000,
              "$orderby": "MatterId asc"}
    r = httpx.get(LEGISTAR_BASE, params=params, timeout=60)
    log.rec["api_calls"]["legistar"] = log.rec["api_calls"].get("legistar", 0) + 1
    log.rec["inputs"].append(f"{LEGISTAR_BASE} $filter=MatterIntroDate ge datetime'{since}'")
    r.raise_for_status()
    matters = [m for m in r.json() if (m.get("MatterTypeName") or "").startswith("P&Z")]

    out = []
    for m in matters:
        title = (m.get("MatterTitle") or "").replace("\r", " ").replace("\n", " ").strip()
        if not title:
            continue
        matter_url = f"https://plano.legistar.com/LegislationDetail.aspx?ID={m['MatterId']}"
        text = (f"MatterTypeName: {m.get('MatterTypeName')}\n"
                f"MatterIntroDate: {m.get('MatterIntroDate')}\n"
                f"MatterPassedDate: {m.get('MatterPassedDate')}\n"
                f"MatterTitle: {title}")
        out.append({
            "source_type": "legistar",
            "source_url": matter_url,
            "title": title,
            "fetched_at": TODAY,
            "text": text[:TRIM_CHARS],
        })
    log.rec["counts"]["legistar_pz_matters_scanned"] = len(matters)
    log.rec["counts"]["legistar_candidates"] = len(out)
    return out


def fetch_tdlr(log, jina):
    out, seen_urls = [], set()
    for q in TDLR_QUERIES:
        results = jina.search(q)
        log.rec["api_calls"]["jina_search"] = log.rec["api_calls"].get("jina_search", 0) + 1
        log.rec["inputs"].append(f"jina.search: {q} ({len(results)} results)")
        for res in results[:6]:
            url = res.get("url", "")
            if not url or url in seen_urls or "zabalist.com/projects/" not in url:
                continue
            if url.rstrip("/").endswith(("/multifamily", "/city/plano", "/city/richardson")):
                continue
            seen_urls.add(url)
            text = jina.read(url)
            log.rec["api_calls"]["jina_read"] = log.rec["api_calls"].get("jina_read", 0) + 1
            title = res.get("title", "") or url
            out.append({
                "source_type": "tabs",
                "source_url": url,
                "title": title,
                "fetched_at": TODAY,
                "text": text[:TRIM_CHARS],
            })
    log.rec["counts"]["tdlr_urls_read"] = len(seen_urls)
    log.rec["counts"]["tdlr_candidates"] = len(out)
    return out


def trim_relevant(text, title, limit=TRIM_CHARS):
    """Trim page markdown to ~limit most relevant chars: prefer the body right after the
    'Markdown Content:' marker Jina prepends, else the head of the page."""
    body_start = text.find("Markdown Content:")
    body = text[body_start:] if body_start >= 0 else text
    return body[:limit]


def fetch_news(log, jina):
    out, seen_urls = [], set()
    for q in NEWS_QUERIES:
        results = jina.search(q)
        log.rec["api_calls"]["jina_search"] = log.rec["api_calls"].get("jina_search", 0) + 1
        log.rec["inputs"].append(f"jina.search: {q} ({len(results)} results)")
        for res in results[:6]:
            url = res.get("url", "")
            if not url or url in seen_urls:
                continue
            # broad net: news/blog domains relevant to local real-estate coverage, plus the
            # city's own site for P&Z / council items
            if not re.search(r"communityimpact\.com|dallasnews\.com|bizjournals\.com/dallas|"
                              r"candysdirt\.com|plano\.gov|cor\.gov|richardsontexas\.gov|"
                              r"civicplus\.com", url):
                continue
            seen_urls.add(url)
            text = jina.read(url)
            log.rec["api_calls"]["jina_read"] = log.rec["api_calls"].get("jina_read", 0) + 1
            title_line = text.splitlines()[0] if text else ""
            title = re.sub(r"^Title:\s*", "", title_line).strip() or res.get("title", "") or url
            # city P&Z/dev-review-list PDFs (civicplus) run to tens of thousands of chars and
            # list dozens of unrelated projects before the relevant ones — the default
            # TRIM_CHARS cut them off before reaching later entries (see extract-notes.md,
            # 2026-09-10 update). Use a much larger limit for these.
            is_city_doc = "civicplus.com" in url
            out.append({
                "source_type": "city" if is_city_doc else "news",
                "source_url": url,
                "title": title,
                "fetched_at": TODAY,
                "text": trim_relevant(text, title, limit=90000 if is_city_doc else TRIM_CHARS),
            })
    log.rec["counts"]["news_urls_read"] = len(seen_urls)
    log.rec["counts"]["news_candidates"] = len(out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--area", required=True)
    a = ap.parse_args()
    with RunLog("find-upcoming", a.area) as log:
        jina = Jina()
        legistar = fetch_legistar(log)
        tdlr = fetch_tdlr(log, jina)
        news = fetch_news(log, jina)
        log.rec["api_calls"].update(jina.calls)

        candidates = legistar + tdlr + news
        f = area_dir(a.area) / "6-upcoming-candidates.jsonl"
        with open(f, "w") as fh:
            for c in candidates:
                fh.write(json.dumps(c) + "\n")
        log.rec["outputs"] = [str(f.relative_to(f.parents[2]))]
        log.rec["counts"]["total_candidates"] = len(candidates)
        by_type = collections.Counter(c["source_type"] for c in candidates)
        log.rec["counts"]["by_source_type"] = dict(by_type)
        print(log.rec["counts"])


if __name__ == "__main__":
    main()
