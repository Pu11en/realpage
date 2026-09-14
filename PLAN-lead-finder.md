# PropertyStack: lead finder (pick an untapped city, find its apartments first)

Written 2026-09-13 with Drew (answers: `/home/drewp/main-projects/handoffs/2026-09-13-area-finder-plan-answers.md`).
**Runs after `PLAN-client-map.md`** (needs its `counts.json`). Replaces `PLAN-scout.md` S6 and
generalizes `PLAN-new-area.md`. A standalone data tool on Drew's computer -- not connected to
the site while it runs; when a city is done its data fills the site on localhost, Drew checks,
Drew pushes.

Goal: be first. Pick the state with the fewest RealPage buildings (of the 15 fast-growing
states from the client map), then the city in it with the most new apartment building and the
fewest RealPage buildings. **One city per run**, cap **150 buildings**, about **450 Jina
searches**, no stop for approval. Leads: **new buildings first** (zoning / under construction,
software not picked yet), then **recently sold**. Existing buildings are the base list only.

Be strategic about sources: for each kind of data, try saved **source recipes** first, test a
source on 5-10 buildings before using it, fall back down a backup list, and save what worked
as a recipe for the next city. Tools (all local): this Claude session (thinking, odd pages, no
extra paid AI), crawl4ai (`localhost:11235`), Playwright + stealth, Jina (only paid, capped),
Claude web search/fetch, `tooling/reddit_search.py`, the X session (read-only, small),
`tooling/pms_detect.py`, Census data (free), Ollama optional. No LinkedIn.

Run with: `Do the next unticked task in PLAN-lead-finder.md, then tick it and stop.`
Check: `python3 -m pytest -q propertystack/ && bash tooling/qa/check-panel.sh`
Try: `bash tooling/dev.sh`
Open: http://localhost:8765 → area picker → the new city's Early Leads

## How to try it (30 seconds)
1. Early Leads → switch the area picker to the new city: new buildings are at the top.
2. Each lead shows why it's a lead (e.g. "zoning approved, software not picked yet").
3. Click Deep dive on the top lead: the chat answers about the new city with sources.

## Tasks

- [ ] **L1 Skeleton + tests.** `propertystack/skills/lead-finder/` with `SKILL.md` and
  `run.py`. Tests with fixtures only: state pick (fewest RealPage among the 15 from
  `propertystack/data/client-map/counts.json`), city pick (most new 5+ unit permits, fewest
  RealPage buildings), 150-building and 450-search caps stop cleanly, lead order (new first,
  then sold). Tests fail first; commit.
- [ ] **L2 City permits (free).** Census place-level building permits (5+ units, last 12-24
  months) for the picked state's cities; combine with the client-map city counts; write
  `propertystack/data/lead-finder/<date>/pick.json` (state, city, counties, why, numbers).
- [ ] **L3 Source recipes + tester.** Recipe format in `propertystack/areas/recipes/*.json`
  (by state, county or system, e.g. Legistar, Accela, Socrata): data kind, source URL, how to
  query, date tested, how complete. A tester that tries a source on 5-10 known buildings and
  scores it. Seed recipes from what already works for Collin County / Plano. Per city, write
  `propertystack/data/<slug>/sources.json` (the chosen source per kind + backups tried).
- [ ] **L4 New buildings first.** For the picked city: zoning / permit agendas (Legistar,
  Accela, Granicus or the city's own site), the Texas TDLR registrations if in Texas, local
  news, Reddit/X mentions; stage from zoning filed to leasing. Adapt `find-upcoming` to use the
  sources file. Save the recipe that worked. Commit.
- [ ] **L5 Existing buildings + sales.** County property records (bulk file or open data) for
  20+ unit apartments (adapter like `find-apartments/run_dallas.py`); deeds / owner changes for
  sales. Where not online: `"none"` with a one-line reason (publish anyway). Save recipes. Commit.
- [ ] **L6 Run it (💲 about 450 searches).** Cap 150 buildings: all new buildings, then
  recently sold, then fill from existing. Websites, software (proof link each), contacts,
  `score-leads` with new-first ordering. Spot-check 10 software calls by opening their proof
  URLs. Log the run to `propertystack/runs/`. Commit.
- [ ] **L7 Site: area picker.** `site/data/build_data.py` builds every area under
  `propertystack/data/` into per-area JSON; an area picker on Early Leads and building pages;
  "not available here" notes where sources said none. Plano-Richardson unchanged by default.
  Check passes. Commit.
- [ ] **L8 Chat reads every area.** The chatbot loads each area's data (area column or
  per-area tables; `ps_schema` lists them). Rebuild; ask one question about the new city and
  one about Plano; both answer with sources. Run `tooling/qa/check-answers.sh`. Commit. Tell
  Drew in plain words it's ready to try.
