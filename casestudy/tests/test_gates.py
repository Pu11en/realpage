"""C1: input normalization and the five gates."""
import json
from datetime import datetime
from pathlib import Path

import pytest

from casestudy.gates import classify_reply, normalize, run_gates

DATA = Path(__file__).resolve().parents[1] / "data"
SAMPLES = [json.loads(l) for l in (DATA / "sample.jsonl").read_text().splitlines() if l.strip()]


def _rule(outcome, name):
    return [r for r in outcome.results if r.rule == name]


@pytest.mark.parametrize("raw", SAMPLES, ids=["sms_example", "email_example"])
def test_both_samples_pass_all_gates(raw):
    out = run_gates(raw)
    assert out.decision == "proceed", [(r.rule, r.status, r.reason) for r in out.results]
    assert out.verified_states == ["consent_verified"]
    assert out.unsupported_states == []
    assert out.tz.key == "America/Chicago"
    # reference clock is the input clock, not today
    assert out.reference_time == datetime.fromisoformat(raw["input"]["last_interaction"].replace("Z", "+00:00"))
    assert _rule(out, "dates_gate")[0].details["days_to_move"] in (33, 71)
    for r in out.results:
        assert r.confidence in {"observed", "input_required", "hypothesis", "conservative_default"}
        assert r.citation and r.reason


def test_stop_with_consent_already_false_marks_opted_out():
    raw = json.loads(json.dumps(SAMPLES[0]))
    raw["consent"] = {"email_opt_in": False, "sms_opt_in": False, "voice_opt_in": False}
    raw["input"]["inbound_reply"] = "STOP"
    out = run_gates(raw)
    assert out.decision == "mark_opted_out"
    assert out.reply_class == "opt_out"
    # opt-out was handled before the consent gate ever ran
    assert _rule(out, "consent_gate") == []


@pytest.mark.parametrize("text", ["stop", "Stop.", " UNSUBSCRIBE ", "quit", "Opt out"])
def test_opt_out_variants(text):
    assert classify_reply(text) == "opt_out"


def test_help_does_not_bypass_consent():
    raw = json.loads(json.dumps(SAMPLES[0]))
    raw["consent"]["sms_opt_in"] = False
    raw["consent"]["email_opt_in"] = False
    raw["input"]["inbound_reply"] = "HELP"
    out = run_gates(raw)
    assert out.reply_class == "help"
    assert out.decision == "suppress" and out.reason == "no_consent"


def test_numeric_reply_with_prior_options_proposes_follow_up():
    raw = json.loads(json.dumps(SAMPLES[0]))
    raw["input"]["inbound_reply"] = "2"
    raw["input"]["prior_options"] = ["Thu", "Fri"]
    out = run_gates(raw)
    assert out.decision == "propose_follow_up" and out.proceed
    assert out.selected_option == "Fri"
    assert "does not book" in _rule(out, "reply_gate")[0].reason
    # consent still enforced for the confirmation
    assert _rule(out, "consent_gate")[0].status == "passed"


def test_numeric_reply_without_prior_options_escalates():
    raw = json.loads(json.dumps(SAMPLES[0]))
    raw["input"]["inbound_reply"] = "1"
    out = run_gates(raw)
    assert out.decision == "escalate" and out.reason == "numeric_reply_without_prior_options"


def test_numeric_reply_out_of_range_escalates():
    raw = json.loads(json.dumps(SAMPLES[0]))
    raw["input"]["inbound_reply"] = "7"
    raw["input"]["prior_options"] = ["Thu", "Fri"]
    assert run_gates(raw).reason == "numeric_reply_out_of_range"


def test_question_reply_classified_and_gates_still_run():
    raw = json.loads(json.dumps(SAMPLES[1]))
    raw["input"]["inbound_reply"] = "Do you allow pets?"
    out = run_gates(raw)
    assert out.reply_class == "question"
    assert out.decision == "proceed"


