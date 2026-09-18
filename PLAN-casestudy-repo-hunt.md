# Repo hunt: find every open-source gem that makes the case-study bot better

Goal: before building, find proven open-source projects, patterns and data that already solve
pieces of the case-study bot, so we reuse the professional way instead of inventing it — and
explain each find in plain words Drew can follow.
Done when: every hunt area below has been searched, all finds are in
`casestudy/research/candidates.md` in the required shape, and `casestudy/research/SUMMARY.md`
gives Drew a short, plain-English shortlist.

Written 2026-09-17 (thread 1549874755622928477). Research only: **do not write application code,
do not edit PLAN-casestudy-bot.md, do not push.**

What we are building: read `casestudy/data/problem_statement.txt`, `casestudy/data/sample.jsonl`
and `PLAN-casestudy-bot.md` first (10 minutes). Prior research is in `casestudy/*-research.md` —
read it so you do not repeat it.

How every task works:
- Search widely: GitHub search and topics, awesome-lists, Hacker News, Reddit (r/LocalLLaMA,
  r/MachineLearning, r/Python), arXiv code links, Papers with Code, PyPI, engineering blogs.
  Go at least three links deep from each good find — the gems are rarely on page one.
- **Verify** each candidate: open the repo, confirm it exists, note license, stars and last
  commit date. Reject anything abandoned (no commit in 18 months) unless it is pure data.
- Add each find to `casestudy/research/candidates.md` using the exact entry shape at the top of
  that file. Aim for 5-15 per area; quality over count. Mark things you could not verify.
- Append 3-5 lines to `PLAN-casestudy-repo-hunt.progress.md`: what you searched, the best find,
  and anything surprising.
- Run Check. Commit.

Check: `python3 casestudy/research/check_candidates.py`

## How to try it (30 seconds)
1. Open `casestudy/research/SUMMARY.md` — a short list of the best finds, each in one plain line.
2. Each find says what we would take from it and whether we should use it.
3. Nothing in the app changed — this was research only.

## Tasks

- [x] **H1 Messaging orchestration platforms (most important).** Open-source products that already
  decide channel, respect preferences and consent, apply quiet hours in the user's time zone, cap
  frequency and run cadences: Novu, Dittofeed, Laudspeaker, listmonk, Mautic, Apache Unomi, and
  whatever else you find. For each, find the actual files implementing preference resolution,
  channel fallback, quiet hours / do-not-disturb, throttling and digests, and note the vocabulary
  they use (subscriber, workflow, step, preference, digest, delay, throttle).
- [x] **H2 Send-time and business-day logic.** Libraries or reference code for "next allowed send
  time" inside a window, day-of-week rules, DST-safe scheduling, "next two weekdays at least N
  days out", and US holidays (dateutil rrule, pendulum, workalendar, holidays). Decide whether
  holidays matter here.
- [x] **H3 Compliance and guardrails beyond what we have.** TCPA/CTIA/CAN-SPAM helpers, opt-out
  keyword handling, fair-housing or discrimination classifiers (e.g. Zillow's open-source Fair
  Housing Classifier — find the code), PII detectors that run offline and light.
- [x] **H4 LLM copywriting for CRM / real estate.** Prompt libraries, brand-voice rules expressed as
  checks, open datasets of good leasing or real-estate SMS and email templates, and any evaluation
  sets for marketing copy.
- [x] **H5 Evaluation that grades against a reference.** Code for checklist-from-reference grading
  (RocketEval, TICK, Check-Eval, AutoChecklist), JSON field-level scoring, and confidence
  intervals (Inspect AI, DeepEval, Weave, others). Which one is the known professional choice for
  a small labelled set?
- [x] **H6 Human review screens.** Lightweight ways to pass/fail 50-200 outputs: Argilla, Label
  Studio, Langfuse annotation queues, Phoenix, Hamel Husain's annotation-app examples, promptfoo's
  viewer. Compare honestly against the existing shipcheck grading screen.
- [ ] **H7 Explaining decisions on screen.** How mature projects show "which rules fired and why":
  OPA decision logs, Cedar, OpenFeature / Unleash evaluation "reason" fields, fraud-rule engines.
  Any Python pattern giving decision + reasons + rule ids out of the box.
- [ ] **H8 Small tool-page skeletons.** The professional minimal way to ship a "paste input, run,
  show result cards, copy/export" page in Python: FastAPI + htmx + Jinja templates, or a
  single-file server. Name well-known template repos.
- [ ] **H9 Directly equivalent systems.** Open-source "next best action", "contact policy",
  "communication governance" or "journey decisioning" engines from banking, telecom or CRM. Even
  if too heavy to adopt, record the concepts and field names worth mirroring.
- [ ] **H10 Wildcard sweep.** Anything the areas above missed: search with fresh terms
  ("consent-aware messaging", "outreach policy engine", "compliant SMS agent", "leasing
  chatbot", "property management AI open source"). Look for the one gem nobody would think of.
- [ ] **H11 Shortlist for Drew.** Read every candidate and write `casestudy/research/SUMMARY.md`:
  at most 10 finds worth using, each as one short plain-English paragraph (what it is, what we'd
  take, why it makes the bot better), then "things we should NOT build ourselves" and "things
  that are 30 lines, just write them". No jargon. Run Check. Commit.
