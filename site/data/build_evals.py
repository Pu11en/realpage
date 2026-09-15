#!/usr/bin/env python3
"""Build page measurements from a current scorecard or the saved historical one.

The saved scorecard is deliberately committed with the site.  That keeps the
recruiter evidence reproducible after the disposable evaluation worktree is
gone, while its ``historical`` status prevents it from being mistaken for a
passing release check.
"""
import json
import os
import re
import statistics
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHIPCHECK_DIR = Path(os.environ["SHIPCHECK_DIR"]) if os.environ.get("SHIPCHECK_DIR") else None
SAVED_SCORECARD = HERE / "recruiter-scorecard.json"
NOT_RUN = "not run yet"


def safe_json(path):
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def saved_measurements():
    """Return the checked-in recruiter evidence, without machine-specific paths."""
    saved = safe_json(SAVED_SCORECARD)
    if not isinstance(saved, dict):
        return None
    return saved


def parse_scorecard_statuses(md_text):
    """Fallback: parse the '| Check | Result | ... |' table in scorecard.md."""
    statuses = {}
    for line in md_text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2 or cells[0] in ("Check", "---") or set(cells[0]) <= {"-"}:
            continue
        name, result = cells[0], cells[1]
        if result in ("PASS", "FAIL"):
            statuses[name] = result
    return statuses


def build_evals():
    saved = saved_measurements()
    if SHIPCHECK_DIR is None or not SHIPCHECK_DIR.exists():
        if saved:
            return saved["evals"]
        return {
            "checks": NOT_RUN,
            "checks_passed": NOT_RUN,
            "checks_total": NOT_RUN,
            "failure_types": NOT_RUN,
            "human_review": NOT_RUN,
            "false_alarm_rate": NOT_RUN,
            "measured_at": date.today().isoformat(),
            "evidence_status": "not run yet",
            "method": "No current scorecard or saved historical scorecard is available.",
            "limitations": ["No evaluation result is available."],
        }
    run_json = safe_json(SHIPCHECK_DIR / "results/latest/run.json")
    scorecard_path = SHIPCHECK_DIR / "results/latest/scorecard.md"
    scorecard_text = scorecard_path.read_text() if scorecard_path.exists() else None
    failure_types = safe_json(SHIPCHECK_DIR / "results/latest/failure-types.json")
    pregrade = safe_json(SHIPCHECK_DIR / "results/labels/pregrade.json")

    label_files = sorted((SHIPCHECK_DIR / "results/labels").glob("drew-*.json")) if \
        (SHIPCHECK_DIR / "results/labels").exists() else []
    drew_labels = safe_json(label_files[-1]) if label_files else None

    verdicts = safe_json(SHIPCHECK_DIR / "results/baseline/verdicts.json")

    checks = []
    n_passed = 0
    n_total = 0
    if run_json and isinstance(run_json.get("checks"), list):
        statuses = parse_scorecard_statuses(scorecard_text) if scorecard_text else {}
        for c in run_json["checks"]:
            name = c.get("name")
            status = statuses.get(name, c.get("status", NOT_RUN))
            checks.append({
                "name": name,
                "status": status,
                "seconds": c.get("seconds"),
                "cost_usd": c.get("cost_usd"),
            })
        n_total = len(checks)
        n_passed = sum(1 for c in checks if c["status"] == "PASS")
    else:
        checks = NOT_RUN

    failure_summary = NOT_RUN
    if failure_types and isinstance(failure_types.get("counts"), dict):
        counts = failure_types["counts"]
        examples = failure_types.get("examples", {})
        failure_summary = {
            "n": failure_types.get("n"),
            "types": [
                {
                    "type": t,
                    "count": n,
                    "example_question": examples.get(t, {}).get("question"),
                }
                for t, n in sorted(counts.items(), key=lambda kv: -kv[1])
                if t != "ok"
            ],
            "ok_count": counts.get("ok"),
        }

    # Human review agreement: compare drew's label decision to the AI's
    # ai_grade for the same question id, where both exist.
    review = NOT_RUN
    if drew_labels and isinstance(drew_labels.get("labels"), dict):
        labels = drew_labels["labels"]
        ai_by_id = {}
        if pregrade:
            for key in ("answers", "bot_steps"):
                for a in pregrade.get(key) or []:
                    ai_by_id[a["id"]] = a.get("ai_grade")
        comparable = 0
        agree = 0
        for qid, entry in labels.items():
            ai_grade = ai_by_id.get(qid)
            if ai_grade not in ("pass", "fail"):
                continue
            comparable += 1
            if ai_grade == entry.get("decision"):
                agree += 1
        review = {
            "n_reviewed": len(labels),
            "n_comparable_to_ai": comparable,
            "agreement_pct": round(100 * agree / comparable, 1) if comparable else None,
            "label_file": label_files[-1].name if label_files else None,
        }

    false_alarm = NOT_RUN
    if isinstance(verdicts, dict) and verdicts:
        vals = list(verdicts.values())
        n = len(vals)
        n_false = sum(1 for v in vals if v.get("verdict") == "false_alarm")
        false_alarm = {
            "n_reviewed": n,
            "false_alarm_count": n_false,
            "false_alarm_pct": round(100 * n_false / n, 1) if n else None,
        }

    return {
        "checks": checks,
        "checks_passed": n_passed if checks != NOT_RUN else NOT_RUN,
        "checks_total": n_total if checks != NOT_RUN else NOT_RUN,
        "failure_types": failure_summary,
        "human_review": review,
        "false_alarm_rate": false_alarm,
        "measured_at": date.today().isoformat(),
        "evidence_status": "current local scorecard",
        "method": "Results from the scorecard directory supplied through SHIPCHECK_DIR.",
        "limitations": ["This is automated evaluation evidence, not a human release approval."],
    }


EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def build_chat_stats():
    saved = saved_measurements()
    if SHIPCHECK_DIR is None or not SHIPCHECK_DIR.exists():
        if saved:
            return saved["chat_stats"]
        return {
            "n_answers": NOT_RUN,
            "p50_seconds": NOT_RUN,
            "p95_seconds": NOT_RUN,
            "median_seconds": NOT_RUN,
            "measured_at": date.today().isoformat(),
            "evidence_status": "not run yet",
            "method": "No timing sample is available.",
            "limitations": ["No response-time result is available."],
        }
    cache_dir = SHIPCHECK_DIR / "work/chatbot-cache"
    if not cache_dir.exists():
        return {
            "n_answers": NOT_RUN,
            "p50_seconds": NOT_RUN,
            "p95_seconds": NOT_RUN,
            "median_seconds": NOT_RUN,
            "measured_at": date.today().isoformat(),
            "evidence_status": "not run yet",
            "method": "The supplied scorecard has no chat timing sample.",
            "limitations": ["No response-time result is available."],
        }
    seconds = []
    for f in cache_dir.glob("*.json"):
        d = safe_json(f)
        if not d:
            continue
        resp = d.get("response") or {}
        answer = resp.get("answer")
        if answer and EMAIL_RE.search(answer):
            # Never copy answer text containing emails; skip it, but the
            # timing is still safe to include.
            pass
        s = d.get("seconds") if d.get("seconds") is not None else resp.get("seconds")
        if isinstance(s, (int, float)):
            seconds.append(s)
    if not seconds:
        return {
            "n_answers": NOT_RUN,
            "p50_seconds": NOT_RUN,
            "p95_seconds": NOT_RUN,
            "median_seconds": NOT_RUN,
            "measured_at": date.today().isoformat(),
            "evidence_status": "not run yet",
            "method": "The supplied scorecard has no usable chat timing sample.",
            "limitations": ["No response-time result is available."],
        }
    seconds.sort()
    n = len(seconds)

    def pct(p):
        idx = min(n - 1, max(0, round(p * (n - 1))))
        return round(seconds[idx], 1)

    return {
        "n_answers": n,
        "median_seconds": round(statistics.median(seconds), 1),
        "p50_seconds": pct(0.50),
        "p95_seconds": pct(0.95),
        "measured_at": date.today().isoformat(),
        "evidence_status": "current local scorecard",
        "method": "Response times from saved scorecard chat responses; answers containing emails are not copied.",
        "limitations": ["This timing sample is not a production-service guarantee."],
    }


def main():
    evals = build_evals()
    chat_stats = build_chat_stats()
    (HERE / "evals.json").write_text(json.dumps(evals, indent=2) + "\n")
    (HERE / "chat-stats.json").write_text(json.dumps(chat_stats, indent=2) + "\n")
    print(f"wrote {HERE / 'evals.json'} and {HERE / 'chat-stats.json'}")


if __name__ == "__main__":
    main()
