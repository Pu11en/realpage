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

## C4 Channel-specific validators — done

What I did:
- Added `casestudy/validators.py` (`validators_v1`): `Draft`, `ValidationReport`, `validate_draft()`
  and `select_draft()`. Checks: profile echo (only first_name/amenity_interest approved; money and
  street addresses allowed when from property/business fields, blocked when from the profile;
  email/phone/SSN patterns hard unless supplied business data), fair-housing lexicon with HARD and
  WARN entries each carrying the §3604(c) citation and a rewrite, brand style (greeting, <=1 "!",
  no emoji/shouting/shorteners), SMS (null subject, literal trailing STOP sentence, numbered
  options, one question, GSM-7/UCS-2 segment count <=3), email (non-null accurate subject, link
  CTA in body, click-or-STOP opt-out). Email delivery compliance (postal address etc.) is reported
  as `unverified`/out of scope, not required and not assumed. Model drafts get the same hard rules;
  `select_draft()` never picks a hard-failing model draft over a passing template.
- Added `casestudy/tests/test_validators.py` (19 tests): both samples pass (email without postal
  address), SMS/email rule failures, segment counting, unsafe profile data ignored when not echoed
  and hard when echoed (last_name, phone, income, city_interest, address), business money/address
  allowed, PII pattern provenance, HARD vs WARN fair housing with citation/rewrite, brand style,
  model draft cannot override.
- Decision log entry 33.

Commit: see git log ("Case study C4").

Check: `python3 -m pytest -q casestudy/tests` — 96 passed.

Left open: the sample SMS is 3 UCS-2 segments because of its em dash, so the 3-segment cap is at
its limit; C5 templates should keep the em dash (observed) but avoid growing the body. Subject
"accuracy" is a shallow word-overlap heuristic. The fair-housing lexicon is a project list, not a
legal authority; C12 must say so.

## C5 Offline templates — done

What I did:
- Added `casestudy/templates.py` (`templates_v1`): `render_templates(outcome, schedule, intent)`
  fills SMS/email templates for welcome, open follow-up, and option-reply flows (email with a link
  or a reply-to-arrange fallback), validates every candidate with C4's `select_draft()`, and returns
  the first passing draft plus the candidates, reports, personalization fields used, and a cited
  trail. SMS welcome reproduces record 1 byte-for-byte; the email template uses amenity interests
  and a "mid-February"-style move-month phrase and the Oak Ridge link learned in C3. Learned Oak
  Ridge facts (short name, "24/7 fitness center") carry provenance and are keyed to that exact
  property only. A compact GSM-7 SMS variant (no em dash) is the fallback when the 3-segment cap
  would be exceeded. Missing fields degrade to neutral wording; only `first_name` and
  `amenity_interest` are read from the profile.
- Added `casestudy/tests/test_templates.py` (14 tests): SMS reference identical + semantic
  checklist, email reference meaning checklist (name, move month, amenities, learned fact, URL,
  opt-out, subject), every candidate validated with cited trail, Oak Ridge facts never generalize,
  unseen property without link → reply fallback, missing optional fields → neutral, missing
  property/first name SMS, unsafe profile fields never used, long name → compact GSM-7 fallback,
  open follow-up SMS and welcome email, option reply confirms without booking, STOP and voice
  produce no draft, helper phrases.
- Decision log entry 34.

Commit: see git log ("Case study C5").

Check: `python3 -m pytest -q casestudy/tests` — 110 passed.

