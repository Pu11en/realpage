# Handoff: independent review of the case-study build plan

**For:** a fresh Codex session (model Astra, highest reasoning effort) run inside
`/home/drewp/main-projects/realpage`.
**Purpose:** a second pair of eyes on the PLAN, before any code is written. Find what we missed.
**Do not write code. Do not modify any file except the one review file named at the end.**

## The situation

Drew has a 60-minute technical interview **tomorrow, 2026-09-18**, with RealPage (multifamily
property-management software), arranged through Motion Recruitment. He must have completed a
take-home before it, screen-share it, and **export or copy-paste 12 outputs from a hold-out set
handed to him live during the interview**.

He has exactly **one** example record. Everything else is inference.

## Read these, in this order

1. `casestudy/data/problem_statement.txt` — the assignment, verbatim (13 lines).
2. `casestudy/data/sample.jsonl` — the single example record, including its `expected` block.
3. `PLAN-casestudy-bot.md` — the build plan (tasks C1-C9). **Note:** this plan predates the three
   research documents below and has NOT yet been revised to match them. Judging that gap is part
   of the job.
4. `casestudy/RULEBOOK-research.md` — reverse-engineered implicit rules, legal grounding
   (TCPA/CAN-SPAM/FHA), the proposed ordered rulebook (5 gates + 6 shapers), 16 predicted hold-out
   cases, and output-shape decisions.
5. `casestudy/OPENSOURCE-research.md` — which open-source pieces to use, vendor, or skip.
6. `casestudy/STATE-OF-THE-ART-research.md` — 2025-2026 practice on deterministic-vs-LLM split,
   structured output, LLM-as-judge evaluation, semantic matching, compliance guardrails, latency.

Useful context, optional: `README.md` (what CraneSignal is), `chatbot/hermes-profile/SOUL.md`
(the existing agent's rulebook style), `/home/drewp/main-projects/drew's eval` (shipcheck — the
eval harness we intend to reuse: `checks/chatbot/claude_judge.py` and `scripts/grade_server.py`).

## Decisions already made (challenge them only with a concrete reason)

- The case-study bot is a **separate service** inside this repo (`casestudy/`), own container, own
  data, no access to `propertystack/data/`, reachable as a full-screen **Case study** tab behind
  CraneSignal's existing sign-in.
- **One structured LLM call inside deterministic code**; no agent loop. Compliance rules in Python,
  never in the prompt alone. The model's draft is re-validated by the rules and discarded if it
  fails.
- Engine: **DeepSeek** (`DEEPSEEK_API_KEY` already on the machine, OpenAI-compatible endpoint).
  Claude Code / Codex subscriptions must not be used as a server backend. A **template fallback**
  must answer correctly with no network at all.
- Evaluation reuses **shipcheck**'s judge and human grading server; deterministic assertions for
  anything measurable, an LLM judge only for tone.
- Every rule and every design choice must **cite its source on screen** (law for rules, papers and
  engineering guidance for design choices), both in each answer's "why" trail and in a new
  Under the Hood section.
- Nothing is pushed to GitHub until Drew tries it locally.

## What we want from you

Be adversarial and specific. Assume we are about to build this tonight in a few hours.

1. **Gaps.** What is missing from the plan that would cost points tomorrow? Especially: anything in
   the assignment's own wording (`required_states`, `thresholds`, `personalization_score_min`,
   `reply_classification_f1_min`, `p95_latency_ms`) that the plan does not visibly satisfy.
2. **Wrong inferences.** Go back to the single example record yourself and re-derive the implicit
   rules independently. Where does `RULEBOOK-research.md` over-fit, over-reach, or guess wrong?
   Name each disagreement and give your reasoning from the data.
3. **The hold-out set.** Are the 16 predicted cases the right ones? What scenario would you add or
   drop? Which single case are we most likely to fail?
4. **Output shape.** Will our output "semantically match" theirs? Flag any field-naming, null
   handling, enum vocabulary or timestamp-format risk. The expected block is the ground truth.
5. **Plan-vs-research drift.** `PLAN-casestudy-bot.md` says six rules; the research says eleven.
   Tell us the correct task list to build tonight, in order, sized so each task is one short
   session, with the check that proves each one.
6. **Scope call.** Given a hard deadline tomorrow, what should we cut, and what is non-negotiable?
7. **Risk list.** What breaks live on a shared screen, and what is the mitigation?

## Deliverable

Write your review to `casestudy/REVIEW-astra.md`. Structure it as:
`## Verdict` (2-3 sentences), `## Must fix before building`, `## Disagreements with the rulebook`,
`## Revised task list`, `## Cut list`, `## Live-demo risks`. Be concrete; quote file and line where
you can. Do not soften findings. If something is actually fine, say so briefly and move on.

---

## Second job: capture how this was planned (for Under the Hood)

Run this as a **separate sub-agent**, in parallel with the review. Its output is not a review; it is
a record.

Drew wants the Under the Hood page to show not just the finished thing but **how the decision was
reached** — the questions asked, the options considered, what was rejected and why, and the source
behind each choice. That story is currently spread across a Discord thread and this repo's git log.

Sources to read:

- The planning conversation, via the local API (no auth needed for reads):
  `curl -s "$CCDB_API_URL/api/threads/1549874755622928477/messages?limit=200"`
  That thread is where the whole plan was argued out on 2026-09-17.
- `git log --oneline --since=2026-09-17 --name-only` in this repo, for what was actually written.
- The three research files (`casestudy/*-research.md`), which carry the citations.

Produce `casestudy/DECISION-LOG.md` with one entry per real decision, in the order they were made.
Each entry: **what was decided**, **what the alternatives were**, **why this one won**, and **the
source** (a law, a paper, an engineering write-up, or "Drew's call"). Keep each entry to a few
lines and write it in plain English a non-engineer can follow — it is going on a public page.

Include the decisions that were *reversed* (for example: Wayfinder-style long planning was proposed
and dropped because the interview is the next day; subscriptions as an LLM backend were investigated
and rejected on terms-of-service and latency grounds). Reversals are the most credible part of the
story; do not tidy them away.
