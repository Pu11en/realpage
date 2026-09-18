# Case-study bot: a context-aware message agent, isolated inside CraneSignal

Goal: a separate, live service that reads an assignment record and decides whether to message a
person, on which channel, at what time, with what words and what next action — every compliance
rule enforced in code, every decision citing its source on screen, a scored eval, and a
full-screen **Case study** tab inside CraneSignal that Drew can use as a real signed-in user.
Done when: the 12 practice records all pass, the page works **live on app.cranesignal.com**, and
12 outputs can be exported in one click.

Written 2026-09-17, rewritten after research (thread 1549874755622928477).
**The interview is 2026-09-18.** Drew will not test on localhost — he tests the live site.

## Source of truth
- `casestudy/data/problem_statement.txt` — the assignment, verbatim.
- `casestudy/data/sample.jsonl` — the ONE example record, with its `expected` block.
- `casestudy/RULEBOOK-research.md` — reverse-engineered rules + legal citations + predicted cases.
- `casestudy/OPENSOURCE-research.md` — what to reuse, vendor, skip.
- `casestudy/STATE-OF-THE-ART-research.md` — 2025-2026 practice; every design choice below traces
  to it.

## Architecture (decided, with sources — put these citations on screen)
- **A routing workflow with one structured LLM call. No agent loop.** The decision path is fixed.
  (Anthropic, *Building Effective Agents*, Dec 2024.)
- **Compliance rules live in Python, never in the prompt alone.** Instruction-following degrades
  past ~6 simultaneous constraints. (IFScale, arXiv 2507.11538, Jul 2025.)
- **Deterministic branches never call the model** (no consent, opted out, quiet-hours-only,
  suppressed). Biggest latency lever; also free correctness.
- **Model draft is re-validated by the rules and discarded if it fails**; one bounded regenerate
  naming the violation, then template. (Evaluator-optimizer, bounded; Anthropic Dec 2024.)
- **DeepSeek `json_object`** (no `json_schema` support): the word "json" + one example in the
  system prompt, temperature 0, `max_tokens<=120`, Pydantic validation, one error-fed retry, then
  template. (DeepSeek JSON-mode docs; instructor pattern.)
- **Deadlines:** 1,200 ms per model call, 2,000 ms total; template fallback is pre-validated.
- **Scoring:** deterministic assertions for everything measurable; a reference-derived yes/no
  checklist; a pointwise binary tone judge. Embedding similarity logged, never gating.
  (Hamel Husain *Evals FAQ*; Braintrust; Check-Eval/RocketEval.)
- **Honesty about numbers:** 12 records cannot establish a rate; report Wilson intervals and say
  what is proven vs estimated. (Bowyer et al., ICML 2025.)

## Rules for every task
- **Isolation is a hard requirement.** `casestudy/` imports nothing from `chatbot/` and reads
  nothing under `propertystack/data/`. Its container copies only `casestudy/`.
- Do not change existing site behaviour. Do not touch AI Visibility.
- Each task ends with: Check passes, a commit, and a few lines appended to
  `casestudy/DECISION-LOG.md` (what was decided, what else was considered, why, the source) —
  that file feeds the Under the Hood page.
- **Do not push.** Drew pushes (he has said he wants it live; he still presses the button).

Check: `python3 -m pytest -q casestudy/tests`
Try: `bash casestudy/dev.sh`
Open: http://localhost:8790

## How to try it (30 seconds)
1. Paste the sample record → a text for Taylor, 9am Chicago, ending "Reply STOP to opt out.",
   with the rules that fired listed beside it, each citing its law.
2. Paste all 12 practice records → 12 cards, "Copy all" and "Download".
3. Unplug the network (or tick Offline) → it still answers all 12, safely.

## Tasks

