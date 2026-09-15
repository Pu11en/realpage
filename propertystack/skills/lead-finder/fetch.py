"""Shared web helper for every lead-finder part: search + cached page reads.

Search: Jina first. Brave Search API only when Jina errors or returns nothing
relevant, and only while under Brave's monthly free-credit cap (tracked in
propertystack/runs/brave-usage.json); once that cap is hit, Brave is skipped and
search falls back to whatever Jina returned. Jina and Brave calls are counted
separately on the WebHelper (and rolled into a run's search cap) so a run's
search budget can tell the two apart.

Page reads go through a fallback chain -- crawl4ai first, then Scrapling if the
page looks blocked, then Playwright as the last resort -- and every fetched page
is cached on disk (by URL) so it is never read twice. Repeated visits to the same
site are spaced >= 2 s apart. A site that blocks us 3 times in a row is marked
skipped with a reason and not retried.

No place names anywhere in this module -- areas/cities are always caller-supplied
data, never literals here.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLING = HERE.parents[2] / "tooling"
if str(TOOLING) not in sys.path:
    sys.path.insert(0, str(TOOLING))

DEFAULT_CACHE_DIR = HERE.parents[2] / "propertystack" / "runs" / "cache"
DEFAULT_BRAVE_USAGE_PATH = HERE.parents[2] / "propertystack" / "runs" / "brave-usage.json"
_UNSET = object()
SITE_GAP_S = 2.0
BLOCK_LIMIT = 3
BRAVE_MONTHLY_CAP = 800

_BLOCK_MARKERS = (
    "access denied",
    "complete the captcha",
    "solve the captcha",
    "are you a human",
    "unusual traffic",
    "403 forbidden",
    "blocked",
    "just a moment",
    "checking your browser",
    "cf-turnstile",
    "challenges.cloudflare.com",
)


class SearchCounts:
    """Tracks how many Jina vs Brave searches a run has made."""

    def __init__(self) -> None:
        self.jina = 0
        self.brave = 0

    @property
    def total(self) -> int:
        return self.jina + self.brave


class BraveUsage:
    """Persists Brave Search API call counts by month so the 800/month free-credit
    cap is tracked across runs, not just within one process."""

    def __init__(self, path: Path = DEFAULT_BRAVE_USAGE_PATH) -> None:
        self.path = Path(path)

    def _month_key(self) -> str:
        return time.strftime("%Y-%m")

    def _load(self) -> dict:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return {}
        return {}

    def count_this_month(self) -> int:
        return self._load().get(self._month_key(), 0)

    def under_cap(self, cap: int = BRAVE_MONTHLY_CAP) -> bool:
        return self.count_this_month() < cap

    def record_call(self) -> None:
        data = self._load()
        key = self._month_key()
        data[key] = data.get(key, 0) + 1
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


@dataclass
class FetchResult:
    url: str
    ok: bool
    html: str = ""
    from_cache: bool = False
    skipped_reason: str = ""


class WebHelper:
    def __init__(
        self,
        cache_dir: Path | str = DEFAULT_CACHE_DIR,
        jina_api_key: str | None = _UNSET,
        brave_api_key: str | None = _UNSET,
        brave_usage: "BraveUsage | None" = None,
        page_fetchers: list | None = None,
        site_gap_s: float = SITE_GAP_S,
    ) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.jina_api_key = _load_jina_key() if jina_api_key is _UNSET else jina_api_key
        self.brave_api_key = _load_brave_key() if brave_api_key is _UNSET else brave_api_key
        self.brave_usage = brave_usage if brave_usage is not None else BraveUsage()
        self.counts = SearchCounts()
        self.junk_jina = 0
        self._last_visit: dict[str, float] = {}
        self._block_counts: dict[str, int] = {}
        self._skipped: dict[str, str] = {}
        self.site_gap_s = site_gap_s
        # S1: details/software/contact lookups now run several records at once
        # (a thread pool in run.py/fill_software/fill_contacts), so every bit
        # of shared state a WebHelper mutates needs its own lock -- otherwise
        # two threads hitting the same site could both pass `_respect_gap`
        # before either records `_last_visit`, or `_block_counts` could lose
        # an increment to a race and never trip `BLOCK_LIMIT`.
        self._lock = threading.Lock()

        self._page_fetchers = page_fetchers if page_fetchers is not None else [
            _fetch_crawl4ai,
            _fetch_scrapling,
            _fetch_playwright,
        ]

    # -- search --------------------------------------------------------

    def search(self, query: str, n: int = 10) -> list[dict]:
        results: list[dict] = []
        if self.jina_api_key:
            try:
                results = self._search_jina(query, n)
            except OSError:
                results = []
            with self._lock:
                self.counts.jina += 1
        if results and not _looks_junk(query, results):
            return results
        if results:
            with self._lock:
                self.junk_jina += 1
        with self._lock:
            brave_ok = bool(self.brave_api_key) and self.brave_usage.under_cap()
        if not brave_ok:
            return results
        brave_results = self._search_brave(query, n)
        with self._lock:
            self.counts.brave += 1
            self.brave_usage.record_call()
        return brave_results or results

    def _search_jina(self, query: str, n: int) -> list[dict]:
        req = urllib.request.Request(
            f"https://s.jina.ai/{urllib.parse.quote(query)}",
            headers={"Authorization": f"Bearer {self.jina_api_key}", "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.load(r)
        except (urllib.error.URLError, OSError):
            return []
        out = []
        for x in data.get("data", [])[:n]:
            out.append({"title": x.get("title", ""), "url": x.get("url", ""), "snippet": (x.get("description") or "")[:300]})
        return out

    def _search_brave(self, query: str, n: int) -> list[dict]:
        req = urllib.request.Request(
            "https://api.search.brave.com/res/v1/web/search?"
            + urllib.parse.urlencode({"q": query, "count": n}),
            headers={"X-Subscription-Token": self.brave_api_key, "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.load(r)
        except (urllib.error.URLError, OSError):
            return []
        out = []
        for x in data.get("web", {}).get("results", [])[:n]:
            out.append({"title": x.get("title", ""), "url": x.get("url", ""), "snippet": (x.get("description") or "")[:300]})
        return out

    # -- page reads ------------------------------------------------------

    def fetch(self, url: str) -> FetchResult:
        site = _site_key(url)
        with self._lock:
            if site in self._skipped:
                return FetchResult(url=url, ok=False, skipped_reason=self._skipped[site])

        cached = self._read_cache(url)
        if cached is not None:
            return FetchResult(url=url, ok=True, html=cached, from_cache=True)

        self._respect_gap(site)
        html = None
        for fetcher in self._page_fetchers:
            html = fetcher(url)
            if html is not None and not _looks_blocked(html):
                break

        if html is None or _looks_blocked(html):
            with self._lock:
                self._block_counts[site] = self._block_counts.get(site, 0) + 1
                count = self._block_counts[site]
                if site not in self._skipped and count >= BLOCK_LIMIT:
                    reason = f"blocked {BLOCK_LIMIT} times"
                    self._skipped[site] = reason
                if site in self._skipped:
                    return FetchResult(url=url, ok=False, skipped_reason=self._skipped[site])
            return FetchResult(url=url, ok=False, skipped_reason="blocked")

        self._write_cache(url, html)
        return FetchResult(url=url, ok=True, html=html)

    # -- cache -------------------------------------------------------

    def _cache_path(self, url: str) -> Path:
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{digest}.html"

    def _read_cache(self, url: str) -> str | None:
        p = self._cache_path(url)
        if p.exists():
            return p.read_text(encoding="utf-8")
        return None

    def _write_cache(self, url: str, html: str) -> None:
        self._cache_path(url).write_text(html, encoding="utf-8")

    def _respect_gap(self, site: str) -> None:
        """Reserve this site's next visit slot under the lock (so two
        threads fetching the same site can't both see no-recent-visit and
        both proceed at once), then sleep outside the lock so a slow visit
        to one site never blocks fetches to other sites."""
        with self._lock:
            last = self._last_visit.get(site)
            now = time.time()
            wait = self.site_gap_s - (now - last) if last is not None else 0.0
            reserved_at = now + max(wait, 0.0)
            self._last_visit[site] = reserved_at
        if wait > 0:
            time.sleep(wait)


_STOPWORDS = {
    "the", "and", "for", "with", "from", "open", "data", "new", "near", "of",
    "in", "on", "a", "an", "to", "is", "are",
}


def _query_words(query: str) -> list[str]:
    words = [w.strip('"').lower() for w in query.split()]
    return [w for w in words if len(w) > 2 and w not in _STOPWORDS]


def _looks_junk(query: str, results: list[dict]) -> bool:
    """True when Jina's top results don't actually match the query.

    A result "matches" when at least one distinctive query word (city/agency
    name, "permit", "apartment", etc; short stopwords excluded) appears in its
    title, URL or snippet. Fewer than 2 of the top 5 matching means the search
    ignored the query and returned generic junk.
    """
    words = _query_words(query)
    if not words:
        return False
    top = results[:5]
    if len(top) < 2:
        return False
    matches = 0
    for r in top:
        haystack = " ".join(
            str(r.get(k, "")) for k in ("title", "url", "snippet")
        ).lower()
        if any(w in haystack for w in words):
            matches += 1
    return matches < 2


def _site_key(url: str) -> str:
    from urllib.parse import urlparse

    return urlparse(url).netloc.lower()


def _looks_blocked(html: str) -> bool:
    lowered = html.lower()
    return any(marker in lowered for marker in _BLOCK_MARKERS)


def _load_env_key(name: str) -> str | None:
    """Read `name` from the realpage repo's .env; if that's missing or
    doesn't have it (e.g. this is a sandboxed worktree copy that can't see
    outside itself), fall back to a `.env` at this repo's own root."""
    prefix = f"{name}="
    for env_path in (
        Path("/home/drewp/main-projects/realpage/.env"),
        Path(__file__).resolve().parents[3] / ".env",
    ):
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith(prefix):
                value = line.split("=", 1)[1].strip()
                if value:
                    return value
    return None


def _load_jina_key() -> str | None:
    return _load_env_key("JINA_API_KEY")


def _load_brave_key() -> str | None:
    return _load_env_key("BRAVE_API_KEY")


def _fetch_crawl4ai(url: str) -> str | None:
    try:
        import asyncio

        from crawl4ai import AsyncWebCrawler
    except ImportError:
        return None
    try:
        async def _run() -> str:
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=url)
                return result.html or ""

        return asyncio.run(_run())
    except Exception:
        return None


def _fetch_scrapling(url: str) -> str | None:
    try:
        from scrapling.fetchers import StealthyFetcher
    except ImportError:
        return None
    try:
        page = StealthyFetcher.fetch(url)
        return page.html_content
    except Exception:
        return None


def _fetch_playwright(url: str) -> str | None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url, timeout=20000)
            html = page.content()
            browser.close()
            return html
    except Exception:
        return None
