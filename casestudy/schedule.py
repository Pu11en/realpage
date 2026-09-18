"""C2: channel and send-time inference.

Channel: the first entry in `channel_preferences` whose consent is an explicit `true`
(observed in both samples). Voice never becomes an automated message; it yields a
call task for a human (project rule: the service proposes, never dials).

Send time (versioned hypothesis `send_time_v1`, disclosed in every result):
  1. explicit input fields win: `input.send_at` (an ISO timestamp) or a cadence delay
     in `input.cadence_days` / `input.follow_up_days` / `input.cadence.delay_days`;
  2. otherwise parse a final `dayN` token from `task_id` as the cadence delay N;
  3. due date = interaction-local date + N, at the channel's observed slot
     (SMS 09:00, email 10:00; voice 10:00 is a project default);
  4. the slot is clamped into the day's permitted window *before* comparison, so a
     Sunday 10:00 email becomes Sunday 12:00;
  5. if the candidate is not strictly after the interaction, advance one permitted day;
  6. if no `dayN` and no explicit field exist, use the earliest eligible slot (N=0)
     and flag the uncertainty.

The quiet-hours window (09:00-20:00 Mon-Sat, 12:00-20:00 Sunday, recipient-local) is a
conservative project default, not a verified national legal rule. `dayN` explains both
sample timestamps but is not proven to be an elapsed cadence delay.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Any, Optional
from zoneinfo import ZoneInfo

from .gates import CHANNELS, GateOutcome, GateResult, NormalizedRecord, _parse_dt

SEND_TIME_VERSION = "send_time_v1"

# observed: SMS 09:00 and email 10:00 in sample.jsonl. voice: conservative_default.
CHANNEL_SLOT = {"sms": time(9, 0), "email": time(10, 0), "voice": time(10, 0)}
CHANNEL_SLOT_CONFIDENCE = {"sms": "observed", "email": "observed", "voice": "conservative_default"}

# conservative_default demo window (recipient local). Monday=0 ... Sunday=6.
WINDOW_START_WEEKDAY = time(9, 0)
WINDOW_START_SUNDAY = time(12, 0)
WINDOW_END = time(20, 0)
WINDOW_CITE = (
    "project default window 09:00-20:00 Mon-Sat / 12:00-20:00 Sun recipient-local; "
    "modelled on TCPA 47 CFR 64.1200(c)(1) 8am-9pm plus stricter state rules, but NOT a verified national legal rule"
)

DAY_TOKEN = re.compile(r"(?:^|[_\-\s])day(\d+)$", re.IGNORECASE)
MAX_CADENCE_DAYS = 365


@dataclass
class Schedule:
    channel: Optional[str]
    kind: str  # "automated_message" | "call_task" | "none"
    send_at: Optional[datetime]
    cadence_days: Optional[int]
    cadence_source: str  # explicit_field | task_id_token | none
    version: str = SEND_TIME_VERSION
    uncertain: bool = False
    results: list[GateResult] = field(default_factory=list)

    @property
    def send_at_iso(self) -> Optional[str]:
        """ISO-8601 with seconds and a numeric recipient-local offset (matches both samples)."""
        if self.send_at is None:
            return None
        return self.send_at.isoformat(timespec="seconds")


# --------------------------------------------------------------------------- channel


def select_channel(rec: NormalizedRecord) -> tuple[Optional[str], GateResult]:
    cite = "observed in sample.jsonl: SMS chosen when first and consented; email when SMS consent is false"
    for ch in rec.channel_preferences:
        if rec.consent.get(ch) is True:
            return ch, GateResult(
                "channel_select", "passed",
                f"{ch} is the first preferred channel with explicit consent (preferences {rec.channel_preferences})",
                cite, "observed", {"channel": ch},
            )
    fallback = [ch for ch in CHANNELS if rec.consent.get(ch) is True]
    if fallback:
        ch = fallback[0]
        return ch, GateResult(
            "channel_select", "passed",
            f"no preferred channel is consented; {ch} is the first consented channel in default order {list(CHANNELS)}",
            "project conservative default: consented channel outside preferences, flagged", "conservative_default",
            {"channel": ch, "warning": "channel_outside_preferences"},
        )
    return None, GateResult("channel_select", "failed", "no channel has explicit consent", cite, "observed")


# --------------------------------------------------------------------------- cadence


def parse_day_token(task_id: Optional[str]) -> Optional[int]:
    """Final `dayN` token of a task_id, all digits (day10 -> 10). None when absent."""
    if not isinstance(task_id, str):
        return None
    m = DAY_TOKEN.search(task_id.strip())
    return int(m.group(1)) if m else None


def _explicit_cadence(rec: NormalizedRecord) -> Optional[int]:
    inp = rec.input
    candidates: list[Any] = [inp.get("cadence_days"), inp.get("follow_up_days")]
    cad = inp.get("cadence")
    if isinstance(cad, dict):
        candidates.append(cad.get("delay_days"))
    for c in candidates:
        if isinstance(c, bool):
            continue
        if isinstance(c, int) and 0 <= c <= MAX_CADENCE_DAYS:
            return c
        if isinstance(c, str) and c.strip().isdigit() and int(c) <= MAX_CADENCE_DAYS:
            return int(c)
    return None


# --------------------------------------------------------------------------- time math


def window_start(day: date) -> time:
    return WINDOW_START_SUNDAY if day.weekday() == 6 else WINDOW_START_WEEKDAY


def permitted_slot(day: date, channel: str) -> time:
    """The channel slot clamped into that day's permitted window (computed before comparing)."""
    slot = CHANNEL_SLOT.get(channel, time(10, 0))
    start = window_start(day)
    if slot < start:
        slot = start
    if slot > WINDOW_END:
        slot = WINDOW_END
    return slot


