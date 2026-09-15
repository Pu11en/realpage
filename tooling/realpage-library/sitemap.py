#!/usr/bin/env python3
"""Build the realpage.com page list from the cms sitemap index.

    python3 tooling/realpage-library/sitemap.py            # live, polite (1 req/sec)
    python3 tooling/realpage-library/sitemap.py --out X.csv

Writes raw/realpage-site/urls.csv with columns url,type,lastmod.
type comes from the sub-sitemap name (posts-sitemap.xml -> posts).
Drops duplicate URLs and anything under /search (robots.txt disallows it).
"""
import argparse
import csv
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

INDEX_URL = "https://www.realpage.com/cms-sitemap.xml"
USER_AGENT = "CraneSignal-library/1.0 (research crawl; polite, 1 req/sec)"
NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "raw" / "realpage-site" / "urls.csv"


def http_fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def parse_index(xml_text):
    """Return list of (sub-sitemap url, type)."""
    root = ET.fromstring(xml_text.strip())
    out = []
    for loc in root.findall("s:sitemap/s:loc", NS):
        url = loc.text.strip()
        out.append((url, sitemap_type(url)))
    return out


def sitemap_type(url):
    name = urlparse(url).path.rsplit("/", 1)[-1]
    return re.sub(r"-?sitemap\d*\.xml$", "", name) or "other"


def parse_urlset(xml_text):
    """Return list of (url, lastmod)."""
    root = ET.fromstring(xml_text.strip())
    out = []
    for u in root.findall("s:url", NS):
        loc = u.find("s:loc", NS)
        if loc is None or not (loc.text or "").strip():
            continue
        lm = u.find("s:lastmod", NS)
        out.append((loc.text.strip(), (lm.text or "").strip() if lm is not None else ""))
    return out


def blocked(url):
    path = urlparse(url).path
    return path == "/search" or path.startswith("/search/") or path.startswith("/search?")


def normalize(url):
    return url.split("#", 1)[0]


def build_rows(fetch, index_url=INDEX_URL, delay=1.0, log=None):
    rows, seen = [], set()
    subs = parse_index(fetch(index_url))
    for sub_url, typ in subs:
        time.sleep(delay)
        try:
            entries = parse_urlset(fetch(sub_url))
        except Exception as e:  # keep going; report the miss
            print(f"WARN {sub_url}: {e}", file=log or sys.stderr)
            continue
        for url, lastmod in entries:
            url = normalize(url)
            if blocked(url) or url in seen:
                continue
            seen.add(url)
            rows.append({"url": url, "type": typ, "lastmod": lastmod})
    return rows


def write_csv(rows, out):
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["url", "type", "lastmod"])
        w.writeheader()
        w.writerows(rows)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--delay", type=float, default=1.0)
    a = ap.parse_args(argv)
    rows = build_rows(http_fetch, delay=a.delay)
    write_csv(rows, a.out)
    counts = {}
    for r in rows:
        counts[r["type"]] = counts.get(r["type"], 0) + 1
    for t, n in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"{t:20} {n}")
    print(f"{'TOTAL':20} {len(rows)} -> {a.out}")


if __name__ == "__main__":
    main()
