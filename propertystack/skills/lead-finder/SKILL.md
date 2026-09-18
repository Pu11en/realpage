---
name: lead-finder
description: PropertyStack lead finder. For any US state, finds new/upcoming apartment leads (permits, HUD loans, state housing awards, planning agendas), fills in details, detects apartment software, and ranks the leads. Local harness only, area-agnostic (no place names in code).
---

# lead-finder

Runs on Drew's computer only, never in the chat agent. Replaces the old Plano-only skills
(`find-apartments`, `find-sales`, `build-table`, `scout-areas`) with one chain that works for
any US state, picked at run time.

**Area-agnostic:** no US state or city name is ever hard-coded in this skill's code. All area
names are data, read from `propertystack/data/<state-slug>/` or passed as arguments.

## The 6 parts

1. **Shared base** (this skill) -- one lead record format (`record.py`), a web helper that
   searches Jina first and Brave second (`fetch.py`) and caches every page, and a run
   folder per state per run with resume support and search/project caps (`runs.py`).
2. **Permits** -- rank a state's cities by new-apartment permit volume (free Census data), find
   each city's permit system (Socrata / ArcGIS / Accela / EnerGov / Tyler catalog lookup, else
   search for its portal), pull new multifamily permits, and fill in project details (address,
   units, developer, opening date).
3. **Early signals** -- HUD FHA multifamily loan list (new projects and refinance/sale
   signals), state housing agency tax-credit/bond award lists, and city planning-commission
   agendas (Legistar, CivicPlus, Granicus, PrimeGov, CivicClerk, BoardDocs, iQM2) for projects
   before they reach permitting.
4. **Software, sales, contacts, ranking** -- fingerprint each project's leasing software,
   find recent building sales, find who to call, and rank all leads.
5. *(reserved -- site wiring)*
6. *(reserved -- search budget and city selection glue)*

## Inputs

- `--state <two-letter or slug>`: required. Picked automatically by the caller from the
  state with the fewest processed leads among the 15 fastest-growing (see `runs.py`), or passed
  explicitly for a rerun.
- `--run-id <id>`: resume an existing run folder instead of starting a new one.

## Outputs

- `propertystack/runs/<state-slug>/<run-id>/<step>-<city-slug>.json`: one file per step per
  city, so a rerun can skip whatever already finished.
- `propertystack/data/<state-slug>/leads.json`: the final ranked lead records for that state
  (see `docs/LEAD-FORMAT.md`), in the same shape the site expects from the old skills.

## Caps

- Stop a run at **150 projects or ~450 searches**, whichever comes first (`runs.py`).
- A state with fewer than 30 projects after Part 2+3 rolls into the next-ranked state, which
  becomes its own area rather than being merged in silently.

## Tools

- Search: `WebHelper.search()` (`fetch.py`) tries Jina first, then Brave Search API only when
  Jina errors or returns nothing relevant (SearXNG is banned, never used); Jina and Brave calls
  are counted separately, and Brave stops once its 800-call/month free-credit cap is hit.
- Page reads: crawl4ai first, Scrapling if blocked, Playwright as the last resort; every fetched
  page is cached on disk under the run folder and never re-read.

## Rules

- No place names (US states, big cities, `Plano`, `Richardson`, `Collin`, `Dallas`, ...) ever
  appear literally in this skill's or any lead-finder-\* skill's code -- see
  `tests/test_no_place_names.py`, which fails the whole check if one shows up.
- Never guess a fact that isn't sourced; an unknown value stays blank/unknown rather than
  invented, and every fact this skill writes carries a source URL.
