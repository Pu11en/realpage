#!/usr/bin/env python3
"""site/data/ai-visibility*.json -> chat-ready CSVs.

These tables mirror the AI Visibility page's read-only score snapshot and action
recommendations. They are copied into the chat image as static CSVs; this script
does not modify the source JSON files under site/data.
"""
from __future__ import annotations

import csv
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
SITE_DATA = ROOT / "site" / "data"
OUT_DIR = ROOT / "propertystack" / "data" / "ai-visibility" / "kb"


def _load(name: str) -> dict:
    return json.loads((SITE_DATA / name).read_text())


def _write_csv(path: pathlib.Path, header: list[str], rows: list[list[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def _joined(values: list[object]) -> str:
    return " | ".join(str(v) for v in values if v not in (None, ""))


def build(out_dir: pathlib.Path = OUT_DIR) -> None:
    scores = _load("ai-visibility.json")
    actions = _load("ai-visibility-actions.json")
    generated_at = scores.get("generatedAt", "")
    target = scores.get("target", "")
    domain = scores.get("domain", "")
    overall = scores.get("overall", {})
    founder = scores.get("founder", {})

    _write_csv(
        out_dir / "ai-visibility-summary.csv",
        [
            "target",
            "domain",
            "generated_at",
            "answers",
            "failed",
            "mention_pct",
            "recommend_pct",
            "first_pct",
            "unprompted_pct",
            "share_of_voice_pct",
            "avg_rank",
            "unbranded_answers",
            "unbranded_named_pct",
            "unbranded_top_pick_pct",
            "branded_answers",
            "lawsuit_pct",
            "negative_pct",
            "missed_questions",
        ],
        [[
            target,
            domain,
            generated_at,
            overall.get("answers", ""),
            overall.get("failed", ""),
            overall.get("mentionPct", ""),
            overall.get("recommendPct", ""),
            overall.get("firstPct", ""),
            overall.get("unpromptedPct", ""),
            overall.get("shareOfVoicePct", ""),
            overall.get("avgRank", ""),
            founder.get("unbrandedAnswers", ""),
            founder.get("unbrandedNamedPct", ""),
            founder.get("unbrandedTopPickPct", ""),
            founder.get("brandedAnswers", ""),
            founder.get("lawsuitPct", ""),
            founder.get("negativePct", ""),
            _joined(founder.get("missedQuestions", [])),
        ]],
    )

    _write_csv(
        out_dir / "ai-visibility-models.csv",
        [
            "model",
            "model_name",
            "generated_at",
            "answers",
            "failed",
            "mention_pct",
            "recommend_pct",
            "first_pct",
            "cite_pct",
            "avg_rank",
            "lawsuit_pct",
            "top_pick_pct",
            "unbranded_mention_pct",
            "missed_questions",
        ],
        [
            [
                row.get("model", ""),
                row.get("name", ""),
                generated_at,
                row.get("answers", ""),
                row.get("failed", ""),
                row.get("mentionPct", ""),
                row.get("recommendPct", ""),
                row.get("firstPct", ""),
                row.get("citePct", ""),
                row.get("avgRank", ""),
                row.get("lawsuitPct", ""),
                row.get("topPickPct", ""),
                row.get("unbrandedMentionPct", ""),
                _joined(row.get("missedQuestions", [])),
            ]
            for row in scores.get("models", [])
        ],
    )

    _write_csv(
        out_dir / "ai-visibility-competitors.csv",
        ["name", "domain", "generated_at", "mention_pct", "recommendations", "wins", "avg_rank"],
        [
            [
                row.get("name", ""),
                row.get("domain", ""),
                generated_at,
                row.get("mentionPct", ""),
                row.get("recommendations", ""),
                row.get("wins", ""),
                row.get("avgRank", ""),
            ]
            for row in scores.get("competitors", [])
        ],
    )

    _write_csv(
        out_dir / "ai-visibility-questions.csv",
        [
            "question_order",
            "question",
            "names_brand",
            "model",
            "model_name",
            "generated_at",
            "status",
            "mentioned",
            "rank",
            "sentiment",
            "winner",
            "brings_up_lawsuit",
            "answer",
        ],
        [
            [
                i,
                row.get("question", ""),
                row.get("namesBrand", ""),
                row.get("model", ""),
                row.get("name", ""),
                generated_at,
                row.get("status", ""),
                row.get("mentioned", ""),
                row.get("rank") or "",
                row.get("sentiment", ""),
                row.get("winner") or "",
                row.get("bringsUpLawsuit", ""),
                row.get("answer", ""),
            ]
            for i, row in enumerate(scores.get("questions", []), 1)
        ],
    )

    top_pick_rows = [
        ["overall", "", "All tested AI answers", generated_at, row.get("name", ""), row.get("count", "")]
        for row in founder.get("topPicks", [])
    ]
    for model in scores.get("models", []):
        top_pick_rows.extend(
            [
                [
                    "model",
                    model.get("model", ""),
                    model.get("name", ""),
                    generated_at,
                    row.get("name", ""),
                    row.get("count", ""),
                ]
                for row in model.get("topPicks", [])
            ]
        )
    _write_csv(
        out_dir / "ai-visibility-top-picks.csv",
        ["scope", "model", "model_name", "generated_at", "name", "count"],
        top_pick_rows,
    )

    _write_csv(
        out_dir / "ai-visibility-actions.csv",
        ["priority", "action_order", "title", "why", "do", "fixes", "effort", "written_for", "based_on", "headline"],
        [
            [
                group.get("when", ""),
                i,
                row.get("title", ""),
                row.get("why", ""),
                row.get("do", ""),
                row.get("fixes", ""),
                row.get("effort", ""),
                actions.get("writtenFor", ""),
                actions.get("basedOn", ""),
                actions.get("headline", ""),
            ]
            for group in actions.get("groups", [])
            for i, row in enumerate(group.get("actions", []), 1)
        ],
    )
    _write_csv(
        out_dir / "ai-visibility-site-facts.csv",
        ["fact_order", "ok", "text", "written_for", "based_on"],
        [
            [i, row.get("ok", ""), row.get("text", ""), actions.get("writtenFor", ""), actions.get("basedOn", "")]
            for i, row in enumerate(actions.get("siteFacts", []), 1)
        ],
    )
    _write_csv(
        out_dir / "ai-visibility-caveats.csv",
        ["caveat_order", "caveat", "written_for", "based_on"],
        [[i, text, actions.get("writtenFor", ""), actions.get("basedOn", "")] for i, text in enumerate(actions.get("caveats", []), 1)],
    )


if __name__ == "__main__":
    build()
    print(f"wrote {OUT_DIR}")
