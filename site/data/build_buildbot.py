#!/usr/bin/env python3
"""Build site/data/buildbot.json from real repo sources: PLAN-*.md,
PLAN-*.progress.md and git log. Nothing here is hand-typed; every number
comes from counting real files/commits."""
import json
import re
import subprocess
from datetime import date, timezone, datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "buildbot.json"

STUCK_RE = re.compile(r"STUCK|retry|re-run|second attempt|redone", re.IGNORECASE)


def count_plan_checkboxes():
    steps_done = 0
    steps_open = 0
    plans = 0
    for p in sorted(ROOT.glob("PLAN-*.md")):
        if p.name.endswith(".progress.md"):
            continue
        plans += 1
        text = p.read_text(errors="ignore")
        steps_done += len(re.findall(r"^\s*-\s*\[x\]", text, re.IGNORECASE | re.MULTILINE))
        steps_open += len(re.findall(r"^\s*-\s*\[ \]", text, re.MULTILINE))
    return plans, steps_done, steps_open


def parse_progress_entries():
    """Each '## ' heading in a *.progress.md file is one step's log entry.
    Returns list of dicts: plan, task (heading text), body, passed_first_try."""
    entries = []
    for p in sorted(ROOT.glob("PLAN-*.progress.md")):
        plan = p.name[len("PLAN-"):-len(".progress.md")]
        text = p.read_text(errors="ignore")
        # split on level-2 headings
        parts = re.split(r"^## +(.+)$", text, flags=re.MULTILINE)
        # parts[0] is preamble, then alternating heading/body
        for i in range(1, len(parts), 2):
            heading = parts[i].strip()
            body = parts[i + 1] if i + 1 < len(parts) else ""
            passed_first_try = not STUCK_RE.search(body)
            entries.append({
                "plan": plan,
                "task": heading,
                "body": body,
                "passed_first_try": passed_first_try,
            })
    return entries


def pick_examples(entries):
    """Prefer 3 examples from 3 different plans, each with a 'Check' line."""
    examples = []
    used_plans = set()
    check_re = re.compile(r"^.*\bCheck(ed|s)?:?\b.*$", re.MULTILINE | re.IGNORECASE)

    def find_check_line(body):
        m = check_re.search(body)
        return m.group(0).strip() if m else None

    # First pass: distinct plans with a check line
    for e in entries:
        if len(examples) >= 3:
            break
        if e["plan"] in used_plans:
            continue
        check = find_check_line(e["body"])
        if not check:
            continue
        recap_line = next((l.strip() for l in e["body"].splitlines() if l.strip().startswith("-")), "")
        recap = recap_line.lstrip("- ").split(".")[0].strip()
        if not recap:
            recap = e["task"]
        examples.append({
            "plan": e["plan"],
            "task": e["task"],
            "check": check[:220],
            "recap": (recap[:200] + ("..." if len(recap) > 200 else "")),
        })
        used_plans.add(e["plan"])

    # Second pass (fill remaining slots even if plan repeats) if fewer than 3
    if len(examples) < 3:
        for e in entries:
            if len(examples) >= 3:
                break
            check = find_check_line(e["body"])
            if not check:
                continue
            key = (e["plan"], e["task"])
            if any(x["plan"] == e["plan"] and x["task"] == e["task"] for x in examples):
                continue
            recap_line = next((l.strip() for l in e["body"].splitlines() if l.strip().startswith("-")), "")
            recap = recap_line.lstrip("- ").split(".")[0].strip() or e["task"]
            examples.append({
                "plan": e["plan"],
                "task": e["task"],
                "check": check[:220],
                "recap": (recap[:200] + ("..." if len(recap) > 200 else "")),
            })
    return examples[:3]


def count_commits():
    try:
        out = subprocess.run(
            ["git", "log", "--oneline"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout
        return len([l for l in out.splitlines() if l.strip()])
    except Exception:
        return None


def main():
    plans, steps_done, steps_open = count_plan_checkboxes()
    entries = parse_progress_entries()
    n_entries = len(entries)
    n_first_try = sum(1 for e in entries if e["passed_first_try"])
    first_try_pct = round(100 * n_first_try / n_entries, 1) if n_entries else None
    examples = pick_examples(entries)
    commits = count_commits()

    data = {
        "plans": plans,
        "steps_done": steps_done,
        "steps_open": steps_open,
        "progress_entries": n_entries,
        "first_try_pct": first_try_pct,
        "commits": commits,
        "examples": examples,
        "measured_at": date.today().isoformat(),
        "method": (
            "Counted every '- [x]' / '- [ ]' line in PLAN-*.md as a done/open step. "
            "Counted every '## ' heading in PLAN-*.progress.md as one step's log entry. "
            "An entry counts as 'passed first try' only if its text has no case-insensitive "
            "match for STUCK, retry, re-run, second attempt, or redone. Commits = "
            "`git log --oneline | wc -l` in this worktree."
        ),
    }
    OUT.write_text(json.dumps(data, indent=2) + "\n")
    print(f"wrote {OUT} ({n_entries} entries, {first_try_pct}% first try, {commits} commits)")


if __name__ == "__main__":
    main()
