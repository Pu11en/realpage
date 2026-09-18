# Case-study bot: a context-aware message agent, isolated inside CraneSignal

Goal: a separate service that reads assignment records and returns the same public shape as each
record's `expected` block: whether to message, the channel and time, the message and CTA, and the
next action. Compliance decisions stay deterministic and every internal decision can be explained
with a cited source on screen.

Done before the interview: both supplied examples pass structural and semantic reference checks; the service accepts
and exports an arbitrary JSONL batch (including the 12 live hold-out records); every per-record
assertion and threshold is visibly evaluated; the offline path passes; and the production wiring is
ready for Drew to push. Drew's live-site acceptance remains required after the authorized deployment;
local verification is an engineering milestone, not a replacement for that acceptance.

Written 2026-09-17; corrected after independent review of **both** records in `sample.jsonl`.
**The interview is 2026-09-18.** Optimize for a reliable demo, exact output shape, and fast recovery.

## Source of truth and confidence

1. `casestudy/data/problem_statement.txt` is the assignment.
2. `casestudy/data/sample.jsonl` contains **two** examples, not one. Their two `expected` blocks are
   the only observed output examples and remain immutable reference fixtures.
3. `casestudy/RULEBOOK-research.md` is a hypothesis list. An observed example overrides it.
4. `casestudy/OPENSOURCE-research.md` and `casestudy/STATE-OF-THE-ART-research.md` guide engineering
   choices, not the grader's unknown semantics.

Label every rule `observed`, `input_required`, `hypothesis`, or `conservative_default` in the internal trail.
Do not describe a law-based safety default as something learned from the two examples.
Preserve existing research as historical evidence; the corrections recorded in `REVIEW-astra.md`
govern implementation where that research or the initial review conflicts with this plan.

## Facts the two examples actually establish

- Preference order is constrained by consent: SMS wins when first and consented; email is used when
  SMS is not consented.
- SMS has `subject: null`, an options CTA, and a trailing `Reply STOP to opt out.` Email has a
  subject, a link CTA, and click-or-STOP opt-out text.
- The observed timestamps are Dec 9 at 09:00 local for SMS and Dec 9 at 10:00 local for email.
  Channel-specific slots plus a cadence-day delay explain them, but so could a shared, unspecified
  Dec 9 evaluation clock; neither general timing algorithm is proven. Both timestamps include seconds
  and a numeric recipient-local offset.
- `short_horizon` covers the 32-day example and `long_horizon` covers the 68-day example. There is
  no evidence for a medium tier or a 120-day boundary. The second label appears in `task_id`, not
  its expected action. Identifier tokens are hints, not authoritative business fields; any inferred
  boundary must remain configurable and marked as a hypothesis.
- Day 0 starts `prospect_welcome_short_horizon`; day 3 returns
  `{ "type": "follow_up_in_days", "value": 3 }`. The latter must not be replaced by a cadence name.
- The email example personalizes with amenity interest and the move-month phrase. A score based only
  on name/property/channel/time can therefore overstate personalization.

## Architecture

- Fixed routing workflow, one optional structured DeepSeek call, no agent loop. (Anthropic,
  *Building Effective Agents*, Dec 2024.)
- This service proposes messages/actions and exports them; it never sends an SMS/email, schedules
  a real tour, or writes to a CRM. Actual delivery integrations are outside this assignment.
- Compliance rules live in Python and validate both model and template drafts. (IFScale,
  arXiv 2507.11538.) Deterministic stop paths never call the model.
- `AssignmentAnswer` is exactly `{next_message, next_action}`. `task_id`, rule trails, states,
  scores, engine, and latency belong to a separate `RunResult`/diagnostics object and must never
  leak into submission JSONL.
- DeepSeek model name is configuration, not a guessed constant. Before the first authorized live
  call, query/verify the available model and run one schema smoke test. Use `json_object`, a tiny
  schema and temperature 0. Make at most one model request per record and use the validated template
  on failure; disable SDK retries. Share a deadline bounded by the record's latency threshold
  (2,000 ms in both samples), including validation and serialization.
