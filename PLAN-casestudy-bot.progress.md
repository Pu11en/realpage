# Progress log

## C0 Freeze the contract and reference tests — done

What I did:
- Added `casestudy/contract.py`: Pydantic models for the exact public export shape —
  `AssignmentAnswer = {next_message, next_action}`, with `NextMessage` (channel, send_at,
  subject, body, cta), CTA variants (`schedule_tour` with `options` for SMS-style or `link`
  for email-style), and next-action variants (`start_cadence` with `name`,
  `follow_up_in_days` with `value`, `mark_opted_out` with `reason`). All models use
  `extra="forbid"` so no diagnostic/internal key (task_id, scores, engine, latency) can
  leak into the public shape.
- Added `casestudy/tests/test_contract.py`: loads both `expected` blocks from
  `casestudy/data/sample.jsonl`, round-trips them through the model, asserts exact
  structure/nulls/enum values/CTA payloads/next actions/timestamps for both the SMS and
  email examples, rejects extra public keys (including a leaked diagnostic key nested in
  `next_message`), and adds a small reference-derived semantic checklist that accepts a
  harmless paraphrase of the SMS body but rejects a version that drops the opt-out
  instruction and the addressee's name (wrong facts, not paraphrase).

Commit: (see next git log entry after this file is committed)

Check: `python3 -m pytest -q casestudy/tests` — 13 passed.

Left open: C1 (input normalization and the five gates) is next. The semantic checklist
here is intentionally small/local to C0 (SMS example only) — later tasks (C3/C9) will need
a fuller reference-derived checklist covering the email example's personalization facts
(amenity interest, move-month phrase) and safety/PII constraints.

## C1 Input normalization and the five gates — done

What I did:
- Added `casestudy/gates.py`: `normalize()` (never crashes; missing/wrong-typed fields become
  warnings, consent is only explicit `true`), `classify_reply()` (opt_out / help / choose_option /
  not_interested / question / unknown), and the gate chain `run_gates()` in the order
  reply → consent → lifecycle/do-not-contact → frequency → dates/timezone. Each `GateResult`
  has status, reason, citation, confidence label. Unknown `required_states` come back as
  `unsupported`; only `consent_verified` is marked verified here. Reference clock comes from
  the input (`reference_time` or `last_interaction`), never the server date.
- Added `casestudy/tests/test_gates.py` (33 tests): both samples pass every gate; STOP with
  consent already false → `mark_opted_out`; HELP still hits consent; `1`/`2` need prior options
  and produce `propose_follow_up` (not a booking); out-of-range option, questions, not-interested;
  missing/non-boolean consent suppresses; unknown required_state is visibly unsupported;
  do-not-contact and blocked lifecycle suppress; frequency cap; bad/missing timezone, missing or
  malformed clock, malformed or past move date all escalate; malformed records (None, int, list,
  string, wrong-typed sections) never crash.
- Decision log entry 30.

Commit: see git log ("Case study C1").

Check: `python3 -m pytest -q casestudy/tests` — 46 passed.

Left open: terminal gate outcomes (`mark_opted_out`, `suppress`, `escalate`) don't yet map to the
public `AssignmentAnswer`, whose `next_message` is non-nullable; C7 must decide whether to make it
nullable for do-not-send cases. Inbound reply / prior-option field names are guesses at the
hold-out shape (several aliases accepted). `days_to_move` is measured from the reference date
(33 and 71 for the samples), not the send date.

## C2 Channel and send-time inference — done

What I did:
- Added `casestudy/schedule.py`: `select_channel()` (first preferred channel with explicit
  consent; voice → `call_task`, never an automated message), `parse_day_token()` (final `dayN`,
  all digits), `compute_send_time()` (interaction-local date + N at the channel slot, SMS 09:00 /
  email 10:00, clamped into the 09:00-20:00 Mon-Sat / 12:00-20:00 Sunday project window before
  comparison, advance a day if not strictly after the interaction), and `infer_schedule()` which
  takes a `GateOutcome` and returns a `Schedule` with an explained, cited, confidence-labelled trail.
  Explicit `input.send_at` / `cadence_days` / `follow_up_days` / `cadence.delay_days` outrank the
  token; no token means N=0 flagged uncertain. Versioned as `send_time_v1`.
- Added `casestudy/tests/test_schedule.py` (16 tests): both exact sample timestamps, email when
  SMS is first but unconsented, voice call task, same-day pre-slot, post-slot (incl. exactly 09:00),
  Sunday noon clamp computed before comparison, Phoenix (no DST), Los Angeles, fall-back and
  spring-forward DST boundaries, malformed timezone never schedules, `day10` parses all digits,
  opaque ID flags uncertainty, explicit fields beat the token, explicit send_at inside/outside window.
- Decision log entry 31.

Commit: see git log ("Case study C2").

Check: `python3 -m pytest -q casestudy/tests` — 62 passed.

Left open: `Schedule.send_at_iso` is the string that C7 should place in `next_message.send_at`.
The voice slot (10:00) and the quiet-hours window are project defaults. Sunday clamp shifts SMS
and email to the same 12:00 slot, which the samples neither confirm nor deny.

## C3 Intent, horizon, CTA, and next action — done

What I did:
- Added `casestudy/intent.py` (`intent_v1`): `infer_intent(outcome, schedule)` returns an `Intent`
  with flow, horizon (+source), CTA dict, next-action dict, uncertainty/unresolved-link flags, and
  a cited, confidence-labelled trail. Precedence is explicit input fields → lifecycle (observed) →
  task_id tokens (hypothesis) → computed fallback. Horizon fallback is <=45 days short / >45 long,
  no medium tier. SMS CTA = 2nd/3rd non-Sunday days after the send date; email CTA = explicit link
  or the Oak Ridge link learned from the sample (provenance kept); unseen property → bare
  `{type: schedule_tour}` plus an `unresolved_link` diagnostic. Welcome → `start_cadence
  prospect_welcome_<horizon>_horizon`; open flow / option reply → `follow_up_in_days 3` (never the
  dayN suffix); STOP → `mark_opted_out`.
- `casestudy/contract.py`: added `ScheduleTourReplyCTA` (bare `{type}`) for the unresolved-link
  fallback only; everything else unchanged.
- Added `casestudy/tests/test_intent.py` (15 tests): both expected CTA/actions exactly (and they
  validate against the public contract), opaque IDs, boundary 45/46 days, explicit fields beating
  a conflicting task_id, day10 still → 3, explicit link over learned, unseen property never gets a
  URL, learned-link provenance, Sunday skipping in option days, unknown primary_cta flagged, STOP,
  option reply, suppressed record.
- Decision log entry 32.

Commit: see git log ("Case study C3").

Check: `python3 -m pytest -q casestudy/tests` — 77 passed.

Left open: record 1's short horizon comes from the move-date fallback (its id carries no horizon
token), so the 45-day boundary is load-bearing for that golden; keep it configurable. The long
welcome cadence name and the Sunday-skip in tour options are project hypotheses. Voice call tasks
get the bare CTA; C7 must decide how a call task appears in the public shape.
