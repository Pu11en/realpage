"""C3: intent, horizon, CTA, and next action.

Precedence (PLAN C3): explicit business fields outrank identifier hints, which outrank
computed fallbacks. Every decision carries a cited trail with a confidence label.

Intent (flow):
  explicit `input.intent` / `input.flow`            -> input_required
  lifecycle_stage == "new" (observed)               -> welcome flow
  `welcome` token in task_id                        -> welcome flow (hypothesis)
  otherwise (open/other lifecycle)                  -> open follow-up flow (observed for "open")

Horizon:
  explicit `input.horizon` ("short" | "long")       -> input_required
  `short_horizon` / `long_horizon` token in task_id -> hypothesis
  days_to_move <= 45 short, > 45 long               -> provisional two-tier fallback (hypothesis);
                                                       there is NO medium tier
  no move date at all                               -> short, conservative_default, uncertain

CTA: `primary_cta: book_tour` maps to `schedule_tour`. SMS -> two day options after the send
date (observed Thu/Fri for a Tuesday send: +2/+3, Sundays skipped). Email -> explicit input
link, else a link learned from the supplied example for that exact property; never an
invented URL. No safe link -> `{type: schedule_tour}` reply fallback plus a visible
`unresolved_link` diagnostic.

Next action: welcome -> `start_cadence` named `prospect_welcome_<horizon>_horizon` (observed for
short); open flow -> `follow_up_in_days` 3 (provisional interval from the sample, NOT the dayN
suffix); STOP -> `mark_opted_out`.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Optional

from .gates import GateOutcome, GateResult, NormalizedRecord
from .schedule import Schedule

INTENT_VERSION = "intent_v1"

SHORT_HORIZON_MAX_DAYS = 45  # hypothesis: provisional two-tier boundary, configurable
FOLLOW_UP_INTERVAL_DAYS = 3  # observed once (prospect_long_horizon_day3); provisional
OPTION_OFFSETS = (2, 3)  # observed: Tuesday send -> Thu, Fri
DAY_ABBR = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")

CTA_MAP = {"book_tour": "schedule_tour", "schedule_tour": "schedule_tour"}  # observed

# Property facts learned from the supplied example, with provenance. Never generalized.
LEARNED_PROPERTY_LINKS: dict[str, dict[str, str]] = {
    "oak ridge apartments": {
        "link": "https://oakridge.example/tour",
        "source": "sample.jsonl record 2 (prospect_long_horizon_day3) expected.next_message.cta.link",
    },
}
LINK_FIELDS = ("tour_link", "booking_link", "cta_link", "tour_url", "booking_url")
INTENT_FIELDS = ("intent", "flow")

WELCOME_TOKEN = re.compile(r"(?:^|[_\-\s])welcome(?:[_\-\s]|$)", re.IGNORECASE)
HORIZON_TOKEN = re.compile(r"(?:^|[_\-\s])(short|long)[_\-\s]horizon(?:[_\-\s]|$)", re.IGNORECASE)

SAMPLE_CITE = "sample.jsonl expected blocks (two records)"
PLAN_CITE = "PLAN-casestudy-bot.md C3"


@dataclass
class Intent:
    flow: Optional[str]  # welcome | open_follow_up | opted_out | none
    horizon: Optional[str]  # short | long | None
    horizon_source: str  # explicit_field | task_id_token | days_to_move_fallback | none
    cta: Optional[dict[str, Any]]
    next_action: Optional[dict[str, Any]]
    version: str = INTENT_VERSION
    uncertain: bool = False
    unresolved_link: bool = False
    results: list[GateResult] = field(default_factory=list)


# --------------------------------------------------------------------------- helpers

def _str(v: Any) -> Optional[str]:
    return v.strip().lower() if isinstance(v, str) and v.strip() else None


def _days_to_move(outcome: GateOutcome) -> Optional[int]:
    for r in outcome.results:
        if r.rule == "dates_gate" and isinstance(r.details.get("days_to_move"), int):
            return r.details["days_to_move"]
    return None


def infer_flow(rec: NormalizedRecord, outcome: GateOutcome) -> tuple[str, GateResult]:
    for f in INTENT_FIELDS:
        v = _str(rec.input.get(f))
        if v:
            flow = "welcome" if "welcome" in v else "open_follow_up"
            return flow, GateResult("intent", "passed", f"input.{f}={v!r} supplied; flow {flow!r}", "explicit business field outranks identifier hints", "input_required", {"flow": flow, "source": "explicit_field"})
    if rec.lifecycle_stage == "new":
        return "welcome", GateResult("intent", "passed", "lifecycle_stage 'new' -> welcome flow", SAMPLE_CITE + ": record 1 lifecycle 'new' -> welcome", "observed", {"flow": "welcome", "source": "lifecycle_stage"})
    if isinstance(rec.task_id, str) and WELCOME_TOKEN.search(rec.task_id):
        return "welcome", GateResult("intent", "passed", f"task_id {rec.task_id!r} contains 'welcome' (identifier hint, lifecycle is {rec.lifecycle_stage!r})", PLAN_CITE + ": tokens are fallbacks only", "hypothesis", {"flow": "welcome", "source": "task_id_token"})
    if rec.lifecycle_stage == "open":
        return "open_follow_up", GateResult("intent", "passed", "lifecycle_stage 'open' -> follow-up flow", SAMPLE_CITE + ": record 2 lifecycle 'open' -> follow_up_in_days", "observed", {"flow": "open_follow_up", "source": "lifecycle_stage"})
    return "open_follow_up", GateResult("intent", "passed", f"lifecycle_stage {rec.lifecycle_stage!r} not observed; defaulting to the follow-up flow", "project conservative default", "conservative_default", {"flow": "open_follow_up", "source": "default"})


def infer_horizon(rec: NormalizedRecord, outcome: GateOutcome) -> tuple[str, str, bool, GateResult]:
    """Returns (horizon, source, uncertain, result)."""
    v = _str(rec.input.get("horizon"))
    if v in ("short", "long"):
        return v, "explicit_field", False, GateResult("horizon", "passed", f"input.horizon={v!r} supplied", "explicit business field outranks identifier hints", "input_required", {"horizon": v, "source": "explicit_field"})
    m = HORIZON_TOKEN.search(rec.task_id) if isinstance(rec.task_id, str) else None
    if m:
        h = m.group(1).lower()
        return h, "task_id_token", False, GateResult("horizon", "passed", f"task_id {rec.task_id!r} contains '{h}_horizon' (identifier hint)", SAMPLE_CITE + ": 32-day record labelled short_horizon, 68-day record long_horizon", "hypothesis", {"horizon": h, "source": "task_id_token"})
    days = _days_to_move(outcome)
    if days is not None:
        h = "short" if days <= SHORT_HORIZON_MAX_DAYS else "long"
        return h, "days_to_move_fallback", False, GateResult("horizon", "passed", f"{days} days to move -> {h} (provisional two-tier boundary at {SHORT_HORIZON_MAX_DAYS} days; no medium tier)", PLAN_CITE + ": boundary is a provisional fallback, not learned", "hypothesis", {"horizon": h, "source": "days_to_move_fallback", "boundary_days": SHORT_HORIZON_MAX_DAYS, "days_to_move": days})
    return "short", "none", True, GateResult("horizon", "passed", "no horizon field, token, or move date; assuming short and flagging uncertainty", "project conservative default", "conservative_default", {"horizon": "short", "source": "none"})


def option_days(send_date: date) -> list[str]:
    """Two tour-day options after the send date: the 2nd and 3rd non-Sunday days following it
    (observed Tue send -> Thu, Fri; Sunday skipping is a project default)."""
    candidates: list[date] = []
    d = send_date
    while len(candidates) < max(OPTION_OFFSETS):
        d += timedelta(days=1)
        if d.weekday() != 6:
            candidates.append(d)
    return [DAY_ABBR[candidates[off - 1].weekday()] for off in OPTION_OFFSETS]


def _cta_type(rec: NormalizedRecord) -> tuple[str, GateResult]:
    raw = _str(rec.constraints.get("primary_cta")) if isinstance(rec.constraints, dict) else None
    if raw in CTA_MAP:
        return CTA_MAP[raw], GateResult("cta_type", "passed", f"constraints.primary_cta={raw!r} -> {CTA_MAP[raw]!r}", SAMPLE_CITE + ": book_tour -> schedule_tour in both records", "observed", {"cta_type": CTA_MAP[raw]})
    if raw:
        return "schedule_tour", GateResult("cta_type", "failed", f"constraints.primary_cta={raw!r} is not a known CTA; falling back to schedule_tour and flagging", PLAN_CITE, "conservative_default", {"cta_type": "schedule_tour", "unknown_primary_cta": raw})
    return "schedule_tour", GateResult("cta_type", "passed", "no primary_cta constraint; tour is the default prospect CTA", "project conservative default", "conservative_default", {"cta_type": "schedule_tour"})


def resolve_link(rec: NormalizedRecord) -> tuple[Optional[str], GateResult]:
    for f in LINK_FIELDS:
        v = rec.input.get(f)
        if isinstance(v, str) and v.strip().lower().startswith(("http://", "https://")):
            return v.strip(), GateResult("tour_link", "passed", f"input.{f} supplied", "explicit business field", "input_required", {"link": v.strip(), "source": "explicit_field"})
    prop = _str(rec.input.get("property_name"))
    learned = LEARNED_PROPERTY_LINKS.get(prop or "")
    if learned:
        return learned["link"], GateResult("tour_link", "passed", f"link for {rec.input.get('property_name')!r} learned from the supplied example", learned["source"], "observed", {"link": learned["link"], "source": "learned_from_sample"})
    return None, GateResult("tour_link", "failed", f"no link supplied and none learned for property {rec.input.get('property_name')!r}; refusing to invent a URL", PLAN_CITE + ": never invent a URL for an unseen property", "conservative_default", {"unresolved_link": True})


def build_cta(rec: NormalizedRecord, schedule: Schedule) -> tuple[dict[str, Any], bool, list[GateResult]]:
    cta_type, tres = _cta_type(rec)
    results = [tres]
    if schedule.channel == "sms" and schedule.send_at is not None:
        opts = option_days(schedule.send_at.date())
        results.append(GateResult("cta_shape", "passed", f"SMS: two day options {opts} (send {schedule.send_at.date()} {DAY_ABBR[schedule.send_at.weekday()]} +2/+3, Sundays skipped)", SAMPLE_CITE + ": record 1 options ['Thu','Fri'] for a Tuesday send", "hypothesis", {"options": opts}))
        return {"type": cta_type, "options": opts}, False, results
    if schedule.channel == "email":
        link, lres = resolve_link(rec)
        results.append(lres)
        if link:
            results.append(GateResult("cta_shape", "passed", "email: link CTA", SAMPLE_CITE + ": record 2 cta.link", "observed", {"link": link}))
            return {"type": cta_type, "link": link}, False, results
        results.append(GateResult("cta_shape", "passed", "email without a safe link: reply-to-arrange-tour fallback; UNRESOLVED LINK, uncertainty warning", PLAN_CITE, "conservative_default", {"unresolved_link": True, "warning": "unresolved_link"}))
        return {"type": cta_type}, True, results
    results.append(GateResult("cta_shape", "passed", f"channel {schedule.channel!r} ({schedule.kind}): reply/arrange fallback CTA, no automated options or link", PLAN_CITE, "conservative_default", {"warning": "no_channel_specific_cta"}))
    return {"type": cta_type}, False, results


def build_next_action(flow: str, horizon: str, outcome: GateOutcome) -> tuple[dict[str, Any], GateResult]:
    if outcome.decision == "propose_follow_up":
        return {"type": "follow_up_in_days", "value": FOLLOW_UP_INTERVAL_DAYS}, GateResult("next_action", "passed", f"option reply {outcome.selected_option!r}: propose a {FOLLOW_UP_INTERVAL_DAYS}-day follow-up, not a booking", PLAN_CITE + " / C1: numeric reply is a proposal", "conservative_default", {"next_action": "follow_up_in_days"})
    if flow == "welcome":
        name = f"prospect_welcome_{horizon}_horizon"
        conf = "observed" if horizon == "short" else "hypothesis"
        return {"type": "start_cadence", "name": name}, GateResult("next_action", "passed", f"welcome flow starts cadence {name!r}", SAMPLE_CITE + ": record 1 start_cadence prospect_welcome_short_horizon" + ("" if horizon == "short" else "; long variant is a naming hypothesis"), conf, {"next_action": "start_cadence", "name": name})
    return {"type": "follow_up_in_days", "value": FOLLOW_UP_INTERVAL_DAYS}, GateResult("next_action", "passed", f"open follow-up flow: follow up in {FOLLOW_UP_INTERVAL_DAYS} days (provisional interval from the sample, NOT the task_id dayN suffix)", SAMPLE_CITE + ": record 2 follow_up_in_days 3", "hypothesis", {"next_action": "follow_up_in_days", "value": FOLLOW_UP_INTERVAL_DAYS})


# --------------------------------------------------------------------------- driver

def infer_intent(outcome: GateOutcome, schedule: Schedule) -> Intent:
    results: list[GateResult] = []
    if outcome.decision == "mark_opted_out":
        results.append(GateResult("next_action", "passed", "opt-out intent: mark_opted_out, no message", "TCPA/CTIA: honor STOP; PLAN C1", "conservative_default", {"next_action": "mark_opted_out"}))
        return Intent("opted_out", None, "none", None, {"type": "mark_opted_out", "reason": outcome.reason}, results=results)
    rec = outcome.record
    if rec is None or not outcome.proceed:
        results.append(GateResult("intent", "skipped", f"gate decision {outcome.decision!r}; no intent inferred", "project rule: terminal gate decisions never compose", "conservative_default"))
        return Intent("none", None, "none", None, None, uncertain=True, results=results)

    flow, fres = infer_flow(rec, outcome)
    horizon, hsrc, huncertain, hres = infer_horizon(rec, outcome)
    results += [fres, hres]
    cta, unresolved, cres = build_cta(rec, schedule)
    results += cres
    action, ares = build_next_action(flow, horizon, outcome)
    results.append(ares)
    return Intent(flow, horizon, hsrc, cta, action, uncertain=huncertain or unresolved or schedule.uncertain, unresolved_link=unresolved, results=results)
