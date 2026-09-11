# PropertyStack v1 — Build Plan

Written 2026-09-10. This is the source of truth for the v1 build.
If anything else disagrees with this doc, this doc wins.

## What we're building

A dashboard called **PropertyStack** that shows, for every apartment building in
Collin County (Plano + the Collin County part of Richardson), which
property-management software they run — plus who just got a new owner and what's
being built. The point: hand a salesperson a ranked list of buildings to call.

- **One repo**, this repo (`realpage`), no split repos.
- **Everything deploys on Railway**, no Vercel.
- **Backend v1 is DONE.** 7 skills, 204 buildings, 152 software identified,
  28 recent sales, 14 upcoming projects, 42 ranked leads.
- **Frontend v1 is NEXT.** 5 pages + a chatbot on Page 2.

## Backend — done (do not re-touch unless bug is found)

Seven skills in `propertystack/skills/`, run against `plano-richardson`:

1. `find-apartments` — county records → 204 buildings
2. `find-website` — real website per building → 183 with sites
3. `detect-software` — visit each site → 152 software identified
4. `build-table` — join 1+2+3 → `master.csv`
5. `find-sales` — county deeds → 28 recent sales
6. `find-upcoming` — permits/news → 14 pipeline projects
7. `score-leads` → `leads.csv` (42 ranked leads with one-sentence "why")

All 7 reviewed and fixed 2026-09-10. See `propertystack/evals/review-weak-spots.md`.

## Frontend — 5 pages + chatbot

### Page 1 — Early Leads (home)
- 4 tiles: total leads · new · units in play · opening soon
- Filters + sort options (score, size, newest)
- Ranked list, 42 rows: score · name · city · units · signal · current software ·
  one-sentence "why" · sources · "NEW" tag
- **Contact info** (phone/email) shown on each row when Jina scraped it
- Click row → Page 4

### Page 2 — Master Table + chatbot
- 4 tiles: apartments · units · % identified · top software
- Search + filters (city, software, year, size) + Export CSV
- **Left ~2/3:** table, 204 rows (name, city, units, year, owner, software pill,
  proof link)
- **Right ~1/3:** chatbot panel, always visible, collapsible
- Coverage sentence below: `204 → 183 website → 152 identified → 52 unknown`
- Click row → Page 4

### Page 3 — Software Share
- 4 tiles: identified · top vendor · 2nd vendor · % on top vendor
- Two charts side by side: share by # buildings · share by # units
- Small table: vendor · # · units · % · change since last run
- Click vendor → Page 2 filtered to that vendor

### Page 4 — Property Detail (spec deferred; smaller)
Header · Software card · Signals card · Lead Score card · Sources · Website link.
Flesh out when we get to it.

### Page 5 — Under the Hood (spec deferred; smaller)
Pipeline diagram with counts · Run history · Accuracy notes.
Flesh out when we get to it.

## Chatbot spec

Follows the **eve-agent** pattern (`github.com/Pu11en/eve-agent`) — Hermes agent
on Railway with a skill folder. Model: **DeepSeek v4 flash**.

### Scope
Full realpage knowledge base: PropertyStack CSVs (`propertystack/data/`) + the
RealPage research folders (`01-company/` … `08-voice-of-customer/`) + Reddit
pack (`04-reddit/`).

### Definition of a good answer
1. Every factual claim points to where it came from (CSV row, research file, URL).
2. If the answer isn't in the data, say **"I don't have that"** — never invent.
3. Short for short questions (one paragraph max). Tables for lists of 3+ items.
4. Numbers only if literally in the data. No estimates, no rounding tricks.
5. Cite inline (e.g. `[5-sales.csv]`, `[04-reddit/index.md]`).

### Hard guardrails — never do
1. Never invent contact info (phone/email/address). Only pass through what
   Jina actually scraped.
2. Never claim a software vendor without a real proof URL from `3-software.csv`.
3. Never quote `raw/*` files verbatim — those are drafts.
4. Never write outreach messages or emails for the user (v1 scope).
5. Never speculate about owners beyond what county records show.
6. Never give legal / financial / compliance advice.

### Memory
- Chat memory: within a single conversation only.
- No per-user memory in v1.
- Global knowledge: yes, the whole KB (via a `query-propertystack` skill using
  SQLite over the CSVs).

### Write behavior
Read-only by default. If a future action would change data, the agent **asks
first** ("are you sure?"). No silent writes.

### Turn shape
One-shot per question in v1. No multi-step agent loops. If we ever want
multi-step, needs a hard budget (max tool calls, max seconds, max $).

## Build tasks — in order

Each task = its own branch. Build → manually verify → merge → next.
**No automated tests written for MVP** (verify by hand, ship, move on).

- **Task 1: Contact info scrape.** New skill `contact-scrape` in
  `propertystack/skills/`. Reads `master.csv`, Jina-reads each building's
  website, extracts phone/email if present, writes `contacts.csv`. ~$0.20 total.
- **Task 2: Railway deploy of current site.** Get the current static site
  (as-is, real data) live on Railway with a real URL. Prove the deploy pipeline
  works before we add anything.
- **Task 3: Build Page 1 (Early Leads).** Wire real data + contact info + sort
  options + click-through.
- **Task 4: Build Page 2 (Master Table).** Table only, no chatbot yet.
- **Task 5: Build Page 3 (Software Share).** Charts + table.
- **Task 6: Build Page 4 (Property Detail).** Detail template + wire routing.
- **Task 7: Build Page 5 (Under the Hood).** Simple admin view.
- **Task 8: Hermes chatbot service on Railway.** Copy eve-agent pattern, add
  `query-propertystack` skill.
- **Task 9: Wire chatbot into Page 2.** Chat panel connects to Hermes. ✅ DONE (7551181)
- **Task 10: Ship + smoke-test end to end.**

## Acceptance test — how we know v1 is done

1. Push to `main` → Railway rebuilds → site is live at a URL. No manual steps.
2. Site loads the current 204-building dataset (not stale sample data).
3. Chatbot on Page 2 correctly answers 5 sample questions with citations.
4. Contact info shows on leads where Jina found it, click-through where it didn't.
5. All 5 pages render with real data and click-throughs work.

## What NOT to do in v1

- No automated test suites.
- No CI (Railway auto-deploy is enough).
- No per-user login / accounts.
- No agent multi-step loops.
- No writing/mutating data from the agent (read-only or ask-first only).
- No expanding beyond Collin County (Dallas County part of Richardson = v2).
- No Vercel (Railway only).
- No splitting the repo.