def test_not_interested_and_unknown():
    assert classify_reply("Not interested, thanks") == "not_interested"
    assert classify_reply("banana") == "unknown"
    assert classify_reply(None) == "none"


def test_no_consent_suppresses_and_never_invents_consent():
    raw = json.loads(json.dumps(SAMPLES[0]))
    del raw["consent"]
    out = run_gates(raw)
    assert out.decision == "suppress" and out.reason == "no_consent"
    assert "consent_verified" not in out.verified_states
    assert "unknown is never treated as consent" in _rule(out, "consent_gate")[0].reason


def test_non_boolean_consent_is_unknown():
    raw = json.loads(json.dumps(SAMPLES[0]))
    raw["consent"] = {"sms_opt_in": "maybe", "email_opt_in": None}
    assert run_gates(raw).decision == "suppress"


def test_unknown_required_state_is_visibly_unsupported():
    raw = json.loads(json.dumps(SAMPLES[0]))
    raw["assertions"]["required_states"].append("magic_check_passed")
    out = run_gates(raw)
    assert out.unsupported_states == ["magic_check_passed"]
    assert "magic_check_passed" not in out.verified_states
    assert any(r.status == "unsupported" for r in out.results)


def test_lifecycle_and_do_not_contact_block():
    raw = json.loads(json.dumps(SAMPLES[0]))
    raw["lifecycle_stage"] = "do_not_contact"
    assert run_gates(raw).reason == "lifecycle_blocked"
    raw = json.loads(json.dumps(SAMPLES[0]))
    raw["input"]["do_not_contact"] = True
    assert run_gates(raw).reason == "lifecycle_blocked"


def test_frequency_cap():
    raw = json.loads(json.dumps(SAMPLES[0]))
    raw["input"]["last_message_sent_at"] = "2025-12-08T10:00:00Z"  # 5h before reference
    assert run_gates(raw).reason == "frequency_cap"
    raw = json.loads(json.dumps(SAMPLES[0]))
    raw["input"]["messages_sent_24h"] = 3
    assert run_gates(raw).reason == "frequency_cap"
    raw = json.loads(json.dumps(SAMPLES[0]))
    raw["input"]["last_message_sent_at"] = "2025-12-05T10:00:00Z"
    assert run_gates(raw).decision == "proceed"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda i: i.__setitem__("timezone", "Mars/Olympus"),
        lambda i: i.pop("timezone"),
        lambda i: i.pop("last_interaction"),
        lambda i: i.__setitem__("last_interaction", "yesterday"),
        lambda i: i.__setitem__("move_date_target", "2025-13-45"),
        lambda i: i.__setitem__("move_date_target", "2025-11-01"),  # past
    ],
    ids=["bad_tz", "no_tz", "no_clock", "bad_clock", "bad_move", "past_move"],
)
def test_dates_and_timezone_escalate(mutate):
    raw = json.loads(json.dumps(SAMPLES[0]))
    mutate(raw["input"])
    out = run_gates(raw)
    assert out.decision == "escalate" and out.reason == "dates_or_timezone_invalid"


def test_missing_move_date_passes_with_unknown_horizon():
    raw = json.loads(json.dumps(SAMPLES[0]))
    del raw["input"]["move_date_target"]
    out = run_gates(raw)
    assert out.decision == "proceed"
    assert _rule(out, "dates_gate")[0].details["days_to_move"] is None


@pytest.mark.parametrize("raw", [None, 42, "text", [], {}, {"input": "x", "consent": [], "channel_preferences": "sms"}])
def test_malformed_input_never_crashes(raw):
    out = run_gates(raw)
    assert out.decision in {"suppress", "escalate"}
    rec = normalize(raw)
    assert rec.task_id == "unknown_task"


def test_reference_clock_never_server_date():
    raw = json.loads(json.dumps(SAMPLES[0]))
    raw["input"]["reference_time"] = "2025-12-09T08:00:00-06:00"
    out = run_gates(raw)
    assert out.reference_time.isoformat() == "2025-12-09T08:00:00-06:00"
