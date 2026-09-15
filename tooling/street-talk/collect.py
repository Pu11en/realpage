#!/usr/bin/env python3
"""Street Talk collector: read-only Reddit pulls saved as raw files for the tab.

Safety (every part): GET only, at most 1 request every 3 seconds, a hard request
budget per run (never above 80), and the first 403/429 stops the run while
keeping whatever was already saved. The cookie is never printed.

Usage:
  python3 tooling/street-talk/collect.py --part rivals [--budget 30] [--date 2026-09-15]

Writes propertystack/data/street-talk/raw/<date>/<part>.json and <part>-report.md.
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "propertystack" / "data" / "street-talk" / "raw"
MAX_REQUESTS = 80
MIN_GAP_SECONDS = 3.0
SEARCH_LIMIT = 25
EXCERPT_CHARS = 300

_spec = importlib.util.spec_from_file_location("reddit_search", ROOT / "tooling" / "reddit_search.py")
rs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rs)

COMPANIES = {
    "RealPage": re.compile(r"\breal\s?page\b", re.I),
    "Yardi": re.compile(r"\byardi\b", re.I),
    "Entrata": re.compile(r"\bentrata\b", re.I),
    "AppFolio": re.compile(r"\bapp\s?folio\b", re.I),
}
TEXAS_WORDS = ["Texas", "Dallas", "Houston", "Austin", "San Antonio", "Fort Worth", "Plano"]
TEXAS_RE = re.compile(r"\b(texas|tx|dallas|houston|austin|san antonio|fort worth|plano|dfw)\b", re.I)
TEXAS_SUBS = {"dallas", "houston", "austin", "sanantonio", "texas"}
JOB_RE = re.compile(r"\[\s*(hiring|job wanted|for hire)\s*\]|who'?s hiring|\bis \[?hiring\]?\b", re.I)
RIVAL_SUBS = ["PropertyManagement", "multifamily", "Dallas", "houston", "Austin", "sanantonio", "texas"]


class Blocked(Exception):
    """Reddit said 403/429 (or sent a login page): stop and keep what we have."""


class Reddit:
    """Rate-limited, budgeted, read-only fetcher. `fetch` is swappable for tests."""

    def __init__(self, cookie: str, budget: int, fetch=None, sleep=time.sleep):
        self.cookie = cookie
        self.budget = min(budget, MAX_REQUESTS)
        self.used = 0
        self.sleep = sleep
        self._last = 0.0
        self._fetch = fetch or self._http

    def left(self) -> int:
        return self.budget - self.used

    def get(self, url: str) -> object:
        if self.left() <= 0:
            raise RuntimeError("request budget used up")
        wait = MIN_GAP_SECONDS - (time.monotonic() - self._last)
        if self._last and wait > 0:
            self.sleep(wait)
        self._last = time.monotonic()
        self.used += 1
        return self._fetch(url)

    def _http(self, url: str) -> object:
        request = urllib.request.Request(url, method="GET", headers={
            "Accept": "application/json", "Cookie": self.cookie,
            "User-Agent": rs.UA, "Accept-Encoding": "identity"})
        try:
            with rs.OPENER.open(request, timeout=25) as response:
                body = response.read().decode("utf-8", "replace")
                kind = (response.headers.get("Content-Type") or "").lower()
        except urllib.error.HTTPError as error:
            if error.code in (401, 403, 429):
                raise Blocked(f"HTTP {error.code}") from None
            return None
        except urllib.error.URLError:
            return None
        if "json" not in kind:
            raise Blocked("login or security page instead of JSON")
        return json.loads(body)


def get_cookie() -> str:
    """Prefer Drew's saved cookie file; fall back to the env/DSH sources."""
    if rs.COOKIE_JSON.exists():
        cookie = rs.cookie_from_json(rs.COOKIE_JSON)
        if cookie:
            return cookie
    return rs.load_cookie("DSH_REDDIT_COOKIE")


def iso_date(created_utc: float) -> str:
    return dt.datetime.fromtimestamp(created_utc, dt.timezone.utc).date().isoformat()


def companies_in(text: str) -> list[str]:
    return [name for name, pattern in COMPANIES.items() if pattern.search(text)]


def is_job_ad(post: dict) -> bool:
    """Job ads mention the companies but are not street talk."""
    return "job" in post["subreddit"].lower() or bool(JOB_RE.search(post["title"]))


def rivals_searches() -> list[tuple[str, str | None]]:
    """(query, subreddit) pairs for part 1, most useful first."""
    texas = "(" + " OR ".join(f'"{w}"' if " " in w else w for w in TEXAS_WORDS) + ")"
    any_company = "(realpage OR yardi OR entrata OR appfolio)"
    searches = [(f"{name.lower()} {texas}", None) for name in COMPANIES]
    searches += [(any_company, sub) for sub in RIVAL_SUBS]
    return searches


