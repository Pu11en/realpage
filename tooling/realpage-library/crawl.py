#!/usr/bin/env python3
"""Download every realpage.com page in urls.csv as clean markdown.

    python3 tooling/realpage-library/crawl.py --limit 20     # practice run
    python3 tooling/realpage-library/crawl.py                # everything (resumes)

Reads raw/realpage-site/urls.csv (from sitemap.py) and writes
raw/realpage-site/pages/<type>/<slug>.md, each starting with a small header
(url, title, type, lastmod, crawled). Pages already saved are skipped, so a
stopped run just restarts. Failures go to raw/realpage-site/failed.csv.

Fetching uses Crawl4AI's plain-HTTP strategy (no browser); our own cleaner
keeps only <main> and drops menus, footers, cookie banners and scripts, then
Crawl4AI turns the rest into markdown. If Crawl4AI errors or the page comes
out under 200 characters, Jina Reader (JINA_API_KEY) is tried instead.
Polite: one request at a time, 1 per second, clear user agent.
"""
import argparse
import asyncio
import csv
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "raw" / "realpage-site"
USER_AGENT = "CraneSignal-library/1.0 (research crawl; polite, 1 req/sec)"
MIN_CHARS = 200

JUNK_TAGS = ["script", "style", "noscript", "iframe", "svg", "form", "nav", "header", "footer", "template"]
JUNK_SELECTORS = [
    "[data-swiftype-index='false']",
    "[id*=cookie i]", "[class*=cookie i]", "[id*=consent i]", "[class*=consent i]",
    "[id*=onetrust i]", "[class*=onetrust i]", "[class*=breadcrumb i]",
    "[class*=social-share i]", "[class*=skip-link i]", "[aria-hidden=true]",
]
JUNK_LINES = re.compile(r"^\s*(\[?skip to (main )?content\]?.*|accept( all)? cookies?|cookie settings|"
                        r"we use cookies.*|share (on|this).*|share|back to top|-+|[|•·]|"
                        r"\[ ?(facebook|twitter|linkedin|email) ?\]\(.*|"
                        r"#* ?have a question about our products or services\??|contact us)\s*$", re.I)

ICON_MARKS = re.compile(r"(?<![\w_])__(?![\w_])\s?")  # leftover icon-font glyphs, e.g. "[ READ  __](...)"

# ---------- cleaning (pure, tested offline) ----------

def page_title(soup):
    for sel in ["meta[property='og:title']", "title"]:
        el = soup.select_one(sel)
        if el:
            t = el.get("content") if el.name == "meta" else el.get_text()
            t = re.sub(r"\s*[|\-–]\s*RealPage\s*$", "", (t or "").strip())
            if t:
                return t
    h1 = soup.find("h1")
    return h1.get_text(" ", strip=True) if h1 else ""


def clean_html(html):
    """Return (title, html of the main content with junk removed)."""
    soup = BeautifulSoup(html, "html.parser")
    title = page_title(soup)
    body = soup.find("main") or soup.find(attrs={"role": "main"}) or soup.find("article") or soup.body or soup
    for sel in JUNK_SELECTORS:
        for el in body.select(sel):
            el.decompose()
    for tag in JUNK_TAGS:
        for el in body.find_all(tag):
            el.decompose()
    return title, str(body)


def html_to_markdown(html, base_url):
    from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
    return DefaultMarkdownGenerator(options={"body_width": 0}).generate_markdown(
        input_html=html, base_url=base_url, citations=False).raw_markdown


def tidy_markdown(md):
    lines, out = md.splitlines(), []
    for ln in lines:
        ln = ICON_MARKS.sub("", ln).rstrip()
        if JUNK_LINES.match(ln):
            continue
        if not ln and out and not out[-1]:
            continue
        out.append(ln)
    return "\n".join(out).strip() + "\n"


def html_page_to_markdown(html, url):
    title, main = clean_html(html)
    return title, tidy_markdown(html_to_markdown(main, url))


# ---------- paths / header / resume ----------

def slug_for(url):
    path = urlparse(url).path.strip("/")
    s = re.sub(r"[^a-z0-9]+", "-", path.lower()).strip("-")
    return (s or "home")[:150]


def page_path(row, site=SITE):
    return site / "pages" / row["type"] / f"{slug_for(row['url'])}.md"


def render(row, title, body, today, source):
    head = {"url": row["url"], "title": title, "type": row["type"], "lastmod": row.get("lastmod", ""),
            "crawled": today, "source": source}
    front = "\n".join(f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in head.items())
    return f"---\n{front}\n---\n\n# {title}\n\n{body}" if title and not body.lstrip().startswith("# ") \
        else f"---\n{front}\n---\n\n{body}"


# ---------- fetchers ----------

