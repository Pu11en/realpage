"""Turn a NiubiGEO report.json into site/data/ai-visibility.json for the AI Visibility tab.

    python3 site/data/build_ai_visibility.py <niubigeo run dir or report.json> [--demo]
    python3 site/data/build_ai_visibility.py <run dir> --baseline "Claude / ChatGPT, Sept 12"

--demo marks the output as practice data (made with a fake AI, not real answers); practice runs
are not added to the run history.
Every real run is also saved as site/data/ai-visibility-history/<date>.json (one small summary per
AI) and listed in index.json, so the tab can draw trend lines. --baseline only adds the run to the
history, with that label, and leaves ai-visibility.json alone.
Each history file also holds the run's lawsuit data (ai_visibility_lawsuit.py): quotes, tone and the
websites Gemini + Google Search quoted. Real runs label tone with one Gemini call per mention; --baseline,
--demo and --word-tone use the free word list instead.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ai_visibility_lawsuit as lawsuit  # noqa: E402

OUT = Path(__file__).with_name("ai-visibility.json")
HISTORY = Path(__file__).with_name("ai-visibility-history")

# Friendly names for the OpenRouter models we ask.
MODEL_NAMES = {
    "openai": "ChatGPT (OpenAI)",
    "anthropic": "Claude (Anthropic)",
    "google": "Gemini (Google)",
    "perplexity": "Perplexity",
    "deepseek": "DeepSeek",
    # local sessions (tooling/ai-visibility/local_ai.py)
    "claude": "Claude (from memory)",
    "claude-web": "Claude + web search",
    "chatgpt": "ChatGPT (from memory)",
    "gemini": "Gemini (memory)",
    "gemini-web": "Gemini + Google Search",
}


LAWSUIT_RE = re.compile(r"antitrust|\bDOJ\b|Department of Justice|lawsuit|collusion|price[- ]fixing|"
                        r"investigation|settle(?:d|ment)|sued|legal (?:scrutiny|challenges?)", re.I)


def _share(part: int, whole: int) -> float | None:
    return round(part * 100 / whole, 1) if whole else None


def pct(fraction: dict | None) -> float | None:
    if not fraction or fraction.get("value") is None:
        return None
    return round(fraction["value"] * 100, 1)


def model_label(model: str) -> str:
    return MODEL_NAMES.get(model) or MODEL_NAMES.get(model.split("/", 1)[0], model)


def excerpt(text: str, limit: int = 600) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0] + "…"


def build(report: dict, demo: bool) -> dict:
    audit, metrics = report["audit"], report["metrics"]
    target = audit["target"]["name"]

    models = []
    for s in metrics["slices"]:
        if s["sliceType"] != "provider_model":
            continue
        model = s["key"].split("::")[-1] if "::" in s["key"] else s["label"].split(" / ")[-1]
        models.append({
            "model": model,
            "name": model_label(model),
            "answers": s["validResponses"],
            "failed": s["failedResponses"],
            "mentionPct": pct(s["mentionRate"]),
            "recommendPct": pct(s["recommendationRate"]),
            "firstPct": pct(s["firstPositionRate"]),
            "citePct": pct(s["citationRate"]),
            "avgRank": s.get("averageRank"),
        })

    runs = {r["id"]: r for r in audit["runs"]}
    questions = []
    for o in metrics["promptOutcomes"]:
        run = next((r for r in runs.values()
                    if r["prompt"]["id"] == o["promptId"] and r["model"] == o["model"]), None)
        questions.append({
            "question": run["prompt"]["text"] if run else o["promptId"],
            "namesBrand": bool(run and run["prompt"].get("targetIncluded")),
            "model": o["model"],
            "name": model_label(o["model"]),
            "status": o["status"],
            "mentioned": o.get("targetMentioned", False),
            "rank": o.get("targetRank"),
            "sentiment": o.get("sentiment"),
            "winner": o.get("winner"),
            "answer": excerpt(run["result"]["text"]) if run and run.get("result") else "",
            "fullAnswer": run["result"]["text"] if run and run.get("result") else "",
        })

    for q in questions:
        q["bringsUpLawsuit"] = bool(LAWSUIT_RE.search(q["fullAnswer"]))
    ok = [q for q in questions if q["status"] == "completed"]
    unbranded = [q for q in ok if not q["namesBrand"]]
    branded = [q for q in ok if q["namesBrand"]]
    lawsuit_qs = [q for q in branded if q["bringsUpLawsuit"]]
    missed = sorted({q["question"] for q in unbranded if not q["mentioned"]})
    wins: dict[str, int] = {}
    for q in unbranded:
        if q["winner"]:
            wins[q["winner"]] = wins.get(q["winner"], 0) + 1
    for m in models:
        mine = [q for q in branded if q["model"] == m["model"]]
        m["lawsuitPct"] = _share(sum(q["bringsUpLawsuit"] for q in mine), len(mine))
        m["topPickPct"] = _share(sum(q["winner"] == target for q in unbranded if q["model"] == m["model"]),
                                 sum(q["model"] == m["model"] for q in unbranded))
        mine_unbranded = [q for q in unbranded if q["model"] == m["model"]]
        m["unbrandedMentionPct"] = _share(sum(q["mentioned"] for q in mine_unbranded), len(mine_unbranded))
        m["missedQuestions"] = sorted({q["question"] for q in mine_unbranded if not q["mentioned"]})
        my_wins: dict[str, int] = {}
        for q in mine_unbranded:
            if q["winner"]:
                my_wins[q["winner"]] = my_wins.get(q["winner"], 0) + 1
        m["topPicks"] = sorted(({"name": k, "count": v} for k, v in my_wins.items()), key=lambda w: -w["count"])
    for q in questions:
        del q["fullAnswer"]

    return {
        "demo": demo,
        "founder": {
            "unbrandedAnswers": len(unbranded),
            "unbrandedNamedPct": _share(sum(q["mentioned"] for q in unbranded), len(unbranded)),
            "unbrandedTopPickPct": _share(sum(q["winner"] == target for q in unbranded), len(unbranded)),
            "brandedAnswers": len(branded),
            "lawsuitPct": _share(len(lawsuit_qs), len(branded)),
            "negativePct": _share(sum(q["sentiment"] == "negative" for q in ok if q["mentioned"]),
                                  sum(q["mentioned"] for q in ok)),
            "topPicks": sorted(({"name": k, "count": v} for k, v in wins.items()), key=lambda w: -w["count"]),
            "missedQuestions": missed,
        },
        "status": ("Practice data made with a fake AI -- not real answers yet." if demo else ""),
        "target": target,
        "domain": audit["target"]["domain"],
        "generatedAt": report.get("generatedAt"),
        "overall": {
            "answers": metrics["validResponses"],
            "failed": metrics["failedResponses"],
            "mentionPct": pct(metrics["mentionRate"]),
            "recommendPct": pct(metrics["recommendationRate"]),
            "firstPct": pct(metrics["firstPositionRate"]),
            "unpromptedPct": pct(metrics.get("naturalDiscoveryRate")),
            "shareOfVoicePct": pct(metrics["shareOfVoice"]),
            "avgRank": metrics.get("averageRank"),
        },
        "models": models,
        "competitors": sorted(
            ({"name": c["name"], "domain": c["domain"], "mentionPct": pct(c["mentionRate"]),
              "recommendations": c["recommendationCount"], "wins": c.get("wins", 0),
              "avgRank": c.get("averageRank")} for c in metrics["competitors"]),
            key=lambda c: -(c["mentionPct"] or 0)),
        "sources": [{"domain": d["domain"], "type": d["type"], "count": d["citationCount"]}
                    for d in metrics["citationDomains"][:12]],
        "questions": questions,
    }


HISTORY_FIELDS = ("model", "name", "answers", "failed", "mentionPct", "unbrandedMentionPct", "topPickPct",
                  "firstPct", "lawsuitPct", "missedQuestions", "topPicks")


def history_entry(data: dict, label: str = "", baseline: bool = False, lawsuit_data: dict | None = None) -> dict:
    """One run's small summary for the trend lines: per AI numbers, never full answers."""
    date = (data.get("generatedAt") or "")[:10]
    return {
        "date": date,
        "generatedAt": data.get("generatedAt"),
        "label": label or f"{', '.join(m['name'] for m in data['models'])}, {date}",
        "baseline": baseline,
        "target": data["target"],
        "models": [{k: m.get(k) for k in HISTORY_FIELDS} for m in data["models"]],
        "lawsuit": lawsuit_data,
    }


