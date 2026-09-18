"""Write archive/realpage/01-company/realpage-key-facts.md from RealPage's own pages (Gemini drafts, code checks).

    python3 tooling/realpage-library/facts.py

Feeds Gemini the company pages plus the newest press-style posts and asks for the company basics,
leadership, acquisitions/renames and anything RealPage says about legal matters. Every fact keeps
the realpage.com link it came from; claims are labelled as RealPage's own.
"""
import importlib.util, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "archive" / "realpage" / "raw" / "realpage-site"
OUT = ROOT / "archive" / "realpage" / "01-company" / "realpage-key-facts.md"
spec = importlib.util.spec_from_file_location("local_ai", ROOT / "tooling" / "ai-visibility" / "local_ai.py")
local_ai = importlib.util.module_from_spec(spec); spec.loader.exec_module(local_ai)

KEYWORDS = ("acquire", "acquisition", "announces", "launches", "rebrand", "renamed", "settlement",
            "lawsuit", "antitrust", "department of justice", "doj", "appoints", "names ")
GROUPS = {
    "basics": "company size, headquarters, ownership, units served, founding year",
    "leadership": "named executives and their roles",
    "acquisitions_and_names": "companies acquired, product renames, retired product names",
    "legal": "anything RealPage says about lawsuits, the Department of Justice, settlements or "
             "regulation (always as RealPage's own statement)",
}
PROMPT = """From the pages below (a software company's own website), list the facts for: {topic}.
Use ONLY the text. Each fact must be one short plain sentence, include its date if the text gives
one, and include the exact page URL it came from (the `url:` line of that page).
Return JSON: {{"facts": [{{"fact": "...", "date": "", "url": "..."}}]}}. Empty list if nothing.

PAGES:
"""


def load(paths, limit):
    out = []
    for p in paths[:limit]:
        out.append(p.read_text(errors="replace")[:4000])
    return "\n\n".join(out)


def pick_posts(n=40):
    scored = []
    for p in SITE.glob("pages/posts/*.md"):
        t = p.read_text(errors="replace").lower()
        score = sum(t.count(k) for k in KEYWORDS)
        if score:
            date = re.search(r'lastmod:\s*"([^"]*)"', t)
            scored.append((score, date.group(1) if date else "", p))
    scored.sort(key=lambda s: (-s[0], s[1]), reverse=False)
    return [p for _, _, p in scored[:n]]


def main():
    company = sorted(SITE.glob("pages/pages/company*.md")) + sorted(SITE.glob("pages/management-team/*.md"))
    posts = pick_posts()
    blocks = {"basics": load(company, 12), "leadership": load(company, 20),
              "acquisitions_and_names": load(posts, 20), "legal": load(posts, 20)}
    lines = ["# RealPage key facts (from RealPage's own website)", "",
             "Built from realpage.com pages crawled 2026-09-15. Everything here is what **RealPage says**; "
             "it is not independently checked. Each line links the page it came from.", ""]
    for key, topic in GROUPS.items():
        raw = local_ai.ask("gemini", PROMPT.format(topic=topic) + blocks[key], want_json=True)
        facts = json.loads(raw).get("facts", [])
        title = key.replace("_", " ").title()
        lines += [f"## {title}", ""]
        if not facts:
            lines += ["- (nothing stated on the pages we have)", ""]
            continue
        for f in facts:
            url = f.get("url", "")
            if "realpage.com" not in url:
                continue
            date = f" ({f['date']})" if f.get("date") else ""
            lines.append(f"- {f['fact'].strip()}{date} — {url}")
        lines.append("")
    OUT.write_text("\n".join(lines))
    print("wrote", OUT.name, len(lines), "lines")


if __name__ == "__main__":
    main()