class Crawl4AIFetcher:
    """Returns raw HTML via Crawl4AI's HTTP strategy (one shared session)."""

    def __init__(self):
        from crawl4ai import AsyncWebCrawler, HTTPCrawlerConfig
        from crawl4ai.async_crawler_strategy import AsyncHTTPCrawlerStrategy
        self.loop = asyncio.new_event_loop()
        strat = AsyncHTTPCrawlerStrategy(browser_config=HTTPCrawlerConfig(headers={"User-Agent": USER_AGENT}))
        self.crawler = AsyncWebCrawler(crawler_strategy=strat, verbose=False)
        self.loop.run_until_complete(self.crawler.start())

    def __call__(self, url):
        from crawl4ai import CrawlerRunConfig, CacheMode
        r = self.loop.run_until_complete(self.crawler.arun(url, config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)))
        if not r.success or (r.status_code or 200) >= 400:
            raise RuntimeError(f"crawl4ai {r.status_code}: {r.error_message}")
        return r.html

    def close(self):
        self.loop.run_until_complete(self.crawler.close())


def jina_fetch(url):
    """Returns (title, markdown) from Jina Reader, or raises."""
    key = os.environ.get("JINA_API_KEY")
    if not key:
        raise RuntimeError("no JINA_API_KEY")
    req = urllib.request.Request("https://r.jina.ai/" + url, headers={
        "Authorization": f"Bearer {key}", "Accept": "application/json", "User-Agent": USER_AGENT,
        "X-Remove-Selector": "nav, header, footer, [data-swiftype-index='false']", "X-Retain-Images": "none"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode("utf-8", "replace")).get("data") or {}
    return (data.get("title") or "").strip(), tidy_markdown(data.get("content") or "")


def load_env(path=ROOT / ".env"):
    if not path.exists():
        return
    for ln in path.read_text().splitlines():
        m = re.match(r"\s*([A-Z_][A-Z0-9_]*)\s*=\s*(.*)$", ln)
        if m and m.group(1) == "JINA_API_KEY" and not os.environ.get("JINA_API_KEY"):
            os.environ["JINA_API_KEY"] = m.group(2).strip().strip("'\"")


# ---------- main loop ----------

def read_rows(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def crawl(rows, fetch_html, fallback=None, site=SITE, delay=1.0, limit=None, today=None, log=print, sleep=time.sleep):
    today = today or dt.date.today().isoformat()
    failed_path = site / "failed.csv"
    stats = {"saved": 0, "skipped": 0, "failed": 0, "fallback": 0}
    failures, done = [], 0
    for row in rows:
        out = page_path(row, site)
        if out.exists():
            stats["skipped"] += 1
            continue
        if limit is not None and done >= limit:
            break
        done += 1
        title, body, source, err = "", "", "crawl4ai", ""
        try:
            title, body = html_page_to_markdown(fetch_html(row["url"]), row["url"])
        except Exception as e:
            err = str(e)[:200]
        if len(body.strip()) < MIN_CHARS and fallback:
            sleep(delay)
            try:
                t2, b2 = fallback(row["url"])
                if len(b2.strip()) >= len(body.strip()):
                    title, body, source = t2 or title, b2, "jina"
                    stats["fallback"] += 1
            except Exception as e:
                err = (err + " | " if err else "") + "jina: " + str(e)[:200]
        if len(body.strip()) < MIN_CHARS:
            failures.append({"url": row["url"], "type": row["type"],
                             "reason": err or f"only {len(body.strip())} chars"})
            stats["failed"] += 1
            log(f"FAIL {row['url']}: {failures[-1]['reason']}")
        else:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(render(row, title, body, today, source))
            stats["saved"] += 1
            log(f"ok   {row['type']:16} {out.name}")
        sleep(delay)
    write_failed(failed_path, failures)
    return stats


def write_failed(path, failures):
    """Rewrite failed.csv with this run's failures (unsaved pages are retried every run)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["url", "type", "reason"])
        w.writeheader()
        w.writerows(failures)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--urls", default=str(SITE / "urls.csv"))
    ap.add_argument("--limit", type=int)
    ap.add_argument("--delay", type=float, default=1.0)
    ap.add_argument("--only-failed", action="store_true", help="retry just the URLs in failed.csv")
    ap.add_argument("--no-fallback", action="store_true")
    a = ap.parse_args(argv)
    load_env()
    src = SITE / "failed.csv" if a.only_failed else a.urls
    rows = read_rows(src)
    fetcher = Crawl4AIFetcher()
    try:
        stats = crawl(rows, fetcher, None if a.no_fallback else jina_fetch, delay=a.delay, limit=a.limit)
    finally:
        fetcher.close()
    print(json.dumps(stats))


if __name__ == "__main__":
    main()
