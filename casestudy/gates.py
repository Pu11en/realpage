"""C1: input normalization and the five deterministic gates.

Every gate returns a `GateResult` carrying status, plain reason, citation, and a
confidence label (`observed`, `input_required`, `hypothesis`, `conservative_default`).
Gates never call a model. They never invent consent and never mark an unknown
`required_state` as passed.

Order (per PLAN C1 / REVIEW-astra "stop order"):
  0. normalize input (no crash on missing fields)
  1. inbound reply: STOP wins even when consent is already false
  2. consent
  3. lifecycle / do-not-contact
  4. frequency
  5. dates and timezone (reference clock is the input's clock, never server time)

The outcome of the gate chain is a `GateOutcome`: either `proceed` (the record may
be composed later) or a terminal decision (`mark_opted_out`, `suppress`, `escalate`)
that later tasks turn into the public answer. `next_message` for terminal decisions
is decided in C7; this module only records what and why.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any, Literal, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

Confidence = Literal["observed", "input_required", "hypothesis", "conservative_default"]
Status = Literal["passed", "failed", "skipped", "unsupported"]

# The only required_states this build knows how to verify, and which check owns each.
KNOWN_REQUIRED_STATES = {
    "consent_verified": "consent_gate",
    "fair_housing_check_passed": "validators.fair_housing",  # C4
    "brand_style_applied": "validators.brand_style",  # C4
}

CHANNELS = ("sms", "email", "voice")
CONSENT_KEYS = {"sms": "sms_opt_in", "email": "email_opt_in", "voice": "voice_opt_in"}

# conservative_default: lifecycle values that mean "do not contact".
BLOCKED_LIFECYCLE = {
    "closed",
    "lost",
    "do_not_contact",
    "opted_out",
    "evicted",
    "deceased",
}
# observed in sample.jsonl: "new", "open". Others are hypotheses kept permissive.
KNOWN_LIFECYCLE = {"new", "open", "active", "applicant", "resident", "former_resident", "renewal"}

OPT_OUT_WORDS = {"stop", "stopall", "unsubscribe", "cancel", "end", "quit", "remove me", "opt out"}
# Spanish keywords and near-misses: revocation is valid by "any reasonable means" (47 CFR 64.1200(a)(10)).
OPT_OUT_FIRST_WORDS = OPT_OUT_WORDS | {"stopp", "stp", "alto", "parar", "para", "cancelar", "detener", "baja", "unsub"}
# The only playbook the supplied examples teach is prospect outreach whose goal is a tour.
TOUR_CTAS = {"book_tour", "schedule_tour", "tour"}
TOUR_PERSONAS = {"prospect", "lead"}
OTHER_PURPOSE_WORDS = ("rent", "payment", "maintenance", "work_order", "renewal", "renew", "survey", "moveout", "move_out",
                       "application", "applicant", "document", "docs", "reminder", "post_tour", "delinquen", "lease_end", "notice")
OTHER_PURPOSE_FIELDS = ("rent_due_date", "work_order_status", "work_order_time", "lease_end_date", "missing_documents",
                        "move_out_date", "tour_at", "tour_scheduled_at", "tour_completed_at", "balance_due", "application_id")
KNOWN_PERSONAS = {"prospect", "lead", "applicant", "resident", "renter", "former_resident"}
HELP_WORDS = {"help", "info"}
NEGATIVE_PHRASES = (
    "not interested",
    "no thanks",
    "no thank you",
    "already leased",
    "signed elsewhere",
    "wrong number",
    "leave me alone",
)
QUESTION_HINTS = ("?", "how much", "price", "rent", "pets", "pet", "available", "deposit", "when", "what", "do you")

MIN_INTERVAL_HOURS = 24  # conservative_default, not learned
MAX_MESSAGES_24H = 3  # conservative_default, not learned


@dataclass
class GateResult:
    rule: str
    status: Status
    reason: str
    citation: str
    confidence: Confidence
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class NormalizedRecord:
    task_id: str
    persona: Optional[str]
    lifecycle_stage: Optional[str]
    consent: dict[str, Optional[bool]]  # channel -> True/False/None(unknown)
    channel_preferences: list[str]
    input: dict[str, Any]
    profile: dict[str, Any]
    assertions: dict[str, Any]
    required_states: list[str]
    constraints: dict[str, Any]
    thresholds: dict[str, Any]
    inbound_reply: Optional[str]
    prior_options: Optional[list[str]]
    warnings: list[str] = field(default_factory=list)


@dataclass
class GateOutcome:
    decision: Literal["proceed", "mark_opted_out", "suppress", "escalate", "propose_follow_up"]
    reason: str
    results: list[GateResult]
    reply_class: Optional[str] = None
    reference_time: Optional[datetime] = None
    tz: Optional[ZoneInfo] = None
    verified_states: list[str] = field(default_factory=list)
    unsupported_states: list[str] = field(default_factory=list)
    selected_option: Optional[str] = None
    record: Optional[NormalizedRecord] = None
    purpose: Optional[str] = None  # set for non-tour tasks, which get a general checked message

    @property
    def proceed(self) -> bool:
        return self.decision in ("proceed", "propose_follow_up")


# --------------------------------------------------------------------------- normalize


def _as_bool_or_none(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        v = value.strip().lower()
        if v in {"true", "yes", "y", "1"}:
            return True
        if v in {"false", "no", "n", "0"}:
            return False
    return None


def normalize(raw: Any) -> NormalizedRecord:
    """Coerce a raw JSON record into a predictable shape. Never raises on missing fields."""
    warnings: list[str] = []
    if not isinstance(raw, dict):
        warnings.append(f"record is not an object (got {type(raw).__name__}); treated as empty")
        raw = {}

    consent_raw = raw.get("consent")
    if not isinstance(consent_raw, dict):
        if consent_raw is not None:
            warnings.append("consent is not an object; all consent treated as unknown")
        consent_raw = {}
    consent: dict[str, Optional[bool]] = {}
    for ch, key in CONSENT_KEYS.items():
        # Consent must be an explicit boolean true. Strings like "yes" are not proof of consent (fail closed).
        raw_val = consent_raw.get(key)
        val = raw_val if isinstance(raw_val, bool) else None
        if key in consent_raw and val is None:
            warnings.append(f"consent.{key} is {raw_val!r}, not true/false; treated as no consent")
        consent[ch] = val

    prefs_raw = raw.get("channel_preferences")
    prefs: list[str] = []
    if isinstance(prefs_raw, list):
        for p in prefs_raw:
            if isinstance(p, str) and p.lower() in CHANNELS:
                prefs.append(p.lower())
            else:
                warnings.append(f"ignored unknown channel preference {p!r}")
    elif prefs_raw is not None:
        warnings.append("channel_preferences is not a list; ignored")

    inp = raw.get("input")
    if not isinstance(inp, dict):
        if inp is not None:
            warnings.append("input is not an object; treated as empty")
        inp = {}
    profile = inp.get("profile")
    if not isinstance(profile, dict):
        if profile is not None:
            warnings.append("input.profile is not an object; treated as empty")
        profile = {}

    assertions = raw.get("assertions")
    if not isinstance(assertions, dict):
        assertions = {}
    required_states = assertions.get("required_states")
    if not isinstance(required_states, list):
        required_states = []
    required_states = [s for s in required_states if isinstance(s, str)]
    constraints = assertions.get("constraints")
    if not isinstance(constraints, dict):
        constraints = {}
    thresholds = raw.get("thresholds")
    if not isinstance(thresholds, dict):
        thresholds = {}

    # Inbound reply may appear at several plausible locations; hold-out shape unknown.
    inbound = None
    for container in (inp, raw):
        for key in ("inbound_reply", "inbound_message", "reply_text", "last_inbound_message"):
            v = container.get(key)
            if isinstance(v, dict):
                v = v.get("text") or v.get("body")
            if isinstance(v, str) and v.strip():
                inbound = v
                break
        if inbound:
            break

    prior = None
    for container in (inp, raw):
        for key in ("prior_options", "last_options_offered", "offered_options"):
            v = container.get(key)
            if isinstance(v, list) and all(isinstance(x, str) for x in v):
                prior = v
                break
        if prior is not None:
            break
    if prior is None:
        # The options may arrive inside the previous message itself, in the same shape as our own output.
        for container in (inp, raw):
            for key in ("prior_message", "last_message", "previous_message", "last_outbound_message", "previous_output"):
                v = container.get(key)
                if isinstance(v, dict):
                    v = v.get("next_message", v)
                    cta = v.get("cta") if isinstance(v, dict) else None
                    opts = cta.get("options") if isinstance(cta, dict) else None
                    if isinstance(opts, list) and opts and all(isinstance(x, str) for x in opts):
                        prior = opts
                        break
            if prior is not None:
                break

    task_id = raw.get("task_id")
    if not isinstance(task_id, str) or not task_id:
        task_id = "unknown_task"
        warnings.append("task_id missing; using 'unknown_task'")

    persona = raw.get("persona") if isinstance(raw.get("persona"), str) else None
    name = profile.get("first_name")
    if name is not None:
        clean = _clean_first_name(name)
        if clean != name:
            warnings.append(f"first_name {name!r} " + (f"cleaned to {clean!r}" if clean else "is not a plausible name; omitted"))
            profile = {k: v for k, v in profile.items() if k != "first_name"}
            if clean:
                profile["first_name"] = clean
    stage = raw.get("lifecycle_stage") if isinstance(raw.get("lifecycle_stage"), str) else None

    return NormalizedRecord(
        task_id=task_id,
        persona=persona,
        lifecycle_stage=stage.lower() if stage else None,
        consent=consent,
        channel_preferences=prefs,
        input=inp,
        profile=profile,
        assertions=assertions,
        required_states=required_states,
        constraints=constraints,
        thresholds=thresholds,
        inbound_reply=inbound,
        prior_options=prior,
        warnings=warnings,
    )


def _unsupported_purpose(rec: "NormalizedRecord") -> Optional[str]:
    cta = rec.constraints.get("primary_cta")
    if isinstance(cta, str) and cta.strip().lower() not in TOUR_CTAS:
        return f"a {cta!r} task"
    persona = (rec.persona or "").strip().lower()
    if persona and persona not in TOUR_PERSONAS:
        return f"a {persona} message"
    tid = rec.task_id.lower()
    for w in OTHER_PURPOSE_WORDS:
        if w in tid:
            return f"a {w.replace('_', ' ')} task"
    for f in OTHER_PURPOSE_FIELDS:
        if rec.input.get(f) not in (None, "", []):
            return f"a task about {f.replace('_', ' ')}"
    return None


def _clean_first_name(value: Any) -> Optional[str]:
    """Keep letters, spaces, hyphens, apostrophes and dots; reject markup, sentences and instructions."""
    if not isinstance(value, str) or "<" in value or ">" in value:
        return None
    kept = re.sub(r"[^\w\s'.-]|[\d_]", "", value).strip()
    kept = re.sub(r"\s+", " ", kept)
    if not kept or len(kept) > 30 or len(kept.split()) > 3:
        return None
    return kept


# --------------------------------------------------------------------------- reply classification


def classify_reply(text: Optional[str]) -> str:
    """Deterministic inbound-reply class. Labels are project-defined (hypothesis)."""
    if text is None:
        return "none"
    t = text.strip().lower()
    t_norm = re.sub(r"[^\w\s]", "", t).strip()
    words = t_norm.split()
    visiting = re.match(r"^stop (by|in|over|at|to)\b", t_norm) is not None  # "stop by tomorrow?" is a visit, not an opt-out
    phrases = ("remove me", "opt out", "unsubscribe", "stop texting", "stop messaging", "lose my number",
               "delete my number", "dont text", "don't text", "do not text", "dont contact",
               "do not contact", "stop contacting", "no more texts", "no more messages")
    if not visiting and (t_norm in OPT_OUT_WORDS
                         or (words and (words[0] in OPT_OUT_FIRST_WORDS or words[0].startswith("stop")))
                         or any(p in t_norm for p in phrases)):
        return "opt_out"
    if t_norm in HELP_WORDS:
        return "help"
    if re.fullmatch(r"\d+", t_norm):
        return "choose_option"
    if any(p in t_norm for p in NEGATIVE_PHRASES):
        return "not_interested"
    if any(h in t for h in QUESTION_HINTS):
        return "question"
    return "unknown"


# --------------------------------------------------------------------------- gates


def reply_gate(rec: NormalizedRecord) -> tuple[GateResult, Optional[GateOutcome]]:
    """Runs first so STOP produces mark_opted_out even when consent is already false."""
    cls = classify_reply(rec.inbound_reply)
    cite = "47 CFR 64.1200(a)(10) revocation by any reasonable means; CTIA Messaging Principles STOP/HELP"
    if cls == "none":
        return GateResult("reply_gate", "skipped", "no inbound reply in record", cite, "input_required"), None
    if cls == "opt_out":
        res = GateResult(
            "reply_gate", "passed", f"inbound reply {rec.inbound_reply!r} is an opt-out keyword; stop everything",
            cite, "conservative_default", {"reply_class": cls},
        )
        return res, GateOutcome("mark_opted_out", "inbound_opt_out", [res], reply_class=cls, record=rec)
    if cls == "choose_option":
        n = int(re.sub(r"\D", "", rec.inbound_reply))
        if not rec.prior_options:
            res = GateResult(
                "reply_gate", "failed",
                f"numeric reply {rec.inbound_reply!r} but record supplies no prior options; cannot map it",
                "project rule: numeric replies need supplied prior options (REVIEW-astra stop order)",
                "conservative_default", {"reply_class": cls},
            )
            return res, GateOutcome("escalate", "numeric_reply_without_prior_options", [res], reply_class=cls, record=rec)
        if not 1 <= n <= len(rec.prior_options):
            res = GateResult(
                "reply_gate", "failed",
                f"numeric reply {n} is outside the {len(rec.prior_options)} supplied options",
                "project rule: option index must exist", "conservative_default", {"reply_class": cls},
            )
            return res, GateOutcome("escalate", "numeric_reply_out_of_range", [res], reply_class=cls, record=rec)
        res = GateResult(
            "reply_gate", "passed",
            f"numeric reply {n} selects option {rec.prior_options[n-1]!r}; this proposes a follow-up, it does not book anything",
            "project rule: service proposes, never books (PLAN architecture)", "conservative_default",
            {"reply_class": cls, "selected_option": rec.prior_options[n - 1]},
        )
        # Not terminal: later gates (consent etc.) still apply to any confirmation message.
        return res, None
    if cls == "not_interested":
        res = GateResult(
            "reply_gate", "passed", f"inbound reply {rec.inbound_reply!r} says the customer is not interested; stop the cadence, send nothing",
            "project rule: never keep marketing to someone who declined", "conservative_default", {"reply_class": cls},
        )
        return res, GateOutcome("suppress", "customer_not_interested", [res], reply_class=cls, record=rec)
    # A question or any free text we cannot map needs a person: an automated welcome would ignore what they said,
    # and answering (pets, rent, availability) would require property facts the record does not contain.
    res = GateResult(
        "reply_gate", "passed", f"inbound reply {rec.inbound_reply!r} classified as {cls}; a leasing agent must answer it, so no automated message",
        "project rule: never ignore or guess an answer to a customer's own words", "conservative_default", {"reply_class": cls},
    )
    return res, None


def consent_gate(rec: NormalizedRecord) -> GateResult:
    cite = "TCPA 47 U.S.C. 227 / 47 CFR 64.1200 (prior express consent); CAN-SPAM 15 U.S.C. 7704 for email"
    consented = [ch for ch in rec.channel_preferences if rec.consent.get(ch) is True]
    # Also consider consented channels not in preferences (preferences may be missing).
    any_consented = [ch for ch in CHANNELS if rec.consent.get(ch) is True]
    unknown = [ch for ch in CHANNELS if rec.consent.get(ch) is None]
    if consented or any_consented:
        chosen = consented or any_consented
        return GateResult(
            "consent_gate", "passed",
            f"explicit opt-in present for {', '.join(chosen)}; preferences considered in order {rec.channel_preferences}",
            cite, "observed", {"consented_channels": chosen, "unknown_channels": unknown},
        )
    return GateResult(
        "consent_gate", "failed",
        "no channel has an explicit true opt-in"
        + (f"; consent unknown for {', '.join(unknown)} and unknown is never treated as consent" if unknown else ""),
        cite, "observed", {"unknown_channels": unknown},
    )


def lifecycle_gate(rec: NormalizedRecord) -> GateResult:
    cite = "project conservative default; do-not-contact flags and closed stages suppress outreach"
    dnc = rec.input.get("do_not_contact")
    if dnc is True or _as_bool_or_none(dnc) is True:
        return GateResult("lifecycle_gate", "failed", "input.do_not_contact is true", cite, "conservative_default")
    stage = rec.lifecycle_stage
    if stage is None:
        return GateResult(
            "lifecycle_gate", "passed", "lifecycle_stage missing; treated as contactable but flagged",
            cite, "conservative_default", {"warning": "lifecycle_stage_missing"},
        )
    if stage in BLOCKED_LIFECYCLE:
        return GateResult("lifecycle_gate", "failed", f"lifecycle_stage {stage!r} means do not contact", cite, "conservative_default")
    if any(w in stage for w in ("closed", "lost", "dead", "inactive", "archiv", "cancel", "evict", "do_not")):
        return GateResult("lifecycle_gate", "failed", f"lifecycle_stage {stage!r} reads as closed or lost; do not contact", cite, "conservative_default")
    if stage in KNOWN_LIFECYCLE:
        conf: Confidence = "observed" if stage in {"new", "open"} else "hypothesis"
        return GateResult("lifecycle_gate", "passed", f"lifecycle_stage {stage!r} is contactable", cite, conf)
    return GateResult(
        "lifecycle_gate", "passed", f"lifecycle_stage {stage!r} unrecognized; treated as contactable but flagged",
        cite, "conservative_default", {"warning": "lifecycle_stage_unrecognized"},
    )


def _parse_dt(value: Any) -> Optional[datetime]:
    if not isinstance(value, str) or not value.strip():
        return None
    v = value.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(v)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def frequency_gate(rec: NormalizedRecord, reference: Optional[datetime]) -> GateResult:
    cite = f"project conservative default: min {MIN_INTERVAL_HOURS}h between messages, max {MAX_MESSAGES_24H}/24h; not a learned rule"
    last_sent = _parse_dt(rec.input.get("last_message_sent_at"))
    count = rec.input.get("messages_sent_24h")
    if isinstance(count, int) and not isinstance(count, bool) and count >= MAX_MESSAGES_24H:
        return GateResult("frequency_gate", "failed", f"messages_sent_24h={count} reaches cap {MAX_MESSAGES_24H}", cite, "conservative_default")
    if last_sent and reference:
        hours = (reference - last_sent).total_seconds() / 3600
        if 0 <= hours < MIN_INTERVAL_HOURS:
            return GateResult(
                "frequency_gate", "failed", f"last message sent {hours:.1f}h before reference time; under {MIN_INTERVAL_HOURS}h minimum",
                cite, "conservative_default",
            )
    if last_sent is None and count is None:
        return GateResult("frequency_gate", "passed", "no send history supplied; nothing to cap", cite, "input_required")
    return GateResult("frequency_gate", "passed", "send history within cap", cite, "conservative_default")


def dates_gate(rec: NormalizedRecord) -> tuple[GateResult, Optional[datetime], Optional[ZoneInfo]]:
    """Resolve the reference clock and timezone from the input. Never uses today's date."""
    cite = "project rule: the reference clock is input.last_interaction (or input.reference_time); server date is never used"
    tz_name = rec.input.get("timezone")
    tz: Optional[ZoneInfo] = None
    if not isinstance(tz_name, str) or not tz_name.strip():
        return GateResult("dates_gate", "failed", "input.timezone missing; cannot compute a recipient-local send time", cite, "input_required"), None, None
    try:
        tz = ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, ValueError):
        return GateResult("dates_gate", "failed", f"input.timezone {tz_name!r} is not a valid IANA zone", cite, "input_required"), None, None

    ref = _parse_dt(rec.input.get("reference_time")) or _parse_dt(rec.input.get("last_interaction"))
    if ref is None:
        return GateResult("dates_gate", "failed", "no parseable reference clock (input.reference_time or input.last_interaction)", cite, "input_required"), None, tz

    move_raw = rec.input.get("move_date_target")
    details: dict[str, Any] = {"reference_time": ref.isoformat(), "timezone": tz_name}
    if move_raw is not None:
        try:
            move = date.fromisoformat(str(move_raw))
        except ValueError:
            return GateResult("dates_gate", "failed", f"move_date_target {move_raw!r} is not a valid date", cite, "input_required", details), ref, tz
        ref_local_date = ref.astimezone(tz).date()
        details["days_to_move"] = (move - ref_local_date).days
        if move < ref_local_date:
            return GateResult("dates_gate", "failed", f"move_date_target {move} is before the reference date {ref_local_date}; escalate rather than guess", cite, "conservative_default", details), ref, tz
    else:
        details["days_to_move"] = None
    return GateResult("dates_gate", "passed", "timezone valid, reference clock parsed, move date sane", cite, "observed", details), ref, tz


