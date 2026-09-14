# PropertyStack: Under the Hood, the page RealPage sees

**Starts only after the lead finder build (`PLAN-lead-finder-build.md`) is finished and merged, and
Drew says "go work".** Drew's answers: `/home/drewp/main-projects/handoffs/2026-09-14-under-the-hood-plan-answers.md`.
Job research: `/home/drewp/main-projects/handoffs/2026-09-14-realpage-job-research.md`.

## What it is
Under the Hood is the link Drew sends RealPage for the **AI Developer IV** job (internal AI Center
of Excellence: AI agents and tools that help engineering teams across the software process). It
proves: (1) a **reusable way for teams to build with AI agents** (plan → build bot builds each step
alone → checks after every step → human OK), (2) **evals** via Drew's open-source tool
**shipcheck** (`/home/drewp/main-projects/drew's eval`, `results/latest/scorecard.json`), (3) measured
impact, cost/speed, guardrails, honest limits.
- **Layout:** one page. Top = 90-second read: the story, 4-5 big numbers, one diagram. Below =
  clickable sections that open for detail. Minimal styling (Drew does design himself).
- **Only measured numbers.** Every number comes from a data file; nothing typed by hand.
- **Privacy:** never log or show sign-in emails or names.
- Localhost only; never push. Links to GitHub code (build bot = `github.com/Pu11en/ebi-agent-chat-relay`,
  shipcheck = `github.com/Pu11en/shipcheck`) are written now and go live when Drew pushes.

Run with: `Do the next unticked task in PLAN-under-the-hood.md, then tick it and stop.`
Check: `bash tooling/qa/check-under-the-hood.sh`
Try: `bash tooling/dev.sh`
Open: http://localhost:8765/under-the-hood.html

## How to try it (30 seconds)
1. Open Under the Hood: the top section reads in 90 seconds -- story, big numbers, one diagram.
2. Click "How I build with AI": a real plan step, its check result and the bot's report, plus a code link.
3. Ask the chat a question and click 👎: it's saved, and the page's feedback count goes up after a rebuild.

## Tasks

- [ ] **U1 Check + chat log.** `tooling/qa/check-under-the-hood.sh` (page loads, every section opens,
  every number on the page exists in `site/data/`, `check-panel.sh`; under 2 minutes, no network).
  In `chatbot/proxy.py`, log one JSON line per answer to `/opt/data/chat-log.jsonl`: time, question,
  tools used, seconds, tokens, cost, links removed by the link guard -- **no emails or names**.
  Tests. Commit.
- [ ] **U2 👍/👎 on chat answers.** Small buttons under each chat answer; the vote (+ optional reason)
  is added to that answer's log line. `tooling/export-chat-log.sh` copies the log out of the container
  to `propertystack/data/chat-log.jsonl` (the format shipcheck imports). Rebuild with
  `bash tooling/dev.sh`. Commit.
- [ ] **U3 Build bot numbers.** `site/data/build_buildbot.py` reads every `PLAN-*.md` +
  `PLAN-*.progress.md` and git history (+ gowork records in `/home/drewp/.local/state/ccdb/gowork*`
  if readable) → `site/data/buildbot.json`: plans, steps built by the bot, % passed checks first
  try, retries, time per step, total hours, and 3 real example steps (plan text, check result, the
  bot's plain recap). Tests. Commit.
- [ ] **U4 Pull in shipcheck + chat numbers.** `site/data/build_evals.py` copies shipcheck's
  `results/latest/scorecard.json` (+ failure types, judge agreement, contest) into
  `site/data/evals.json`, and totals from the chat log (answers, 👍/👎, p50/p95 seconds, $ per
  answer, links removed) into `site/data/chat-stats.json`. Missing file → the section says "not run
  yet". Commit.
- [ ] **U5 Apply shipcheck's fixes.** If `/home/drewp/main-projects/drew's eval/results/realpage-fixes/`
  has patches, apply each here, run the checks, commit each fix separately with what it fixed. None
  yet → tick and move on.
- [ ] **U6 The 90-second top.** New top of `site/under-the-hood.html`: one-line story ("A reusable way
  for any team to build with AI agents, proven on this product"), 4-5 big numbers from the data
  files (steps built by the bot, % passed first try, shipcheck checks passing, grader-agrees-with-human
  %, $ per chat answer), and one simple SVG diagram: plan → build bot → checks → human OK → live,
  with the product (lead finder → data → site + chatbot) under it. Commit.
- [ ] **U7 Section: How I build with AI.** Collapsible: how the build bot works (diagram), the 3 real
  example steps from U3, the safety rules (own copy, checks after every step, human OK before
  anything goes live, never pushes), the code link, and the "adopt it in an hour" playbook link.
  Commit.
- [ ] **U8 Sections: Evals.** Collapsible: shipcheck scorecard (every check, pass/fail, date), grader
  vs human (agreement %, TPR/TNR, kappa), failure types with counts and one example each, the
  contest result (plain AI vs AI + shipcheck), and a link to shipcheck. Commit.
- [ ] **U9 Sections: cost, safety, choices, limits, data.** Collapsible: cost and speed (per chat
  answer and per build step; free search first, which AI does which job and why); guardrails (link
  guard, a source for every fact, never guess, search caps, secrets scan, no emails logged, human
  OK); build vs buy (one line per tool); honest limits and what's next; lead finder numbers per
  area (new state, sources, skipped cities); the existing run history at the bottom. Commit.
- [ ] **U10 Playbook: adopt the build bot in an hour.** First research 3-5 real playbooks/onboarding
  guides from respected open-source projects (note what makes them good); then write
  `docs/PLAYBOOK-build-bot.md` in our own words: what it is, 5-minute setup, a first tiny plan,
  how checks and human OK work, when not to use it. Linked from U7. Commit.
- [ ] **U11 Final pass.** Run the Check, `check-answers.sh` and shipcheck's `scripts/shipcheck.sh`
  against this repo; open the page at phone and desktop size with Playwright (screenshots in
  `tooling/qa/`); every number matches its data file; fix anything off. Commit. Recap in plain words
  for Drew what the page now shows.
