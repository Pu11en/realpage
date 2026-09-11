# PropertyStack v2 — Task Plan

Written 2026-09-10. v1 is shipped (see `HANDOFF-V1-SHIPPED.md`). Drew chose all four
directions except scheduled refresh, in this order: chatbot polish → Dallas County →
outreach → new metro.

## How to run this plan

- One fresh session per task. Start it with:
  `Do the next unticked task in PLAN-v2.md, then tick it and stop.`
- Each task: build, check on localhost, commit locally, tick the box. **Do not push.**
  Drew tries it on localhost first, then says "put it on GitHub".
- Tasks marked 💲 spend money on scraping or model calls. Ask Drew before running them.
- Tasks marked ❓ are decisions: ask Drew one question at a time, write the answers here,
  and don't build anything.

## Part 1 — Chatbot polish

- [ ] **1.1 Table format at the source.** Tell the model in
  `chatbot/hermes-profile/SOUL.md` to always write the `|---|` row. Keep `repairTables`
  as a fallback.
- [ ] **1.2 "New chat" button.** Add it to the Page 2 chat panel and the phone full-screen
  chat. It clears the message list and the `history` the page sends.
- [ ] **1.3 Answer spot check.** 💲 Ask 10 real questions and check each citation against
  the data. Log the results in `chatbot/SPOT-CHECK.md`, and fix up to 2 prompt issues.

## Part 2 — Dallas County part of Richardson

- [ ] **2.1 Find the source.** Find where Dallas County apartment records and deeds come
  from (DCAD), and write what's needed in `propertystack/DALLAS-SOURCES.md`. No scraping yet.
- [ ] **2.2 find-apartments for Dallas.** Extend the skill to read Dallas County records
  for Richardson, and write the new buildings next to the current data.
- [ ] **2.3 Website + software for the new buildings.** 💲 Run `find-website` and
  `detect-software` on the new buildings only.
- [ ] **2.4 Sales + contacts for the new buildings.** 💲 Run `find-sales` (Dallas deeds)
  and `contact-scrape` on the new buildings.
- [ ] **2.5 Merge + rebuild.** Run `build-table` and `score-leads` over the combined set,
  run `site/data/build_data.py`, and check all 5 pages on localhost with a county label.
- [ ] **2.6 Fix the dead 23Hundred @ Ridgeview website** while the data is open.

## Part 3 — Outreach / lead workflow

- [ ] **3.1 ❓ Scope decision.** Who uses it, what it does (for example lead status
  tracking, call notes, or drafted intro emails), and what it must never do (for
  example sending anything by itself). Write the answers here as tasks 3.2+.

## Part 4 — New metro

- [ ] **4.1 ❓ Pick the metro.** Ask Drew which area, and why it helps the interview
  story. Write the choice here.
- [ ] **4.2 Make the pipeline area-aware.** Run the skills with an area name instead
  of the hard-coded `plano-richardson`, and let the site switch between areas.
- [ ] **4.3+ Per-skill runs for the new metro.** 💲 Split them the same way as 2.2–2.5
  once 4.1 is decided.