def previous_entry(date: str, folder: Path | None = None) -> dict | None:
    """The newest earlier non-baseline run that has lawsuit data (for the leaderboard's up/down)."""
    folder = folder or HISTORY
    for f in sorted(folder.glob("????-??-??.json"), reverse=True):
        if f.stem < date:
            e = json.loads(f.read_text())
            if not e.get("baseline") and e.get("lawsuit"):
                return e
    return None


def save_history(entry: dict, folder: Path | None = None) -> Path:
    """Write <date>.json (a second run on the same day replaces the first) and refresh index.json."""
    folder = folder or HISTORY
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{entry['date']}.json"
    path.write_text(json.dumps(entry, indent=1))
    runs = []
    for f in sorted(folder.glob("????-??-??.json")):
        e = json.loads(f.read_text())
        runs.append({"date": e["date"], "file": f.name, "label": e["label"], "baseline": e["baseline"],
                     "models": [m["model"] for m in e["models"]]})
    (folder / "index.json").write_text(json.dumps({"runs": runs}, indent=1))
    return path


def main(argv: list[str]) -> None:
    label, args, it = None, [], iter(argv)
    for a in it:
        if a == "--baseline":
            label = next(it, "")
        elif not a.startswith("--"):
            args.append(a)
    if not args:
        sys.exit(__doc__)
    baseline = label is not None
    src = Path(args[0])
    if src.is_dir():
        src = src / "report.json"
    demo = "--demo" in argv
    report = json.loads(src.read_text())
    data = build(report, demo=demo)
    names = {m["model"]: m["name"] for m in data["models"]}
    if baseline:
        found = lawsuit.lawsuit_data(report, src.parent, None, None, names)
        print(f"Saved baseline {save_history(history_entry(data, label, baseline=True, lawsuit_data=found))}")
        return
    OUT.write_text(json.dumps(data, indent=1))
    print(f"Wrote {OUT} ({len(data['models'])} AIs, {len(data['questions'])} answers)")
    if not demo:
        ask = None if "--word-tone" in argv else lawsuit.gemini_tone
        prev = previous_entry((data.get("generatedAt") or "")[:10])
        found = lawsuit.lawsuit_data(report, src.parent, ask, prev, names)
        print(f"Lawsuit: {len(found['mentions'])} mentions, {len(found['sources'])} websites")
        print(f"Saved history {save_history(history_entry(data, lawsuit_data=found))}")


if __name__ == "__main__":
    main(sys.argv[1:])
