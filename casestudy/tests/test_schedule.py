"""C2: channel and send-time inference."""
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from casestudy.gates import run_gates
from casestudy.schedule import compute_send_time, infer_schedule, parse_day_token, permitted_slot

DATA = Path(__file__).resolve().parents[1] / "data"
SAMPLES = [json.loads(l) for l in (DATA / "sample.jsonl").read_text().splitlines() if l.strip()]


def _variant(idx=0, **inp):
    raw = json.loads(json.dumps(SAMPLES[idx]))
    raw["input"].update(inp)
    return raw


def _schedule(raw):
    return infer_schedule(run_gates(raw))


@pytest.mark.parametrize("raw", SAMPLES, ids=["sms_example", "email_example"])
def test_both_sample_timestamps_exact(raw):
    s = _schedule(raw)
    assert s.channel == raw["expected"]["next_message"]["channel"]
    assert s.send_at_iso == raw["expected"]["next_message"]["send_at"]
    assert s.kind == "automated_message"
    assert s.cadence_source == "task_id_token"
    assert not s.uncertain
    for r in s.results:
        assert r.citation and r.reason and r.confidence


def test_channel_email_when_sms_not_consented_even_if_first():
    raw = _variant(0)
    raw["consent"]["sms_opt_in"] = False
    s = _schedule(raw)
    assert s.channel == "email"
    # 09:04 local interaction; the email slot 10:00 is still strictly after it -> same day
    assert s.send_at_iso == "2025-12-08T10:00:00-06:00"


def test_voice_proposes_call_task():
    raw = _variant(0)
    raw["consent"] = {"sms_opt_in": False, "email_opt_in": False, "voice_opt_in": True}
    raw["channel_preferences"] = ["voice", "sms"]
    s = _schedule(raw)
    assert s.channel == "voice" and s.kind == "call_task"
    assert s.send_at_iso == "2025-12-08T10:00:00-06:00"


def test_same_day_pre_slot_sends_same_day():
    # 07:00 local Dec 8 (Mon) + day0 -> 09:00 same day
    s = _schedule(_variant(0, last_interaction="2025-12-08T13:00:00Z"))
    assert s.send_at_iso == "2025-12-08T09:00:00-06:00"


def test_same_day_post_slot_advances_a_day():
    # 09:04 local: 09:00 candidate is not strictly after -> next day (this is the SMS sample)
    s = _schedule(_variant(0, last_interaction="2025-12-08T15:04:00Z"))
    assert s.send_at_iso == "2025-12-09T09:00:00-06:00"
    # exactly 09:00:00 is also not *strictly* after
    s = _schedule(_variant(0, last_interaction="2025-12-08T15:00:00Z"))
    assert s.send_at_iso == "2025-12-09T09:00:00-06:00"


def test_sunday_uses_noon_start_computed_before_comparison():
    # Sat Dec 6 05:30 local, day1 -> Sunday Dec 7: email 10:00 clamps to 12:00
    raw = _variant(1)
    raw["task_id"] = "prospect_long_horizon_day1"
    s = _schedule(raw)
    assert s.send_at_iso == "2025-12-07T12:00:00-06:00"
    # Sunday 11:00 interaction, day0: 12:00 is still strictly after -> same Sunday
    s = _schedule(_variant(0, last_interaction="2025-12-07T17:00:00Z"))
    assert s.send_at_iso == "2025-12-07T12:00:00-06:00"
    assert permitted_slot(datetime(2025, 12, 7).date(), "sms").strftime("%H:%M") == "12:00"


def test_phoenix_no_dst_offset():
    s = _schedule(_variant(0, timezone="America/Phoenix", last_interaction="2025-07-08T15:04:00Z"))
    # 15:04Z is 08:04 in Phoenix (no DST, always -07:00) -> 09:00 same day
    assert s.send_at_iso == "2025-07-08T09:00:00-07:00"


def test_los_angeles_offset():
    # 15:04Z is 07:04 in Los Angeles (PST) -> 09:00 same day
    s = _schedule(_variant(0, timezone="America/Los_Angeles"))
    assert s.send_at_iso == "2025-12-08T09:00:00-08:00"


def test_dst_boundary_offset_follows_send_date():
    # Chicago falls back 2025-11-02. Interaction Sat Nov 1 (CDT -05:00), day1 -> Sunday Nov 2 12:00 CST (-06:00)
    raw = _variant(1, last_interaction="2025-11-01T12:00:00Z")
    raw["task_id"] = "x_day1"
    s = _schedule(raw)
    assert s.send_at_iso == "2025-11-02T12:00:00-06:00"
    # Spring forward 2026-03-08: LA interaction Sat Mar 7 (-08:00), day1 -> Sun 12:00 PDT (-07:00)
    raw = _variant(0, timezone="America/Los_Angeles", last_interaction="2026-03-07T20:00:00Z", move_date_target="2026-04-10")
    raw["task_id"] = "x_day1"
    s = _schedule(raw)
    assert s.send_at_iso == "2026-03-08T12:00:00-07:00"


def test_malformed_timezone_never_schedules():
    s = _schedule(_variant(0, timezone="Mars/Olympus"))
    assert s.send_at is None and s.channel is None and s.uncertain
    assert s.results[0].status == "skipped"


def test_day10_parses_all_digits():
    assert parse_day_token("prospect_day10") == 10
    assert parse_day_token("prospect_welcome_day0") == 0
    assert parse_day_token("day123") == 123
    assert parse_day_token("day3_prospect") is None  # not the final token
    assert parse_day_token("holiday7") is None  # must be its own token
    assert parse_day_token(None) is None
    raw = _variant(0)
    raw["task_id"] = "prospect_day10"
    s = _schedule(raw)
    assert s.cadence_days == 10
    assert s.send_at_iso == "2025-12-18T09:00:00-06:00"


def test_no_day_token_uses_earliest_slot_and_flags():
    raw = _variant(0)
    raw["task_id"] = "a1b2c3"
    s = _schedule(raw)
    assert s.uncertain and s.cadence_source == "none" and s.cadence_days == 0
    assert s.send_at_iso == "2025-12-09T09:00:00-06:00"


def test_explicit_cadence_field_beats_token():
    raw = _variant(0, cadence_days=2)
    s = _schedule(raw)
    assert s.cadence_source == "explicit_field" and s.cadence_days == 2
    assert s.send_at_iso == "2025-12-10T09:00:00-06:00"


def test_explicit_send_at_used_when_valid():
    s = _schedule(_variant(0, send_at="2025-12-10T14:30:00-06:00"))
    assert s.send_at_iso == "2025-12-10T14:30:00-06:00" and s.cadence_source == "explicit_field"
    # outside the window (22:00) -> failed, no send time
    s = _schedule(_variant(0, send_at="2025-12-10T22:00:00-06:00"))
    assert s.send_at is None and s.uncertain


def test_compute_send_time_direct():
    tz = ZoneInfo("America/Chicago")
    ref = datetime.fromisoformat("2025-12-06T11:30:00+00:00")
    at, d = compute_send_time("email", ref, tz, 3)
    assert at.isoformat(timespec="seconds") == "2025-12-09T10:00:00-06:00"
    assert d["advanced_days"] == 0 and d["weekday"] == "Tuesday"
