"""C5: offline templates satisfy both reference checklists and every validator rule."""
import json
from pathlib import Path

import pytest

from casestudy.contract import AssignmentAnswer
from casestudy.gates import run_gates
from casestudy.intent import infer_intent
from casestudy.schedule import infer_schedule
from casestudy.templates import (LEARNED_PROPERTY_FACTS, amenity_phrases, move_month_phrase,
                                 render_templates, short_property_name)
from casestudy.validators import sms_segments

from casestudy.tests.test_contract import semantic_checklist_sms

DATA = Path(__file__).resolve().parents[1] / "data"
SAMPLES = [json.loads(l) for l in (DATA / "sample.jsonl").read_text().splitlines() if l.strip()]


def _render(raw):
    out = run_gates(raw)
    sched = infer_schedule(out)
    intent = infer_intent(out, sched)
    return render_templates(out, sched, intent), sched, intent, out


def _variant(idx=0, task_id=None, profile=None, **inp):
    raw = json.loads(json.dumps(SAMPLES[idx]))
    raw["input"].update(inp)
    if profile is not None:
        raw["input"]["profile"] = profile
    if task_id is not None:
        raw["task_id"] = task_id
    return raw


def _answer(t, sched, intent):
    return AssignmentAnswer.model_validate({
        "next_message": {"channel": t.draft.channel, "send_at": sched.send_at_iso, "subject": t.draft.subject,
                         "body": t.draft.body, "cta": t.draft.cta},
        "next_action": intent.next_action,
    })


# ------------------------------------------------------------------ the two references

def test_sms_reference_passes_checklist_and_validators():
    t, sched, intent, _ = _render(SAMPLES[0])
    assert t.draft is not None and t.report.passed, [r.reason for r in t.report.hard_failures]
    assert t.draft.label == "sms.welcome"
    answer = _answer(t, sched, intent)
    assert semantic_checklist_sms(answer, SAMPLES[0]["expected"]) is True
    assert answer.model_dump() == AssignmentAnswer.model_validate(SAMPLES[0]["expected"]).model_dump()  # optional regression: identical
    assert t.draft.body.endswith("Reply STOP to opt out.")
    assert t.report.segments <= 3
    assert {"profile.first_name", "input.property_name"} <= set(t.personalization_fields)


def test_email_reference_meaning_and_validators():
    t, sched, intent, _ = _render(SAMPLES[1])
    ref = SAMPLES[1]["expected"]["next_message"]
    assert t.draft is not None and t.report.passed, [r.reason for r in t.report.hard_failures]
    assert t.draft.label == "email.open_follow_up"
    answer = _answer(t, sched, intent)
    nm = answer.next_message
    # reference-derived meaning checklist
    assert nm.channel == "email" and nm.subject
    assert nm.cta.model_dump() == ref["cta"]
    assert "Taylor" in nm.body
    assert "mid-February" in nm.body  # natural move-month phrase
    assert "pool" in nm.body and "fitness" in nm.body  # amenity interests
    assert "24/7 fitness center" in nm.body  # learned Oak Ridge fact, with provenance
    assert "https://oakridge.example/tour" in nm.body  # URL from the training example, not a slug
    assert "click here or reply STOP" in nm.body
    assert "Oak Ridge" in nm.subject and "pool" in nm.subject
    assert answer.next_action.model_dump() == SAMPLES[1]["expected"]["next_action"]
    assert {"profile.first_name", "profile.amenity_interest", "input.move_date_target"} <= set(t.personalization_fields)
    assert any(r.rule == "template.provenance" and r.confidence == "observed" for r in t.results)


@pytest.mark.parametrize("raw", SAMPLES, ids=["sms", "email"])
def test_every_candidate_is_validated_and_trail_is_cited(raw):
    t, _, _, _ = _render(raw)
    assert len(t.reports) == len(t.candidates)
    for r in t.results:
        assert r.citation and r.reason and r.confidence


# ------------------------------------------------------------------ provenance

def test_oak_ridge_facts_never_generalize():
    raw = _variant(1, property_name="Maple Court Residences")
    raw["input"]["tour_link"] = "https://maplecourt.example/visit"
    t, _, intent, _ = _render(raw)
    assert t.report.passed
    assert "24/7" not in t.draft.body and "Oak Ridge" not in t.draft.body
    assert "oakridge.example" not in t.draft.body
    assert "Maple Court" in t.draft.subject and "https://maplecourt.example/visit" in t.draft.body
    assert "fitness center" in t.draft.body  # generic display name only
    assert not any(r.rule == "template.provenance" for r in t.results)
    assert set(LEARNED_PROPERTY_FACTS) == {"oak ridge apartments"}


def test_unseen_property_without_link_uses_reply_fallback():
    t, _, intent, _ = _render(_variant(1, property_name="Maple Court Residences"))
    assert intent.unresolved_link and t.report.passed
    assert "http" not in t.draft.body
    assert "Reply to this email" in t.draft.body
    assert "click here or reply STOP" in t.draft.body
    assert any(r.details.get("warning") == "unresolved_link" for r in t.results)


# ------------------------------------------------------------------ degradation

