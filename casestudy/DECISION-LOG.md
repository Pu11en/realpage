# How the case-study bot was planned

These decisions were made on September 17, 2026, in the order shown. The interview was the next
day, so the team deliberately favored a small, explainable system that could fail safely over a
larger or more impressive-looking one.

This is a historical record, not the active specification: entries 26-28 revise earlier assumptions.
Read `PLAN-casestudy-bot.md` for the current implementation requirements.

## 1. Drop the long planning process

**Decided:** Do a short, bounded planning pass and build from small tasks; do not use the proposed
Wayfinder-style process. **Alternatives:** map every open question first, or start building at once.
**Why it won:** Drew revealed that the interview was the next day, turning planning ceremony into a
delivery risk. **Source:** Drew's call after confirming the September 18 deadline.

## 2. Build the skill the assignment actually tests

**Decided:** Center the project on safe decisions under rules, plus visible proof that those rules
worked. **Alternatives:** emphasize a conversational demo or polished copy alone. **Why it won:** the
hold-out set, required states, safety threshold, latency limit and reasons for decisions all reward
reliable judgment more than chatbot theater. **Source:** the RealPage problem statement and sample.

## 3. Put the rule trail beside every answer

**Decided:** Show both the clean answer the interviewer can export and a plain-English trail of the
rules that fired. **Alternatives:** return only the graded JSON, or hide the explanation in logs.
**Why it won:** the exact output stays easy to copy while the second panel makes consent, timing and
safety decisions inspectable during the walkthrough. **Source:** Drew's call.

## 4. Make it part of CraneSignal, but isolate it

**Decided:** Present the bot through a full-screen **Case study** tab in CraneSignal, backed by its
own service, container and data directory and sharing only the existing sign-in. **Alternatives:** a
separate throwaway app, or code inside the existing chat service. **Why it won:** Drew wanted a real
product surface, while isolation prevents case-study failures or data from affecting the live chat
or property data. **Source:** Drew's call; the boundary is documented in commit `ad1cbba`.

## 5. Reuse the existing evaluation workflow