- Deterministic checks grade exact fields and constraints. A pointwise judge is optional and only
  grades tone; it cannot gate correctness with this sample size. Report Wilson intervals for rates.
- Keep `expected` in the evaluator only. Derive a versioned policy and templates from the supplied
  examples before evaluation, then strip any held-out record's `expected` before calling the engine.
  Test that deleting or changing `expected` does not change the engine's answer.

## Rules for every task

- `casestudy/` imports nothing from `chatbot/` and reads nothing under `propertystack/data/`; its
  container copies only `casestudy/`.
- Do not touch AI Visibility or alter existing site behavior.
- Each task ends with its named check, one focused commit, and a short addition to
  `casestudy/DECISION-LOG.md`.
- Do not push. Stop at ready-to-push and let Drew authorize production deployment.

Check: `python3 -m pytest -q casestudy/tests`

## Tasks

- [x] **C0 Freeze the contract and reference tests.** Parse both sample lines and snapshot only their
  `expected` blocks. Define `AssignmentAnswer`, `NextMessage`, CTA variants (`options` or `link`),
  and next-action variants (`name`, `value`, or `reason` as applicable). Reject extra public keys.
  Assert structure, nulls, enum values, CTA payloads, next actions and supplied timestamps exactly;
  grade prose with a reference-derived checklist for meaning, personalization and constraints.
  Identical body wording is optional template regression coverage, not the assignment's requirement.
  Check: both expected blocks round-trip and harmless paraphrases pass while wrong facts fail.

- [x] **C1 Input normalization and the five gates.** Normalize missing fields without crashing, but
  never invent consent or claim an unknown required state passed. Process opt-out intent before
  early exits for missing consent/lifecycle so STOP still produces `mark_opted_out`; then enforce
  consent, lifecycle/do-not-contact, frequency, and invalid/past dates or timezone. Never bypass
  later validation for HELP or an option reply; a numeric reply needs supplied prior options and
  creates a proposed follow-up, not a booked appointment.
  Each result carries status, reason, citation, and confidence label. Unknown `required_states`
  cause a visible unsupported-state failure; known states are marked passed only by the named check.
  Tests cover STOP with consent already false, HELP/1/2/questions, missing prior options, malformed
  input, and both samples passing. Missing clocks or invalid zones escalate; historical sample
  dates must be evaluated using the input/reference clock, never today's server date.

- [x] **C2 Channel and send-time inference.** Select the first preferred consented channel; voice
  proposes a call task rather than an automated message. Use explicit schedule/cadence fields if
  supplied. Otherwise use this versioned, disclosed hypothesis for the sample cadence form: parse a final
  `dayN` token from `task_id`, set the due date to interaction-local date + N, and use the observed
  channel slot (SMS 09:00, email 10:00). If that wall-clock candidate is not strictly after the
  interaction, advance to the next permitted day. Use `zoneinfo`, numeric offsets, and a conservative
  09:00-20:00 Mon-Sat / 12:00-20:00 Sunday demo window, labeled as a project default, not a verified
  national legal rule. Compute the day's permitted slot before comparing it with the reference
  time, so Sunday 10:00 can yield Sunday 12:00. If `dayN` is absent, use the earliest eligible slot
  and flag uncertainty. Do not claim the suffix proves an elapsed cadence delay.
  Tests: both exact sample timestamps, same-day pre-slot, post-slot, Sunday, Phoenix, Los Angeles,
  DST boundary, malformed timezone, and `day10` (do not parse only one digit).

