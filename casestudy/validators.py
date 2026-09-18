"""C4: channel-specific validators for a drafted message.

Validation is deterministic Python and applies equally to template drafts and model drafts
(IFScale, arXiv 2507.11538: rules in code, not in the prompt). A HARD failure can never be
overridden by a model draft; `select_draft()` always falls back to the first candidate that
passes. Every finding is a `GateResult` with status, reason, citation, confidence, and (for
fair-housing hits) a suggested rewrite.

What this module verifies:
  * `fair_housing_check_passed`  — no HARD lexicon hit (42 U.S.C. §3604(c)); WARN entries are
                                    reported, cited, and do not block.
  * `brand_style_applied`        — project style defaults (greeting, <=1 "!", no emoji, no
                                    ALL-CAPS shouting except STOP/HELP, no URL shorteners).
  * `no_pii_leak` / profile echo — unapproved profile fields must not be echoed. Money and street
                                    addresses are NOT PII per se: they are blocked only when they
                                    come from the profile, and allowed when they are supplied
                                    property/business data.
  * SMS                          — null subject, literal trailing "Reply STOP to opt out.",
                                    one-question style with numbered options when the CTA has
                                    options, GSM-7/UCS-2 segment count.
  * Email                        — non-null accurate subject, link CTA present in the body when
                                    the CTA carries a link, conspicuous click-or-STOP opt-out.

What this module does NOT verify (and says so): actual email-delivery compliance (CAN-SPAM
postal address, header accuracy, unsubscribe mechanics). The supplied simulation example omits a
postal address, no transport exists to add a footer, so that requirement is reported as
`unverified` and out of scope rather than failed or assumed.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

from .gates import GateResult, NormalizedRecord

VALIDATORS_VERSION = "validators_v1"

FHA_CITE = "Fair Housing Act, 42 U.S.C. §3604(c); HUD advertising guidance (24 CFR 109, historical)"
CTIA_CITE = "CTIA Messaging Principles & Best Practices (STOP/HELP keywords); 47 CFR §64.1200(a)(10)"
CANSPAM_CITE = "CAN-SPAM, 15 U.S.C. §7704(a)"
SAMPLE_CITE = "sample.jsonl expected blocks (two records)"
PLAN_CITE = "PLAN-casestudy-bot.md C4"
REVIEW_CITE = "REVIEW-astra.md (channel-specific validation; no imaginary footer)"

SMS_STOP_SENTENCE = "Reply STOP to opt out."  # observed, record 1
SMS_MAX_SEGMENTS = 3  # conservative_default
GSM7_BASIC = set(
    "@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞ\x1bÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>?"
    "¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà"
)
GSM7_EXT = set("^{}\\[~]|€")

# Profile fields whose values may be echoed in marketing copy (observed in the samples).
APPROVED_PROFILE_FIELDS = {"first_name", "amenity_interest", "amenities", "preferred_name"}
# Profile fields that are always unsafe to echo, even when not literally matched.
SENSITIVE_PROFILE_FIELDS = {
    "last_name", "phone", "phone_number", "email", "email_address", "ssn", "ssn4", "income",
    "annual_income", "credit_score", "date_of_birth", "dob", "age", "religion", "race",
    "ethnicity", "national_origin", "disability", "accommodation", "wheelchair_user",
    "household", "children", "kids", "familial_status", "marital_status", "sexual_orientation",
    "gender", "gender_identity", "immigration_status", "military_status", "source_of_income",
    "voucher", "address", "street_address", "current_address", "city_interest", "notes",
}
# Business/property fields whose money or address text is allowed in copy.
BUSINESS_FIELDS = (
    "property_name", "property_address", "address", "rent", "rent_from", "starting_rent",
    "pricing", "special", "deposit", "tour_link", "booking_link", "office_hours",
)

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}(?!\d)")
SSN_RE = re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)")
MONEY_RE = re.compile(r"\$\s?\d[\d,]*(?:\.\d{2})?")
STREET_RE = re.compile(
    r"\b\d{1,6}\s+(?:[A-Z][a-z]+\s){1,3}(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Dr|Drive|"
    r"Ln|Lane|Ct|Court|Way|Pkwy|Parkway|Pl|Place|Trl|Trail)\b\.?"
)
URL_RE = re.compile(r"https?://[^\s<>\"]+")
SHORTENER_RE = re.compile(r"https?://(?:bit\.ly|tinyurl\.com|t\.co|goo\.gl|ow\.ly|is\.gd)/", re.I)
EMOJI_RE = re.compile("[\U0001F000-\U0001FAFF☀-➿\U0001F900-\U0001F9FF]")
CAPS_WORD_RE = re.compile(r"\b[A-Z]{3,}\b")
CAPS_ALLOWED = {"STOP", "HELP", "SMS", "USA", "TX", "PDF", "FAQ"}
GREETING_RE = re.compile(r"^\s*(hi|hello|hey)\b", re.I)


@dataclass(frozen=True)
class LexiconEntry:
    pattern: str
    level: str  # HARD | WARN
    category: str
    rewrite: str

    @property
    def regex(self) -> "re.Pattern[str]":
        return re.compile(self.pattern, re.IGNORECASE)


# Fair-housing lexicon. HARD = explicit preference/limitation on a protected class or an
# obvious proxy for one; WARN = coded language HUD guidance flags as risky in context.
FAIR_HOUSING_LEXICON: tuple[LexiconEntry, ...] = (
    LexiconEntry(r"\b(no|without)\s+(kids|children)\b", "HARD", "familial_status", "Remove; describe the unit, not who should live in it."),
    LexiconEntry(r"\badults?[\s-]only\b", "HARD", "familial_status", "Remove 'adults only'."),
    LexiconEntry(r"\b(perfect|ideal|great)\s+for\s+(families|singles|couples|students|seniors|retirees|young professionals|professionals|bachelors|empty nesters)\b", "HARD", "protected_class_targeting", "Describe features (e.g. 'three-bedroom floor plans'), not the intended household."),
    LexiconEntry(r"\b(christian|jewish|muslim|catholic|hindu|buddhist|church-?going)\s+(community|neighborhood|building|residents?)\b", "HARD", "religion", "Remove religious characterization."),
    LexiconEntry(r"\b(white|black|asian|hispanic|latino|latina)\s+(neighborhood|community|area|residents?)\b", "HARD", "race_national_origin", "Remove racial/ethnic characterization."),
    LexiconEntry(r"\b(english|spanish)[\s-]speaking\s+(only|residents?|community|tenants?)\b", "HARD", "national_origin", "Remove language restriction; offer translation instead."),
    LexiconEntry(r"\b(no|not suitable for)\s+(wheelchairs?|disabled|handicapped)\b", "HARD", "disability", "Remove; accommodations are handled on request (FHA §3604(f))."),
    LexiconEntry(r"\b(citizens?|legal residents?)\s+only\b", "HARD", "national_origin", "Remove immigration/citizenship restriction."),
    LexiconEntry(r"\b(no|without)\s+(section\s*8|vouchers?)\b", "HARD", "source_of_income", "Remove source-of-income restriction (protected in many states)."),
    LexiconEntry(r"\b(male|female|men|women)\s+only\b", "HARD", "sex", "Remove sex restriction."),
    LexiconEntry(r"\b(good|great|top|excellent|best)\s+schools?\b", "WARN", "familial_status_proxy", "Name the school district factually or omit."),
    LexiconEntry(r"\b(safe|quiet|exclusive|upscale|traditional)\s+(neighborhood|community|area)\b", "WARN", "coded_proxy", "Describe amenities, not neighborhood character."),
    LexiconEntry(r"\byoung\s+professionals?\b", "WARN", "age_familial_proxy", "Say 'close to downtown offices' instead."),
    LexiconEntry(r"\b(walkable|perfect|ideal)\s+for\s+seniors\b", "WARN", "age_proxy", "Describe elevator access / single-level plans."),
    LexiconEntry(r"\bfamily[\s-]friendly\b", "WARN", "familial_status_proxy", "List the playground or pool instead."),
    LexiconEntry(r"\bnear\s+(churches?|mosques?|synagogues?|temples?)\b", "WARN", "religion_proxy", "Omit places of worship as selling points."),
)


@dataclass
class Draft:
    channel: str
    body: str
    subject: Optional[str] = None
    cta: Optional[dict[str, Any]] = None
    source: str = "template"  # template | model
    label: str = ""


@dataclass
class ValidationReport:
    channel: str
    source: str
    results: list[GateResult] = field(default_factory=list)
    hard_failures: list[GateResult] = field(default_factory=list)
    warnings: list[GateResult] = field(default_factory=list)
    verified_states: list[str] = field(default_factory=list)
    unverified: dict[str, str] = field(default_factory=dict)
    segments: Optional[int] = None
    version: str = VALIDATORS_VERSION

    @property
    def passed(self) -> bool:
        return not self.hard_failures

    def add(self, res: GateResult, *, hard: bool = False, warn: bool = False) -> None:
        self.results.append(res)
        if res.status == "failed" and hard:
            self.hard_failures.append(res)
        elif warn:
            self.warnings.append(res)


# --------------------------------------------------------------------------- helpers

def _text(draft: Draft) -> str:
    return f"{draft.subject or ''}\n{draft.body or ''}"


def _flatten(value: Any) -> list[str]:
    if value is None or isinstance(value, bool):
        return []
    if isinstance(value, (int, float)):
        return [str(value)]
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, (list, tuple, set)):
        out: list[str] = []
        for v in value:
            out.extend(_flatten(v))
        return out
    if isinstance(value, dict):
        out = []
        for v in value.values():
            out.extend(_flatten(v))
        return out
    return [str(value)]


def _business_values(rec: Optional[NormalizedRecord]) -> list[str]:
    if rec is None:
        return []
    vals: list[str] = []
    src = rec.input or {}
    for k in BUSINESS_FIELDS:
        vals.extend(_flatten(src.get(k)))
    prop = src.get("property") if isinstance(src.get("property"), dict) else {}
    vals.extend(_flatten(prop))
    return [v for v in vals if len(v) >= 3]


def sms_segments(body: str) -> int:
    """GSM-7: 160 chars single / 153 per segment; UCS-2: 70 / 67."""
    if not body:
        return 0
    gsm = all((c in GSM7_BASIC) or (c in GSM7_EXT) for c in body)
    if gsm:
        length = sum(2 if c in GSM7_EXT else 1 for c in body)
        return 1 if length <= 160 else -(-length // 153)
    length = len(body)
    return 1 if length <= 70 else -(-length // 67)


# --------------------------------------------------------------------------- checks

def check_profile_leak(draft: Draft, rec: Optional[NormalizedRecord]) -> list[GateResult]:
    """Block unapproved profile-field echoing; allow property/business data by context."""
    text = _text(draft)
    low = text.lower()
    out: list[GateResult] = []
    profile = (rec.profile if rec else {}) or {}
    business = [b.lower() for b in _business_values(rec)]

    def from_business(s: str) -> bool:
        s = s.lower()
        return any(s in b or b in s for b in business)

    for key, value in profile.items():
        if key in APPROVED_PROFILE_FIELDS:
            continue
        for v in _flatten(value):
            if len(v) < 3:
                continue
            if v.lower() in low and not from_business(v):
                out.append(GateResult(
                    "no_pii_leak.profile_echo", "failed",
                    f"Unapproved profile field '{key}' is echoed in the message.",
                    f"assertions.constraints.no_pii_leak; {PLAN_CITE} (approved fields: first_name, amenity_interest)",
                    "conservative_default",
                    {"field": key, "sensitive": key in SENSITIVE_PROFILE_FIELDS, "rewrite": f"Remove the '{key}' value from the copy."},
                ))
    # Pattern-based PII regardless of provenance: emails, phones, SSNs are never marketing copy
    # unless they are supplied business contact data.
    for name, rx in (("email_address", EMAIL_RE), ("phone_number", PHONE_RE), ("ssn", SSN_RE)):
        for m in rx.finditer(text):
            if name == "ssn" or not from_business(m.group(0)):
                out.append(GateResult(
                    "no_pii_leak.pattern", "failed",
                    f"Message contains a {name.replace('_', ' ')} that is not supplied business data.",
                    f"assertions.constraints.no_pii_leak; {PLAN_CITE}", "conservative_default",
                    {"pattern": name, "match": m.group(0)},
                ))
                break
    # Money and street addresses: only a leak when they come from the profile (already caught
    # above by literal match); otherwise they are allowed business data. Report, don't fail.
    money = MONEY_RE.findall(text)
    streets = STREET_RE.findall(text)
    if (money or streets) and not out:
        out.append(GateResult(
            "no_pii_leak.business_data", "passed",
            "Money/address text present and not sourced from the profile; treated as property/business data.",
            f"{REVIEW_CITE}; {PLAN_CITE}", "conservative_default",
            {"money": money, "streets": streets},
        ))
    if not out:
        out.append(GateResult(
            "no_pii_leak", "passed", "No unapproved profile data or PII pattern found in the message.",
            f"assertions.constraints.no_pii_leak; {PLAN_CITE}", "conservative_default",
            {"ignored_profile_fields": sorted(k for k in profile if k not in APPROVED_PROFILE_FIELDS)},
        ))
    return out


def check_fair_housing(draft: Draft) -> list[GateResult]:
    text = _text(draft)
    out: list[GateResult] = []
    for entry in FAIR_HOUSING_LEXICON:
        m = entry.regex.search(text)
        if m:
            out.append(GateResult(
                f"fair_housing.{entry.level.lower()}", "failed" if entry.level == "HARD" else "passed",
                f"{entry.level}: '{m.group(0)}' ({entry.category}).",
                FHA_CITE, "conservative_default",
                {"level": entry.level, "category": entry.category, "match": m.group(0), "rewrite": entry.rewrite},
            ))
    if not any(r.details.get("level") == "HARD" for r in out):
        out.append(GateResult(
            "fair_housing_check_passed", "passed",
            "No protected-class preference or limitation found in the message.",
            FHA_CITE, "conservative_default",
            {"warn_count": sum(1 for r in out if r.details.get("level") == "WARN")},
        ))
    return out


def check_brand_style(draft: Draft, rec: Optional[NormalizedRecord]) -> list[GateResult]:
    body = draft.body or ""
    out: list[GateResult] = []
    hard = False
    if not GREETING_RE.match(body):
        out.append(GateResult("brand_style.greeting", "failed", "Body must open with a greeting (observed 'Hi Taylor').", SAMPLE_CITE, "observed"))
        hard = True
    if body.count("!") > 1:
        out.append(GateResult("brand_style.exclamations", "failed", "More than one '!' (observed at most one).", SAMPLE_CITE, "hypothesis"))
        hard = True
    if EMOJI_RE.search(_text(draft)):
        out.append(GateResult("brand_style.emoji", "failed", "Emoji are not part of the observed brand style.", SAMPLE_CITE, "hypothesis"))
        hard = True
    caps = [w for w in CAPS_WORD_RE.findall(_text(draft)) if w not in CAPS_ALLOWED]
    if caps:
        out.append(GateResult("brand_style.shouting", "failed", f"ALL-CAPS words other than STOP/HELP: {caps[:3]}.", f"{PLAN_CITE}; {CTIA_CITE}", "conservative_default"))
        hard = True
    if SHORTENER_RE.search(_text(draft)):
        out.append(GateResult("brand_style.url_shortener", "failed", "URL shorteners are blocked by carriers and hide the destination.", CTIA_CITE, "conservative_default"))
        hard = True
    first = (rec.profile.get("first_name") if rec and isinstance(rec.profile, dict) else None)
    if isinstance(first, str) and first.strip() and first.strip().lower() not in body.lower():
        out.append(GateResult("brand_style.first_name", "passed", "First name supplied but not used (warn only).", SAMPLE_CITE, "hypothesis", {"warn": True}))
    if not hard:
        out.append(GateResult("brand_style_applied", "passed", "Greeting, tone, and casing match the observed brand style.", SAMPLE_CITE, "hypothesis"))
    return out


def check_sms(draft: Draft) -> list[GateResult]:
    body = draft.body or ""
    out: list[GateResult] = []
    if draft.subject is not None:
        out.append(GateResult("sms.subject_null", "failed", "SMS must have subject null.", SAMPLE_CITE, "observed"))
    else:
        out.append(GateResult("sms.subject_null", "passed", "Subject is null.", SAMPLE_CITE, "observed"))
    if body.rstrip().endswith(SMS_STOP_SENTENCE):
        out.append(GateResult("sms.stop_sentence", "passed", f"Ends with '{SMS_STOP_SENTENCE}'.", f"{SAMPLE_CITE}; {CTIA_CITE}", "observed"))
    else:
        out.append(GateResult("sms.stop_sentence", "failed", f"SMS must end with the literal '{SMS_STOP_SENTENCE}'.", f"{SAMPLE_CITE}; {CTIA_CITE}", "observed"))
    cta = draft.cta or {}
    options = cta.get("options") if isinstance(cta, dict) else None
    if options:
        numbered = all(re.search(rf"\b{i}\s+for\s+{re.escape(str(opt))}", body, re.I) for i, opt in enumerate(options, 1))
        if numbered:
            out.append(GateResult("sms.numbered_options", "passed", "Every CTA option is offered as a numbered reply.", SAMPLE_CITE, "observed"))
        else:
            out.append(GateResult("sms.numbered_options", "failed", "CTA options must appear as 'Reply 1 for X, 2 for Y' in the body.", SAMPLE_CITE, "observed"))
    questions = body.count("?")
    if questions > 1:
        out.append(GateResult("sms.one_question", "failed", f"SMS asks {questions} questions; ask one.", SAMPLE_CITE, "hypothesis"))
    else:
        out.append(GateResult("sms.one_question", "passed", "At most one question.", SAMPLE_CITE, "hypothesis"))
    seg = sms_segments(body)
    if seg > SMS_MAX_SEGMENTS:
        out.append(GateResult("sms.segments", "failed", f"{seg} segments exceeds the {SMS_MAX_SEGMENTS}-segment cap.", PLAN_CITE, "conservative_default", {"segments": seg}))
    else:
        out.append(GateResult("sms.segments", "passed", f"{seg} SMS segment(s).", PLAN_CITE, "conservative_default", {"segments": seg}))
    return out


def check_email(draft: Draft, rec: Optional[NormalizedRecord]) -> list[GateResult]:
    body = draft.body or ""
    subject = draft.subject
    out: list[GateResult] = []
    if not isinstance(subject, str) or not subject.strip():
        out.append(GateResult("email.subject_present", "failed", "Email needs a non-null, non-empty subject.", f"{SAMPLE_CITE}; {CANSPAM_CITE}", "observed"))
    else:
        out.append(GateResult("email.subject_present", "passed", "Subject present.", SAMPLE_CITE, "observed"))
        prop = (rec.input.get("property_name") if rec else None) or ""
        prop_token = prop.split()[0].lower() if isinstance(prop, str) and prop.strip() else ""
        body_words = set(re.findall(r"[a-z]{4,}", body.lower()))
        subj_words = set(re.findall(r"[a-z]{4,}", subject.lower()))
        accurate = (prop_token and prop_token in subject.lower()) or bool(subj_words & body_words)
        if accurate:
            out.append(GateResult("email.subject_accurate", "passed", "Subject names the property or reflects the body.", f"{CANSPAM_CITE} (non-deceptive subject)", "conservative_default"))
        else:
            out.append(GateResult("email.subject_accurate", "failed", "Subject shares nothing with the body or property; treated as potentially deceptive.", f"{CANSPAM_CITE} (non-deceptive subject)", "conservative_default"))
    cta = draft.cta or {}
    link = cta.get("link") if isinstance(cta, dict) else None
    if link:
        if link in body:
            out.append(GateResult("email.link_cta", "passed", "CTA link appears in the body.", SAMPLE_CITE, "observed"))
        else:
            out.append(GateResult("email.link_cta", "failed", "CTA carries a link that the body never shows.", SAMPLE_CITE, "observed"))
    low = body.lower()
    conspicuous = ("opt out" in low or "unsubscribe" in low) and "stop" in low and ("click" in low or "unsubscribe" in low)
    if conspicuous:
        out.append(GateResult("email.opt_out", "passed", "Click-or-STOP opt-out sentence present.", f"{SAMPLE_CITE}; {CANSPAM_CITE}", "observed"))
    else:
        out.append(GateResult("email.opt_out", "failed", "Email must include a conspicuous click-or-STOP opt-out sentence.", f"{SAMPLE_CITE}; {CANSPAM_CITE}", "observed"))
    return out


# --------------------------------------------------------------------------- entry points

def validate_draft(draft: Draft, rec: Optional[NormalizedRecord] = None) -> ValidationReport:
    rep = ValidationReport(channel=draft.channel, source=draft.source)
    constraints = (rec.constraints if rec else {}) or {}

    for r in check_profile_leak(draft, rec):
        rep.add(r, hard=True)
    fh = check_fair_housing(draft)
    for r in fh:
        rep.add(r, hard=r.details.get("level") == "HARD", warn=r.details.get("level") == "WARN")
    if any(r.rule == "fair_housing_check_passed" for r in fh):
        rep.verified_states.append("fair_housing_check_passed")
        if constraints.get("no_sensitive_discrimination") is not None:
            rep.results.append(GateResult("no_sensitive_discrimination", "passed", "Covered by the fair-housing check.", FHA_CITE, "conservative_default"))
    bs = check_brand_style(draft, rec)
    for r in bs:
        rep.add(r, hard=True, warn=bool(r.details.get("warn")))
    if any(r.rule == "brand_style_applied" for r in bs):
        rep.verified_states.append("brand_style_applied")

    if draft.channel == "sms":
        for r in check_sms(draft):
            rep.add(r, hard=True)
            if r.rule == "sms.segments":
                rep.segments = r.details.get("segments")
        opt_out_ok = any(r.rule == "sms.stop_sentence" and r.status == "passed" for r in rep.results)
    elif draft.channel == "email":
        for r in check_email(draft, rec):
            rep.add(r, hard=True)
        rep.unverified["email_delivery_compliance"] = (
            "Not verified and out of scope: CAN-SPAM postal address, header accuracy, and unsubscribe "
            "mechanics belong to a delivery transport this service does not have. The supplied "
            "simulation example omits a postal address, so none is required here and none is assumed "
            "to be appended."
        )
        opt_out_ok = any(r.rule == "email.opt_out" and r.status == "passed" for r in rep.results)
    else:
        rep.add(GateResult("channel.unsupported", "failed", f"No validator for channel '{draft.channel}'.", PLAN_CITE, "conservative_default"), hard=True)
        opt_out_ok = False

    if constraints.get("include_opt_out_instructions") is not None:
        rep.results.append(GateResult(
            "include_opt_out_instructions", "passed" if opt_out_ok else "failed",
            "Opt-out instructions present." if opt_out_ok else "Opt-out instructions missing.",
            f"assertions.constraints.include_opt_out_instructions; {SAMPLE_CITE}", "observed",
        ))
    if draft.source == "model":
        rep.results.append(GateResult(
            "validation.model_draft", "passed" if rep.passed else "failed",
            "Model draft is subject to the same hard rules as a template; it cannot override a HARD failure.",
            "PLAN architecture (compliance in Python validates model and template drafts); IFScale arXiv 2507.11538",
            "conservative_default",
        ))
    return rep


def select_draft(candidates: Iterable[Draft], rec: Optional[NormalizedRecord] = None) -> tuple[Optional[Draft], list[ValidationReport]]:
    """Return the first candidate with no HARD failure, plus every report. A model draft that
    fails is never chosen over a passing template, whatever its order."""
    reports: list[ValidationReport] = []
    chosen: Optional[Draft] = None
    for d in candidates:
        rep = validate_draft(d, rec)
        reports.append(rep)
        if chosen is None and rep.passed:
            chosen = d
    return chosen, reports
