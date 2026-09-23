#!/usr/bin/env python3
"""Ask the AI engines the questions in questions.csv and save what they answer.

This is the before-picture. Today CraneSignal is almost certainly named in none of the
the answers; running the same questions again in a few weeks is the only way to show
whether the SEO work moved anything. Every question is one CraneSignal's own buyer would
ask -- where to find buildings under construction, who just bought a complex, who to call
before a building opens -- not which property-management software to buy, which is a
different market and was the archived RealPage project.

Two engines, because they are the two we actually have:

  claude-web  `claude -p` on the subscription, web search allowed. Each question runs in
              a fresh process with --setting-sources "" so this repo's own files and
              instructions cannot leak into the answer and flatter us.
  gemini      gemini-2.5-flash with Google Search grounding, key from .env.seo.

Neither is the consumer app. An API or CLI answer is not word-for-word what a person sees
in chatgpt.com or the Gemini app, and every report this writes says so.

    python3 tooling/seo/sample.py                      # both engines, all questions
    python3 tooling/seo/sample.py --engine gemini      # one engine
    python3 tooling/seo/sample.py --set A --limit 5    # a slice
    python3 tooling/seo/sample.py --report-only        # rebuild the report from saved answers

Answers are written one JSON file per question per engine, so a stopped run resumes
without re-asking anything it already has.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUESTIONS = Path(__file__).resolve().parent / "questions.csv"
ENV_FILE = ROOT / ".env.seo"
OUT_ROOT = ROOT / "docs" / "seo" / "answer-share"

ENGINES = ("claude-web", "gemini")

# A hard ceiling on subscription usage. The run stops and says what it skipped rather
# than quietly spending an afternoon of someone's quota.
CLAUDE_CALL_CAP = 60
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_PAUSE_SECONDS = 2.0

# Who we are competing with for these answers. CraneSignal sells lead data on buildings,
# so the names that matter are the property-data and construction-pipeline services -- not
# the property-management software vendors, which are a different market entirely and were
# the subject of the archived RealPage work, not this one.
BRANDS = {
    "CraneSignal": ["cranesignal", "crane signal"],
    # Paid property and construction data -- the direct competition.
    "CoStar": ["costar"],
    "Yardi Matrix": ["yardi matrix"],
    "Dodge": ["dodge construction", "dodge data", "dodge analytics"],
    "ConstructConnect": ["constructconnect", "construct connect"],
    "BuildCentral": ["buildcentral", "build central"],
    "Reonomy": ["reonomy"],
    "PropertyShark": ["propertyshark", "property shark"],
    "LoopNet": ["loopnet"],
    "Crexi": ["crexi"],
    "BuildZoom": ["buildzoom"],
    "Cherre": ["cherre"],
    "HelloData": ["hellodata", "hello data"],
    "Moody's": ["moody's analytics", "moodys analytics", "real capital analytics"],
    # Brokerages that publish the market reports these questions often land on.
    "CBRE": ["cbre"],
    "Berkadia": ["berkadia"],
    "Marcus & Millichap": ["marcus & millichap", "marcus and millichap"],
    "Cushman & Wakefield": ["cushman"],
    "JLL": ["jll"],
    "Northmarq": ["northmarq"],
    "MMG": ["mmg real estate", "mmgrea"],
    # Contact and prospecting tools, for the "who do I call" questions.
    "ZoomInfo": ["zoominfo"],
    "Apollo": ["apollo.io"],
    "LinkedIn Sales Navigator": ["sales navigator"],
    # Renter-facing listing sites. If these come back, the question was read as a renter
    # asking for somewhere to live, which tells us the phrasing is wrong for our buyer.
    "Apartments.com": ["apartments.com"],
    "Zillow": ["zillow"],
    # Property-management software, kept only because the engines volunteer it on the
    # "which software does this building run" questions.
    "RealPage": ["realpage"],
    "Yardi (software)": ["yardi voyager", "yardi breeze"],
    "AppFolio": ["appfolio"],
    "Entrata": ["entrata"],
    # Not a vendor: the answer "go read the public records yourself". Worth counting,
    # because that is our own source, and an engine that says this is one step from
    # citing a site that has already done it.
    "Public records (DIY)": [
        "appraisal district", "permit office", "county clerk", "building department",
        "open records", "public records request", "tdlr", "permit portal",
    ],
}

ASK = (
    "{question}\n\n"
    "Answer as you normally would for someone researching this. "
    "Name specific companies, products or data sources where they apply, and list any "
    "sources you used."
)


def load_env_key(name: str) -> str | None:
    """Read one key out of .env.seo without importing anything or printing it."""
    if not ENV_FILE.exists():
        return None
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        if key.strip() == name:
            return value.strip().strip('"').strip("'") or None
    return None


def read_questions(which_set: str | None, limit: int | None) -> list[dict]:
    rows = list(csv.DictReader(QUESTIONS.open(encoding="utf-8")))
    if which_set:
        rows = [r for r in rows if r["set"].upper() == which_set.upper()]
    for i, row in enumerate(rows, start=1):
        row["n"] = i
    return rows[:limit] if limit else rows


def slug_for(row: dict) -> str:
    return f"{row['set'].lower()}-{row['n']:02d}"


# ------------------------------------------------------------------ the two engines


def ask_claude(question: str, timeout: int = 300) -> dict:
    """One question, one fresh `claude -p`. No repo context, web search allowed."""
    cmd = [
        "claude", "-p",
        "--model", "sonnet",
        "--setting-sources", "",
        "--allowedTools", "WebSearch,WebFetch",
    ]
    try:
        done = subprocess.run(
            cmd,
            input=ASK.format(question=question),
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(Path.home()),  # away from this repo, so nothing local is in reach
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"timed out after {timeout}s"}
    if done.returncode != 0:
        return {"ok": False, "error": (done.stderr or done.stdout or "").strip()[:400]}
    return {"ok": True, "answer": done.stdout.strip()}


def ask_gemini(question: str, api_key: str, timeout: int = 120) -> dict:
    """gemini-2.5-flash with Google Search grounding, so it answers from the live web."""
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent"
    )
    payload = {
        "contents": [{"parts": [{"text": ASK.format(question=question)}]}],
        "tools": [{"google_search": {}}],
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        detail = err.read().decode("utf-8", "replace")[:300]
        return {"ok": False, "error": f"HTTP {err.code}: {detail}"}
    except Exception as err:  # noqa: BLE001 - network shapes vary; the message is what matters
        return {"ok": False, "error": str(err)[:300]}

    try:
        candidate = body["candidates"][0]
        text = "".join(
            part.get("text", "") for part in candidate["content"]["parts"]
        ).strip()
    except (KeyError, IndexError):
        return {"ok": False, "error": f"unexpected response shape: {str(body)[:200]}"}

    # Grounded answers carry the pages the model actually read. Those are worth keeping:
    # they say who the engine treats as authoritative on the question.
    sources = []
    grounding = candidate.get("groundingMetadata") or {}
    for chunk in grounding.get("groundingChunks") or []:
        web = chunk.get("web") or {}
        if web.get("uri"):
            sources.append({"title": web.get("title") or "", "url": web["uri"]})
    return {"ok": True, "answer": text, "sources": sources}


# ------------------------------------------------------------------ reading answers


def brands_in(text: str) -> list[dict]:
    """Which brands an answer names, and where each first appears.

    Position matters more than count: the first name in a recommendation is the one a
    reader acts on.
    """
    lowered = (text or "").lower()
    found = []
    for brand, needles in BRANDS.items():
        hits = [lowered.find(n) for n in needles if lowered.find(n) != -1]
        if hits:
            first = min(hits)
            found.append(
                {
                    "brand": brand,
                    "first_at": first,
                    "mentions": sum(lowered.count(n) for n in needles),
                }
            )
    found.sort(key=lambda item: item["first_at"])
    for rank, item in enumerate(found, start=1):
        item["rank"] = rank
    return found


def urls_in(text: str) -> list[str]:
    raw = re.findall(r"https?://[^\s)\]>,\"']+", text or "")
    seen, out = set(), []
    for url in raw:
        url = url.rstrip(".,;")
        host = re.sub(r"^https?://(www\.)?", "", url).split("/")[0]
        if host and host not in seen:
            seen.add(host)
            out.append(url)
    return out


# ------------------------------------------------------------------ run and report


def run(engine: str, rows: list[dict], out_dir: Path, api_key: str | None,
        force: bool) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    calls = 0
    skipped: list[str] = []

    for row in rows:
        path = out_dir / f"{engine}-{slug_for(row)}.json"
        if path.exists() and not force:
            continue

        if engine == "claude-web":
            if calls >= CLAUDE_CALL_CAP:
                skipped.append(row["question"])
                continue
            result = ask_claude(row["question"])
        else:
            result = ask_gemini(row["question"], api_key or "")
            time.sleep(GEMINI_PAUSE_SECONDS)
        calls += 1

        record = {
            "engine": engine,
            "engine_label": {
                "claude-web": "Claude (Sonnet) via claude -p, web search on",
                "gemini": f"Gemini ({GEMINI_MODEL}) via API, Google Search grounding on",
            }[engine],
            "is_consumer_app": False,
            "set": row["set"],
            "question": row["question"],
            "intent": row.get("intent", ""),
            "asked_on": date.today().isoformat(),
            **result,
        }
        if result.get("ok"):
            record["brands"] = brands_in(result["answer"])
            record["links"] = result.get("sources") or [
                {"title": "", "url": u} for u in urls_in(result["answer"])
            ]
        path.write_text(json.dumps(record, indent=2), encoding="utf-8")

        state = "ok" if result.get("ok") else "FAILED"
        names = ", ".join(b["brand"] for b in record.get("brands", [])[:4]) or "-"
        print(f"  [{engine}] {slug_for(row)} {state}: {names}", flush=True)

        # An auth or quota failure will not fix itself on the next question.
        if not result.get("ok") and re.search(
            r"auth|credit|quota|rate limit|429|401|403", result.get("error", ""), re.I
        ):
            print(f"  stopping {engine}: {result['error'][:160]}", file=sys.stderr)
            break

    return {"calls": calls, "skipped": skipped}


def host_of(link: dict) -> str:
    """The site an engine actually read.

    Gemini's grounding links are Vertex redirect URLs, which say nothing; the chunk's
    title carries the real domain, so prefer that when it looks like one.
    """
    title = (link.get("title") or "").strip()
    if re.fullmatch(r"[a-z0-9.-]+\.[a-z]{2,}", title, re.I):
        return title.lower()
    url = link.get("url") or ""
    if "vertexaisearch.cloud.google.com" in url:
        return title or "(redirect)"
    return re.sub(r"^https?://(www\.)?", "", url).split("/")[0]


def build_report(out_dir: Path, rows: list[dict]) -> str:
    records = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(out_dir.glob("*.json"))]
    answered = [r for r in records if r.get("ok")]
    failed = [r for r in records if not r.get("ok")]
    engines = sorted({r["engine"] for r in records})
    today = date.today().isoformat()

    by_question: dict[str, dict[str, dict]] = {}
    for record in answered:
        by_question.setdefault(record["question"], {})[record["engine"]] = record

    def share(subset: list[dict]) -> list[tuple[str, int, int]]:
        counts: dict[str, int] = {}
        for record in subset:
            for brand in record.get("brands", []):
                counts[brand["brand"]] = counts.get(brand["brand"], 0) + 1
        return sorted(
            ((brand, n, len(subset)) for brand, n in counts.items()),
            key=lambda t: -t[1],
        )

    lines = [
        f"# Who the AI engines name when someone is looking for apartment leads — {today}",
        "",
        "The before-picture, taken while the SEO work sits on a branch and nothing is",
        "deployed. Re-run `tooling/seo/sample.py` in a few weeks and compare.",
        "",
        "Every question here is one CraneSignal's own buyer would ask: how to find",
        "buildings under construction, who just bought a complex, where to get the data",
        "free, who to call before a building opens. We are not measuring the",
        "property-management software market -- that was the archived RealPage project, a",
        "different business.",
        "",
        "**These are not the consumer apps.** `claude-web` is `claude -p` on the",
        "subscription with web search; `gemini` is the Gemini API with Google Search",
        "grounding. A person typing into chatgpt.com or the Gemini app may see something",
        "different. Treat this as a directional read, not a transcript.",
        "",
        f"Engines: {', '.join(engines)} · Questions answered: {len(answered)}"
        + (f" · Failed: {len(failed)}" if failed else ""),
        "",
        "## The headline number",
        "",
    ]

    overall = share(answered)
    total = len(answered)
    cs = next((row for row in overall if row[0] == "CraneSignal"), None)
    lines += [
        f"**CraneSignal is named in {cs[1] if cs else 0} of {total} answers.**",
        "",
        "When that number starts moving, the SEO work is landing. Everything below is who",
        "is getting named instead.",
        "",
        "## Who gets named, across every question",
        "",
        "| Named | Answers | Share |",
        "|---|---|---|",
    ]
    for brand, n, tot in overall:
        lines.append(f"| {brand} | {n} / {tot} | {round(100 * n / tot)}% |")
    lines.append("")

    # Splitting by intent is what makes this actionable: "buy CoStar" on a pipeline
    # question means something different from "read the permit office" on the same one.
    intents = []
    for record in answered:
        if record.get("intent") and record["intent"] not in intents:
            intents.append(record["intent"])
    if intents:
        lines += [
            "## By what the asker actually wants",
            "",
            "Top three names per intent, so it is clear which questions are winnable.",
            "",
            "| What they asked for | Answers | Most-named |",
            "|---|---|---|",
        ]
        for intent in intents:
            subset = [r for r in answered if r.get("intent") == intent]
            top = share(subset)[:3]
            named = ", ".join(f"{b} {round(100 * n / t)}%" for b, n, t in top) or "nobody"
            lines.append(f"| {intent} | {len(subset)} | {named} |")
        lines.append("")

    # Which sites the engines read is more actionable than which brands they name: it is
    # the list of places that already earn citations on these questions.
    cited: dict[str, int] = {}
    for record in answered:
        for host in {host_of(link) for link in record.get("links", [])}:
            if host and host != "(redirect)":
                cited[host] = cited.get(host, 0) + 1
    top_cited = sorted(cited.items(), key=lambda kv: -kv[1])[:20]
    if top_cited:
        lines += [
            "## Which sites the engines actually read",
            "",
            "Counted across every answer, so this is who the engines currently treat as",
            "authoritative on these questions — and therefore what a new page has to sit",
            "alongside to get cited.",
            "",
            "| Site | Answers citing it |",
            "|---|---|",
        ]
        lines += [f"| {host} | {n} |" for host, n in top_cited]
        lines.append("")

    lines += ["## Question by question", ""]
    for row in rows:
        per_engine = by_question.get(row["question"])
        if not per_engine:
            continue
        lines.append(f"### {row['question']}")
        if row.get("intent"):
            lines.append(f"*{row['intent']}*")
        lines.append("")
        for engine in engines:
            record = per_engine.get(engine)
            if not record:
                continue
            named = ", ".join(
                f"{b['brand']} (#{b['rank']})" for b in record.get("brands", [])
            ) or "no tracked names"
            lines.append(f"- **{engine}** — {named}")
            hosts = []
            for link in record.get("links", [])[:6]:
                host = host_of(link)
                if host and host not in hosts:
                    hosts.append(host)
            if hosts:
                lines.append(f"  - cited: {', '.join(hosts)}")
        # Where the two engines name different leaders, that difference is the finding.
        leaders = {
            engine: (rec.get("brands") or [{}])[0].get("brand")
            for engine, rec in per_engine.items()
        }
        distinct = {v for v in leaders.values() if v}
        if len(distinct) > 1:
            lines.append(
                "  - **engines disagree on who comes first:** "
                + "; ".join(f"{e} says {b}" for e, b in leaders.items() if b)
            )
        lines.append("")

    if failed:
        lines += ["## Questions that did not get an answer", ""]
        for record in failed:
            lines.append(
                f"- `{record['engine']}` {record['set']}: {record['question']} — "
                f"{record.get('error', '')[:160]}"
            )
        lines.append("")

    lines += [
        "## How to read this",
        "",
        "- Position beats volume: the first name in an answer is the one a reader acts on.",
        "- 'cited' lists the hosts the engine actually read, which says who it treats as",
        "  authoritative on the question. Those are the pages to be published alongside.",
        "- Counts move week to week on their own. Only a repeated, sizeable change means",
        "  anything.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", choices=ENGINES, help="default: both")
    parser.add_argument("--set", dest="which_set", choices=["A", "B"])
    parser.add_argument("--limit", type=int)
    parser.add_argument("--force", action="store_true", help="re-ask questions already saved")
    parser.add_argument("--report-only", action="store_true")
    parser.add_argument("--out", help="run folder name (default: today)")
    args = parser.parse_args()

    rows = read_questions(args.which_set, args.limit)
    out_dir = OUT_ROOT / (args.out or date.today().isoformat())

    if not args.report_only:
        engines = [args.engine] if args.engine else list(ENGINES)
        api_key = load_env_key("GEMINI_API_KEY")
        if "gemini" in engines and not api_key:
            print("no GEMINI_API_KEY in .env.seo -- skipping gemini", file=sys.stderr)
            engines = [e for e in engines if e != "gemini"]
        for engine in engines:
            print(f"{engine}: {len(rows)} questions", flush=True)
            result = run(engine, rows, out_dir, api_key, args.force)
            if result["skipped"]:
                print(
                    f"  {engine}: {len(result['skipped'])} question(s) skipped at the "
                    f"{CLAUDE_CALL_CAP}-call cap",
                    file=sys.stderr,
                )

    if not out_dir.exists():
        print("nothing to report on", file=sys.stderr)
        return 1
    report = build_report(out_dir, rows)
    (out_dir / "report.md").write_text(report, encoding="utf-8", newline="\n")
    print(f"\nwrote {out_dir.relative_to(ROOT).as_posix()}/report.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
