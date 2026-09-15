"""Run history: each real run becomes a small per-AI summary file plus an index (sample report, no network)."""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "site" / "data"))
import build_ai_visibility as bav  # noqa: E402

REPORT = json.loads((REPO / "tooling/ai-visibility/fixtures/report-gemini.json").read_text())


def by_model(entry):
    return {m["model"]: m for m in entry["models"]}


def test_history_entry_has_per_ai_numbers():
    e = bav.history_entry(bav.build(REPORT, demo=False))
    assert e["date"] == "2026-09-20" and not e["baseline"]
    assert e["label"] == "Gemini (memory), Gemini + Google Search, 2026-09-20"
    g, w = by_model(e)["gemini"], by_model(e)["gemini-web"]
    assert (g["answers"], g["mentionPct"], g["unbrandedMentionPct"], g["topPickPct"], g["firstPct"]) == (3, 66.7, 50.0, 0.0, 33.3)
    assert g["lawsuitPct"] == 100.0 and w["lawsuitPct"] == 0.0
    assert g["missedQuestions"] == ["Which revenue management software do big landlords use?"]
    assert g["topPicks"] == [{"name": "Yardi", "count": 2}]
    assert (w["topPickPct"], w["missedQuestions"], w["topPicks"]) == (100.0, [], [{"name": "RealPage", "count": 2}])
    assert "questions" not in e  # no full answers in history


def test_save_history_writes_file_and_index(tmp_path):
    data = bav.build(REPORT, demo=False)
    bav.save_history(bav.history_entry(dict(data, generatedAt="2026-09-12T15:51:39Z"), "Claude / ChatGPT, Sept 12", baseline=True), tmp_path)
    bav.save_history(bav.history_entry(data), tmp_path)
    bav.save_history(bav.history_entry(data), tmp_path)  # same day again replaces, doesn't duplicate
    index = json.loads((tmp_path / "index.json").read_text())["runs"]
    assert [r["date"] for r in index] == ["2026-09-12", "2026-09-20"]
    assert index[0]["baseline"] and index[0]["label"] == "Claude / ChatGPT, Sept 12"
    assert index[1]["models"] == ["gemini", "gemini-web"]
    assert json.loads((tmp_path / "2026-09-20.json").read_text())["models"][0]["model"] == "gemini"


def test_main_demo_skips_history_and_baseline_skips_tab(tmp_path, monkeypatch):
    monkeypatch.setattr(bav, "OUT", tmp_path / "ai-visibility.json")
    monkeypatch.setattr(bav, "HISTORY", tmp_path / "hist")
    src = tmp_path / "report.json"
    src.write_text(json.dumps(REPORT))
    bav.main([str(src), "--demo"])
    assert json.loads((tmp_path / "ai-visibility.json").read_text())["demo"] and not (tmp_path / "hist").exists()
    (tmp_path / "ai-visibility.json").unlink()
    bav.main([str(src), "--baseline", "Old run"])
    assert not (tmp_path / "ai-visibility.json").exists()
    assert json.loads((tmp_path / "hist/index.json").read_text())["runs"][0]["label"] == "Old run"
    bav.main([str(src)])
    assert (tmp_path / "ai-visibility.json").exists()


def test_committed_baseline_is_sept_12():
    index = json.loads((REPO / "site/data/ai-visibility-history/index.json").read_text())["runs"]
    base = [r for r in index if r["baseline"]]
    assert base and base[0]["date"] == "2026-09-12" and base[0]["label"] == "Claude / ChatGPT, Sept 12"
    assert set(base[0]["models"]) == {"chatgpt", "claude", "claude-web"}