- [ ] **C1 Rulebook part 1: the five gates.** `casestudy/rules/gates.py` + tests.
  Pure Python, no network. In order, each returning pass/stop with a one-line reason **and a
  citation string**:
  1. `consent_gate` — a channel may be used only if `consent.<channel>_opt_in is True`; missing
     field = false; never infer consent from `channel_preferences`; none consented → stop,
     `next_action.type="suppress"`, reason `no_consent`.
     Cite: TCPA 47 U.S.C. §227 / 47 CFR §64.1200(a)(2).
  2. `lifecycle_gate` — stop on `closed|lost|do_not_contact|opted_out|moved_out`, or
     `do_not_contact: true`. Unknown persona → `escalate_to_human`.
  3. `inbound_reply_gate` — if the record carries an inbound reply: `STOP|STOPALL|UNSUBSCRIBE|
     CANCEL|END|QUIT` → stop + `mark_opted_out` (send NOTHING, not even a goodbye);
     `HELP` → help text; `1`/`2` → confirm that option; negative phrases ("not interested",
     "already leased", "wrong number") → stop + `stop_cadence`; a question → short ack +
     `escalate_to_human`. Emit `reply_classification` on the output.
     Cite: FCC revocation rule, effective 2025-04-11; CTIA Messaging Principles.
  4. `frequency_gate` — nothing within 24 h of `last_message_sent_at`; nothing if
     `messages_sent_24h >= 3`. Missing → pass.
  5. `sanity_gate` — move-in date already past, or an unparseable `timezone` → `escalate_to_human`,
     no message. (Do not silently default a bad timezone.)
  Tests: one per gate, plus the sample record passing all five. Run Check. Commit. Log decisions.
- [ ] **C2 Rulebook part 2: send time.** `casestudy/rules/send_time.py` + tests. The single most
  likely trap. Rule: **the next 09:00 local strictly after the reference time**, where reference =
  `last_interaction` (in `input.timezone`), rolling forward only if 09:00 has already passed.
  Window 09:00–20:00 Mon–Sat; Sunday not before 12:00. Render ISO-8601 with the recipient's numeric
  offset (`-06:00`), never `Z`, using `zoneinfo` (add `tzdata` to the image).
  Tests that MUST pass: the sample (09:04 Mon Chicago → 2025-12-09T09:00:00-06:00);
  07:15 local → **same day** 09:00; 20:30 local → next day; `America/Phoenix` in July → `-07:00`
  (no DST); `America/Los_Angeles` in December → `-08:00`; a Saturday; a Sunday → 12:00.
  Cite: TCPA 47 CFR §64.1200(c)(1); Texas Bus. & Com. Code §305.053 (Sun 12:00).
  Run Check. Commit. Log decisions.
- [ ] **C3 Rulebook part 3: the six shapers.** `casestudy/rules/shapers.py` + tests.
  `channel_select` (first preferred channel that is consented; voice is never automated → a call
  task), `intent_select` (persona × lifecycle → welcome, follow_up, tour_reminder,
  application_status, renewal, payment_reminder, maintenance_followup),
  `horizon` (≤45 d short, ≤120 d medium, else long, missing = unknown),
  `cta_select` (map `assertions.constraints.primary_cta` → output vocabulary, e.g.
  `book_tour → schedule_tour`; tour options = the first two weekdays at least two days out inside
  the same Mon–Fri week, else Mon/Tue next week),
  `cadence_name` (`{persona}_{intent}_{horizon}_horizon`),
  `states` (emit each `assertions.required_states` once its rule has passed).
  Run Check. Commit. Log decisions.
- [ ] **C4 The validators (what the model can never override).** `casestudy/rules/validate.py` +
  `casestudy/data/fair_housing.json` + `casestudy/data/pii_patterns.json` + tests.
  Checks any candidate body: opt-out sentence present and last (SMS) / unsubscribe + property
  postal address present (email); no PII (phone, email, street address, SSN, money amounts, last
  name) via ~6 regexes; no protected-class or coded language — HARD list ("no kids", "adults only",
  "Christian community", "safe neighborhood", "able-bodied") and WARN list ("great schools",
  "family-friendly", "perfect for young professionals"), each entry carrying its citation and a
  suggested compliant rewrite; style lint (first-name greeting, ≤1 "!", no emoji, one question,
  numbered options, length ≤ 320 chars); segment count via `sms-toolkit`.
  Cite: Fair Housing Act 42 U.S.C. §3604(c); CAN-SPAM 15 U.S.C. §7704; Zillow's open-source Fair
  Housing Classifier as prior art. Run Check. Commit. Log decisions.
- [ ] **C5 Templates that can answer with no internet.** `casestudy/templates.py` + tests.
  One short template per (intent × channel × language en/es), filled from the record; every
  template is run through C4's validators in the tests, so the fallback is provably safe.
  Spanish keeps the literal word STOP. Run Check. Commit. Log decisions.