Left open: the email body's apostrophes are ASCII while the reference uses curly ones (meaning
identical, bytes differ; fine per plan). Non-English `language` is flagged, not translated (C8
Spanish fixture will need a decision). The email option-reply template exists but is only exercised
via SMS in tests. Subject wording for the email reference differs from the sample ("pool and
fitness center" vs "pool & fitness rooms") by design.

## C6 Bounded writer — done

What I did:
- Added `casestudy/writer.py` (`writer_v1`): `WriterConfig.from_env()` reads `DEEPSEEK_API_KEY`,
  `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL`, `CASESTUDY_OFFLINE` (no guessed model constant);
  `make_client()` builds the OpenAI-compatible client with `max_retries=0`; `verify_model()`
  preflights the configured model against the endpoint list (cached); `Deadline` is a monotonic
  per-record budget bounded by the record's `p95_latency_ms` and a 2,000 ms ceiling with a 250 ms
  reserve; `build_messages()` sends a stable system prefix and the record last with only approved
  profile fields; `write()` makes at most one `json_object`/temperature-0/`max_tokens=400` request,
  validates the reply with a strict Pydantic `ModelDraft` (extra keys forbidden, CTA must equal the
  intent CTA, `finish_reason=length` rejected), runs the C4 validators on it as a model draft, and
  otherwise returns the validated C5 template with a cited `writer.fallback` trail entry.
- Added `casestudy/tests/test_writer.py` (22 tests, fake client, no network): successful SMS and
  email drafts; timeout, empty, None, invalid JSON, wrong CTA, extra key, truncated → template with
  exactly one request; unsafe (fair-housing) and STOP-less drafts rejected; budget exhausted before
  the call skips the model; record threshold bounds the budget; slow reply after the deadline is
  discarded; deadline is monotonic; offline/unconfigured never builds a client; env config has no
  guessed model; unverified model gets no request; preflight cached and error-tolerant; client
  built with retries disabled; prompt excludes unsafe profile fields; terminal decisions never
  call the model.
- Decision log entry 35.

Commit: see git log ("Case study C6").

Check: `python3 -m pytest -q casestudy/tests` — 132 passed.

Left open: the output-limit/truncation behaviour is proven only against a fake client; the live
schema smoke test and model-list preflight against the real endpoint wait for Drew's
authorization (C11/C13). The prompt is English-only, matching the templates.

## C7 Assemble one record and batch JSONL — done

What I did:
- Added `casestudy/pipeline.py`: assembles the gate, schedule, intent, validated template, and
  bounded-writer stages into one `AssignmentAnswer`; strips `expected` before inference; and keeps
  the public `{next_message, next_action}` export separate from diagnostics containing task ID,
  cited reasoning, verified/unsupported states, reply class, personalization evidence, engine,
  errors, versions, and latency. Malformed JSON, non-object values, and internal per-record errors
  return a safe no-message escalation without stopping the rest of the batch.
- Extended the public contract for deterministic no-send outcomes with `next_message: null` and a
  reason-bearing `suppress`, `escalate`, or `create_call_task` action. STOP similarly exports no
  message plus the existing `mark_opted_out` action. These shapes are project-defined because the
  two supplied examples contain only sendable messages, and diagnostics label that provenance.
- Added `casestudy/cli.py`: JSONL from a file or stdin, `--offline`, `--submission-out`, and
  `--diagnostics-out`. Both library and CLI use one compact UTF-8 submission serializer.
- Added 17 pipeline/CLI tests covering both references, poisoned/deleted `expected`, public-key
  isolation, required diagnostic fields, terminal outcomes, malformed records, contained internal
  errors, a 12-line ordered batch, file/stdin operation, identical serialization bytes, and proof
  that offline mode never builds a network client.
- Decision log entry 36.

Commit: see git log ("Case study C7").

Check: `python3 -m pytest -q casestudy/tests` — 149 passed.

Left open: the no-message action variants are conservative project shapes, not observed assignment
outputs; the diagnostics make that explicit. C8 adversarial fixtures are next.

## C7 independent-review correction — done

What I fixed:
- Personalization evidence is computed from the final public message, including model-written
  messages, and is empty when the safe public answer contains no message.
- Diagnostics merge the final validator's verified states with the gate states and include the
  final validator's cited rule results in the visible reasoning trail.
- Blank and whitespace-only JSONL lines now return a safe escalation answer instead of being
  dropped; physical line numbers remain correct for every later malformed line.
- Added focused regression tests for all three review findings.

Code commit: `769ce03` (`Fix C7 final diagnostics and blank lines`).

Check: `python3 -m pytest -q casestudy/tests` — 151 passed.

Left open: nothing for C7; C8 adversarial fixtures are next.

## C8 Adversarial practice data — done

What I did:
- Added 20 evaluator-separated practice records covering every requested scenario: email-only and
  no consent, preference order, before/after slots, day3/day10, Phoenix, Los Angeles DST, Sunday,
  Spanish, renewal, a transactional note without SMS consent, STOP, option reply, protected-class
  and PII profile fields, past/missing move dates, and voice-only.
- Added a separate expectation manifest. Every fixture names one primary rule, an expected public
  structure, and a prose/diagnostic checklist; none of those evaluator answers enter service input.
  The two immutable goldens stay only in `sample.jsonl`.
- Added a balanced 24-item reply corpus: four examples for each of six classes, with capitalization,
  punctuation, synonyms, numeric options, and ambiguous language. It deliberately makes no F1
  claim; C9 will calculate the labeled corpus metric.
- The option-reply fixture caught booking-adjacent wording. SMS and email now say a team member will
  follow up to arrange the tour, without claiming it is booked or confirmed.
- Added decision log entry 37.

Code commit: `35e6b5f` (`Case study C8: add adversarial practice data`).

Check: `python3 -m pytest -q casestudy/tests` — 198 passed.

Left open: C9 must calculate macro-F1 from the balanced synthetic corpus and report it honestly;
the Spanish fixture currently verifies the visible English-only warning rather than claiming
translation support.

## C9 Evaluate every assignment field — done

What I did:
- Added a separate evaluator that visibly reports every required state, constraint, and threshold;
  unknown fields are unsupported, and single-answer F1/p95 are honestly `not_measured`.
- Added the labeled six-class confusion matrix and macro-F1 for all 24 synthetic reply cases, plus
  warm end-to-end median/p95, fallback, and failure counts over 100 offline runs. Live-model timing
  remains separately `not_measured`; the optional shipcheck tone judge is retained as non-gating
  and `not_run`, so this task made no paid/live calls.
- Added a disclosed safe-field personalization proxy. A safe but generic model draft below the
  declared threshold now falls back to the validated template and is rechecked; a still-low result
  is reported as failed.
- Added evaluator-only golden structure and meaning checks, Wilson intervals only for their binary
  pass fractions, and the explicit warning that synthetic cases are not hold-out or real-world
  reliability evidence.
- Added decision log entry 38.

Code commit: `2904d88` (`Case study C9: evaluate assignment thresholds`).

Check: `python3 -m pytest -q casestudy/tests` — 208 passed. Also ran
`python3 -m py_compile casestudy/*.py` and `git diff --check` successfully.

Measured evidence: 24 labeled synthetic replies produced macro-F1 1.0; 100 warm offline runs
completed with 100 template fallbacks and 0 failures. Timing values are machine/run-specific and
are emitted by the report with their sample count rather than frozen as a claim here.

Left open: live-model latency and the optional tone judge require separate authorization and remain
honestly unmeasured/not run. C10 (the demo page) is next.
