# CraneSignal: give the chat the data we already have

Written 2026-09-15 from a read-only audit of what the chat can reach (plain version:
`handoffs/2026-09-15-what-the-chat-knows.md` in the main checkout). **Starts only when Drew says
"go work".** Localhost only: never push, never deploy, never change Railway settings.

Ground rules for every task:
- **No new scraping or lead finding (Drew, 2026-09-15).** Only reuse files already in the repo. No web
  calls, no lead-finder runs, no new sources.
- How the chat gets data: `chatbot/Dockerfile` (stage `kb`) copies CSVs into `/kb/data`; the plugin
  `chatbot/hermes-profile/plugins/propertystack/__init__.py` loads every `*.csv` there as a SQLite table
  (`_build_db`). New data = a CSV produced by a small build step, shipped by the Dockerfile, and described
  in `chatbot/hermes-profile/skills/query-propertystack/SKILL.md` (what it holds, its scope, how to say it).
- Chat counts must keep matching the site. Never double-count (e.g. `state_leads` tx already includes
  the 42 Plano/Richardson leads).
- User-facing name is **CraneSignal**; never show "PropertyStack", "Hermes" or "Open WebUI" to users.
- Every task adds one small offline test in `tooling/qa/fixes_tests/test_<task>.py` (no network, no paid
  AI calls) that fails without the fix — e.g. build the kb the Dockerfile way into a temp dir, run
  `_build_db`, and query the new table. Never weaken an existing test.
- **AI Visibility is read-only**: never edit `site/ai-visibility.html`, `site/data/*ai*`,
  `09-ai-visibility/` or its scripts; only read their files. Don't touch `tooling/street-talk/` or the
  Under the Hood page.
- `check_answers.py` questions may be added but never run (they cost money); Drew runs them.
- Tech choices are yours. Anything only Drew can do goes in the final report, not a question.

AI for the build: Claude Sonnet.

Run with: `Do the next unticked task in PLAN-chat-data.md, then tick it and stop.`
Check: `bash tooling/qa/check-fixes.sh && python3 -m pytest -q chatbot/tests`
Try: `bash tooling/dev.sh` (site plus chat; rebuild the chat container after data changes)
Open: http://localhost:8765/map.html

## How to try it (30 seconds)
1. Ask the chat "What property software do Dallas buildings use?": it answers from the Dallas data.
2. Ask "Which state has the most leads, and its top cities?": it matches the map.
3. Ask "How was CraneSignal built?": it gives real numbers (steps, checks), not a guess.

## Tasks
- [x] **D1 Parked Dallas data in the chat.** `propertystack/data/dallas-parked/` (buildings, websites,
  software, sales, contacts; files named `1-buildings-dallas.csv` etc.) never loads. Ship it as clearly
  named tables (e.g. `dallas_buildings`, `dallas_software`, …) with an `area` column; describe in SKILL.md
  that it's a separate Dallas building survey, not extra leads, so Texas/DFW lead counts don't change.
  Test: the tables load and Texas lead count is unchanged. Add a check_answers question. Commit.
- [x] **D2 Map numbers in the chat.** Ship a small `map_summary` table built from `site/data/client-map.json`
  / `map-markers.json` (state, leads, top cities with counts) so "where are most leads?" matches the map.
  Test: totals equal the site's. Commit.
- [x] **D3 Software market share.** Ship the site's `site/data/software-share.json` (and the `reach.json`
  proof list if it's lead-relevant) as a table, labeled "Plano and Richardson only" in SKILL.md. Test.
  Commit.
- [x] **D4 Building-page extras.** From `site/data/properties.json`, ship the fields the chat lacks (owner,
  website confidence, reason something is unknown, sale/lead notes) keyed to the existing building id so
  they join `master`. Test: a join returns the owner for a known building. Commit.
- [ ] **D5 CraneSignal's own numbers.** Ship `site/data/pipeline.json`, `chat-stats.json`, `evals.json`,
  `buildbot.json` (whichever exist) as small tables so "how was this built / how accurate is it?" gets real
  numbers with dates. SKILL.md: only use them for questions about CraneSignal itself; eval numbers may be
  old, so state their date. Test. Commit.
- [ ] **D6 AI Visibility scores, read-only.** Ship `site/data/ai-visibility.json` (and actions) as tables
  the chat can query, copying at build time without modifying the source files. Test. Commit.
- [ ] **D7 Final checks and report.** Run the Check and the panel check; rebuild the local chat container;
  write `handoffs/<date>-chat-data-report.md` in plain English: what the chat can now answer, three sample
  questions to try, and what's still missing (software outside Plano/Richardson needs new scraping, so it
  was left out on purpose). Commit.
