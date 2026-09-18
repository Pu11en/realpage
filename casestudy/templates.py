"""C5: offline templates.

The offline path never calls a model. `render_templates()` takes the gate outcome, schedule and
intent, fills a small set of templates, runs every candidate through the C4 validators, and
returns the first candidate that passes together with the full trail. Templates are ordered
so the reference-shaped draft is tried first and a compact GSM-7 variant (no em dash) is the
fallback when the SMS segment cap would be exceeded.

Template coverage (smallest set for the intents/channels tested so far):
  sms   welcome | open_follow_up | option_reply
  email welcome | open_follow_up | option_reply   (each with a link or no-link variant)
Voice / call tasks and terminal gate decisions (opt-out, suppress, escalate) produce no draft;
the trail says why and C7 decides how they appear in the public shape.

Provenance rules:
  * Property facts learned from the supplied example (short display name "Oak Ridge", the
    "24/7 fitness center" detail, the tour URL) are keyed to that exact property and are never
    generalized to another property. Another property gets neutral wording.
  * The email template uses amenity interests and a natural move-month phrase
    (Feb 15 -> "mid-February") when the fields exist; missing fields degrade to neutral copy.
  * SMS keeps the literal "Reply STOP to opt out." sentence.
  * Unsafe profile fields are never read by a template; only first_name and amenity_interest
    are used, matching the validators' approved list.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Optional

from .gates import GateOutcome, GateResult, NormalizedRecord
from .intent import Intent
from .schedule import Schedule
from .validators import Draft, ValidationReport, select_draft

TEMPLATES_VERSION = "templates_v1"

SAMPLE_CITE = "sample.jsonl expected blocks (two records)"
PLAN_CITE = "PLAN-casestudy-bot.md C5"

SMS_STOP = "Reply STOP to opt out."
EMAIL_OPT_OUT = "To opt out of emails, click here or reply STOP."

DAY_FULL = {"Mon": "Monday", "Tue": "Tuesday", "Wed": "Wednesday", "Thu": "Thursday", "Fri": "Friday", "Sat": "Saturday", "Sun": "Sunday"}
MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December")

# Generic suffixes stripped to form a short display name ("Oak Ridge Apartments" -> "Oak Ridge").
# The rule is a hypothesis generalized from one observed example; the Oak Ridge entry below is
# the observed fact with provenance.
NAME_SUFFIX_RE = re.compile(r"\s+(apartments?|apts?\.?|residences?|homes?|community|lofts?|flats|towers?|place|village)$", re.I)

# Amenity display names (project defaults; the reference wrote "fitness center" for "fitness").
AMENITY_DISPLAY = {
    "pool": "pool", "fitness": "fitness center", "gym": "fitness center", "fitness_center": "fitness center",
    "parking": "covered parking", "garage": "garage parking", "pet": "pet-friendly spaces", "pets": "pet-friendly spaces",
    "dog_park": "dog park", "balcony": "private balconies", "washer_dryer": "in-unit washer and dryer",
    "laundry": "in-unit washer and dryer", "clubhouse": "clubhouse", "coworking": "coworking lounge",
    "ev_charging": "EV charging", "rooftop": "rooftop lounge", "playground": "playground",
}

# Facts learned from the supplied example, keyed to the exact property. Never generalized.
LEARNED_PROPERTY_FACTS: dict[str, dict[str, Any]] = {
    "oak ridge apartments": {
        "short_name": "Oak Ridge",
        "amenity_detail": {"fitness": "24/7 fitness center"},
        "source": "sample.jsonl record 1 body ('welcome to Oak Ridge') and record 2 body ('24/7 fitness center')",
    },
}


@dataclass
class TemplateOutput:
    draft: Optional[Draft]
    candidates: list[Draft]
    reports: list[ValidationReport]
    personalization_fields: list[str]  # safe fields actually used in the chosen draft
    results: list[GateResult] = field(default_factory=list)
    version: str = TEMPLATES_VERSION

    @property
    def report(self) -> Optional[ValidationReport]:
        if self.draft is None:
            return None
        return self.reports[self.candidates.index(self.draft)]


# --------------------------------------------------------------------------- field helpers

def _first_name(rec: NormalizedRecord) -> Optional[str]:
    v = rec.profile.get("first_name") if isinstance(rec.profile, dict) else None
    return v.strip() if isinstance(v, str) and v.strip() else None


def _property_name(rec: NormalizedRecord) -> Optional[str]:
    v = rec.input.get("property_name")
    return v.strip() if isinstance(v, str) and v.strip() else None


def _learned(rec: NormalizedRecord) -> dict[str, Any]:
    prop = _property_name(rec)
    return LEARNED_PROPERTY_FACTS.get(prop.lower(), {}) if prop else {}


def short_property_name(rec: NormalizedRecord) -> tuple[Optional[str], str]:
    """Returns (short name, confidence). Learned name is observed; stripped suffix is a hypothesis."""
    prop = _property_name(rec)
    if not prop:
        return None, "conservative_default"
    learned = _learned(rec)
    if learned.get("short_name"):
        return learned["short_name"], "observed"
    short = NAME_SUFFIX_RE.sub("", prop).strip()
    return (short or prop), "hypothesis"


def amenity_phrases(rec: NormalizedRecord, detailed: bool = True) -> list[str]:
    raw = rec.profile.get("amenity_interest") if isinstance(rec.profile, dict) else None
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, (list, tuple)):
        return []
    detail = _learned(rec).get("amenity_detail", {}) if detailed else {}
    out: list[str] = []
    for a in raw:
        if not isinstance(a, str) or not a.strip():
            continue
        key = a.strip().lower().replace(" ", "_")
        phrase = detail.get(key) or AMENITY_DISPLAY.get(key) or a.strip().lower()
        if phrase not in out:
            out.append(phrase)
    return out[:3]


def join_natural(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def move_month_phrase(rec: NormalizedRecord) -> Optional[str]:
    """'2026-02-15' -> 'mid-February' (observed); early <= 10, mid 11-20, late > 20 (hypothesis)."""
    raw = rec.input.get("move_date_target")
    if not isinstance(raw, str):
        return None
    try:
        d = date.fromisoformat(raw.strip()[:10])
    except ValueError:
        return None
    part = "early" if d.day <= 10 else "mid" if d.day <= 20 else "late"
    return f"{part}-{MONTHS[d.month - 1]}"


# --------------------------------------------------------------------------- SMS templates

def _sms_options(intent: Intent) -> Optional[list[str]]:
    cta = intent.cta or {}
    opts = cta.get("options")
    return [str(o) for o in opts] if isinstance(opts, list) and len(opts) >= 2 else None


def sms_candidates(rec: NormalizedRecord, outcome: GateOutcome, intent: Intent) -> list[Draft]:
    first = _first_name(rec)
    short, _ = short_property_name(rec)
    opts = _sms_options(intent)
    who = first or "there"
    place = short or "our community"
    if not opts:
        ask = "Reply with a day that works for a tour."
        ask_compact = ask
    else:
        full = [DAY_FULL.get(o, o) for o in opts]
        ask = f"Would you like to book a time on {full[0]} or {full[1]}? Reply 1 for {opts[0]}, 2 for {opts[1]}."
        ask_compact = f"Reply 1 for {opts[0]}, 2 for {opts[1]} to book a tour."
    drafts: list[Draft] = []
    if outcome.decision == "propose_follow_up" and outcome.selected_option:
        sel = outcome.selected_option
        body = f"Hi {who}—thanks, we will confirm your {sel} tour at {place}. Prefer another day? {ask_compact} {SMS_STOP}"
        compact = f"Hi {who}, we will confirm your {sel} tour at {place}. {ask_compact} {SMS_STOP}"
        label = "sms.option_reply"
    elif intent.flow == "welcome":
        body = f"Hi {who}—welcome to {place}! Tours are available this week. {ask} {SMS_STOP}"
        compact = f"Hi {who}, welcome to {place}! Tours are open this week. {ask_compact} {SMS_STOP}"
        label = "sms.welcome"
    else:
        body = f"Hi {who}—tours at {place} are open this week. {ask} {SMS_STOP}"
        compact = f"Hi {who}, tours at {place} are open this week. {ask_compact} {SMS_STOP}"
        label = "sms.open_follow_up"
    drafts.append(Draft("sms", body, None, intent.cta, "template", label))
    drafts.append(Draft("sms", compact, None, intent.cta, "template", label + ".compact"))
    return drafts


# --------------------------------------------------------------------------- email templates

def email_candidates(rec: NormalizedRecord, outcome: GateOutcome, intent: Intent) -> list[Draft]:
    first = _first_name(rec)
    short, _ = short_property_name(rec)
    amen = amenity_phrases(rec)
    amen_plain = amenity_phrases(rec, detailed=False)
    month = move_month_phrase(rec)
    link = (intent.cta or {}).get("link")
    who = first or "there"
    place = short or "our community"

    article = "an" if month and month[0].lower() in "aeiou" else "a"
    lead = f"Since you're planning {article} {month} move, " if month else "As you plan your move, "
    if amen:
        look = f"here's a quick look at our {join_natural(amen)}."
        subj_focus = f"See the {join_natural(amen_plain)} you asked about"
    else:
        look = "here's a quick look at our floor plans and amenities."
        subj_focus = "See our floor plans and amenities"

    if link:
        cta_line = f"Book now → {link}"
        ask = "Book a visit this week to compare floor plans."
    else:
        cta_line = "Reply to this email and we'll arrange a time."
        ask = "Visit this week to compare floor plans."

    if outcome.decision == "propose_follow_up" and outcome.selected_option:
        sel = outcome.selected_option
        subject = f"Your {sel} tour at {place}"
        body = f"Hi {who},\nThanks, we will follow up to confirm your {sel} tour at {place}. {cta_line}\n{EMAIL_OPT_OUT}"
        label = "email.option_reply"
    elif intent.flow == "welcome":
        subject = f"Welcome to {place}—{subj_focus.lower()}" if amen else f"Welcome to {place}—book your tour"
        body = f"Hi {who},\nWelcome to {place}! {lead}{look} {ask}\n{cta_line}\n{EMAIL_OPT_OUT}"
        label = "email.welcome"
    else:
        subject = f"Tour {place}—{subj_focus}"
        body = f"Hi {who},\n{lead}{look} {ask}\n{cta_line}\n{EMAIL_OPT_OUT}"
        label = "email.open_follow_up"
    return [Draft("email", body, subject, intent.cta, "template", label)]


# --------------------------------------------------------------------------- driver

def personalization_fields(rec: NormalizedRecord, draft: Draft) -> list[str]:
    """Return safe input fields visibly used by this specific draft.

    This must be run against the final selected draft (model or template), not merely the
    template offered to the writer as a fallback.
    """
    used: list[str] = []
    text = f"{draft.subject or ''}\n{draft.body}".lower()
    if _first_name(rec) and _first_name(rec).lower() in text:
        used.append("profile.first_name")
    if _property_name(rec) and (short_property_name(rec)[0] or "").lower() in text:
        used.append("input.property_name")
    if any(p.lower() in text for p in amenity_phrases(rec)):
        used.append("profile.amenity_interest")
    m = move_month_phrase(rec)
    if m and m.lower() in text:
        used.append("input.move_date_target")
    if draft.channel:
        used.append("channel")
    return used


def render_templates(outcome: GateOutcome, schedule: Schedule, intent: Intent) -> TemplateOutput:
    results: list[GateResult] = []
    rec = outcome.record
    if rec is None or not outcome.proceed or intent.flow in (None, "none", "opted_out"):
        results.append(GateResult("template", "skipped", f"gate decision {outcome.decision!r}: no message drafted", "project rule: terminal gate decisions never draft", "conservative_default"))
        return TemplateOutput(None, [], [], [], results)
    if schedule.kind != "automated_message" or schedule.channel not in ("sms", "email"):
        results.append(GateResult("template", "skipped", f"channel {schedule.channel!r} ({schedule.kind}) has no automated template; a call task is proposed instead", PLAN_CITE, "conservative_default", {"kind": schedule.kind}))
        return TemplateOutput(None, [], [], [], results)

    short, short_conf = short_property_name(rec)
    if short:
        results.append(GateResult("template.property_name", "passed", f"display name {short!r}" + (" learned from the supplied example" if short_conf == "observed" else " by stripping a generic suffix"), SAMPLE_CITE if short_conf == "observed" else PLAN_CITE, short_conf, {"short_name": short}))
    else:
        results.append(GateResult("template.property_name", "passed", "no property_name; neutral wording 'our community'", PLAN_CITE + ": degrade to neutral, never crash", "conservative_default"))
    if not _first_name(rec):
        results.append(GateResult("template.first_name", "passed", "no first_name; neutral greeting 'Hi there'", PLAN_CITE, "conservative_default"))
    learned = _learned(rec)
    if learned:
        results.append(GateResult("template.provenance", "passed", "property facts for this exact property come from the supplied example and are not generalized", learned["source"], "observed", {"property": _property_name(rec)}))
    lang = rec.input.get("language")
    if isinstance(lang, str) and lang.strip().lower() not in ("en", "en-us", ""):
        results.append(GateResult("template.language", "passed", f"language {lang!r} requested; only English templates exist, flagging uncertainty", PLAN_CITE, "conservative_default", {"warning": "language_unsupported"}))

    if schedule.channel == "sms":
        candidates = sms_candidates(rec, outcome, intent)
    else:
        candidates = email_candidates(rec, outcome, intent)
        if intent.unresolved_link:
            results.append(GateResult("template.link", "passed", "no safe tour link; reply-to-arrange fallback wording", PLAN_CITE, "conservative_default", {"warning": "unresolved_link"}))
        if amenity_phrases(rec):
            results.append(GateResult("template.amenities", "passed", f"amenity interests used: {amenity_phrases(rec)}", SAMPLE_CITE + ": record 2 names pool and fitness", "observed", {"amenities": amenity_phrases(rec)}))
        if move_month_phrase(rec):
            results.append(GateResult("template.move_month", "passed", f"move-month phrase {move_month_phrase(rec)!r}", SAMPLE_CITE + ": record 2 'mid-February' for 2026-02-15", "observed"))

    chosen, reports = select_draft(candidates, rec)
    if chosen is None:
        results.append(GateResult("template", "failed", "every template candidate failed a hard validator rule", PLAN_CITE, "conservative_default", {"failures": [[r.rule for r in rep.hard_failures] for rep in reports]}))
        return TemplateOutput(None, candidates, reports, [], results)
    results.append(GateResult("template", "passed", f"template {chosen.label!r} passes all hard validator rules", PLAN_CITE, "conservative_default", {"label": chosen.label, "candidates_tried": candidates.index(chosen) + 1}))
    return TemplateOutput(chosen, candidates, reports, personalization_fields(rec, chosen), results)
