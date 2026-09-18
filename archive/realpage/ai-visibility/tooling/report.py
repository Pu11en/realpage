"""Short plain summary of the newest AI Visibility run, for Discord.

    python3 tooling/ai-visibility/report.py [history_folder]

Each AI is compared with its own previous run (never with a different AI). An AI with no earlier
run of its own is shown next to the Sept 12 baseline average instead, marked as such.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NUMBERS = [("mentionPct", "named"), ("unbrandedMentionPct", "named when not asked by name"),
           ("topPickPct", "top pick"), ("lawsuitPct", "lawsuit raised")]
LINK = "http://localhost:8765/ai-visibility.html"


def load(folder: Path) -> list[dict]:
    index = json.loads((folder / "index.json").read_text())
    return [json.loads((folder / r["file"]).read_text()) for r in index["runs"]]


def fmt(v) -> str:
    return "n/a" if v is None else f"{v:.0f}%"


def delta(now, before) -> str:
    if now is None or before is None:
        return ""
    d = now - before
    return " (same)" if abs(d) < 0.5 else f" ({'+' if d > 0 else ''}{d:.0f})"


def summary(runs: list[dict]) -> str:
    real = [r for r in runs if not r.get("baseline")]
    if not real:
        return "No real run yet -- only the Sept 12 baseline."
    latest = real[-1]
    base = next((r for r in runs if r.get("baseline")), None)
    lines = [f"AI Visibility run {latest['date']} (RealPage)"]
    for m in latest["models"]:
        prev = next((pm for r in reversed(real[:-1]) for pm in r["models"] if pm["model"] == m["model"]), None)
        vs = "vs its last run"
        if prev is None and base:
            vs = "vs Sept 12 Claude/ChatGPT average"
            prev = {k: _avg(base["models"], k) for k, _ in NUMBERS}
        answered = m.get("answers", 0) - (m.get("failed") or 0)
        parts = [f"{label} {fmt(m.get(k))}{delta(m.get(k), (prev or {}).get(k))}" for k, label in NUMBERS]
        lines.append(f"- {m['name']} ({answered} answers, {vs}): " + ", ".join(parts))
    sources = (latest.get("lawsuit") or {}).get("sources") or []
    top = [s for s in sources if s["count"] > 0][:3]
    if top:
        lines.append("- Top lawsuit sources: " + ", ".join(
            f"{s['site']} {s['count']}{' (realpage.com!)' if s.get('isTarget') else ''}" for s in top))
    mix = (latest.get("lawsuit") or {}).get("toneMix") or {}
    if mix:
        lines.append("- Lawsuit tone: " + "; ".join(
            f"{k}: " + ", ".join(f"{t} {n}" for t, n in v.items() if n) for k, v in mix.items() if v))
    lines.append(f"- Look: {LINK}")
    return "\n".join(lines)


def _avg(models: list[dict], key: str):
    vals = [m[key] for m in models if m.get(key) is not None]
    return sum(vals) / len(vals) if vals else None


if __name__ == "__main__":
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "site/data/ai-visibility-history"
    print(summary(load(folder)))