# --------------------------------------------------------------------------- driver


def run_gates(raw: Any) -> GateOutcome:
    rec = normalize(raw)
    results: list[GateResult] = []
    for w in rec.warnings:
        results.append(GateResult("normalize", "passed", w, "project rule: normalize without crashing", "conservative_default"))

    unsupported = [s for s in rec.required_states if s not in KNOWN_REQUIRED_STATES]
    for s in unsupported:
        results.append(GateResult(
            "required_state", "unsupported", f"required_state {s!r} has no implemented check; it is NOT marked passed",
            "project rule: unknown states are a visible failure", "input_required", {"state": s},
        ))

    # 1. reply first
    reply_res, terminal = reply_gate(rec)
    results.append(reply_res)
    reply_class = reply_res.details.get("reply_class")
    selected = reply_res.details.get("selected_option")
    if terminal:
        terminal.results = results + [r for r in terminal.results if r is not reply_res]
        terminal.unsupported_states = unsupported
        return terminal

    # 1b. persona we have no playbook for
    if rec.persona is not None and rec.persona.strip().lower() not in KNOWN_PERSONAS:
        p = GateResult("persona_gate", "failed", f"persona {rec.persona!r} is not a renter or prospect; no approved messaging playbook, so a person decides",
                       "project rule: unknown audiences are escalated, not guessed", "conservative_default")
        results.append(p)
        return GateOutcome("escalate", "unknown_persona", results, reply_class, unsupported_states=unsupported, record=rec)

    # 2. consent
    verified: list[str] = []
    c = consent_gate(rec)
    results.append(c)
    if c.status == "failed":
        return GateOutcome("suppress", "no_consent", results, reply_class, unsupported_states=unsupported, record=rec)
    if "consent_verified" in rec.required_states:
        verified.append("consent_verified")

    # 3. lifecycle
    lc = lifecycle_gate(rec)
    results.append(lc)
    if lc.status == "failed":
        return GateOutcome("suppress", "lifecycle_blocked", results, reply_class, verified_states=verified, unsupported_states=unsupported, record=rec)

    # 3a. is this a tour-outreach task? Other tasks get a short, general, checked message instead of a tour pitch.
    purpose = _unsupported_purpose(rec)
    if purpose:
        results.append(GateResult("purpose_gate", "passed", f"this looks like {purpose}, not prospect tour outreach; a general checked message is used, never a tour pitch",
                                  "project rule: never send a tour pitch for a different job", "conservative_default", {"purpose": purpose}))

    # 3b. the customer said something we must not ignore (checked after consent, so no-consent still wins)
    if reply_class in ("question", "help", "unknown"):
        return GateOutcome("escalate", f"customer_reply_needs_human_{reply_class}", results, reply_class,
                           verified_states=verified, unsupported_states=unsupported, record=rec)

    # 5 (needs reference clock before 4)
    d, ref, tz = dates_gate(rec)
    # 4. frequency
    f = frequency_gate(rec, ref)
    results.append(f)
    results.append(d)
    if f.status == "failed":
        return GateOutcome("suppress", "frequency_cap", results, reply_class, ref, tz, verified, unsupported, record=rec)
    if d.status == "failed":
        return GateOutcome("escalate", "dates_or_timezone_invalid", results, reply_class, ref, tz, verified, unsupported, record=rec)

    decision = "propose_follow_up" if reply_class == "choose_option" and not purpose else "proceed"
    return GateOutcome(decision, "all_gates_passed", results, reply_class, ref, tz, verified, unsupported,
                       None if purpose else selected, record=rec, purpose=purpose)
