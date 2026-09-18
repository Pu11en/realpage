"""C4: channel-specific validators."""
import json
from pathlib import Path

import pytest

from casestudy.gates import normalize
from casestudy.validators import (
    Draft,
    FAIR_HOUSING_LEXICON,
    select_draft,
    sms_segments,
    validate_draft,
)

SAMPLE = Path(__file__).resolve().parents[1] / "data" / "sample.jsonl"


def _records():
    return [json.loads(l) for l in SAMPLE.read_text().splitlines() if l.strip()]


def _draft_from(raw, source="template", **over):
    e = dict(raw["expected"]["next_message"])
    e.update(over)
    return Draft(e["channel"], e["body"], e["subject"], e["cta"], source=source)


def _rules(rep, status=None):
    return {r.rule for r in rep.results if status is None or r.status == status}


# ------------------------------------------------------------------ samples

def test_sms_sample_passes():
    raw = _records()[0]
    rep = validate_draft(_draft_from(raw), normalize(raw))
    assert rep.passed, [r.reason for r in rep.hard_failures]
    assert set(rep.verified_states) == {"fair_housing_check_passed", "brand_style_applied"}
    assert {"sms.subject_null", "sms.stop_sentence", "sms.numbered_options", "sms.one_question",
            "include_opt_out_instructions", "no_sensitive_discrimination"} <= _rules(rep, "passed")
    assert rep.segments == 3  # em dash forces UCS-2 encoding: 165 chars -> 3 segments


def test_email_sample_passes_without_postal_address():
    raw = _records()[1]
    rep = validate_draft(_draft_from(raw), normalize(raw))
    assert rep.passed, [r.reason for r in rep.hard_failures]
    assert {"email.subject_present", "email.subject_accurate", "email.link_cta", "email.opt_out",
            "include_opt_out_instructions"} <= _rules(rep, "passed")
    assert "email_delivery_compliance" in rep.unverified
    assert "out of scope" in rep.unverified["email_delivery_compliance"]
    assert "no_sensitive_discrimination" not in _rules(rep)  # record 2 does not assert it


# ------------------------------------------------------------------ SMS rules

def test_sms_requires_null_subject_and_literal_stop():
    raw = _records()[0]
    rec = normalize(raw)
    assert "sms.subject_null" in _rules(validate_draft(_draft_from(raw, subject="Hi"), rec), "failed")
    body = raw["expected"]["next_message"]["body"].replace(" Reply STOP to opt out.", " Text STOP to quit.")
    rep = validate_draft(_draft_from(raw, body=body), rec)
    assert not rep.passed
    assert {"sms.stop_sentence", "include_opt_out_instructions"} <= _rules(rep, "failed")


def test_sms_numbered_options_and_one_question():
    raw = _records()[0]
    rec = normalize(raw)
    body = "Hi Taylor—welcome to Oak Ridge! Want a tour Thursday or Friday? Reply STOP to opt out."
    rep = validate_draft(_draft_from(raw, body=body), rec)
    assert "sms.numbered_options" in _rules(rep, "failed")
    body = "Hi Taylor—tour this week? Thursday or Friday? Reply 1 for Thu, 2 for Fri. Reply STOP to opt out."
    assert "sms.one_question" in _rules(validate_draft(_draft_from(raw, body=body), rec), "failed")


def test_sms_segment_count():
    assert sms_segments("Hi there") == 1
    assert sms_segments("a" * 160) == 1
    assert sms_segments("a" * 161) == 2
    assert sms_segments("é" * 70) == 1  # é is GSM-7 basic
    assert sms_segments("—" + "a" * 70) == 2  # em dash -> UCS-2
    raw = _records()[0]
    long_body = "Hi Taylor—" + "tour " * 120 + "Reply 1 for Thu, 2 for Fri. Reply STOP to opt out."
    rep = validate_draft(_draft_from(raw, body=long_body), normalize(raw))
    assert "sms.segments" in _rules(rep, "failed")


# ------------------------------------------------------------------ email rules

def test_email_requires_subject_link_and_opt_out():
    raw = _records()[1]
    rec = normalize(raw)
    assert "email.subject_present" in _rules(validate_draft(_draft_from(raw, subject=None), rec), "failed")
    assert "email.subject_present" in _rules(validate_draft(_draft_from(raw, subject="  "), rec), "failed")
    body = raw["expected"]["next_message"]["body"].replace("https://oakridge.example/tour", "our site")
    assert "email.link_cta" in _rules(validate_draft(_draft_from(raw, body=body), rec), "failed")
    body = raw["expected"]["next_message"]["body"].replace("To opt out of emails, click here or reply STOP.", "Thanks.")
    rep = validate_draft(_draft_from(raw, body=body), rec)
    assert {"email.opt_out", "include_opt_out_instructions"} <= _rules(rep, "failed")


def test_email_subject_must_reflect_body_or_property():
    raw = _records()[1]
    rep = validate_draft(_draft_from(raw, subject="Congratulations winner"), normalize(raw))
    assert "email.subject_accurate" in _rules(rep, "failed")


# ------------------------------------------------------------------ profile / PII

