# Case-study bot: a context-aware message agent, isolated inside CraneSignal

Goal: a separate service in this repo that reads assignment records (JSONL) and decides whether to
message a person, on which channel, at what time, with what body and what next action — matching
the assignment's expected output — with every hard rule enforced in code, a visible rule trail per
answer, an offline fallback, a scored eval, and a full-screen **Case study** tab inside CraneSignal.
Done when: `casestudy/` runs standalone, all our test records pass, the tab works signed in on
localhost, and Drew can export 12 outputs in one click.

Written 2026-09-17 (thread 1549874755622928477). **The interview is 2026-09-18** — speed matters,
but nothing may break the live CraneSignal site or chat.

## The assignment (source of truth)
`casestudy/data/problem_statement.txt` and `casestudy/data/sample.jsonl` (one example record).
A record carries: `task_id`, `persona`, `lifecycle_stage`, `consent` (email/sms/voice opt-in),
`channel_preferences`, `input` (property, move date, last interaction, timezone, language,
profile), `assertions.required_states`, `assertions.constraints`, `thresholds`, and `expected`
(`next_message` {channel, send_at, subject, body, cta} + `next_action` {type, name}).

## Decisions already made (do not re-litigate)
- **Engine**: DeepSeek (`DEEPSEEK_API_KEY`, OpenAI-compatible at `https://api.deepseek.com`,
  model `deepseek-flash`). Cap `max_tokens` ~90 and set a 1.5 s timeout — SMS copy is short.
  Subscriptions (Claude Code / Codex) must NOT be used as a server backend.
- **Offline fallback is required**: if the key is missing, the model is slow or it errors, the
  service still returns a valid, safe, templated message. `--offline` forces it.
- **Isolated**: own folder, own container, own data. No access to `propertystack/data/`, no import
  from `chatbot/`, no shared state with the live chat. It may reuse ideas, not wiring.
- **Eval reuses shipcheck** (`/home/drewp/main-projects/drew's eval`): copy its judge
  (`checks/chatbot/claude_judge.py`, local `claude -p`, no API key) and its human grading server
  (`scripts/grade_server.py`). Do not wire into `shipcheck.yaml` or `run-all.sh`.
- **Sign-in**: the tab sits behind CraneSignal's existing sign-in. No second account system.
- **Never push.** Drew pushes after trying it. Do not touch AI Visibility.

Check: `python3 -m pytest -q casestudy/tests`
Try: `bash casestudy/dev.sh`
Open: http://localhost:8790

## How to try it (30 seconds)
1. Paste the one sample record into the box → it returns a text message for Taylor, sent 9am
   Chicago time, with "Reply STOP to opt out", plus the list of rules that fired.
2. Paste all 12 of our test records → 12 answers, a Copy button and a Download button.
3. Turn the internet off (or run with `--offline`) and paste again → it still answers, safely.

## Tasks

