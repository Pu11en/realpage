"""The frozen question list: same questions every run so trends are fair."""

import csv
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]


def rows():
    with open(HERE / "questions.csv", newline="") as f:
        return list(csv.DictReader(f))


def test_frozen_list_is_the_sept_12_questions():
    qs = rows()
    assert len(qs) == 17
    assert qs[0]["question"] == "What is the best property management software for a multifamily apartment portfolio?"
    assert qs[-1]["question"] == "What property management accounting software do most multifamily operators use?"
    assert all(r["baseline_id"].endswith("-realpage.com-" + r["baseline_id"].rsplit("-", 1)[1]) for r in qs)


def test_questions_are_well_formed():
    qs = rows()
    assert len({r["id"] for r in qs}) == len(qs), "ids must be unique"
    assert len({r["question"] for r in qs}) == len(qs)
    for r in qs:
        assert r["type"] in {"brand", "category", "recommendation", "comparison", "alternative", "scenario"}
        assert r["audit_category"] in {"brand_awareness", "organic_discovery", "comparison", "other"}
        assert r["target_included"] in {"true", "false"}
        assert r["question"].strip()


def test_run_sh_uses_frozen_questions_and_gemini():
    run = (HERE / "run.sh").read_text()
    assert "frozen_audit.ts" in run and "questions.csv" in run
    assert "${AI_VIS_MODELS:-gemini,gemini-web}" in run
    assert "--prompt-count" not in run  # no freshly generated questions
