"""Write one short card per RealPage product from the crawled pages (Gemini drafts, code checks).

    python3 tooling/realpage-library/cards.py [--limit N] [--only slug]

Reads archive/realpage/raw/realpage-site/products.csv + the saved pages, asks Gemini for a short JSON summary of
each product using ONLY that product's own pages, and writes archive/realpage/02-products/realpage/<slug>.md.
Every card ends with the realpage.com links it was built from. Resumes: existing cards are kept.
"""
import argparse, csv, importlib.util, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "archive" / "realpage" / "raw" / "realpage-site"
OUT = ROOT / "archive" / "realpage" / "02-products" / "realpage"
MAX_CHARS = 12000

spec = importlib.util.spec_from_file_location("local_ai", ROOT / "tooling" / "ai-visibility" / "local_ai.py")
local_ai = importlib.util.module_from_spec(spec); spec.loader.exec_module(local_ai)

PROMPT = """You are summarising ONE product area from a software company's own website.
Use ONLY the page text below. Never add outside knowledge. If something is not stated, leave it empty.

Return JSON with these keys:
 "name": the product's name as the site writes it,
 "what": 1-2 plain sentences on what it does,
 "who": who it is for (portfolio size, property type, role) or "",
 "also_called": list of other or older names the text mentions (e.g. acquired brands), else [],
 "parts": list of up to 6 named features or sub-products mentioned,
 "claims": list of up to 4 short factual claims the site makes (numbers, integrations, awards).
Plain buyer language, no marketing adjectives.

PAGES:
"""


def page_files(urls):
    by_url = {}
    for p in SITE.glob("pages/*/*.md"):
        text = p.read_text(errors="replace")
        m = re.search(r'url:\s*"([^"]+)"', text)
        if m:
            by_url[m.group(1)] = text
    return [by_url[u] for u in urls if u in by_url]


def slug(url):
    return re.sub(r"[^a-z0-9]+", "-", re.sub(r"^https?://[^/]+/", "", url).strip("/")).strip("-") or "realpage"


def card(row, texts):
    body = "\n\n".join(texts)[:MAX_CHARS]
    raw = local_ai.ask("gemini", PROMPT + body, want_json=True)
    d = json.loads(raw)
    urls = [row["url"]] + [u for u in row["related"].split() if u]
    lines = [f"# RealPage {d.get('name') or row['name']}", "",
             f"**What it is:** {d.get('what','').strip()}"]
    if d.get("who"):
        lines.append(f"**Who it's for:** {d['who'].strip()}")
    if d.get("also_called"):
        lines.append("**Also called:** " + ", ".join(d["also_called"]))
    if d.get("parts"):
        lines += ["", "**Parts of it:**"] + [f"- {x}" for x in d["parts"][:6]]
    if d.get("claims"):
        lines += ["", "**What RealPage says about it:**"] + [f"- {x}" for x in d["claims"][:4]]
    lines += ["", "**Source pages (realpage.com):**"] + [f"- {u}" for u in urls]
    lines += ["", "_Built from RealPage's own website, crawled 2026-09-15. Claims are RealPage's, not checked._"]
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    ap.add_argument("--only")
    a = ap.parse_args(argv)
    OUT.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader((SITE / "products.csv").open()))
    done = failed = 0
    for row in rows:
        s = slug(row["url"])
        if a.only and a.only != s:
            continue
        path = OUT / f"{s}.md"
        if path.exists():
            continue
        texts = page_files([row["url"]] + row["related"].split())
        if not texts:
            print("skip (no pages)", s); continue
        try:
            path.write_text(card(row, texts))
            done += 1
            print("ok  ", s)
        except Exception as exc:
            failed += 1
            print("FAIL", s, type(exc).__name__, exc)
            if isinstance(exc, local_ai.RateLimited):
                break
        if a.limit and done >= a.limit:
            break
    print(json.dumps({"written": done, "failed": failed}))


if __name__ == "__main__":
    main()
