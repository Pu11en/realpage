"""Build the compact realpage.com page index and the product list from the crawled pages.

    python3 tooling/realpage-library/index.py

Reads raw/realpage-site/pages/<type>/*.md (from crawl.py) and writes:
  01-company/realpage-site-index.md   one line per non-blog page, grouped by type; blog-like
                                      types only as a count plus the newest titles
  raw/realpage-site/products.csv      name, url, related pages (same top-level section)
No network, no AI.
"""
import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "raw" / "realpage-site"
INDEX_OUT = ROOT / "01-company" / "realpage-site-index.md"
PRODUCTS_OUT = SITE / "products.csv"

LISTED = ["pages", "case-studies", "ebooks", "management-team", "testimonials", "hub-terms"]
COUNTED = ["posts", "videos", "webcasts", "episodes"]
NEWEST = 50
# Top-level sections of "pages" that are not products.
NOT_PRODUCT = {
    "", "about", "company", "careers", "contact", "contact-us", "legal", "support", "user-group",
    "training", "trademarks", "events", "news", "blog", "resources", "privacy", "accessibility",
    "sitemap", "login", "partners", "investors", "leadership", "customer-stories", "webinars",
    "accessibility-statement", "client-login", "podcasts", "resident-resource-center", "standard-sow-services",
    "vendor-support", "markets",
}


def read_page(path):
    """Header fields of one saved page (the small front-matter block crawl.py writes)."""
    meta = {}
    lines = path.read_text(errors="replace").splitlines()
    if lines and lines[0] == "---":
        for line in lines[1:]:
            if line == "---":
                break
            m = re.match(r'(\w+):\s*"?(.*?)"?$', line)
            if m:
                meta[m.group(1)] = m.group(2)
    meta.setdefault("title", path.stem.replace("-", " ").title())
    meta.setdefault("type", path.parent.name)
    return meta


def load(pages_dir):
    by_type = defaultdict(list)
    for p in sorted(pages_dir.glob("*/*.md")):
        m = read_page(p)
        if m.get("url"):
            by_type[m["type"]].append(m)
    return by_type


def section(url):
    path = re.sub(r"^https?://[^/]+/", "", url).strip("/")
    return path.split("/")[0] if path else ""


def products(pages):
    by_sec = defaultdict(list)
    for m in pages:
        by_sec[section(m["url"])].append(m)
    rows = []
    for sec, items in sorted(by_sec.items()):
        if sec in NOT_PRODUCT:
            continue
        items.sort(key=lambda m: m["url"].rstrip("/").count("/"))
        head = items[0]
        rows.append({
            "name": head["title"],
            "url": head["url"],
            "related": " ".join(m["url"] for m in items[1:]),
        })
    return rows


def render(by_type, crawled_count):
    out = ["# realpage.com page index", "",
           f"Every page RealPage publishes on realpage.com ({crawled_count} saved pages). "
           "Titles link to the live page. Blog posts, videos, webcasts and podcast episodes "
           "are listed as a count plus the newest titles.", ""]
    for t in LISTED:
        items = sorted(by_type.get(t, []), key=lambda m: m["title"].lower())
        if not items:
            continue
        out += [f"## {t.replace('-', ' ').title()} ({len(items)})", ""]
        out += [f"- [{m['title']}]({m['url']})" for m in items]
        out.append("")
    for t in COUNTED:
        items = sorted(by_type.get(t, []), key=lambda m: m.get("lastmod", ""), reverse=True)
        if not items:
            continue
        out += [f"## {t.replace('-', ' ').title()} ({len(items)} total, newest {min(NEWEST, len(items))})", ""]
        out += [f"- [{m['title']}]({m['url']})" for m in items[:NEWEST]]
        out.append("")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", default=str(SITE / "pages"))
    ap.add_argument("--index-out", default=str(INDEX_OUT))
    ap.add_argument("--products-out", default=str(PRODUCTS_OUT))
    a = ap.parse_args(argv)
    by_type = load(Path(a.pages))
    total = sum(len(v) for v in by_type.values())
    Path(a.index_out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.index_out).write_text(render(by_type, total))
    rows = products(by_type.get("pages", []))
    with open(a.products_out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["name", "url", "related"])
        w.writeheader()
        w.writerows(rows)
    print(f"index: {total} pages; products: {len(rows)}")


if __name__ == "__main__":
    main()
