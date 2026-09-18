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

## C9 independent-review correction — done

What I fixed:
- Replaced fixture-specific names and phrases in the meaning evaluator with checks derived from
  each record's first name, property, amenity interests, move month, CTA, and opt-out requirement.
- Made an explicit `expected.next_message: null` a safe, measured no-message meaning check.
- Separated per-input evaluation from timing samples and matched results by list position, so
  duplicate task IDs stay independent and inputs beyond the 100-run latency sample are evaluated.
- Added regression coverage for changed record facts, null expected messages, duplicate IDs, and
  a 101-record input batch.

Code commit: `7d71dc5` (`Fix C9 evaluation coverage and meaning checks`).

Check: `python3 -m pytest -q casestudy/tests` — 212 passed. Also ran
`python3 -m py_compile casestudy/*.py` and `git diff --check` successfully.

Left open: live-model latency and the optional tone judge remain unmeasured/not run by design;
C10 is still the next task.

- Reviewer still had concerns about **C9 Evaluate every assignment field.** For each record, report every `required_state`, every: Preserve the reference’s move-timing meaning in casestudy/evaluation.py instead of checking only the month, and add a regression test proving early February fails against the mid-February reference.

## C10 Build the demo page — done

What I did:
- Added a full-width case-study workbench that accepts pasted or uploaded JSONL, defaults to the
  offline templates, and keeps all batch records selectable even when one is malformed.
- Kept the exact public export on the left and separate diagnostics on the right, including engine,
  latency, fallback, record-local errors, the cited decision trail, and a row for every required
  state, constraint, and threshold (including unsupported or not-measured values).
- Copy one, Copy all, and Download use the server-returned C7 serializer bytes rather than
  rebuilding JSON in the browser. Added API, structure, accessibility/state, and real Chromium
  coverage for 1, 2, 12, uploaded, malformed, and offline inputs, including clipboard and download
  byte reparsing.
- Added decision log entry 39. Authentication proxying, navigation, container, health, and request
  limits remain C11 as planned.

Code commit: `03f14d4` (`Case study C10: build exact export demo page`).

Check: `python3 -m pytest -q casestudy/tests` — 216 passed. Also ran
`python3 -m py_compile casestudy/*.py`, `node --check casestudy/web_assets/app.js`, and
`git diff --check` successfully. A repository-wide bare `pytest` cannot collect three unrelated
legacy/archive suites because of their existing import-path collisions (`merge`, `census`, and a
duplicate test module); the plan's complete case-study suite passes.

Left open: C11 must put `/case-study*` behind the existing Caddy sign-in gate, add the navigation
entry, containerize this service, and prove health, limits, restart, and isolation. No live model
call was made.

## C11 Container and local production wiring — done

What I did:
- Added a slim Python container that installs `tzdata`, runs as the unprivileged `casestudy` user,
  and copies only `casestudy/` into the image. It has a Docker health check and a direct `/health`
  endpoint.
- Added configurable 2 MiB request and 100-record batch limits with JSON 413 responses. The local
  Compose stack now starts the service, and the private human preview keeps it internal.
- Routed `/case-study*` through the existing Caddy authentication check before proxying to the
  separate service, and added the Case Study navigation link. Signed-out requests redirect to sign
  in; a signed-in 12-record request succeeds through the front door.
- Documented the separate Railway service, Dockerfile and start command, private upstream, health
  path, `DEEPSEEK_API_KEY`/`DEEPSEEK_MODEL`, optional limits, and missing-key template fallback.
- Added decision log entry 40 and deployment coverage. The first limit test used a deliberately
  tiny request cap that was too small for 12 sample records, so the test cap was corrected while
  keeping the production default at 2 MiB. A pre-existing browser upload assertion also exposed an
  async race under the parallel run; it now waits for the file read before asserting.

Code commit: `f2f8028` (`Case study C11: add production container wiring`).

Check:
- `python3 -m pytest -q casestudy/tests` — 220 passed.
- `python3 -m pytest -q chatbot/tests tooling/realpage-library/tests tooling/qa/fixes_tests` —
  254 passed.
- Caddy validation, both Compose configurations, the human-preview offline check, Python compile,
  JavaScript syntax checks, and `git diff --check` passed.
- Built the real image and proved `/health`, a 12-record request, missing-key template fallback,
  non-root runtime, restart recovery, no key material in logs, and no `/app/propertystack/data`,
  `/app/chatbot`, or `/app/site` paths.

