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

# Same story as the Under the Hood page, in the words the chat should use.
SOFTWARE_HAND_CHECK = "10/10"
HOW_TESTED = [
    ("build process", "Work is planned as small steps. The AI builds each step in its own isolated copy, an automatic check (tests, a build, or loading the page) runs after every step, and a person tries and approves the change before it goes live. The AI never pushes code or deploys on its own."),
    ("test set", "A fixed set of 100 questions a sales rep would really ask, plus trick questions: off-topic trivia, requests to change data, and attempts to talk the agent out of its rules."),
    ("grading", "An AI grader scores every answer against a rubric: correct, sourced from CraneSignal's data, and in scope. 92 of 100 passed."),
    ("grader check", "Drew graded the 17 hardest cases by hand; the AI grader agreed with him on 94% of them."),
    ("data spot-check", "Software matches were checked by hand: 10 of 10 held up, each proof link opening to the named vendor's portal. A review of buildings with no website found real misses; after fixes, buildings without a trusted website dropped from 67 to about 18."),
    ("speed", "A typical answer takes about 14 seconds; 95% arrive within 28 seconds."),
    ("safety", "Read-only (cannot change data), every link must come from CraneSignal's data or a page read that turn, never guesses software/owners/contacts without a proof source, no personal data in answers, standard browser security headers, and every page and data file requires sign-in."),
    ("known limits", "About 3 in 10 buildings in the Plano/Richardson sample have no public sign of their software; those are marked unknown rather than guessed. Leads today are strongest in Texas and Arizona; any other US area can be added with the same lead finder."),
]


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
        ["review_doc", "spotcheck_doc"],
        [[
            pipeline.get("accuracy", {}).get("reviewDoc", ""),
            pipeline.get("accuracy", {}).get("spotcheckDoc", ""),
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
    _write_csv(
        out_dir / "cranesignal-eval-summary.csv",
        [
            "test_answers_total",
            "test_answers_correct",
            "human_reviewed",
            "human_review_agreement_pct",
            "software_hand_check",
            "measured_at",
        ],
        [[
            failure_types.get("n", ""),
            failure_types.get("ok_count", ""),
            human_review.get("n_reviewed", ""),
            human_review.get("agreement_pct", ""),
            SOFTWARE_HAND_CHECK,
            measured_at,
        ]] if evals else [],
    )
    _write_csv(
        out_dir / "cranesignal-how-tested.csv",
        ["topic", "fact"],
        [[topic, fact] for topic, fact in HOW_TESTED],
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