- [ ] **C6 The writer.** `casestudy/writer.py` + tests (no network in tests — monkeypatch).
  DeepSeek via the `openai` SDK, `base_url=https://api.deepseek.com`, model `deepseek-flash`,
  `response_format={"type":"json_object"}`, temperature 0, `max_tokens<=120`, per-call deadline
  1,200 ms. System prompt = stable prefix (role, ≤6 wording constraints, one worked example) so
  provider prefix caching applies; the record goes last. Pydantic-validate the reply; on failure
  retry once with the validation error named; then template. Every draft is re-checked by C4 and
  discarded if it fails. Record `engine` (`deepseek` | `template`) and `latency_ms`.
  Run Check. Commit. Log decisions.
- [ ] **C7 One record in, one answer out.** `casestudy/agent.py` + tests. Assemble the output:
  `task_id`, `decision` ("send" | "do_not_send"), `next_message` ({channel, send_at, subject, body,
  cta} or null), `next_action` ({type, name, reason?}), `why` (array of {rule, plain_english,
  citation}), `states`, `reply_classification` (null unless an inbound reply), `personalization_score`
  (filled slots ÷ available slots), `latency_ms`. Deterministic branches must never call the model.
  CLI: `python3 -m casestudy.agent --in f.jsonl --out answers.jsonl [--offline] [--pretty]`.
  Malformed or missing fields must never crash. Run Check. Commit. Log decisions.
- [ ] **C8 The 12 practice records.** `casestudy/data/holdout-ours.jsonl` + `holdout-ours.md`
  (one plain-English paragraph per case: the situation, which rule it probes, the expected answer).
  The 12: email-only consent; nothing consented; prefers email though both allowed; 20:30 local;
  **07:15 local (same-day trap)**; Phoenix/LA offset trap; Saturday/Sunday; Spanish; resident
  renewal at 60 days; maintenance note with SMS consent off; inbound "STOP"; profile containing
  children, a wheelchair and "wants good schools". Each carries an `expected` block.
  Run the agent over all 12 — every one must return a valid answer. Run Check. Commit. Log.
- [ ] **C9 The eval.** `casestudy/eval/`: deterministic assertions per record (channel, exact
  `send_at`, send-or-not, opt-out present, banned phrases absent, latency under 2,000 ms), a
  reference-derived yes/no checklist per record (3-6 items), and a pointwise binary tone judge
  reusing shipcheck's `claude_judge.py` (local `claude -p`, no API key). `casestudy/eval/run.sh`
  prints a table and writes `results.json` including **Wilson intervals** and a line stating what is
  proven vs estimated. Also copy shipcheck's `grade_server.py` so Drew can press 1/2 per answer.
  Run Check. Commit. Log decisions.
- [ ] **C10 The page.** `casestudy/app.py` (stdlib `http.server` or FastAPI — no heavy deps) +
  `casestudy/static/`. Full width, CraneSignal's real header, fonts and colours (read
  `site/css/`), NOT the chat side panel. Paste one record, paste many, or upload `.jsonl`.
  Per record a card: **left** the exact assignment output with a Copy button; **right** the plain
  English "why", each line carrying its citation. Buttons: Copy all, Download answers.jsonl.
  Badge showing engine and milliseconds; a clear banner in offline mode. `casestudy/dev.sh` runs it
  on 8790. Run Check. Commit. Log decisions.
- [ ] **C11 Its own container, wired in and live.** `casestudy/Dockerfile` (slim, non-root, copies
  only `casestudy/`, installs `tzdata`), a `/case-study*` route in `site/Caddyfile` behind the
  existing sign-in, and a **Case study** item in the site navigation opening full screen. Write
  `casestudy/DEPLOY.md`: the Railway service name, start command, and the `DEEPSEEK_API_KEY`
  variable. Prove the container cannot read `propertystack/data/`. Existing site tests must still
  pass. Run Check. Commit. **Stop and tell Drew it is ready to push.**
- [ ] **C12 Under the Hood: the case-study section.** In `site/under-the-hood.html`: what the bot
  does, the eleven rules in plain English each with its law, the design choices each with its
  source (no agent loop, rules outside the model, skip-the-model branches, checklist scoring, the
  12-records-can't-prove-a-rate caveat), the score from C9, median and p95 speed, the offline
  fallback, and an honest "not handled yet" list. Pull the story from `casestudy/DECISION-LOG.md`.
  Keep the existing shipcheck and build-bot links. Run Check. Commit. Log decisions.
- [ ] **C13 Dress rehearsal.** Run all 12 through the live-style stack, export the answers, then
  repeat with the network off. Paste the real output into `PLAN-casestudy-bot.progress.md`.
  Write `casestudy/README.md`: what it is, how to run it, the rulebook, the score, known gaps, and
  a "how I'd explain this in 3 minutes" script. Run Check. Commit. Do not push.