**Decided:** Reuse shipcheck's deterministic checks, local tone judge and keyboard human-grading
screen. **Alternatives:** build a new evaluator, install a separate evaluation platform, or fine-tune
a model. **Why it won:** this is an evaluation-and-revision loop, not model retraining, and the proven
tools already cover machine-checkable facts plus human review. **Source:** Drew's call; Hamel Husain,
[Evals FAQ](https://hamel.dev/blog/posts/evals-faq/).

## 6. Use a batch tool, not a chat interface

**Decided:** Use a paste/upload box, a Run button, answer cards, Copy All and Download; the same page
accepts one record or twelve. **Alternatives:** a chat transcript, or separate single-record and batch
screens. **Why it won:** the assignment explicitly requires exporting or copy-pasting 12 outputs,
and one batch-capable tool also handles records delivered one at a time. **Source:** the RealPage
interview instructions; Drew's call after reviewing the proposed screen.

## 7. No implementation until the plan is understood

**Decided:** Stop the first attempted build, continue one decision at a time, and have an independent
review before writing app code. **Alternatives:** let the automated build loop continue from the
first nine-step plan. **Why it won:** Drew could not yet explain the plan and explicitly required a
complete mental model before authorizing implementation. No app code had been written when the loop
was stopped. **Source:** Drew's call.

## 8. Choose DeepSeek and require an offline answer

**Decided:** Use the existing DeepSeek API key for wording, with a deterministic template fallback
that works without a network. **Alternatives:** power the deployed app with Claude Code or Codex
subscriptions, buy Anthropic API credit, or omit the fallback. **Why it won:** coding subscriptions
were rejected as a deployed server backend; DeepSeek was already available, and Drew selected the
offline-safe option so the live demo cannot freeze on an API failure. **Source:** Drew's call after
the backend investigation; DeepSeek's [JSON Output guide](https://api-docs.deepseek.com/guides/json_mode/).

## 9. Derive timing from the example, not from a guess

**Decided:** Schedule the next eligible 9:00 a.m. in the recipient's local time; if 9:00 has not
passed, use the same day. Preserve the local numeric UTC offset. **Alternatives:** always schedule the
next day, use UTC, or hard-code one offset. **Why it won:** the sample's last interaction was 9:04
a.m. Chicago time, which explains the next-day answer and exposes the likely same-day and daylight-
saving hold-out traps. **Source:** the RealPage sample; Python `zoneinfo` engineering guidance.

## 10. Derive tour choices from the example

**Decided:** Offer exactly two weekdays at least two days after the send date, staying in the same
week when possible and using numbered replies. **Alternatives:** treat Thursday and Friday as fixed,
offer the next two calendar days, or let the model invent choices. **Why it won:** this is the smallest
rule that explains Tuesday's expected Thursday/Friday options and the `Reply 1` / `Reply 2` pattern.
**Source:** the RealPage sample; this remains an explicit inference to validate against hold-outs.

## 11. Use an ordered rulebook in plain Python

**Decided:** Run five stop gates before six message-shaping steps, each adding an auditable reason.
**Alternatives:** put all rules in the prompt or adopt a general-purpose rules engine. **Why it won:**
the path is short and ordered; plain functions are easier to test, faster to run and naturally
produce the rule trail. Existing rule-engine packages added machinery without solving a project
need. **Source:** the open-source review in `OPENSOURCE-research.md`; Anthropic,
[Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents).

## 12. Make consent a fail-closed gate

**Decided:** Use only a channel with explicit opt-in; missing consent means no consent, and channel
preference never creates permission. **Alternatives:** infer permission from preferences or treat
some message types as exceptions. **Why it won:** this makes the safest interpretation deterministic
and prevents the model from talking itself into sending. **Source:** TCPA, 47 U.S.C. §227 and
47 CFR §64.1200(a)(2).

## 13. Enforce contact windows with local-time code

**Decided:** Compute quiet hours in the recipient's IANA time zone, using the stricter planned window
of 9:00 a.m.–8:00 p.m. Monday–Saturday and noon–8:00 p.m. Sunday. Invalid time zones stop for human
review rather than silently defaulting. **Alternatives:** use only the federal window, use server
time, or let the model choose a time. **Why it won:** one deterministic national policy is safer for
a live demo and handles state and daylight-saving traps. **Source:** 47 CFR §64.1200(c)(1), Texas
Bus. & Com. Code §301.051, and the state-hours research recorded in `RULEBOOK-research.md`.

**C12 scope correction:** Texas §301.051 covers defined consumer telephone calls and contains
express-request and prior-relationship exceptions; it does not expressly make this window an SMS
rule. The narrower 09:00–20:00 Monday–Saturday and 12:00–20:00 Sunday window is therefore a
conservative project default inspired by federal and Texas call rules, not a universal legal claim.

## 14. Treat opt-outs and inbound replies as decisions, not prose

**Decided:** Recognize STOP-family keywords as an immediate no-send/mark-opted-out result; classify
numbered choices, negative replies and questions into explicit follow-up actions. **Alternatives:**
send a polite farewell, or ask the LLM to interpret every reply. **Why it won:** STOP must not produce
another marketing message, and a deterministic classifier makes the assignment's F1 threshold
measurable. **Source:** FCC revocation rule, 47 CFR §64.1200(a)(10), effective April 11, 2025; CTIA
Messaging Principles.

## 15. Keep compliance out of generated wording

**Decided:** Never generate protected-class or sensitive personal details into marketing copy; scan
every draft and fall back to a known-safe template if it fails. Email also requires a subject,
unsubscribe mechanism and physical postal address. **Alternatives:** trust the prompt, redact only
after display, or use a large privacy package. **Why it won:** compliance must hold even when the
input contains children, disability, religion, income or location cues. **Source:** Fair Housing Act,
42 U.S.C. §3604(c); CAN-SPAM, 15 U.S.C. §7704; Zillow's
[Fair Housing Classifier](https://www.zillowgroup.com/news/zillows-fair-housing-classifier/).

## 16. Reuse small components, not whole frameworks

**Decided:** Use `sms-toolkit` for segment counting, `zoneinfo`/`tzdata` for offsets, and optionally
`phonenumbers` only when a record lacks a time zone; vendor small reviewed phrase tables and regexes.
**Alternatives:** Presidio, Guardrails AI, NeMo Guardrails, a JavaScript TCPA package, or a full rules
engine. **Why it won:** the selected pieces are narrow, inspectable and feasible before the deadline;
the larger frameworks add dependencies and setup without improving the core decisions. **Source:**
the repository and license review in `OPENSOURCE-research.md`.

## 17. Use a fixed workflow with one structured model call

**Decided:** Let ordinary code decide whether, when and how to contact; make at most one bounded LLM
step for wording rather than running an autonomous agent loop. **Alternatives:** a multi-step agent or
a model-only pipeline. **Why it won:** the route is known in advance, and an agent loop adds latency,
cost and new failure modes without adding useful judgment. **Source:** Anthropic,
[Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents/).

## 18. Keep the model's instruction load small

**Decided:** Put only a handful of wording constraints and one example in the prompt; keep the full
compliance policy in testable code. **Alternatives:** paste the entire rulebook into the system
prompt. **Why it won:** instruction-following degrades as simultaneous constraints accumulate, so a
legal guarantee cannot depend on model attention. **Source:** IFScale, arXiv 2507.11538; the bounded-
constraint findings summarized in `STATE-OF-THE-ART-research.md`.

## 19. Validate, retry once, then use the template

**Decided:** Ask DeepSeek for a small JSON object, validate it with Pydantic, retry once with the
specific error, re-check the resulting body against every hard rule, then fall back to the template.
**Alternatives:** prompt-only JSON, unlimited repair attempts, or displaying the first draft.
**Why it won:** DeepSeek JSON mode can return malformed or empty content, while bounded repair keeps
latency predictable and the post-check makes code the final authority. **Source:** DeepSeek's
[JSON Output guide](https://api-docs.deepseek.com/guides/json_mode/) and the
[Instructor DeepSeek integration](https://python.useinstructor.com/integrations/deepseek/).

## 20. Skip the model on deterministic branches

**Decided:** No-consent, opted-out, suppressed and other fully determined cases return without an
LLM call; model calls have a 1.2-second deadline inside a 2-second total budget. **Alternatives:** call
the model for every record or stream text before validation. **Why it won:** skipping needless calls
is the largest latency improvement and avoids exposing unvalidated words during the demo. **Source:**
Anthropic's routing guidance in *Building Effective Agents*; the assignment's `p95_latency_ms: 2000`.

## 21. Grade facts with code and tone with a judge

**Decided:** Use exact assertions for channel, time, opt-out, forbidden language, output shape and
latency; use a pointwise binary LLM judge only for whether the wording sounds like a leasing agent,
plus Drew's 1/2 human review. **Alternatives:** one overall AI score, a five-point scale, or human-
grade every property. **Why it won:** deterministic facts do not need subjective judgment, and binary
tone labels are easier to apply consistently. **Source:** Hamel Husain,
[Evals FAQ](https://hamel.dev/blog/posts/evals-faq/); Braintrust,
[What is LLM-as-a-judge?](https://www.braintrust.dev/articles/what-is-llm-as-a-judge).

## 22. Use checklists, not semantic similarity, for expected messages

**Decided:** Turn each expected message into three to six yes/no requirements; log embedding
similarity only as non-gating context. **Alternatives:** require exact wording or gate on cosine/
BERTScore similarity. **Why it won:** similarity can rate messages with the wrong number, date or
entity as close, while the assignment asks for a semantic match whose critical facts are known.
**Source:** Check-Eval, arXiv 2407.14467; RocketEval, arXiv 2503.05142.

## 23. Build 12 targeted practice cases, but make a modest claim

**Decided:** Cover distinct failure modes—consent, channel preference, local time/DST, weekends,
Spanish, renewal, transactional-message consent, STOP and protected-class data—and report which
named rules pass. **Alternatives:** clone the one sample, generate many shallow examples, or claim a
general success rate from 12 tests. **Why it won:** a small set is useful for branch coverage but too
small to estimate production reliability; even 12/12 has a Wilson lower bound near 74%.
**Source:** Bowyer et al., *Don't Use the CLT in LLM Evals With Fewer Than a Few Hundred Datapoints*,
ICML 2025, arXiv 2503.01747.

## 24. Put a source on every visible rule and design choice

**Decided:** Each answer's explanation cites the relevant law, and Under the Hood cites the paper or
engineering guidance behind each architecture and evaluation choice. **Alternatives:** citations only
in developer notes, or only one bibliography on the proof page. **Why it won:** the interviewer can
distinguish requirements, researched evidence and team judgment at the point each claim is made.
**Source:** Drew's call.

## 25. Preserve reversals and invite an adversarial review

**Decided:** Record abandoned paths and have a separate Astra review re-derive the rules, challenge
the plan and fix holes before implementation. **Alternatives:** present a cleaned-up story with no
dead ends, or let the planning model review its own work. **Why it won:** the Wayfinder reversal,
subscription-backend rejection and stopped premature build show real tradeoffs; a second model reduces
shared blind spots. **Source:** Drew's call; commits `b4f14c8`, `d8bf0a3`, `43e9643`, and `7866be5`.

## 26. Promote both supplied examples over the first-example rulebook

**Decided:** Make both `sample.jsonl` records exact golden tests, keep exported answers limited to
the `expected` shape, and label every added rule as observed, input-required, or a conservative
default. **Alternatives:** continue treating the first SMS as the only example and add audit fields
to the exported answer. **Why it won:** the overlooked email example directly disproves the universal
9:00 slot, medium-horizon boundary, options-only CTA, and cadence-name-only action; it instead shows
10:00 email timing, link CTAs, amenity/move-date personalization, and `follow_up_in_days`. **Source:**
the independent Astra review in `REVIEW-astra.md` and both supplied expected blocks; Drew's request to
find and fix the plan's holes.

## 27. Correct the review before handing it to builders

**Decided:** Check message meaning instead of requiring identical prose, label the timing/horizon
formula as uncertain, and prevent expected answers from entering live inference. **Alternatives:**
accept the first review unchanged or start another broad planning process. **Why it won:** the
assignment says "semantically matches," and two examples cannot identify a universal schedule;
the review itself needed correction. Shipcheck reuse and live-site acceptance remain in scope.
**Source:** problem statement, both sample records, and parent self-review after Drew asked to inspect
each change; implementation remains pending that walkthrough.

## 28. Return the review to the original building session

**Decided:** Finish the second opinion and return to the original session to build, test a working
preview with Drew, and iterate. **Alternatives:** continue a mandatory item-by-item review here or
start a competing implementation in this session. **Why it won:** Drew clarified which session owns
the build and wants to learn from the working result. DeepSeek V4 Flash remains his intended app
model; Astra Advisor's coding-helper cost notes do not concern that API. **Source:** Drew's latest
instruction in this review session; exact provider model identifier remains to be checked at setup.

## 29. Freeze the public contract as its own module, separate from diagnostics

**Decided:** Define `AssignmentAnswer` (`next_message`, `next_action`) in `casestudy/contract.py`
with `extra="forbid"` on every nested model, and prove both reference `expected` blocks round-trip
through it before writing any inference logic. **Alternatives:** infer the shape ad hoc from each
task's code as it's written, or bundle diagnostics fields (task_id, scores, engine, latency) into
the same model behind optional fields. **Why it won:** the plan requires the public export to never
leak internal keys, so forbidding extras at the model level catches that mistake at every later task
automatically instead of relying on manual review each time. A small reference-derived semantic
checklist (paraphrase-tolerant, wrong-facts-rejecting) was added alongside the structural test so
later tasks have a pattern to extend rather than grading prose by exact string match.
**Source:** `PLAN-casestudy-bot.md` task C0 and both records in `casestudy/data/sample.jsonl`.

## 30. Gates are ordered reply → consent → lifecycle → frequency → dates, with labeled confidence

**Decided:** `casestudy/gates.py` normalizes any input without crashing, classifies an inbound
reply first (so STOP yields `mark_opted_out` even when consent is already false), then enforces
consent, lifecycle/do-not-contact, frequency, and date/timezone validity. Every `GateResult`
carries status, reason, citation, and one of `observed` / `input_required` / `hypothesis` /
`conservative_default`. Unknown `required_states` are emitted as `unsupported`, never passed;
`consent_verified` is the only state this module verifies (fair-housing and brand-style belong to
C4). Consent is only ever an explicit `true`; missing or non-boolean values are unknown and never
count. A numeric reply requires supplied prior options and produces `propose_follow_up`, not a
booking. The reference clock is `input.reference_time` or `input.last_interaction`, never the
server date. Frequency caps (24 h / 3 per day) are project defaults, not learned rules.
**Alternatives:** consent first (would swallow STOP), treat missing consent as true, treat unknown
states as passed, use `datetime.now()`. **Why it won:** PLAN C1 and REVIEW-astra's stop-order
correction; two examples cannot justify inventing consent or state passes. Terminal decisions do
not yet map to the public contract (`next_message` is non-nullable there); C7 decides that shape.
**Source:** `PLAN-casestudy-bot.md` C1, `REVIEW-astra.md`, `RULEBOOK-research.md` §3 (as hypotheses).

## 31. Send time = interaction-local date + `dayN`, at the channel slot, clamped to the window first

**Decided:** `casestudy/schedule.py` picks the first preferred channel with explicit consent
(voice yields a human call task, never an automated message). Send time (`send_time_v1`): an
explicit `input.send_at` or cadence field wins; otherwise the final `dayN` token of `task_id`
(all digits, so `day10` is 10) is the delay; due date = interaction-local date + N at the observed
slot (SMS 09:00, email 10:00); the slot is clamped into the day's window (09:00-20:00 Mon-Sat,
12:00-20:00 Sunday) *before* comparing with the interaction, and if the candidate is not strictly
after the interaction it advances one day. No token and no field means N=0 with a visible
uncertainty flag. This reproduces both sample timestamps (Dec 8 09:04 local + day0 → Dec 9 09:00;
Dec 6 05:30 local + day3 → Dec 9 10:00). Offsets come from `zoneinfo` on the send date, so DST
and Phoenix behave. **Alternatives:** a shared Dec 9 evaluation clock; parsing one digit; treating
the token as proof of elapsed cadence time. **Why it won:** it is the simplest rule that explains
both observations, and PLAN C2 requires it disclosed as a hypothesis. The window is a project
default, not a verified national legal rule; the token is an identifier hint, not a business field.
**Source:** `PLAN-casestudy-bot.md` C2, both records in `casestudy/data/sample.jsonl`.

## 32. Intent, horizon, CTA, and next action: explicit fields > identifier tokens > computed fallback

**Decided:** `casestudy/intent.py` (`intent_v1`). Flow: an explicit `input.intent`/`flow` wins;
otherwise lifecycle `new` is the welcome flow and `open` is the follow-up flow (both observed); a
`welcome` token in `task_id` is only a hypothesis fallback. Horizon: explicit `input.horizon`,
else a `short_horizon`/`long_horizon` token (hypothesis), else a provisional two-tier fallback
(<=45 days to move short, >45 long, configurable, no medium tier), else short with an uncertainty
flag. Record 1's id has no horizon token, so its short horizon comes from the 33-day fallback.
`primary_cta: book_tour` maps to `schedule_tour`. SMS CTA = the 2nd and 3rd non-Sunday days after
the send date (observed Tue -> Thu, Fri). Email CTA = an explicit input link, else the Oak Ridge
link learned from record 2 with provenance recorded; an unseen property gets no invented URL but a
bare `{type: schedule_tour}` reply fallback plus a visible `unresolved_link` diagnostic. The public
contract gained that bare CTA variant for this case only. Next action: welcome starts
`prospect_welcome_<horizon>_horizon` (observed for short; the long name is a hypothesis); the open
flow returns `follow_up_in_days: 3` as a provisional interval, never the `dayN` suffix (day10 still
yields 3); an option reply proposes a 3-day follow-up, not a booking; STOP yields `mark_opted_out`.
**Alternatives:** trusting the task_id over fields; a 120-day or medium tier; deriving the follow-up
interval from dayN; inventing `https://<slug>.example/tour` for unknown properties.
**Why it won:** PLAN C3 and REVIEW-astra: identifier tokens are hints, the two records prove no
boundary, and a fabricated URL is worse than a visible gap.
**Source:** `PLAN-casestudy-bot.md` C3, both records in `casestudy/data/sample.jsonl`.

## 33. Channel-specific validators: hard rules in Python, no imaginary email footer

**Decided:** `casestudy/validators.py` (`validators_v1`) validates any draft, template or model,
with the same deterministic rules; `select_draft()` returns the first candidate with no HARD
failure, so a model draft can never override a hard rule. SMS: subject must be null, body must end
with the literal `Reply STOP to opt out.`, CTA options must appear as numbered replies, at most one
question, and at most 3 segments (GSM-7/UCS-2 counted; the observed em dash makes the sample body
3 UCS-2 segments). Email: non-null subject that names the property or shares words with the body,
CTA link present in the body, and a conspicuous click-or-STOP opt-out sentence. No postal address
is required: the supplied simulation example has none and no transport exists to append one, so
`email_delivery_compliance` is reported as unverified and out of scope, never passed or assumed.
Profile echo: only `first_name` and `amenity_interest` may be echoed; any other profile value found
literally in the copy is a HARD `no_pii_leak` failure, and emails/phones/SSNs are hard unless they
are supplied business contact data. Money and street addresses are not PII by themselves; they are
allowed when they come from property/business fields and blocked only when they come from the
profile. Fair housing is a lexicon with HARD entries (explicit protected-class preference/limitation
or obvious proxy) and WARN entries (coded language); every hit carries the 42 U.S.C. §3604(c)
citation and a rewrite; only HARD blocks `fair_housing_check_passed`. Brand style (greeting, <=1 "!",
no emoji, no shouting, no URL shorteners) is what `brand_style_applied` means here, labelled a
hypothesis from two examples. **Alternatives:** the old rulebook's CAN-SPAM address requirement plus
a generic street-address PII regex (self-contradictory), banning all `$` amounts, a model-based
fair-housing judge. **Why it won:** PLAN C4 and REVIEW-astra: the email sample must pass as
supplied, and a rule the model can talk its way past is not a compliance rule.
**Source:** `PLAN-casestudy-bot.md` C4, `REVIEW-astra.md`, `RULEBOOK-research.md` §2 (citations).

## 34. Offline templates: reference-shaped first, compact GSM-7 fallback, learned facts never generalized

**Decided:** `casestudy/templates.py` (`templates_v1`) renders a small ordered set of templates
(SMS and email × welcome / open follow-up / option reply, email with or without a link) and runs
every candidate through the C4 validators via `select_draft()`, so no template can be emitted
unvalidated. The SMS welcome template reproduces record 1's body byte-for-byte (optional
regression, not a requirement); the email template uses the amenity interests and a natural
move-month phrase ("mid-February" for Feb 15; early <= 10, mid 11-20, late > 20 is a hypothesis)
and takes its Oak Ridge URL from the C3 learned-link table, never a fabricated slug. Property
facts learned from the supplied example (short name "Oak Ridge", the "24/7 fitness center"
detail, the tour link) are keyed to the exact property name with provenance and are not applied
to any other property; another property gets a generic display name (suffix stripping is a
hypothesis) and generic amenity names. SMS keeps the literal `Reply STOP to opt out.`. Because
the observed em dash forces UCS-2 encoding, long names can push the reference-shaped SMS past the
3-segment cap; a compact ASCII variant without the em dash is tried second and passes. Missing
first name, property name, move date, or amenities degrade to neutral wording ("Hi there",
"our community", "floor plans and amenities"); templates read only `first_name` and
`amenity_interest` from the profile, so unsafe fields cannot leak by construction. Voice/call
tasks and terminal gate decisions produce no draft, with a cited `skipped` trail entry.
**Alternatives:** one template per record with hard-coded Oak Ridge wording; model-only drafting;
a single long SMS template that fails the segment cap for long names.
**Why it won:** PLAN C5: pass both reference checklists, add the smallest tested set, preserve
provenance, degrade instead of crash.
**Source:** `PLAN-casestudy-bot.md` C5, both records in `casestudy/data/sample.jsonl`,
decision 33 (validators).

## 35. Bounded writer: one verified model request per record, template on every failure path

**Decided:** `casestudy/writer.py` (`writer_v1`) makes at most one structured DeepSeek request per
record through the OpenAI-compatible endpoint. The API key, base URL and model name are
configuration (`DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL`, `CASESTUDY_OFFLINE`);
no model name is guessed in code, and the configured model is preflight-verified against the
endpoint's model list (cached) before any request. The SDK client is built with `max_retries=0`
and the writer never re-asks. The prompt is a stable system prefix with the record last, sent with
`json_object`, temperature 0 and `max_tokens=400`; only approved profile fields (first name,
amenity interest) and business input reach the model. A monotonic per-record deadline is bounded
by the record's `p95_latency_ms` threshold and a 2,000 ms project ceiling, with 250 ms reserved for
validation and serialization: too little budget skips the call, and a reply after the deadline is
discarded. Model JSON is validated by Pydantic with extra keys forbidden, the CTA must equal the
deterministic intent CTA, `finish_reason == "length"` is treated as truncation, and the draft is
then run through the C4 validators as `source="model"`. Every failure path (offline, missing
config, unverified model, exhausted budget, timeout, empty content, truncation, invalid JSON, bad
schema, changed CTA, unsafe draft, late reply) returns the already-validated C5 template with a
cited `writer.fallback` trail entry and the engine label `template`.
**Alternatives:** a hard-coded model constant; SDK retries; letting the model choose the CTA or
next action; a parse-and-repair loop on bad JSON; calling the model even for terminal decisions.
**Why it won:** PLAN C6 and the architecture section: configurable, preflight-verified model, one
request per record, shared deadline, deterministic validation that a model draft cannot override.
**Open:** the 400-token output limit has been tested against truncation and empty content only
with a fake client; the live smoke test needs Drew's authorization and happens in C11/C13.
**Source:** `PLAN-casestudy-bot.md` C6 and architecture, decision 33 (validators), decision 34
(templates), IFScale arXiv 2507.11538.

## 36. Assembly and JSONL: one public serializer, diagnostics kept separate, bad records contained

**Decided:** `casestudy/pipeline.py` (`pipeline_v1`) is the sole orchestration layer for one record
and a JSONL batch. It defensively removes `expected` before any inference, runs the C1-C6 stages,
and validates the final public object as `AssignmentAnswer`. `submission_line()` is the one compact
UTF-8 serializer for library, CLI, and later page/download use. The public stream contains exactly
`next_message` and `next_action`; a separate diagnostics stream contains task ID, cited `why`
entries, verified and unsupported states, reply class, personalization evidence, engine, errors,
latency, fallback reason, and component versions. A malformed JSON line, non-object record, or
unexpected per-record exception cannot stop the batch: it produces `next_message: null` and a
reason-bearing `escalate` action plus a structured diagnostic. Deterministic no-send outcomes use
the same nullable message shape with `suppress`, `escalate`, or `create_call_task`; STOP uses the
existing `mark_opted_out` action. These no-message variants are conservative project-defined
extensions because neither supplied example demonstrates a no-send public answer. The CLI reads a
file or stdin and supports `--offline`, `--submission-out`, and `--diagnostics-out`; offline mode
constructs no model client. **Alternatives:** aborting the batch on bad JSON; mixing diagnostics
into submission objects; exposing a fabricated message for suppression/escalation; separate CLI
and library serializers that could drift. **Why it won:** PLAN C7 requires ordered one-answer-per-
record export, exact public-key isolation, visible diagnostics, safe malformed-record handling, and
proof that `expected` cannot influence inference.
**Source:** `PLAN-casestudy-bot.md` C7 and architecture; both records in
`casestudy/data/sample.jsonl`.

**Review correction:** Diagnostics now derive personalization evidence from the final public
message, merge the final validator report's verified states with gate states, and expose that
validator's cited results in `why`. Blank and whitespace-only JSONL lines produce safe escalation
answers and retain their physical line numbers, so later parse errors are never misnumbered.

## 37. Practice data: evaluator-owned expectations and a balanced reply corpus

**Decided:** The two supplied records remain untouched in `sample.jsonl`. Twenty focused inputs
live separately in `practice.jsonl`, while each input's primary rule, expected public structure,
and prose checklist live in an evaluator-only manifest so the service cannot learn from its answer.
The cases cover consent and channel order, slot boundaries, day3/day10, Phoenix and Los Angeles
DST, Sunday timing, Spanish, renewal, a transactional note without consent, STOP, an option reply,
protected-class and PII profile fields, past/missing move dates, and voice-only handling. A second
24-item corpus has exactly four examples for each project-defined reply class and deliberately
varies case, punctuation, synonyms, option numbers, and ambiguous language. C8 freezes and checks
the labels but makes no F1 claim; C9 must calculate and label macro-F1 on this synthetic corpus.
The option-reply fixture exposed wording that could sound like a booking confirmation, so both SMS
and email now say a team member will follow up to arrange the tour.
**Alternatives:** mixing expected answers into service inputs; copying the two goldens into the
practice set; reporting an F1 threshold from one STOP example; leaving the booking-adjacent wording.
**Why it won:** PLAN C8 requires separate goldens, adversarial coverage, per-fixture structure and
meaning checks, balanced reply examples, and honest claims about what that synthetic data proves.
**Source:** `PLAN-casestudy-bot.md` C8; decisions 31-36.

## 38. Evaluation: every field visible, aggregate evidence never invented per record

**Decided:** `casestudy/evaluation.py` (`evaluation_v1`) reports every named required state,
constraint, and threshold for each record. Unknown fields are `unsupported`; reply F1 and p95 are
`not_measured` in a single-record diagnostic and become pass/fail only when the batch evaluator has
the labeled 24-case reply corpus or at least 100 warm offline end-to-end runs. The reply report is a
labeled multiclass confusion matrix with macro-F1 and sample count. Offline timing includes the full
pipeline plus public and diagnostic serialization, reports median/p95, fallback/failure counts, and
stays separate from live-model timing (`not_measured` without authorization). Personalization is a
disclosed project proxy over safe, message-relevant field coverage: name/property/channel for both
channels, plus amenity and move timing opportunities for email. A safe model draft below the record's
threshold falls back to the validated template and is rechecked; a still-low template is reported as
failed rather than passed. Golden structural and meaning results use Wilson intervals only for their
binary pass fractions. Synthetic cases are explicitly not represented as hold-out or real-world
reliability. The existing shipcheck Claude judge and grading server are retained by path as optional,
uncalibrated, non-gating tools and are reported `not_run`; C9 spends no model credits.
**Alternatives:** treating per-record latency as p95; assigning F1 from one reply; using a Wilson
interval for macro-F1; counting every profile field as desirable personalization; letting a generic
but validator-safe model draft pass; running the optional judge without authorization.
**Why it won:** PLAN C9 requires complete field accounting, honest corpus/run metrics and sample
counts, threshold-enforced personalization fallback, and a clear proven-versus-estimated boundary.
**Source:** `PLAN-casestudy-bot.md` C9; the two expected blocks in `sample.jsonl` (evaluator only),
`reply_corpus.jsonl`, decisions 33-37.

**Review correction:** `evaluation_v2` derives message-meaning requirements from each record's
own safe input facts and expected CTA instead of recognizing the two fixture identities. An
explicit null expected message is a measured no-message check. Full assignment evaluation runs
every input once in list order, independently of the latency sample, so duplicate task IDs and
batches larger than 100 timing runs cannot be skipped, collapsed, or matched to another record.

## 39. Demo page: exact server-owned export bytes and separate diagnostics

**Decided:** The case-study web service returns `submission_jsonl` and each compact
`submission_line` directly from the C7 serializer, alongside a separate diagnostics object. The
browser only pretty-prints a parsed line for display; Copy one appends the same terminating line
break as the CLI, while Copy all and Download use `submission_jsonl` without rebuilding it. The
full-width workbench defaults to offline templates, accepts pasted or uploaded arbitrary JSONL,
keeps every record selectable, shows record-local errors, and renders every required state,
constraint, and threshold status including unsupported and not-measured values. **Alternatives:**
serializing public answers again in JavaScript; mixing diagnostics into the submission display;
dropping malformed lines; making live model mode the default. **Why it won:** C10 requires the
three export controls to produce the CLI's exact bytes and requires one bad record to remain
visible without losing the others. Caddy authentication, route proxying, limits, health, and the
container remain C11 work.
**Source:** `PLAN-casestudy-bot.md` C10; decisions 36 and 38.

## 40. Production wiring: isolated service behind the existing sign-in gate

**Decided:** The case-study workbench runs as its own non-root Python container, with `tzdata`
installed and only the `casestudy/` source copied into the image. The service exposes a direct
`/health` endpoint for Railway, caps request bodies at 2 MiB and batches at 100 records by default,
and keeps both limits configurable. CraneSignal's Caddy front door authenticates every
`/case-study*` request before proxying it to the private service; the service health endpoint is
not exposed through that public route. Local Compose includes the service, and the private human
preview uses the same authenticated Caddy route. Missing model configuration uses the already
validated offline templates rather than failing or attempting an unconfigured call. **Alternatives:**
bundling the service into the static site image; exposing it on a second public domain; putting
authentication into this service as a second source of truth; allowing unbounded uploads; copying
the full repository into the runtime image. **Why it won:** C11 requires separate deployment,
existing-auth reuse, bounded requests, deterministic missing-key behavior, and proof that the
container cannot read `propertystack/data/`.
**Source:** `PLAN-casestudy-bot.md` C11; decision 39.

## 41. Under the Hood: publish the boundary, not a polished certainty

**Decided:** The case-study workbench now includes a compact evidence section drawn from this
decision log. It leads with the two supplied examples, labels the scheduling and horizon rules as
hypotheses, shows the deterministic gates and validators around the optional wording call, records
the major reversed decisions, and names the unmeasured and unsupported areas. The result snapshot
reports 2/2 structural passes, 2/2 meaning passes, macro F1 1.00 on 24 explicitly synthetic replies,
and 0.61 ms median / 1.22 ms p95 over 100 warm offline runs; it does not describe those results as
hidden-set or production performance. All 100 measured runs used the template fallback. Live model
timing and the optional tone judge remain unmeasured/not run. **Alternatives:** a success-only story;
mixing assumptions with observations; presenting practice data as hold-out evidence; publishing the
conflicting Texas citations unchanged. **Why it won:** C12 requires the interviewer to see what the
system knows, what the project chose, and where evidence ends. Primary-source review corrected the
Texas citation from §305.053 to §301.051 and confirmed that the project contact window and exact STOP
sentence must remain labeled project defaults. The public source cards use primary sources for the
Fair Housing rule, federal calling rule, workflow guidance, and instruction-following research; the
shipcheck and build-bot project links remain separate from those citations. **Source:**
`PLAN-casestudy-bot.md` C12, decisions 26–40, `C12-citation-verification.md`, the two supplied expected
blocks, and the C9 evaluator snapshot measured 2026-09-17.

## 42. Dress rehearsal: prove recovery without spending a live call

**Decided:** The final rehearsal uses the actual local HTTP service and verifies five cases: both
goldens in configured mode with no credentials, 12 ordered practice records in that same
missing-key fallback, both batches in explicit offline mode, and a malformed row between the two
goldens. A standard-library checker saves and reparses the canonical export, validates every line
against `AssignmentAnswer`, checks batch bytes against each server-owned line, requires the
template engine for messages (or `none` for a deterministic no-send), and confirms that the
malformed row becomes a safe escalation without losing its
neighbors. The live 12 hold-outs are not stored in this repository; the card tells Drew how to
paste or upload them during the interview. **Alternatives:** spending a live model call for a
rehearsal; copying diagnostics into the submission; inventing 12 supposed hold-outs; checking only
the Python pipeline rather than the HTTP boundary. **Why it won:** C13 needs a production-shaped,
repeatable recovery proof while the build rules prohibit unapproved keys, spend, push, or deploy.
**Source:** `PLAN-casestudy-bot.md` C13; decisions 36, 39, and 40.
