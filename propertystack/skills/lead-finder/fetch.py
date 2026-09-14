"""Shared web helper for every lead-finder part: search + cached page reads.

Search: SearXNG (tooling/searx_search.py) first, free and local. Jina only when
SearXNG returns nothing or is unreachable; Jina calls are counted separately so a
run's search budget can tell paid from free calls apart.

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
_UNSET = object()
SITE_GAP_S = 2.0
BLOCK_LIMIT = 3

_BLOCK_MARKERS = (
    "access denied",
    "captcha",
    "are you a human",
    "unusual traffic",
    "403 forbidden",
    "blocked",
)


class SearchCounts:
    """Tracks how many free (SearXNG) vs paid (Jina) searches a run has made."""

    def __init__(self) -> None:
        self.searxng = 0
        self.jina = 0

    @property
    def total(self) -> int:
        return self.searxng + self.jina


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
        searx_search=None,
        page_fetchers: list | None = None,
        site_gap_s: float = SITE_GAP_S,
    ) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.jina_api_key = _load_jina_key() if jina_api_key is _UNSET else jina_api_key
        self.counts = SearchCounts()
        self._last_visit: dict[str, float] = {}
        self._block_counts: dict[str, int] = {}
        self._skipped: dict[str, str] = {}
        self.site_gap_s = site_gap_s

        if searx_search is not None:
            self._searx_search = searx_search
        else:
            import searx_search as searx_mod  # tooling/searx_search.py

            self._searx_search = searx_mod.search

        self._page_fetchers = page_fetchers if page_fetchers is not None else [
            _fetch_crawl4ai,
            _fetch_scrapling,
            _fetch_playwright,
        ]

    # -- search --------------------------------------------------------

    def search(self, query: str, n: int = 10) -> list[dict]:
        try:
            results = self._searx_search(query, n)
        except OSError:
            results = []
        else:
            self.counts.searxng += 1
        if results:
            return results
        if not self.jina_api_key:
            return []
        results = self._search_jina(query, n)
        self.counts.jina += 1
        return results

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

    # -- page reads ------------------------------------------------------

    def fetch(self, url: str) -> FetchResult:
        site = _site_key(url)
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
            self._block_counts[site] = self._block_counts.get(site, 0) + 1
            if self._block_counts[site] >= BLOCK_LIMIT:
                reason = f"blocked {self._block_counts[site]} times"
                self._skipped[site] = reason
                return FetchResult(url=url, ok=False, skipped_reason=reason)
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
        last = self._last_visit.get(site)
        now = time.time()
        if last is not None and now - last < self.site_gap_s:
            time.sleep(self.site_gap_s - (now - last))
        self._last_visit[site] = time.time()


def _site_key(url: str) -> str:
    from urllib.parse import urlparse

    return urlparse(url).netloc.lower()


def _looks_blocked(html: str) -> bool:
    lowered = html.lower()
    return any(marker in lowered for marker in _BLOCK_MARKERS)


def _load_jina_key() -> str | None:
    env_path = Path("/home/drewp/main-projects/realpage/.env")
    if not env_path.exists():
        return None
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("JINA_API_KEY="):
            return line.split("=", 1)[1].strip()
    return None


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
