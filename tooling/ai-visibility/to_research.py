"""Write the AI Visibility results as a research note the chatbot can read.

Reads site/data/ai-visibility.json + ai-visibility-actions.json and writes
09-ai-visibility/summary.md (copied into the chatbot image with the other research folders).
Re-run after tooling/ai-visibility/run.sh.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
d = json.loads((ROOT / "site/data/ai-visibility.json").read_text())
a = json.loads((ROOT / "site/data/ai-visibility-actions.json").read_text())
o, f = d["overall"], d["founder"]

L = [f"# AI Visibility: what AIs say about RealPage (test of {d['generatedAt'][:10]})", "",
     "Shown on the dashboard in the AI Visibility tab.",
     f"Based on: {a['basedOn']}", "", f"**Verdict:** {a['headline']}", "", "## Key numbers",
     f"- {o['answers']} AI answers. RealPage mentioned in {o['mentionPct']:.0f}%, recommended in {o['recommendPct']:.0f}%, named first in {o['firstPct']:.0f}%.",
     f"- When the question does not name RealPage: named in {f['unbrandedNamedPct']:.0f}%, top pick in only {f['unbrandedTopPickPct']:.0f}%.",
     f"- When the question names RealPage: {f['lawsuitPct']:.0f}% of answers bring up the antitrust lawsuit.",
     "- Top picks: " + ", ".join(f"{t['name']} {t['count']}" for t in f["topPicks"]) + ".",
     "", "## By AI"]
L += [f"- {m['name']}: mentioned {m['mentionPct']:.0f}%, recommended {m['recommendPct']:.0f}%, lawsuit {m['lawsuitPct']:.0f}%." for m in d["models"]]
L += ["", "## Competitors in AI answers"]
L += [f"- {c['name']}: mentioned {c['mentionPct']:.0f}%, won {c['wins']} questions." for c in d["competitors"]]
L += ["", "## Questions RealPage missed (a competitor won)"] + [f"- {q}" for q in f["missedQuestions"]]
L += ["", "## realpage.com facts"] + [("- OK: " if s["ok"] else "- Problem: ") + s["text"] for s in a["siteFacts"]]
L += ["", "## To-do list"]
for g in a["groups"]:
    L.append(f"### {g['when']}")
    for x in g["actions"]:
        L.append(f"- **{x['title']}** ({x.get('effort', '')}). Why: {x['why']} Do: {x['do']}")
out = ROOT / "09-ai-visibility/summary.md"
out.parent.mkdir(exist_ok=True)
out.write_text("\n".join(L) + "\n")
print(out)
