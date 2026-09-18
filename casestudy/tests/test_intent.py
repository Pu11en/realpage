"""C3: intent, horizon, CTA, and next action."""
import json
from datetime import date
from pathlib import Path

import pytest

from casestudy.contract import AssignmentAnswer
from casestudy.gates import run_gates
from casestudy.intent import infer_intent, option_days
from casestudy.schedule import infer_schedule

DATA = Path(__file__).resolve().parents[1] / "data"
SAMPLES = [json.loads(l) for l in (DATA / "sample.jsonl").read_text().splitlines() if l.strip()]


def _run(raw):
    out = run_gates(raw)
    sched = infer_schedule(out)
    return infer_intent(out, sched), sched, out


def _variant(idx=0, task_id=None, **inp):
    raw = json.loads(json.dumps(SAMPLES[idx]))
    raw["input"].update(inp)
    if task_id is not None:
        raw["task_id"] = task_id
    return raw


@pytest.mark.parametrize("raw", SAMPLES, ids=["sms_example", "email_example"])
def test_both_expected_cta_and_actions(raw):
    intent, sched, _ = _run(raw)
    assert intent.cta == raw["expected"]["next_message"]["cta"]
    assert intent.next_action == raw["expected"]["next_action"]
    assert not intent.unresolved_link
    for r in intent.results:
        assert r.citation and r.reason and r.confidence
    # the pieces fit the frozen public contract
    AssignmentAnswer.model_validate({
        "next_message": {"channel": sched.channel, "send_at": sched.send_at_iso, "subject": None if sched.channel == "sms" else "x", "body": "x", "cta": intent.cta},
        "next_action": intent.next_action,
    })


def test_sample_horizons_come_from_token_and_are_labelled_hypothesis():
    i0, _, _ = _run(SAMPLES[0])
    i1, _, _ = _run(SAMPLES[1])
    # record 1's task_id (prospect_welcome_day0) has no horizon token: 33 days to move -> short
    assert (i0.horizon, i0.horizon_source) == ("short", "days_to_move_fallback")
    assert (i1.horizon, i1.horizon_source) == ("long", "task_id_token")
    for i in (i0, i1):
        assert next(r for r in i.results if r.rule == "horizon").confidence == "hypothesis"


def test_opaque_id_still_works_via_lifecycle_and_move_date():
    intent, _, _ = _run(_variant(0, task_id="a1b2c3"))
    assert intent.flow == "welcome"  # lifecycle 'new'
    assert intent.horizon == "short" and intent.horizon_source == "days_to_move_fallback"  # 33 days
    assert intent.next_action == {"type": "start_cadence", "name": "prospect_welcome_short_horizon"}
    assert intent.cta["options"] == ["Thu", "Fri"]

    intent, _, _ = _run(_variant(1, task_id="zzz-9"))
    assert intent.flow == "open_follow_up"
    assert intent.horizon == "long" and intent.horizon_source == "days_to_move_fallback"  # 71 days
    assert intent.next_action == {"type": "follow_up_in_days", "value": 3}


def test_two_tier_fallback_boundary_no_medium():
    raw = _variant(0, task_id="opaque", move_date_target="2026-01-22")  # 45 days from Dec 8
    assert _run(raw)[0].horizon == "short"
    raw = _variant(0, task_id="opaque", move_date_target="2026-01-23")  # 46 days
    assert _run(raw)[0].horizon == "long"
    assert _run(raw)[0].next_action["name"] == "prospect_welcome_long_horizon"


def test_explicit_fields_beat_conflicting_task_id():
    raw = _variant(0, horizon="long", intent="follow_up")  # task_id says welcome + short_horizon... via lifecycle new
    raw["task_id"] = "prospect_welcome_short_horizon_day0"
    intent, _, _ = _run(raw)
    assert intent.horizon == "long" and intent.horizon_source == "explicit_field"
    assert intent.flow == "open_follow_up"
    assert intent.next_action == {"type": "follow_up_in_days", "value": 3}
    assert all(r.confidence == "input_required" for r in intent.results if r.rule in ("intent", "horizon"))


def test_day10_does_not_mean_wait_ten_days():
    intent, _, _ = _run(_variant(1, task_id="prospect_long_horizon_day10"))
    assert intent.next_action == {"type": "follow_up_in_days", "value": 3}


def test_email_uses_explicit_input_link_over_learned():
    intent, _, _ = _run(_variant(1, tour_link="https://example.org/book"))
    assert intent.cta == {"type": "schedule_tour", "link": "https://example.org/book"}


def test_unseen_property_never_gets_invented_url():
    intent, _, _ = _run(_variant(1, property_name="Maple Court"))
    assert intent.cta == {"type": "schedule_tour"}
    assert intent.unresolved_link and intent.uncertain
    link_res = next(r for r in intent.results if r.rule == "tour_link")
    assert link_res.status == "failed" and "invent" in link_res.reason
    AssignmentAnswer.model_validate({
        "next_message": {"channel": "email", "send_at": "2025-12-09T10:00:00-06:00", "subject": "s", "body": "b", "cta": intent.cta},
        "next_action": intent.next_action,
    })


def test_learned_link_keeps_provenance():
    intent, _, _ = _run(SAMPLES[1])
    r = next(r for r in intent.results if r.rule == "tour_link")
    assert "sample.jsonl" in r.citation and r.confidence == "observed"


def test_option_days_skip_sunday():
    assert option_days(date(2025, 12, 9)) == ["Thu", "Fri"]  # Tuesday
    assert option_days(date(2025, 12, 12)) == ["Mon", "Tue"]  # Friday: Sun skipped -> Mon, Tue
    assert option_days(date(2025, 12, 11)) == ["Sat", "Mon"]  # Thursday


def test_unknown_primary_cta_is_flagged():
    raw = _variant(0)
    raw["assertions"]["constraints"]["primary_cta"] = "apply_now"
    intent, _, out = _run(raw)
    assert out.purpose and intent.flow == "general"
    assert intent.cta["type"] == "apply_now"  # the record's own goal, never a tour pitch


def test_stop_yields_mark_opted_out():
    raw = _variant(0, inbound_reply="STOP")
    intent, _, _ = _run(raw)
    assert intent.next_action["type"] == "mark_opted_out" and intent.cta is None


def test_option_reply_proposes_follow_up_not_booking():
    raw = _variant(0, inbound_reply="1", prior_options=["Thu", "Fri"])
    intent, _, out = _run(raw)
    assert out.decision == "propose_follow_up"
    assert intent.next_action == {"type": "follow_up_in_days", "value": 3}


def test_suppressed_record_has_no_intent():
    raw = _variant(0)
    raw["consent"] = {"sms_opt_in": False, "email_opt_in": False, "voice_opt_in": False}
    intent, _, _ = _run(raw)
    assert intent.flow == "none" and intent.cta is None and intent.next_action is None