- [ ] **C1 The rulebook in code.** `casestudy/rules.py` + `casestudy/tests/test_rules.py`.
  Pure Python, no network, no LLM. Given a record it returns a decision object:
  `should_send`, `channel`, `send_at` (ISO with the person's own UTC offset), `reason_trail`
  (one short line per rule that fired), `blocked_by` (if not sending).
  Rules, all enforced here and never by the model:
  1. **Consent** — only a channel whose opt-in is true. None consented → do not send.
  2. **Channel preference order** — first preferred channel that is consented.
  3. **Quiet hours** — never before 09:00 or after 20:00 in `input.timezone`; move to the next
     09:00 local. Handle DST via `zoneinfo`.
  4. **Opt-out** — SMS bodies must end with "Reply STOP to opt out."; email must carry an
     unsubscribe line. Enforced as a post-check, not a hope.
  5. **No personal data leak** — never put phone numbers, emails, unit numbers, balances or any
     `input` field not on an allow-list into the body.
  6. **Fair housing** — reject any body mentioning race, colour, religion, sex, family status,
     national origin, disability, or proxies (e.g. "perfect for families", "safe neighbourhood",
     "Christian community"). Word/phrase list in `casestudy/fair_housing.py`.
  Also: honour `assertions.constraints` present in the record (e.g. `primary_cta`), and
  `required_states` — each must appear in the trail as a passed state.
  Tests: the sample record produces channel `sms` and `send_at` 2025-12-09T09:00:00-06:00.
  Run Check. Commit.
- [ ] **C2 The writer, with a fallback that cannot fail.** `casestudy/writer.py` +
  `casestudy/templates.py` + tests. Given the decision and the record, produce `subject`, `body`,
  `cta`. Order: (1) DeepSeek Flash via the `openai` SDK, `max_tokens<=90`, `timeout=1.5`,
  temperature 0.3, a system prompt that states the rules and the required CTA; (2) on any error,
  timeout or missing key, fall back to `templates.py` — one short template per
  persona × lifecycle_stage, filled from the record. **Whatever comes back is then re-checked by
  the rules** (opt-out present, no PII, fair-housing clean); a failing model draft is discarded and
  the template used. Record `engine: "deepseek" | "template"` and `latency_ms` in the output.
  Tests must pass with no network (monkeypatch the client). Run Check. Commit.
- [ ] **C3 One record in, one answer out.** `casestudy/agent.py` — glue: record → rules → writer →
  output object shaped exactly like the assignment's `expected`
  (`next_message` {channel, send_at, subject, body, cta} + `next_action` {type, name}), plus a
  sibling `trace` object (rule trail, engine, latency_ms) kept OUT of the graded block.
  `next_action` mapping: new prospect → `start_cadence`; renewal → `schedule_followup`;
  no consent / opted out → `suppress`; anything unclear → the safest action, recorded in the trail.
  CLI: `python3 -m casestudy.agent --in file.jsonl --out answers.jsonl [--offline] [--pretty]`.
  Must handle a record with missing or malformed fields without crashing. Run Check. Commit.
- [ ] **C4 Our own hold-out set.** `casestudy/data/holdout-ours.jsonl` — 12 records we write,
  same shape as the sample, each with an `expected` block, covering: current resident renewal
  offer, late rent (money — careful tone, no threats), maintenance follow-up, tour no-show,
  someone who opted out of everything (**expected: send nothing**), SMS-only consent,
  email-only consent, a 2 a.m. local last-interaction (quiet hours), a non-US timezone,
  Spanish-language preference, a record with a missing timezone, and a record whose constraints
  demand a different CTA. Document each one's point in `casestudy/data/holdout-ours.md`.
  Run the agent over all 12; every one must produce a valid answer. Run Check. Commit.
- [ ] **C5 Score it (reuse shipcheck).** `casestudy/eval/`: a promptfoo config generated from the
  JSONL, deterministic assertions on the strict fields (channel, send_at, should-send-or-not,
  opt-out present, no fair-housing words, latency under threshold) and `llm-rubric` on the body
  only, judged by a copy of shipcheck's `claude_judge.py` (local `claude -p`, no API key).
  `casestudy/eval/run.sh` prints a plain score table and writes `casestudy/eval/results.json`.
  Also copy shipcheck's `grade_server.py` as `casestudy/eval/grade_server.py` so Drew can
  pass/fail each answer by keyboard. Run Check. Commit.
- [ ] **C6 The full-screen page.** `casestudy/app.py` (FastAPI or stdlib http.server — no heavy
  deps), `casestudy/static/`. One page, full width, no CraneSignal side panel. Three inputs:
  paste one record, paste many (one JSON per line), upload a `.jsonl` file. For each record show
  two columns: **left** the exact assignment output (monospace JSON, Copy button), **right** the
  rule trail in plain English plus engine and milliseconds. Buttons: "Copy all 12" and
  "Download answers.jsonl". Show a clear banner when running in offline mode. `casestudy/dev.sh`
  starts it on port 8790 and stops cleanly. Run Check. Commit.
- [ ] **C7 Its own container, wired into the site.** `casestudy/Dockerfile` (slim, non-root, only
  `casestudy/` copied in — prove it cannot read `propertystack/data/`), plus the route: add
  `/case-study*` to `site/Caddyfile` forwarding to the new service behind the existing sign-in
  check, and a **Case study** item in the site navigation that opens it full screen (not the chat
  panel). Add the Railway service notes (name, start command, the `DEEPSEEK_API_KEY` variable) to
  `casestudy/README.md`. Do not change any existing route's behaviour; run the site tests.
  Run Check. Commit.
- [ ] **C8 Under the Hood: the case-study section.** In `site/under-the-hood.html` (+
  `site/data/` as needed) add a section that explains, in plain English: the six rules and that
  they live in code, the score from C5, the median and 95th-percentile answer time, the offline
  fallback, and an honest "not handled yet" list. Keep the existing shipcheck and build-bot links.
  Run Check. Commit.
- [ ] **C9 Dry run and talk track.** Run the whole thing end to end: 12 records pasted at once,
  12 answers exported; then with the network off. Save the real output in
  `PLAN-casestudy-bot.progress.md`. Write `casestudy/README.md`: what it is, how to run it, the
  rulebook, the score, the known gaps — and a short "how I'd explain this in 3 minutes" section.
  Run Check. Commit. Do not push.