def compute_send_time(channel: str, reference: datetime, tz: ZoneInfo, cadence_days: int) -> tuple[datetime, dict[str, Any]]:
    """Recipient-local send time. Advances day by day until the candidate is strictly after the reference."""
    local_ref = reference.astimezone(tz)
    day = local_ref.date() + timedelta(days=max(0, cadence_days))
    advanced = 0
    while True:
        slot = permitted_slot(day, channel)
        candidate = datetime.combine(day, slot, tzinfo=tz)
        if candidate > local_ref:
            break
        day += timedelta(days=1)
        advanced += 1
        if advanced > 14:  # defensive; the window has a slot every day so this cannot loop forever
            break
    # Re-derive through the zone so the numeric offset reflects DST on the send date.
    candidate = candidate.astimezone(tz)
    return candidate, {
        "interaction_local": local_ref.isoformat(timespec="seconds"),
        "due_date": (local_ref.date() + timedelta(days=cadence_days)).isoformat(),
        "slot": slot.strftime("%H:%M"),
        "advanced_days": advanced,
        "weekday": candidate.strftime("%A"),
        "utc_offset": candidate.strftime("%z"),
    }


# --------------------------------------------------------------------------- driver


def infer_schedule(outcome: GateOutcome) -> Schedule:
    """Turn a proceeding GateOutcome into a channel + send time with an explained trail."""
    results: list[GateResult] = []
    rec = outcome.record
    if rec is None or not outcome.proceed or outcome.reference_time is None or outcome.tz is None:
        results.append(GateResult(
            "schedule", "skipped", f"gate decision {outcome.decision!r}; no send time computed",
            "project rule: terminal gate decisions never schedule a message", "conservative_default",
        ))
        return Schedule(None, "none", None, None, "none", uncertain=True, results=results)

    channel, ch_res = select_channel(rec)
    results.append(ch_res)
    if channel is None:
        return Schedule(None, "none", None, None, "none", uncertain=True, results=results)
    kind = "call_task" if channel == "voice" else "automated_message"
    if channel == "voice":
        results.append(GateResult(
            "channel_select", "passed", "voice consent selected; proposing a human call task, never an automated call or robotext",
            "project rule: service proposes, never dials (TCPA autodialer/prerecorded restrictions, 47 U.S.C. 227(b))",
            "conservative_default", {"kind": kind},
        ))

    # 1. explicit send_at wins outright
    explicit_at = _parse_dt(rec.input.get("send_at"))
    if explicit_at is not None:
        local = explicit_at.astimezone(outcome.tz)
        ok = local > outcome.reference_time.astimezone(outcome.tz) and window_start(local.date()) <= local.time() <= WINDOW_END
        results.append(GateResult(
            "send_time", "passed" if ok else "failed",
            f"input.send_at supplied ({local.isoformat(timespec='seconds')}); " + ("inside the permitted window" if ok else "outside the permitted window or not after the reference clock"),
            WINDOW_CITE, "input_required", {"version": SEND_TIME_VERSION, "source": "explicit_send_at"},
        ))
        return Schedule(channel, kind, local if ok else None, None, "explicit_field", uncertain=not ok, results=results)

    # 2. cadence delay: explicit field, else task_id token, else N=0 flagged
    cadence = _explicit_cadence(rec)
    uncertain = False
    if cadence is not None:
        source, conf, why = "explicit_field", "input_required", f"cadence delay {cadence} day(s) supplied in input"
    else:
        token = parse_day_token(rec.task_id)
        if token is not None:
            cadence, source, conf = token, "task_id_token", "hypothesis"
            why = f"task_id {rec.task_id!r} ends in day{token}; treated as a {token}-day cadence delay (identifier hint, not proof of elapsed time)"
        else:
            cadence, source, conf, uncertain = 0, "none", "conservative_default", True
            why = f"no cadence field and no dayN token in task_id {rec.task_id!r}; using the earliest eligible slot and flagging uncertainty"
    results.append(GateResult("cadence", "passed", why, "sample.jsonl task_id pattern (day0, day3) — PLAN C2 hypothesis", conf, {"cadence_days": cadence, "source": source}))

    send_at, detail = compute_send_time(channel, outcome.reference_time, outcome.tz, cadence)
    detail.update({"version": SEND_TIME_VERSION, "slot_confidence": CHANNEL_SLOT_CONFIDENCE.get(channel, "conservative_default")})
    reason = (
        f"{channel} slot {detail['slot']} on {detail['due_date']} (interaction-local {detail['interaction_local']} + {cadence}d)"
        + (f"; not strictly after the interaction, advanced {detail['advanced_days']} day(s)" if detail["advanced_days"] else "")
        + f" -> {send_at.isoformat(timespec='seconds')} ({detail['weekday']})"
    )
    results.append(GateResult("send_time", "passed", reason, WINDOW_CITE, "hypothesis", detail))
    return Schedule(channel, kind, send_at, cadence, source, uncertain=uncertain, results=results)
