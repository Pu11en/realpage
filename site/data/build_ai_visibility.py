"""Turn a NiubiGEO report.json into site/data/ai-visibility.json for the AI Visibility tab.

    python3 site/data/build_ai_visibility.py <niubigeo run dir or report.json> [--demo]

--demo marks the output as practice data (made with a fake AI, not real answers).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

OUT = Path(__file__).with_name("ai-visibility.json")

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
    lawsuit = [q for q in branded if q["bringsUpLawsuit"]]
    missed = sorted({q["question"] for q in unbranded if not q["mentioned"]})
    wins: dict[str, int] = {}
    for q in unbranded:
        if q["winner"]:
            wins[q["winner"]] = wins.get(q["winner"], 0) + 1
    for q in questions:
        del q["fullAnswer"]

    return {
        "demo": demo,
        "founder": {
            "unbrandedAnswers": len(unbranded),
            "unbrandedNamedPct": _share(sum(q["mentioned"] for q in unbranded), len(unbranded)),
            "unbrandedTopPickPct": _share(sum(q["winner"] == target for q in unbranded), len(unbranded)),
            "brandedAnswers": len(branded),
            "lawsuitPct": _share(len(lawsuit), len(branded)),
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


def main(argv: list[str]) -> None:
    args = [a for a in argv if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    src = Path(args[0])
    if src.is_dir():
        src = src / "report.json"
    data = build(json.loads(src.read_text()), demo="--demo" in argv)
    OUT.write_text(json.dumps(data, indent=1))
    print(f"Wrote {OUT} ({len(data['models'])} AIs, {len(data['questions'])} answers)")


if __name__ == "__main__":
    main(sys.argv[1:])
