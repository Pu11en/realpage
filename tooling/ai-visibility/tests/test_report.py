import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import report  # noqa: E402


def _model(name, mention, top, law):
    return {"model": name, "name": name.title(), "answers": 17, "failed": 0, "mentionPct": mention,
            "unbrandedMentionPct": mention, "topPickPct": top, "firstPct": 40.0, "lawsuitPct": law}


def _write(tmp: Path, runs):
    for r in runs:
        (tmp / f"{r['date']}.json").write_text(json.dumps(r))
    (tmp / "index.json").write_text(json.dumps({"runs": [
        {"date": r["date"], "file": f"{r['date']}.json", "baseline": r["baseline"]} for r in runs]}))


def test_first_gemini_run_compares_with_baseline_average(tmp_path):
    _write(tmp_path, [
        {"date": "2026-09-12", "baseline": True, "models": [_model("claude", 90, 10, 50), _model("chatgpt", 80, 30, 0)]},
        {"date": "2026-09-15", "baseline": False, "models": [_model("gemini", 70, 20, 40)],
         "lawsuit": {"sources": [{"site": "justice.gov", "count": 3}, {"site": "realpage.com", "count": 1, "isTarget": True}],
                     "toneMix": {"gemini": {"harsh": 2, "neutral": 1, "settled": 0}}}},
    ])
    out = report.summary(report.load(tmp_path))
    assert "vs Sept 12 Claude/ChatGPT average" in out
    assert "named 70% (-15)" in out and "top pick 20% (same)" in out
    assert "justice.gov 3" in out and "realpage.com!" in out
    assert "harsh 2" in out and "settled" not in out.split("tone:")[1]


def test_second_run_compares_with_its_own_last_run(tmp_path):
    _write(tmp_path, [
        {"date": "2026-09-12", "baseline": True, "models": [_model("claude", 90, 10, 50)]},
        {"date": "2026-09-15", "baseline": False, "models": [_model("gemini", 70, 20, 40)]},
        {"date": "2026-10-01", "baseline": False, "models": [_model("gemini", 75, 20, 30)]},
    ])
    out = report.summary(report.load(tmp_path))
    assert "vs its last run" in out and "named 75% (+5)" in out and "lawsuit raised 30% (-10)" in out


def test_only_baseline(tmp_path):
    _write(tmp_path, [{"date": "2026-09-12", "baseline": True, "models": [_model("claude", 90, 10, 50)]}])
    assert "No real run yet" in report.summary(report.load(tmp_path))
