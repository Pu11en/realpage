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