def collect_rivals(reddit: Reddit, now: dt.datetime, comment_posts: int = 99) -> dict:
    cutoff = (now - dt.timedelta(days=365)).timestamp()
    kept: dict[str, dict] = {}
    dropped: dict[str, int] = {}
    blocked = ""

    def drop(reason: str) -> None:
        dropped[reason] = dropped.get(reason, 0) + 1

    try:
        for query, sub in rivals_searches():
            if reddit.left() <= 0:
                break
            payload = reddit.get(rs.search_url(query, sub, "relevance", "year", SEARCH_LIMIT))
            for child in rs.children(payload):
                post = rs.post_from(child)
                if post is None:
                    drop("missing title or link")
                    continue
                if post["url"] in kept:
                    drop("duplicate link")
                    continue
                if not post["createdUtc"] or post["createdUtc"] < cutoff:
                    drop("older than 12 months")
                    continue
                if is_job_ad(post):
                    drop("job ad")
                    continue
                text = f"{post['title']} {post['body']}"
                names = companies_in(text)
                if not names:
                    drop("names none of the four companies")
                    continue
                in_texas_sub = post["subreddit"].lower() in TEXAS_SUBS
                if not in_texas_sub and not TEXAS_RE.search(text):
                    drop("no Texas mention")
                    continue
                kept[post["url"]] = {
                    "url": post["url"],
                    "subreddit": post["subreddit"],
                    "title": post["title"],
                    "excerpt": rs.excerpt(post["body"], EXCERPT_CHARS),
                    "comments": [],
                    "score": post["score"],
                    "commentCount": post["commentCount"],
                    "date": iso_date(post["createdUtc"]),
                    "companies": names,
                    "part": "rivals",
                    "query": query if sub is None else f"r/{sub}: {query}",
                }
        # Top 2 comments for the most-discussed posts while budget lasts.
        by_talk = sorted(kept.values(), key=lambda p: p["commentCount"], reverse=True)
        for post in by_talk[:comment_posts]:
            if reddit.left() <= 0 or not post["commentCount"]:
                break
            thread = reddit.get(post["url"] + ".json?sort=top&limit=2&depth=1&raw_json=1")
            post["comments"] = [rs.excerpt(c["body"], EXCERPT_CHARS)
                                for c in rs.comments_from(thread, 2)]
    except Blocked as error:
        blocked = str(error)

    posts = sorted(kept.values(), key=lambda p: p["date"], reverse=True)
    return {"part": "rivals", "fetchedAt": now.isoformat(), "requestsUsed": reddit.used,
            "blocked": blocked, "dropped": dropped, "posts": posts}


def report_md(result: dict) -> str:
    lines = [f"# Street Talk raw pull: {result['part']}", "",
             f"- Fetched: {result['fetchedAt']}",
             f"- Reddit requests used: {result['requestsUsed']}",
             f"- Posts kept: {len(result['posts'])}",
             f"- Blocked by Reddit: {result['blocked'] or 'no'}", "", "## Posts dropped", ""]
    if result["dropped"]:
        lines += [f"- {reason}: {n}" for reason, n in sorted(result["dropped"].items())]
    else:
        lines.append("- none")
    counts: dict[str, int] = {}
    for post in result["posts"]:
        for name in post.get("companies", []):
            counts[name] = counts.get(name, 0) + 1
    if counts:
        lines += ["", "## Posts per company", ""]
        lines += [f"- {name}: {n}" for name, n in counts.items()]
    lines += ["", "## 5 sample posts", ""]
    for post in result["posts"][:5]:
        lines.append(f"- {post['date']} r/{post['subreddit']}: {post['title']} ({post['url']})")
    return "\n".join(lines) + "\n"


def save(result: dict, day: str) -> pathlib.Path:
    folder = RAW_DIR / day
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{result['part']}.json"
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    (folder / f"{result['part']}-report.md").write_text(report_md(result))
    return path


PARTS = {"rivals": collect_rivals}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--part", required=True, choices=sorted(PARTS))
    parser.add_argument("--budget", type=int, default=30, help=f"Reddit requests (max {MAX_REQUESTS})")
    parser.add_argument("--date", default=dt.date.today().isoformat())
    args = parser.parse_args()
    reddit = Reddit(get_cookie(), args.budget)
    result = PARTS[args.part](reddit, dt.datetime.now(dt.timezone.utc))
    path = save(result, args.date)
    print(f"{args.part}: {len(result['posts'])} posts kept, {reddit.used} requests, "
          f"blocked={result['blocked'] or 'no'} -> {path.relative_to(ROOT)}")
    if result["blocked"]:
        sys.exit(2)


if __name__ == "__main__":
    main()
