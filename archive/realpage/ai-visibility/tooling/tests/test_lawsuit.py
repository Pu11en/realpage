"""Lawsuit data: quotes, tone, source leaderboard (saved sample run and Gemini replies, no network)."""

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
FIXTURES = REPO / "tooling/ai-visibility/fixtures"
RUN = FIXTURES / "lawsuit-run"
sys.path.insert(0, str(REPO / "site" / "data"))
sys.path.insert(0, str(REPO / "tooling" / "ai-visibility"))
import ai_visibility_lawsuit as law  # noqa: E402
import build_ai_visibility as bav  # noqa: E402
import local_ai  # noqa: E402

REPORT = json.loads((RUN / "report.json").read_text())


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(local_ai, "GEMINI_GAP", 0.0)
    monkeypatch.setattr(local_ai, "_gemini_stopped", "")
    monkeypatch.setattr(local_ai, "_gemini_key", lambda: pytest.fail("tests must not read the key"))
    sent = []
    monkeypatch.setattr(local_ai, "_gemini_post",
                        lambda body: sent.append(body) or json.loads((FIXTURES / "gemini-tone.json").read_text()))
    return sent


def test_mentions_keep_exact_sentences_question_and_sources():
    found = law.mentions(REPORT, RUN)
    assert [(m["model"], m["question"]) for m in found] == [
        ("gemini", "Is RealPage a good company to work with?"),
        ("gemini-web", "Is RealPage a good company to work with?"),
        ("gemini-web", "Is RealPage legit?")]
    assert found[0]["sentences"] == ["It faced a DOJ antitrust lawsuit accusing it of price-fixing rents!"]
    assert found[1]["sentences"] == ["In 2025 it settled the DOJ case and agreed to change its software."]
    assert found[0]["sources"] == []  # memory answers have no websites
    assert [s["site"] for s in found[1]["sources"]] == ["justice.gov", "realpage.com"]  # deduped
    assert [s["site"] for s in found[2]["sources"]] == ["propublica.org", "justice.gov"]  # matched by question


def test_word_list_tone_without_ai():
    assert [m["tone"] for m in law.mentions(REPORT, RUN)] == ["harsh", "settled", "neutral"]
    assert {m["toneBy"] for m in law.mentions(REPORT, RUN)} == {"words"}


def test_gemini_tone_one_call_per_mention(offline):
    found = law.mentions(REPORT, RUN, ask=law.gemini_tone)
    assert [(m["tone"], m["toneBy"]) for m in found] == [("harsh", "gemini")] * 3
    assert len(offline) == 3
    assert offline[0]["generationConfig"] == {"responseMimeType": "application/json"}
    assert "tools" not in offline[0]  # tone labelling never searches


def test_failed_tone_call_falls_back_to_word_list(monkeypatch):
    monkeypatch.setattr(local_ai, "_gemini_stopped", "12:00:00")  # as after a 429
    found = law.mentions(REPORT, RUN, ask=law.gemini_tone)
    assert [(m["tone"], m["toneBy"]) for m in found] == [("harsh", "words"), ("settled", "words"), ("neutral", "words")]


def test_leaderboard_counts_changes_and_flags_realpage():
    first = law.lawsuit_data(REPORT, RUN)
    assert first["toneMix"] == {"gemini": {"harsh": 1, "neutral": 0, "settled": 0},
                                "gemini-web": {"harsh": 0, "neutral": 1, "settled": 1}}
    rows = {r["site"]: r for r in first["sources"]}
    assert first["sources"][0]["site"] == "justice.gov" and rows["justice.gov"]["count"] == 2
    assert rows["realpage.com"]["isTarget"] and not rows["propublica.org"]["isTarget"]
    assert rows["justice.gov"]["change"] is None and first["comparedWith"] is None  # nothing to compare yet

    prev = {"date": "2026-09-14", "lawsuit": {"sources": [{"site": "justice.gov", "count": 3},
                                                          {"site": "nytimes.com", "count": 1}]}}
    rows = {r["site"]: r for r in law.lawsuit_data(REPORT, RUN, previous=prev)["sources"]}
    assert (rows["justice.gov"]["count"], rows["justice.gov"]["change"]) == (2, -1)
    assert (rows["realpage.com"]["previous"], rows["realpage.com"]["change"]) == (0, 1)
    assert (rows["nytimes.com"]["count"], rows["nytimes.com"]["change"]) == (0, -1)  # dropped out


def test_real_build_saves_lawsuit_into_history(tmp_path, monkeypatch):
    monkeypatch.setattr(bav, "OUT", tmp_path / "ai-visibility.json")
    monkeypatch.setattr(bav, "HISTORY", tmp_path / "hist")
    base = json.loads((FIXTURES / "report-gemini.json").read_text())
    for date in ("2026-09-20", "2026-09-21"):
        run = tmp_path / date
        run.mkdir()
        (run / "report.json").write_text(json.dumps(dict(base, generatedAt=f"{date}T12:00:00Z",
                                                         audit=dict(base["audit"], runs=REPORT["audit"]["runs"]))))
        (run / "gemini-sources.jsonl").write_text((RUN / "gemini-sources.jsonl").read_text())
        bav.main([str(run)])
    later = json.loads((tmp_path / "hist/2026-09-21.json").read_text())["lawsuit"]
    assert len(later["mentions"]) == 3 and later["comparedWith"] == "2026-09-20"
    assert later["mentions"][0]["name"] == "Gemini (memory)" and later["mentions"][0]["toneBy"] == "gemini"
    assert {r["site"]: r["change"] for r in later["sources"]} == {"justice.gov": 0, "realpage.com": 0, "propublica.org": 0}


def test_demo_and_word_tone_never_call_gemini(tmp_path, monkeypatch, offline):
    monkeypatch.setattr(bav, "OUT", tmp_path / "ai-visibility.json")
    monkeypatch.setattr(bav, "HISTORY", tmp_path / "hist")
    src = tmp_path / "report.json"
    base = json.loads((FIXTURES / "report-gemini.json").read_text())
    src.write_text(json.dumps(base))
    bav.main([str(src), "--demo"])
    bav.main([str(src), "--word-tone"])
    bav.main([str(src), "--baseline", "Old run"])
    assert offline == []
    entry = json.loads((tmp_path / "hist/2026-09-20.json").read_text())
    assert entry["lawsuit"]["mentions"][0]["toneBy"] == "words"


def test_committed_baseline_has_lawsuit_data():
    base = json.loads((REPO / "site/data/ai-visibility-history/2026-09-12.json").read_text())
    assert base["lawsuit"] is not None and "toneMix" in base["lawsuit"]