def test_unsafe_profile_data_is_ignored_when_not_echoed():
    raw = json.loads(json.dumps(_records()[0]))
    raw["input"]["profile"].update({
        "last_name": "Nguyen", "phone": "214-555-0199", "email": "t@example.com",
        "income": "$85,000", "religion": "Catholic", "household": "2 adults 3 kids",
        "wheelchair_user": True, "notes": "wants good schools",
    })
    rep = validate_draft(_draft_from(raw), normalize(raw))
    assert rep.passed
    leak = next(r for r in rep.results if r.rule == "no_pii_leak")
    assert "religion" in leak.details["ignored_profile_fields"]
    assert "first_name" not in leak.details["ignored_profile_fields"]


@pytest.mark.parametrize("field,value,snippet", [
    ("last_name", "Nguyen", "Hi Taylor Nguyen—"),
    ("phone", "214-555-0199", "Hi Taylor—we'll call 214-555-0199. "),
    ("income", "$85,000", "Hi Taylor—with your $85,000 income "),
    ("city_interest", "Richardson, TX", "Hi Taylor—since you like Richardson, TX, "),
    ("current_address", "12 Elm St", "Hi Taylor—near 12 Elm St, "),
])
def test_echoing_unapproved_profile_field_is_hard(field, value, snippet):
    raw = json.loads(json.dumps(_records()[0]))
    raw["input"]["profile"][field] = value
    body = snippet + "tours this week. Reply 1 for Thu, 2 for Fri. Reply STOP to opt out."
    rep = validate_draft(_draft_from(raw, body=body), normalize(raw))
    assert not rep.passed
    hit = next(r for r in rep.hard_failures if r.rule == "no_pii_leak.profile_echo")
    assert hit.details["field"] == field and hit.citation


def test_business_money_and_address_are_allowed():
    raw = json.loads(json.dumps(_records()[0]))
    raw["input"]["rent_from"] = "$1,450"
    raw["input"]["property_address"] = "100 Oak Ridge Dr"
    body = ("Hi Taylor—welcome to Oak Ridge at 100 Oak Ridge Dr! Homes from $1,450. "
            "Reply 1 for Thu, 2 for Fri. Reply STOP to opt out.")
    rep = validate_draft(_draft_from(raw, body=body), normalize(raw))
    assert rep.passed, [r.reason for r in rep.hard_failures]
    assert "no_pii_leak.business_data" in _rules(rep, "passed")


def test_pattern_pii_without_business_provenance_is_hard():
    raw = _records()[0]
    body = "Hi Taylor—email me at leasing@oakridge.example. Reply 1 for Thu, 2 for Fri. Reply STOP to opt out."
    rep = validate_draft(_draft_from(raw, body=body), normalize(raw))
    assert "no_pii_leak.pattern" in _rules(rep, "failed")
    raw2 = json.loads(json.dumps(raw))
    raw2["input"]["property"] = {"contact_email": "leasing@oakridge.example"}
    assert validate_draft(_draft_from(raw2, body=body), normalize(raw2)).passed


# ------------------------------------------------------------------ fair housing

def test_fair_housing_hard_and_warn_keep_citation_and_rewrite():
    raw = _records()[0]
    rec = normalize(raw)
    body = "Hi Taylor—welcome to Oak Ridge, an adults-only community! Reply 1 for Thu, 2 for Fri. Reply STOP to opt out."
    rep = validate_draft(_draft_from(raw, body=body), rec)
    assert not rep.passed
    hit = next(r for r in rep.hard_failures if r.rule == "fair_housing.hard")
    assert "3604" in hit.citation and hit.details["rewrite"]
    assert "fair_housing_check_passed" not in rep.verified_states

    body = "Hi Taylor—welcome to Oak Ridge, near great schools! Reply 1 for Thu, 2 for Fri. Reply STOP to opt out."
    rep = validate_draft(_draft_from(raw, body=body), rec)
    assert rep.passed
    warn = next(r for r in rep.warnings if r.rule == "fair_housing.warn")
    assert "3604" in warn.citation and warn.details["rewrite"]
    assert "fair_housing_check_passed" in rep.verified_states


def test_lexicon_entries_all_have_citations_via_levels():
    assert {e.level for e in FAIR_HOUSING_LEXICON} == {"HARD", "WARN"}
    assert all(e.rewrite for e in FAIR_HOUSING_LEXICON)


# ------------------------------------------------------------------ brand style

def test_brand_style_violations_block():
    raw = _records()[0]
    rec = normalize(raw)
    body = "Taylor!! AMAZING deals 🎉 Reply 1 for Thu, 2 for Fri. Reply STOP to opt out."
    rep = validate_draft(_draft_from(raw, body=body), rec)
    assert {"brand_style.greeting", "brand_style.exclamations", "brand_style.emoji", "brand_style.shouting"} <= _rules(rep, "failed")
    assert "brand_style_applied" not in rep.verified_states


# ------------------------------------------------------------------ model draft

def test_model_draft_cannot_override_hard_failure():
    raw = _records()[0]
    rec = normalize(raw)
    template = _draft_from(raw, source="template")
    model = _draft_from(raw, source="model", body="Hi Taylor Smith—no kids allowed. Reply 1 for Thu, 2 for Fri. Reply STOP to opt out.")
    raw_prof = json.loads(json.dumps(raw)); raw_prof["input"]["profile"]["last_name"] = "Smith"
    rec = normalize(raw_prof)
    chosen, reports = select_draft([model, template], rec)
    assert chosen is template
    assert not reports[0].passed and reports[1].passed
    assert "validation.model_draft" in _rules(reports[0], "failed")
    assert select_draft([model], rec)[0] is None
