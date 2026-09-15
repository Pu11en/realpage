#!/usr/bin/env python3
"""site/data/{pipeline,chat-stats,evals,buildbot}.json -> chat-ready CSVs.

These are the numbers shown on the Under the Hood page: how CraneSignal was built,
what ran, what was checked, chat timing, and build-agent progress. They are only
for questions about CraneSignal itself, not building/property/software claims.
"""
from __future__ import annotations

import csv
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
SITE_DATA = ROOT / "site" / "data"
OUT_DIR = ROOT / "propertystack" / "data" / "cranesignal-build" / "kb"


def _load(name: str) -> dict:
    path = SITE_DATA / name
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _write_csv(path: pathlib.Path, header: list[str], rows: list[list[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def build(out_dir: pathlib.Path = OUT_DIR) -> None:
    pipeline = _load("pipeline.json")
    chat_stats = _load("chat-stats.json")
    evals = _load("evals.json")
    buildbot = _load("buildbot.json")

    _write_csv(
        out_dir / "cranesignal-pipeline-steps.csv",
        ["step_order", "name", "label", "count"],
        [[i, row.get("name", ""), row.get("label", ""), row.get("count", "")] for i, row in enumerate(pipeline.get("steps", []), 1)],
    )
    _write_csv(
        out_dir / "cranesignal-pipeline-runs.csv",
        ["run_id", "started", "skill", "area", "status", "counts", "errors", "duration_sec"],
        [
            [
                row.get("runId", ""),
                row.get("started") or "",
                row.get("skill", ""),
                row.get("area") or "",
                row.get("status") or "",
                row.get("counts", ""),
                row.get("errors", ""),
                row.get("durationSec", ""),
            ]
            for row in pipeline.get("runs", [])
        ],
    )
    _write_csv(
        out_dir / "cranesignal-review-reasons.csv",
        ["reason", "count"],
        [[reason, count] for reason, count in (pipeline.get("reviewQueue", {}).get("byReason", {}) or {}).items()],
    )
    _write_csv(
        out_dir / "cranesignal-review-queue.csv",
        ["apt_id", "community", "city", "units", "reason", "website"],
        [
            [
                row.get("id", ""),
                row.get("community", ""),
                row.get("city", ""),
                row.get("units", ""),
                row.get("reason", ""),
                row.get("website") or "",
            ]
            for row in pipeline.get("reviewQueue", {}).get("rows", [])
        ],
    )
    _write_csv(
        out_dir / "cranesignal-accuracy-docs.csv",
        ["review_doc", "spotcheck_doc", "cost_note"],
        [[
            pipeline.get("accuracy", {}).get("reviewDoc", ""),
            pipeline.get("accuracy", {}).get("spotcheckDoc", ""),
            pipeline.get("costPerArea", {}).get("note", ""),
        ]],
    )

    _write_csv(
        out_dir / "cranesignal-chat-stats.csv",
        ["n_answers", "median_seconds", "p50_seconds", "p95_seconds", "measured_at"],
        [[
            chat_stats.get("n_answers", ""),
            chat_stats.get("median_seconds", ""),
            chat_stats.get("p50_seconds", ""),
            chat_stats.get("p95_seconds", ""),
            chat_stats.get("measured_at", ""),
        ]] if chat_stats else [],
    )

    measured_at = evals.get("measured_at", "")
    failure_types = evals.get("failure_types", {}) if isinstance(evals.get("failure_types"), dict) else {}
    human_review = evals.get("human_review", {}) if isinstance(evals.get("human_review"), dict) else {}
    false_alarm = evals.get("false_alarm_rate", {}) if isinstance(evals.get("false_alarm_rate"), dict) else {}
    _write_csv(
        out_dir / "cranesignal-eval-checks.csv",
        ["name", "status", "seconds", "cost_usd", "measured_at"],
        [
            [
                row.get("name", ""),
                row.get("status", ""),
                row.get("seconds", ""),
                row.get("cost_usd", ""),
                measured_at,
            ]
            for row in evals.get("checks", [])
        ],
    )
    _write_csv(
        out_dir / "cranesignal-eval-summary.csv",
        [
            "checks_passed",
            "checks_total",
            "failure_answer_count",
            "failure_ok_count",
            "human_reviewed",
            "human_review_agreement_pct",
            "false_alarm_reviewed",
            "false_alarm_count",
            "false_alarm_pct",
            "measured_at",
        ],
        [[
            evals.get("checks_passed", ""),
            evals.get("checks_total", ""),
            failure_types.get("n", ""),
            failure_types.get("ok_count", ""),
            human_review.get("n_reviewed", ""),
            human_review.get("agreement_pct", ""),
            false_alarm.get("n_reviewed", ""),
            false_alarm.get("false_alarm_count", ""),
            false_alarm.get("false_alarm_pct", ""),
            measured_at,
        ]] if evals else [],
    )
    _write_csv(
        out_dir / "cranesignal-eval-failure-types.csv",
        ["type", "count", "example_question", "measured_at"],
        [
            [row.get("type", ""), row.get("count", ""), row.get("example_question", ""), measured_at]
            for row in failure_types.get("types", [])
        ],
    )

    _write_csv(
        out_dir / "cranesignal-buildbot-summary.csv",
        ["plans", "steps_done", "steps_open", "progress_entries", "first_try_pct", "commits", "measured_at", "method"],
        [[
            buildbot.get("plans", ""),
            buildbot.get("steps_done", ""),
            buildbot.get("steps_open", ""),
            buildbot.get("progress_entries", ""),
            buildbot.get("first_try_pct", ""),
            buildbot.get("commits", ""),
            buildbot.get("measured_at", ""),
            buildbot.get("method", ""),
        ]] if buildbot else [],
    )
    _write_csv(
        out_dir / "cranesignal-buildbot-examples.csv",
        ["plan", "task", "check", "recap", "measured_at"],
        [
            [
                row.get("plan", ""),
                row.get("task", ""),
                row.get("check", ""),
                row.get("recap", ""),
                buildbot.get("measured_at", ""),
            ]
            for row in buildbot.get("examples", [])
        ],
    )


if __name__ == "__main__":
    build()
    print(f"wrote {OUT_DIR}")