- [x] **C3 Intent, horizon, CTA, and next action.** Explicit business fields outrank identifier hints.
  Use recognized `welcome`, `short_horizon`, `long_horizon`, and `dayN` tokens only as fallbacks with
  hypothesis labels; opaque IDs must still work. Without a horizon token, short <=45 days and long
  >45 days is a provisional two-tier fallback, not a learned boundary; do not invent a
  medium tier. Map `book_tour` to `schedule_tour`. SMS tour CTA uses two day options; email uses the
  explicit input link or a property-specific link learned from the supplied example; never invent a
  URL for an unseen property. If no safe link exists, emit a visible unresolved-link diagnostic and
  use a reply-to-arrange-tour fallback with `cta:{type:"schedule_tour"}` and an uncertainty warning.
  The observed new-prospect welcome starts the named cadence; the observed open long-horizon flow
  follows up in 3 days. Use 3 as the provisional interval for that flow, not the arbitrary dayN suffix:
  day10 does not imply waiting another 10 days. Tests assert both expected CTA/actions, an opaque ID,
  and conflicting ID versus explicit fields.

- [x] **C4 Channel-specific validators.** SMS: null subject, trailing STOP sentence, applicable
  one-question/numbered-options style, no unsafe profile leakage, and segment count. Email: non-null
  accurate subject, link CTA when expected, and conspicuous click-or-STOP opt-out. Do **not** require
  a postal address to pass the supplied simulation example, which omits it; explicitly mark actual
  email-delivery compliance as unverified and out of scope. Do not assume a transport adds a footer
  when no such transport exists. Do not classify all money or all street
  addresses as PII; block unapproved profile-field echoing and allow required property/business data
  by context. Fair-housing HARD/WARN entries retain citation and rewrite. Tests prove the email sample
  passes, unsafe profile data is ignored, and a model draft cannot override a hard failure.

- [x] **C5 Offline templates.** Start with templates that satisfy both reference checklists, then
  add the smallest set needed for tested intents/channels. The email template must use amenity
  interests and a natural move-month phrase; its Oak Ridge URL comes from the supplied training
  example rather than a fabricated property slug. SMS keeps literal STOP. Every template passes C4.
  Preserve provenance for property facts learned from a supplied example; never generalize Oak Ridge's
  hours/link to another property. Missing unsafe or optional fields degrades to a neutral template,
  never a crash. Check: offline generation passes both references and all template validator tests.

- [ ] **C6 Bounded writer.** Use the OpenAI-compatible DeepSeek endpoint with a configurable,
  preflight-verified model. Stable prompt prefix, record last, `json_object`, temperature 0,
  Pydantic validation, and a small output limit that has been smoke-tested against truncation/empty
  content. Enforce one monotonic end-to-end deadline and no SDK/model retries; reserve time for
  template validation and serialization. Tests monkeypatch timeout, empty content, invalid JSON,
  wrong CTA shape, unsafe draft, exhausted budget, and successful draft; no test calls the network.

- [ ] **C7 Assemble one record and batch JSONL.** The public submission path emits one
  `AssignmentAnswer` per input line with no diagnostic keys. A separate diagnostics path carries
  `task_id`, `why[{rule, plain_english, citation, confidence}]`, verified states, reply class,
  personalization evidence, engine, errors, and latency. Malformed records yield a structured
  diagnostic and a safe public answer rather than aborting the batch. CLI supports `--offline`,
  `--submission-out`, and `--diagnostics-out`. Check: both reference outputs pass structure/meaning
  checks, `expected` cannot influence inference, and a 12-line batch exports 12 ordered lines.

- [ ] **C8 Adversarial practice data.** Keep the two goldens separate and add at least 16 focused
  records: email-only consent; none; preference ordering; before/after slot; day3/day10; Phoenix;
  Los Angeles DST; weekend; Spanish; renewal; transactional note without SMS consent; STOP; option
  reply; protected-class profile; PII profile; past/missing move date; voice-only. Each fixture names
  one primary rule and has expected structure plus a prose checklist. Add a separate balanced reply corpus with
  capitalization, punctuation, synonyms, and ambiguous questions; do not pretend one STOP example
  establishes F1 >= .90. Check: all fixtures pass offline.