Left open: the service is ready for Drew's localhost acceptance and then an authorized push and
Railway setup. Nothing was pushed, deployed, or sent to a live model. C12 is next.

## C12 Under the Hood — done

What I did:
- Added an Under the Hood evidence section to the case-study workbench. It separates observed facts
  from project hypotheses, shows the deterministic/model boundary, preserves the major reversed
  decisions, and names the unhandled or unmeasured areas.
- Published a dated evaluator snapshot: 2/2 structural passes, 2/2 meaning passes, macro F1 1.00 on
  24 explicitly synthetic replies, and 0.61 ms median / 1.22 ms p95 over 100 warm offline runs. It
  says plainly that all timing runs used the template fallback and that live-model evidence was not
  measured.
- Verified the public legal and engineering claims against primary sources. Corrected the Texas
  statute from §305.053 to §301.051 and labeled the narrower contact window and exact STOP wording as
  project defaults rather than universal legal requirements. All four published citation URLs
  returned HTTP 200 on 2026-09-17. Preserved the shipcheck and build-bot project links separately.
- Added responsive browser coverage and checked the section at 390, 820, and 1440 pixels with no
  horizontal overflow. Added decision log entry 41 and saved the detailed citation review.

Code commit: `d2139e5` (`Case study C12: add evidence boundary page`).

Check:
- `python3 -m pytest -q casestudy/tests` — 222 passed.
- The C12 browser section rendered at phone, tablet, and desktop widths with four evidence cards and
  four primary-source cards, and every published citation returned HTTP 200.
- `git diff --check` passed. A repository-wide bare `pytest` still cannot collect the same unrelated
  archive/client-map suites noted in C10 (`merge`, `census`, and a duplicate archived test module);
  the complete case-study suite passes.

Left open: the shipcheck GitHub project URL currently returns 404 because that separate repository
has not been published; it is a preserved project link, not a source citation. C13 dress rehearsal
and the recovery card are next. No live model call, push, or deployment happened.

## C13 Dress rehearsal and recovery card — done

What I did:
- Added `casestudy/rehearsal.py`, a repeatable HTTP-boundary checker that runs both supplied
  examples, the first 12 focused practice records, explicit offline copies of both batches, and a
  malformed row between the goldens. It saves and reparses canonical JSONL, validates every line
  against the strict public contract, compares batch bytes with the server's per-record bytes,
  requires template/deterministic engines, and proves the malformed row safely escalates without
  losing either neighbor.
- Expanded `casestudy/README.md` with paste/upload, exact export, download location, offline switch,
  restart, malformed-row recovery, and reproducible rehearsal commands. Added the one-page
  `casestudy/INTERVIEW-CARD.md` with the three-minute explanation, steps for the live 12, under-one-
  minute recovery, saved-download location, and honest limits.
- Added focused rehearsal coverage and decision-log entry 42. The real 12 hold-outs are not stored
  in this repository, so the rehearsal uses 12 labeled practice records; the page and card are
  ready to accept the arbitrary live 12 during the interview.

Implementation commit: `320e981` (`Case study C13: add rehearsal and recovery card`).

Rehearsal commands and actual results:
- Built the deployment image with
  `docker build -f casestudy/Dockerfile -t cranesignal-case-study-c13 .` — passed.
- Started that non-root image on port 18091 with no model credentials and ran
  `python3 -m casestudy.rehearsal --base-url http://127.0.0.1:18091 --output-dir <run-dir>` twice.
  Each run passed all five exports and 31 result rows: 2 configured-mode goldens, 12 configured-
  mode practice records, 2 offline goldens, 12 offline practice records, and 3 offline rows with a
  malformed middle record. Both runs reported exact counts 2/12/2/12/3; every saved line reparsed.
- Repeated the same full rehearsal twice against the direct Python HTTP service as an additional
  check; both runs also passed all 31 results. `/health` returned `{"status": "ok"}`, and Docker
  reported runtime user `casestudy`.

Checks:
- `python3 -m pytest -q casestudy/tests` — 223 passed.
- `python3 -m pytest -q chatbot/tests tooling/realpage-library/tests tooling/qa/fixes_tests` —
  254 passed.
- `python3 -m py_compile casestudy/*.py`, `node --check casestudy/web_assets/app.js`, and
  `git diff --check` — passed.

Left open: no live model call, deployment, push, or interview hold-out run occurred. Production
deployment and Drew's live-site acceptance still require separate authorization after localhost
acceptance, exactly as planned.
