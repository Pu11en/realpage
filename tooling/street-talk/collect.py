#!/usr/bin/env python3
"""Street Talk collector: read-only Reddit pulls saved as raw files for the tab.

Safety (every part): GET only, at most 1 request every 3 seconds, a hard request
budget per run (never above 80), and the first 403/429 stops the run while
keeping whatever was already saved. The cookie is never printed.

Usage:
  python3 tooling/street-talk/collect.py --part rivals [--budget 30] [--date 2026-09-15]
  python3 tooling/street-talk/collect.py --part buildings --budget 60

Part 2 (buildings) also searches YouTube through yt-dlp (the Agent Reach YouTube
channel, no login): title + link, plus a transcript excerpt only if the
transcript names the building.

Writes propertystack/data/street-talk/raw/<date>/<part>.json and <part>-report.md.
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import pathlib
import re
import subprocess
import sys
import tempfile
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
             f"- Blocked by Reddit: {result['blocked'] or 'no'}"]
    if "buildingsSearched" in result:
        by_source: dict[str, int] = {}
        for post in result["posts"]:
            by_source[post.get("source", "reddit")] = by_source.get(post.get("source", "reddit"), 0) + 1
        lines += [f"- Buildings searched: {result['buildingsSearched']}",
                  f"- YouTube lookups: {result.get('youtubeCalls', 0)}",
                  f"- Posts by source: " + (", ".join(f"{k} {v}" for k, v in sorted(by_source.items())) or "none"),
                  f"- Buildings with at least one post: {len({p['buildingId'] for p in result['posts']})}"]
    lines += ["", "## Posts dropped", ""]
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
        where = f"r/{post['subreddit']}" if post.get("subreddit") else f"YouTube {post.get('channel', '')}".strip()
        about = f" [{post['building']}]" if post.get("building") else ""
        lines.append(f"- {post['date']} {where}{about}: {post['title']} ({post['url']})")
    return "\n".join(lines) + "\n"


def save(result: dict, day: str) -> pathlib.Path:
    folder = RAW_DIR / day
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{result['part']}.json"
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    (folder / f"{result['part']}-report.md").write_text(report_md(result))
    return path


# ---- Part 2: Texas lead buildings -------------------------------------------------

AREAS_DIR = ROOT / "site" / "data" / "areas"
TOP_BUILDINGS = 40
NAME_SUFFIX_RE = re.compile(
    r"(\s+(apartments?|apartment homes|apts|homes|residences|multifamily|"
    r"phase\s+[ivx0-9]+|[ivx]+))+$", re.I)
ADDRESS_RE = re.compile(
    r"unit project|\b(st|street|rd|road|dr|drive|ave|avenue|blvd|pkwy|parkway|ln|lane|hwy)\.?$", re.I)
HOME_RE = re.compile(r"\b(apartments?|apts?|complex(es)?|leas(e|ing)|rent(ing|s)?|tenants?|"
                     r"management|landlord|units?|move[ds]? in|lived? (at|here))\b", re.I)
FILLER_WORDS = {"the", "at", "on", "of", "@", "and", "&"}


def core_name(name: str) -> str:
    """'Station 121 At Town Center Apts' -> 'Station 121 At Town Center'."""
    core = NAME_SUFFIX_RE.sub("", name.strip()).strip()
    return core or name.strip()


def is_searchable(name: str) -> bool:
    """Street addresses and '390-unit project at ...' are not names people use."""
    core = core_name(name)
    if re.search(r"multifamily", name, re.I) and len(core.split()) <= 2:
        return False  # 'South Lamar Multifamily' is a permit label, not a name
    return not ADDRESS_RE.search(name) and not ADDRESS_RE.search(core) and len(core) >= 4


def name_pattern(core: str) -> re.Pattern:
    words = [re.escape(w) for w in re.split(r"\s+", core) if w]
    return re.compile(r"\b" + r"[\s\-]+".join(words) + r"\b", re.I)


def names_building(text: str, building: dict) -> bool:
    """Short names ('Oak Park', 'The Reid') are too common alone: they also need
    the city and an apartment word (so a hawk called 'Cooper' does not count)."""
    if not name_pattern(building["core"]).search(text):
        return False
    real_words = [w for w in building["core"].lower().split() if w not in FILLER_WORDS]
    if len(real_words) >= 3:
        return True
    city = re.search(r"\b" + re.escape(building["city"]) + r"\b", text, re.I)
    return bool(city and HOME_RE.search(text))


def texas_buildings(areas_dir: pathlib.Path | None = None, top: int = TOP_BUILDINGS) -> list[dict]:
    """Biggest Texas lead buildings across every area file whose leads are in TX
    (a state area named 'tx', or leads tagged state TX), one per name+city."""
    areas_dir = areas_dir or AREAS_DIR
    rows = []
    for path in sorted(areas_dir.glob("*.json")):
        data = json.loads(path.read_text())
        area_is_tx = str(data.get("area", path.stem)).lower() == "tx"
        for lead in data.get("leads", []):
            in_tx = area_is_tx or str(lead.get("state", "")).upper() == "TX"
            name = lead.get("property") or lead.get("community") or ""
            if in_tx and name and lead.get("id") and is_searchable(name):
                rows.append(lead)
    rows.sort(key=lambda r: r.get("units") or 0, reverse=True)
    picked, seen = [], set()
    for lead in rows:
        name = lead.get("property") or lead.get("community")
        key = (core_name(name).lower(), lead.get("units"))
        key2 = (core_name(name).lower(), (lead.get("city") or "").lower())
        if key in seen or key2 in seen:
            continue
        seen.update({key, key2})
        picked.append({"id": lead["id"], "name": name, "core": core_name(name),
                       "city": lead.get("city") or "", "units": lead.get("units") or 0})
        if len(picked) >= top:
            break
    return picked


class YouTube:
    """No-login YouTube search via yt-dlp (Agent Reach's YouTube channel).
    `run` is swappable for tests; failures just mean no videos."""

    def __init__(self, run=None, sleep=time.sleep, gap: float = 2.0):
        self._run = run or self._yt_dlp
        self.sleep = sleep
        self.gap = gap
        self.calls = 0

    def _yt_dlp(self, args: list[str], workdir: str | None = None) -> str:
        try:
            done = subprocess.run(["yt-dlp", "--no-warnings", "--no-update", *args],
                                  capture_output=True, text=True, timeout=90, cwd=workdir)
        except (OSError, subprocess.TimeoutExpired):
            return ""
        return done.stdout if done.returncode == 0 else ""

    def _call(self, args: list[str], workdir: str | None = None) -> str:
        if self.calls:
            self.sleep(self.gap)
        self.calls += 1
        return self._run(args, workdir)

    def search(self, query: str, limit: int = 5) -> list[dict]:
        out = self._call(["--flat-playlist", "-J", f"ytsearch{limit}:{query}"])
        try:
            return [e for e in json.loads(out).get("entries", []) if isinstance(e, dict)]
        except (ValueError, AttributeError):
            return []

    def details(self, url: str) -> dict:
        """Upload date plus English auto-caption text ('' if none)."""
        with tempfile.TemporaryDirectory() as tmp:
            out = self._call(["-J", "--no-simulate", "--skip-download", "--write-auto-subs",
                              "--write-subs", "--sub-langs", "en.*", "--sub-format", "vtt",
                              "-o", "v.%(ext)s", url], tmp)
            text = " ".join(vtt_text(p.read_text(errors="replace"))
                            for p in sorted(pathlib.Path(tmp).glob("*.vtt")))
        try:
            info = json.loads(out.strip().splitlines()[-1]) if out.strip() else {}
        except ValueError:
            info = {}
        return {"upload_date": info.get("upload_date") or "", "transcript": text}


def vtt_text(vtt: str) -> str:
    """Caption lines only, tags stripped, repeated rolling lines collapsed."""
    lines, last = [], ""
    for line in vtt.splitlines():
        line = re.sub(r"<[^>]+>", "", line).strip()
        if not line or "-->" in line or line.startswith(("WEBVTT", "Kind:", "Language:")):
            continue
        if line != last:
            lines.append(line)
        last = line
    return " ".join(lines)


def around(text: str, pattern: re.Pattern, chars: int = EXCERPT_CHARS) -> str:
    """A short window of `text` centred on the first match."""
    match = pattern.search(text)
    if not match:
        return ""
    start = max(0, match.start() - chars // 2)
    piece = text[start:start + chars].strip()
    return ("…" if start else "") + piece + ("…" if start + chars < len(text) else "")


def yt_date(value: str) -> str:
    return f"{value[:4]}-{value[4:6]}-{value[6:8]}" if re.fullmatch(r"\d{8}", value or "") else ""


def collect_buildings(reddit: Reddit, now: dt.datetime, buildings: list[dict] | None = None,
                      youtube: YouTube | None = None, comment_posts: int = 99) -> dict:
    buildings = texas_buildings() if buildings is None else buildings
    youtube = youtube or YouTube()
    kept: dict[str, dict] = {}
    dropped: dict[str, int] = {}
    blocked = ""
    reddit_stopped = False

    def drop(reason: str) -> None:
        dropped[reason] = dropped.get(reason, 0) + 1

    def base(b: dict) -> dict:
        return {"buildingId": b["id"], "building": b["name"], "city": b["city"], "part": "buildings"}

    for b in buildings:
        query = f'"{b["core"]}" {b["city"]}'
        if not reddit_stopped and reddit.left() > 0:
            try:
                payload = reddit.get(rs.search_url(query, None, "relevance", "all", SEARCH_LIMIT))
            except Blocked as error:
                blocked, reddit_stopped, payload = str(error), True, None
            for child in rs.children(payload):
                post = rs.post_from(child)
                if post is None:
                    drop("missing title or link")
                    continue
                if post["url"] in kept:
                    drop("duplicate link")
                    continue
                if not post["createdUtc"]:
                    drop("no date")
                    continue
                if is_job_ad(post):
                    drop("job ad")
                    continue
                if not names_building(f"{post['title']} {post['body']}", b):
                    drop("does not name the building")
                    continue
                kept[post["url"]] = {
                    **base(b), "source": "reddit", "url": post["url"],
                    "subreddit": post["subreddit"], "title": post["title"],
                    "excerpt": rs.excerpt(post["body"], EXCERPT_CHARS), "comments": [],
                    "score": post["score"], "commentCount": post["commentCount"],
                    "date": iso_date(post["createdUtc"]),
                    "companies": companies_in(f"{post['title']} {post['body']}"), "query": query}
        for video in youtube.search(f'"{b["core"]}" {b["city"]} apartments'):
            url = video.get("url") or ""
            if not url.startswith("https://www.youtube.com/"):
                drop("missing title or link")
                continue
            if url in kept:
                drop("duplicate link")
                continue
            text = f"{video.get('title') or ''} {video.get('description') or ''}"
            if not names_building(text, b):
                drop("does not name the building")
                continue
            info = youtube.details(url)
            date = yt_date(info["upload_date"])
            if not date:
                drop("no date")
                continue
            quote = around(info["transcript"], name_pattern(b["core"]))
            kept[url] = {
                **base(b), "source": "youtube", "url": url,
                "subreddit": "", "channel": video.get("channel") or video.get("uploader") or "",
                "title": video.get("title") or "", "excerpt": quote, "comments": [],
                "score": video.get("view_count") or 0, "commentCount": 0, "date": date,
                "companies": companies_in(f"{text} {quote}"), "query": query}

    # Top 2 comments for the most-discussed Reddit posts while budget lasts.
    if not reddit_stopped:
        talk = [p for p in kept.values() if p["source"] == "reddit" and p["commentCount"]]
        try:
            for post in sorted(talk, key=lambda p: p["commentCount"], reverse=True)[:comment_posts]:
                if reddit.left() <= 0:
                    break
                thread = reddit.get(post["url"] + ".json?sort=top&limit=2&depth=1&raw_json=1")
                post["comments"] = [rs.excerpt(c["body"], EXCERPT_CHARS)
                                    for c in rs.comments_from(thread, 2)]
        except Blocked as error:
            blocked = str(error)

    posts = sorted(kept.values(), key=lambda p: p["date"], reverse=True)
    return {"part": "buildings", "fetchedAt": now.isoformat(), "requestsUsed": reddit.used,
            "youtubeCalls": youtube.calls, "buildingsSearched": len(buildings),
            "blocked": blocked, "dropped": dropped, "posts": posts}


PARTS = {"rivals": collect_rivals, "buildings": collect_buildings}


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