- [ ] **C9 Evaluate every assignment field.** For each record, report every `required_state`, every
  constraint, the record's `personalization_score_min`, `reply_classification_f1_min`,
  `p95_latency_ms`, and `safety_violations_max`; no field may be silently ignored. Personalization
  evidence is safe-field coverage relevant to that message (including amenities/move timing when
  used), and below-threshold drafts fall back and are rechecked; if still below, report failure rather
  than claiming success. Label this score a project-defined proxy: the employer's formula is unknown.
  Report a labeled
  multiclass confusion matrix and macro-F1 for the balanced reply corpus. Measure warm end-to-end
  p95 over >=100 offline runs and, only when authorized, a clearly separate live-model sample;
  count fallbacks and failures. F1/p95 are corpus/run metrics, not measurements from a single answer;
  show their dataset/sample count and use `not_measured` when evidence is absent. Emit structural
  match, meaning-check results, Wilson intervals only for binary pass fractions, and an honest
  proven-vs-estimated note (synthetic cases do not estimate real-world reliability). Reuse shipcheck's
  `checks/chatbot/claude_judge.py` and `scripts/grade_server.py` from `/home/drewp/main-projects/drew's eval`
  for the planned optional tone/human grading; retain this choice, and label unavailable judge runs
  `not_run`. The tone judge is non-gating and uncalibrated; it is never a deployed server backend.

- [ ] **C10 Build the demo page.** Full-width Case study page behind existing sign-in; paste/upload
  arbitrary JSONL. Left side shows only the exact export object; right side shows diagnostics and a
  row for every assertion/threshold, including unsupported ones. Copy one, Copy all, and Download
  must serialize the same submission bytes as the CLI. Show engine, latency, fallback/offline state,
  and per-record error without losing the other records. Check in a browser with 1, 2, 12, malformed,
  and offline inputs; verify clipboard/download by reparsing the bytes.

- [ ] **C11 Container and local production wiring.** Non-root slim image, `tzdata`, health endpoint,
  request-size/batch-size limits, no secrets in logs, and only `casestudy/` copied. Wire
  `/case-study*` and navigation locally behind existing auth; document Railway service/start command
  and `DEEPSEEK_API_KEY`. Prove health, auth redirect, 12-record request, restart, missing-key offline
  fallback, and inability to read `propertystack/data/`. Run existing site checks. Stop and tell Drew
  it is ready to push; production verification is a separate, authorized step.

- [ ] **C12 Under the Hood.** Use `DECISION-LOG.md` to show the observed-vs-assumed distinction,
  reversed decisions, rules and legal sources, deterministic/LLM boundary, exact-match and threshold
  results, median/p95, offline fallback, sample-size caveat, and honest unhandled list. Before publishing
  a legal or engineering claim, verify its primary citation and scope: the existing research conflicts
  on Texas statute numbers and Sunday rules. Hypotheses cite the sample/decision, not a law. Keep existing
  shipcheck/build-bot links. Check every citation link and never claim a synthetic practice score is
  hold-out performance.

- [ ] **C13 Dress rehearsal and recovery card.** Run both goldens and a 12-record batch through the
  local live-style stack; export and parse it; repeat offline and with a malformed middle record.
  Record commands and actual results in `PLAN-casestudy-bot.progress.md`. Write the README and a
  one-page interview card: 3-minute explanation, how to paste/export the live 12, switch offline,
  restart the service, and find the saved download. Check the full rehearsal twice. Do not push.

## Deadline cut order

Non-negotiable: C0-C9, the paste/export/offline/error parts of C10, local container/auth proof in C11,
and the C13 recovery card. If time runs short, cut live LLM judging first, then decorative UI, broad
intent/template coverage beyond observed + practice cases, and finally the expanded Under the Hood
narrative. Do not cut reference structure/meaning tests, threshold reporting, offline fallback, or
export verification. Restore the full live-site acceptance after Drew's deployment authorization.
