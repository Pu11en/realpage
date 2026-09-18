"""C0: freeze the contract and reference tests.

Both `expected` blocks in sample.jsonl are immutable reference fixtures. This test
proves the AssignmentAnswer model accepts them exactly, rejects extra public keys,
and that a reference-derived checklist can tell a harmless paraphrase from a
wrong-facts answer (grading prose by meaning, not literal wording).
"""
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from casestudy.contract import AssignmentAnswer

DATA = Path(__file__).resolve().parents[1] / "data"


def _load_expected():
    lines = [l for l in (DATA / "sample.jsonl").read_text().splitlines() if l.strip()]
    return [json.loads(l)["expected"] for l in lines]


EXPECTED = _load_expected()


def test_two_examples_present():
    assert len(EXPECTED) == 2


@pytest.mark.parametrize("expected", EXPECTED, ids=["sms_example", "email_example"])
def test_expected_round_trips(expected):
    answer = AssignmentAnswer.model_validate(expected)
    # round-trip: re-serialize and re-parse, compare against the original dict
    dumped = answer.model_dump(exclude_none=False)
    reparsed = AssignmentAnswer.model_validate(dumped)
    assert reparsed.model_dump() == answer.model_dump()


def test_sms_example_structure():
    expected = EXPECTED[0]
    answer = AssignmentAnswer.model_validate(expected)
    assert answer.next_message.channel == "sms"
    assert answer.next_message.subject is None
    assert answer.next_message.cta.type == "schedule_tour"
    assert answer.next_message.cta.options == ["Thu", "Fri"]
    assert answer.next_action.type == "start_cadence"
    assert answer.next_action.name == "prospect_welcome_short_horizon"
    assert answer.next_message.send_at == "2025-12-09T09:00:00-06:00"
    assert answer.next_message.body.endswith("Reply STOP to opt out.")


def test_email_example_structure():
    expected = EXPECTED[1]
    answer = AssignmentAnswer.model_validate(expected)
    assert answer.next_message.channel == "email"
    assert answer.next_message.subject is not None
    assert answer.next_message.cta.type == "schedule_tour"
    assert answer.next_message.cta.link == "https://oakridge.example/tour"
    assert answer.next_action.type == "follow_up_in_days"
    assert answer.next_action.value == 3
    assert answer.next_message.send_at == "2025-12-09T10:00:00-06:00"
    assert "STOP" in answer.next_message.body


def test_extra_public_keys_rejected():
    expected = dict(EXPECTED[0])
    expected["task_id"] = "should not be here"
    with pytest.raises(ValidationError):
        AssignmentAnswer.model_validate(expected)


def test_extra_next_message_key_rejected():
    bad = json.loads(json.dumps(EXPECTED[0]))
    bad["next_message"]["engine"] = "leaked-diagnostic"
    with pytest.raises(ValidationError):
        AssignmentAnswer.model_validate(bad)


def test_wrong_cta_shape_rejected():
    """An SMS body with an email-style link-only CTA (no options) must fail."""
    bad = json.loads(json.dumps(EXPECTED[0]))
    bad["next_message"]["cta"] = {"type": "schedule_tour", "link": "https://example.com"}
    # SMS example's checklist requires numbered options, not a link
    answer = AssignmentAnswer.model_validate(bad)
    assert answer.next_message.cta.type == "schedule_tour"
    # structurally valid CTA union member, but semantically wrong for SMS —
    # caught by the meaning checklist below, not the schema
    assert semantic_checklist_sms(answer, EXPECTED[0]) is False


def semantic_checklist_sms(answer, reference_expected) -> bool:
    """Reference-derived checklist: does an SMS answer mean the same thing as the
    reference, tolerating paraphrase but catching wrong facts (channel, CTA kind,
    opt-out presence, addressee name)?
    """
    ref = AssignmentAnswer.model_validate(reference_expected)
    if answer.next_message.channel != ref.next_message.channel:
        return False
    if answer.next_message.cta.type != "schedule_tour":
        return False
    if not hasattr(answer.next_message.cta, "options"):
        return False  # SMS must offer numbered options, not a link
    if "STOP" not in answer.next_message.body:
        return False
    if "Taylor" not in answer.next_message.body:
        return False
    return True


def test_semantic_checklist_accepts_harmless_paraphrase():
    expected = EXPECTED[0]
    paraphrased = json.loads(json.dumps(expected))
    paraphrased["next_message"]["body"] = (
        "Hey Taylor, thanks for checking out Oak Ridge! We've got tours open this "
        "week — want Thursday or Friday? Text 1 for Thu, 2 for Fri. Reply STOP to opt out."
    )
    answer = AssignmentAnswer.model_validate(paraphrased)
    assert semantic_checklist_sms(answer, expected) is True


def test_semantic_checklist_rejects_wrong_facts():
    expected = EXPECTED[0]
    wrong = json.loads(json.dumps(expected))
    # drops the opt-out instruction and the addressee's name — wrong facts, not paraphrase
    wrong["next_message"]["body"] = "Tours available this week. Book on Thu or Fri."
    answer = AssignmentAnswer.model_validate(wrong)
    assert semantic_checklist_sms(answer, expected) is False


def test_mark_opted_out_action_shape():
    """Not present in the two samples, but required by the contract for STOP handling (C1)."""
    payload = {
        "next_message": {
            "channel": "sms",
            "send_at": "2025-12-09T09:00:00-06:00",
            "subject": None,
            "body": "You have been opted out. Reply START to resubscribe.",
            "cta": {"type": "schedule_tour", "options": []},
        },
        "next_action": {"type": "mark_opted_out", "reason": "sms_stop_reply"},
    }
    # empty options list on an opt-out confirmation is still structurally valid
    answer = AssignmentAnswer.model_validate(payload)
    assert answer.next_action.type == "mark_opted_out"
    assert answer.next_action.reason == "sms_stop_reply"
