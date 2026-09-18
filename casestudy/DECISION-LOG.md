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
Bus. & Com. Code §305.053, and the state-hours research recorded in `RULEBOOK-research.md`.

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