def test_missing_optional_fields_degrade_to_neutral_not_crash():
    raw = _variant(1, profile={}, move_date_target=None)
    raw["input"].pop("move_date_target")
    t, _, _, out = _render(raw)
    assert out.proceed and t.draft is not None and t.report.passed, [r.reason for r in (t.report.hard_failures if t.report else [])]
    assert t.draft.body.startswith("Hi there,")
    assert "floor plans and amenities" in t.draft.body
    assert "-" not in (move_month_phrase(out.record) or "")
    assert "profile.first_name" not in t.personalization_fields


def test_missing_property_name_and_first_name_sms():
    raw = _variant(0, profile={"last_name": "Reyes"})
    raw["input"].pop("property_name")
    t, _, _, _ = _render(raw)
    assert t.draft is not None and t.report.passed
    assert t.draft.body.startswith("Hi there")
    assert "our community" in t.draft.body
    assert "Reyes" not in t.draft.body  # unsafe field never read
    assert t.draft.body.endswith("Reply STOP to opt out.")


def test_unsafe_profile_fields_are_never_used():
    raw = _variant(1, profile={"first_name": "Taylor", "amenity_interest": ["pool"], "income": "$92,000",
                               "phone": "214-555-0100", "religion": "x", "children": 2})
    t, _, _, _ = _render(raw)
    assert t.report.passed
    for bad in ("92,000", "214-555", "religion", "children"):
        assert bad not in t.draft.body


def test_long_property_name_falls_back_to_compact_gsm7_sms():
    raw = _variant(0, property_name="The Residences at Preston Hollow Crossing North Apartments",
                   profile={"first_name": "Alexandria-Catherine"})
    t, _, _, _ = _render(raw)
    assert t.draft is not None and t.report.passed
    assert t.draft.label == "sms.welcome.compact"
    assert "—" not in t.draft.body  # GSM-7 variant avoids the em dash
    assert sms_segments(t.draft.body) <= 3
    assert "Reply 1 for Thu, 2 for Fri" in t.draft.body
    assert t.draft.body.endswith("Reply STOP to opt out.")
    assert len(t.reports) == 2 and not t.reports[0].passed and t.reports[1].passed


# ------------------------------------------------------------------ other flows / channels

def test_open_follow_up_sms_and_welcome_email():
    raw = _variant(1)
    raw["consent"]["sms_opt_in"] = True
    raw["channel_preferences"] = ["sms", "email"]
    t, _, _, _ = _render(raw)
    assert t.draft.channel == "sms" and t.draft.label == "sms.open_follow_up" and t.report.passed
    assert t.draft.subject is None and "Oak Ridge" in t.draft.body

    raw = _variant(0)
    raw["consent"]["sms_opt_in"] = False
    t, _, intent, _ = _render(raw)
    assert t.draft.channel == "email" and t.draft.label == "email.welcome" and t.report.passed
    assert "Welcome to Oak Ridge" in t.draft.body and "https://oakridge.example/tour" in t.draft.body
    assert "planning an early-January move" in t.draft.body  # Jan 10 -> early; article agrees
    assert intent.next_action == {"type": "start_cadence", "name": "prospect_welcome_short_horizon"}


def test_option_reply_proposes_follow_up_without_claiming_a_booking():
    raw = _variant(0)
    raw["input"]["inbound_reply"] = "2"
    raw["input"]["prior_options"] = ["Thu", "Fri"]
    t, _, intent, out = _render(raw)
    assert out.decision == "propose_follow_up" and out.selected_option == "Fri"
    assert t.draft.label == "sms.option_reply" and t.report.passed
    assert "Fri" in t.draft.body and "follow up" in t.draft.body and "arrange your tour" in t.draft.body
    assert "confirmed" not in t.draft.body and "booked" not in t.draft.body
    assert t.draft.body.count("?") <= 1
    assert intent.next_action == {"type": "follow_up_in_days", "value": 3}


def test_stop_and_voice_produce_no_draft():
    raw = _variant(0)
    raw["input"]["inbound_reply"] = "STOP"
    t, _, intent, out = _render(raw)
    assert out.decision == "mark_opted_out" and t.draft is None
    assert t.results[0].status == "skipped"

    raw = _variant(0)
    raw["consent"] = {"voice_opt_in": True, "sms_opt_in": False, "email_opt_in": False}
    raw["channel_preferences"] = ["voice"]
    t, sched, _, _ = _render(raw)
    assert sched.kind == "call_task" and t.draft is None
    assert "call task" in t.results[0].reason


# ------------------------------------------------------------------ helpers

def test_helper_phrases():
    rec = run_gates(SAMPLES[1]).record
    assert move_month_phrase(rec) == "mid-February"
    assert move_month_phrase(run_gates(_variant(1, move_date_target="2026-02-03")).record) == "early-February"
    assert move_month_phrase(run_gates(_variant(1, move_date_target="2026-02-28")).record) == "late-February"
    assert amenity_phrases(rec) == ["pool", "24/7 fitness center"]
    assert amenity_phrases(rec, detailed=False) == ["pool", "fitness center"]
    assert short_property_name(rec) == ("Oak Ridge", "observed")
    assert short_property_name(run_gates(_variant(1, property_name="Maple Court Residences")).record) == ("Maple Court", "hypothesis")
    assert short_property_name(run_gates(_variant(1, property_name="Skyline")).record) == ("Skyline", "hypothesis")
