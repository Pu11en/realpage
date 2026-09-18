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
