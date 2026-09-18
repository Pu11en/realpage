"""C8: adversarial offline practice fixtures and balanced reply-classification corpus."""
import json
from collections import Counter
from pathlib import Path

import pytest

from casestudy.contract import AssignmentAnswer
from casestudy.gates import classify_reply
from casestudy.pipeline import run_record
from casestudy.writer import WriterConfig

DATA = Path(__file__).resolve().parents[1] / "data"
OFFLINE = WriterConfig(enabled=False)


def _jsonl(name):
    return [json.loads(line) for line in (DATA / name).read_text().splitlines() if line.strip()]


PRACTICE = _jsonl("practice.jsonl")
EXPECTATIONS = _jsonl("practice_expectations.jsonl")
REPLIES = _jsonl("reply_corpus.jsonl")


def test_practice_data_is_separate_complete_and_evaluator_only():
    golden_ids = {row["task_id"] for row in _jsonl("sample.jsonl")}
    practice_ids = [row["task_id"] for row in PRACTICE]
    expectation_ids = [row["task_id"] for row in EXPECTATIONS]
    assert len(PRACTICE) >= 16
    assert len(practice_ids) == len(set(practice_ids))
    assert practice_ids == expectation_ids
    assert golden_ids.isdisjoint(practice_ids)
    # Expected answers and prose checks live in the evaluator manifest, never model/service input.
    assert all("expected" not in row and "primary_rule" not in row and "prose_checklist" not in row for row in PRACTICE)
    assert all(e["primary_rule"].strip() and e["expected_structure"] and e["prose_checklist"] for e in EXPECTATIONS)


def _assert_structure(result, expected):
    public = result.submission()
    AssignmentAnswer.model_validate(public)
    assert set(public) == {"next_message", "next_action"}
    message = public["next_message"]
    assert (message is not None) is expected["has_message"]
    if message is not None:
        assert message["channel"] == expected["channel"]
        if "send_at" in expected:
            assert message["send_at"] == expected["send_at"]
        cta_shape = expected.get("cta_shape")
        if cta_shape == "link":
            assert set(message["cta"]) == {"type", "link"}
        elif cta_shape == "options":
            assert set(message["cta"]) == {"type", "options"}
            assert len(message["cta"]["options"]) == 2
    assert public["next_action"] == expected["next_action"]


def _assert_prose(result, checklist):
    body = result.answer.next_message.body if result.answer.next_message else ""
    for phrase in checklist.get("body_contains", []):
        assert phrase in body
    for phrase in checklist.get("body_excludes", []):
        assert phrase not in body
    if "reply_class" in checklist:
        assert result.reply_class == checklist["reply_class"]
    rules = {entry.rule for entry in result.why}
    assert set(checklist.get("why_rules", [])) <= rules


@pytest.mark.parametrize("record,expectation", zip(PRACTICE, EXPECTATIONS), ids=[r["task_id"] for r in PRACTICE])
def test_each_adversarial_fixture_passes_offline(record, expectation):
    result = run_record(record, config=OFFLINE)
    assert result.task_id == expectation["task_id"]
    assert result.engine in {"template", "none"}
    assert result.errors == []
    _assert_structure(result, expectation["expected_structure"])
    _assert_prose(result, expectation["prose_checklist"])


def test_reply_corpus_is_balanced_and_covers_requested_variation():
    counts = Counter(case["expected_class"] for case in REPLIES)
    assert counts == {label: 4 for label in ("opt_out", "help", "choose_option", "not_interested", "question", "unknown")}
    features = {case["feature"] for case in REPLIES}
    assert any("capitalization" in feature for feature in features)
    assert any("punctuation" in feature for feature in features)
    assert any("synonym" in feature for feature in features)
    assert any("ambiguous" in feature for feature in features)


@pytest.mark.parametrize("case", REPLIES, ids=[f"{c['expected_class']}:{c['text']}" for c in REPLIES])
def test_reply_corpus_current_classifier(case):
    assert classify_reply(case["text"]) == case["expected_class"]


def test_reply_corpus_does_not_claim_a_quality_threshold():
    # C9 will compute and label macro-F1 over this synthetic corpus. C8 only freezes cases.
    raw = (DATA / "reply_corpus.jsonl").read_text()
    assert "f1" not in raw.lower() and "0.90" not in raw
