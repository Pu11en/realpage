# PropertyStack: lead finder (any area, new buildings first)

Rewritten 2026-09-13 with Drew (all answers: `/home/drewp/main-projects/handoffs/2026-09-13-area-finder-plan-answers.md`).
**NOT approved to run yet** -- all holes answered 2026-09-13; waiting for Drew's "go work". Runs after `PLAN-client-map.md` (done).
Replaces `PLAN-scout.md` S6 and `PLAN-new-area.md`.

## What it is
One skill, **`lead-finder`**, that runs a chain of smaller skills, each doing one job. It picks
a state, walks its cities, and builds one statewide list of early leads. It is **area-agnostic**:
no place name is ever written in code. Everything about a place comes from the run itself and
from saved **source recipes** (data files). **Plano–Richardson is one finished area; it is never
rerun.** A standalone data tool on Drew's computer; when a state is done its data fills the site
on localhost, Drew checks, Drew pushes.

## Rules decided with Drew
- **State:** fewest RealPage buildings among the 15 fastest-growing states (client-map `counts.json`).
- **Cities:** most new apartment permits first (Census, free); **skip** a city with no permits online.
- **Run size:** whole state, city by city, until **150 new projects** or **~450 searches**. If a
  state gives **fewer than 30 projects**, carry on into the next state on the list (next-fewest
  RealPage buildings) inside the same cap; that state gets **its own button**.
- **New buildings:** stages **permit issued → leasing** (~6-18 months before opening). **Permits
  first** (city open data or permit portal, Playwright click-through if needed), then **1 web
  lookup per project** for address, units, developer, opening date and links.
- **Apartments only, 20+ units:** keep a permit only if its type/description says apartment or
  multifamily, or it lists 20+ units. Missing units → the details lookup finds them; still unknown
  → **drop**. Several permits for one project are **merged into one lead**.
- **Unknown opening date:** rank by permit date and show "**Opens: not public yet**"; never estimate.
- **Already-called leads:** no change now (comes with team memory later). Keeping data fresh is later.
- **Polite to city sites:** 2 s between visits, cache every page (never read one twice), skip a city
  after **3 blocks** and note why.
- **Sold buildings:** from **news only** (no county records).
- **Software:** check where there's a website; **drop RealPage clients**; mark the rest
  "on Yardi today" / "not picked yet".
- **Who to call:** 1 lookup per lead -- developer (or new owner), office phone + website; a named
  person only if a permit or news story names one.
- **Ranking:** soonest opening first, then more units, "not picked yet" above "on a competitor".
- **Site:** Early Leads gets a **row of area buttons** (one per area, incl. Plano–Richardson), each
  its own table; a state area has a **city filter** above its table. Sidebar area dropdown goes.
  (Software Share page already removed.)
- **Tools (all local, run only in harness sessions in this folder, never the deployed chatbot):**
  this Claude session, **SearXNG first** (`tooling/searx_search.py`, `127.0.0.1:8888`), **Jina only
  as fallback** (paid, capped), crawl4ai (`localhost:11235`), Playwright + stealth, Claude web
  search/fetch, Socrata/ArcGIS catalog APIs (find city permit data), GDELT (sale news), usaddress +
  Census batch geocoder (matching). No Ollama. `tooling/pms_detect.py`, Census data, optional
  Reddit/X (read-only). No LinkedIn.

Run with: `Do the next unticked task in PLAN-lead-finder.md, then tick it and stop.`
Check: `bash tooling/qa/check-lead-finder.sh`
Try: `bash tooling/dev.sh`
Open: http://localhost:8765 → Early Leads → the new state's button

## How to try it (30 seconds)
1. Early Leads: a row of area buttons; click the new state -- its own table, soonest openings on top.
2. Pick a city in the filter: only that city's leads; each row says why it's a lead.
3. Click ✦ Deep dive on the top lead: address, opening date and real links.

## Tasks

- [ ] **L1 Skeleton, caps, no-place-names test.** Delete the 4 old Plano-only skills
  (`find-apartments`, `find-sales`, `build-table`, `scout-areas`); Plano data files stay. `propertystack/skills/lead-finder/` (`SKILL.md`
  describing the chain + `run.py` that calls each step) and `tooling/qa/check-lead-finder.sh`
  (runs this skill's tests + `check-panel.sh`). Fixture-only tests: state pick from `counts.json`,
  150-project and 450-search caps stop cleanly, <30 projects rolls into the next state, lead ranking order (unknown opening → by permit date), and a test that **fails if any
  lead-finder step's code contains a place name** (Plano, Richardson, Collin, Dallas, any state or
  city literal). Tests fail first; commit.
- [ ] **L2 Rank the state's cities (free).** Census place-level building permits (5+ units, last
  12-24 months) for the picked state; write `propertystack/data/<state-slug>/cities.json`
  (city, permits, RealPage count from client map). Commit.
- [ ] **L3 `find-sources` (new).** Recipe format in `propertystack/recipes/*.json` (by permit
  system, e.g. Socrata / ArcGIS / Accela / EnerGov / Tyler, or by city): how to query new
  multifamily permits, fields, date tested, how complete. For a city with no recipe: search for its
  permit data, identify the system, test on 5 permits, save the recipe; none found = mark the city
  "skipped: no permits online". Fixture tests. Commit.
- [ ] **L4 `find-upcoming` rebuilt for any city.** Replace the old Plano-only version: given a city
  and its recipe, pull new apartment permits (permit issued → leasing, apartments only, 20+ units),
  merging several permits into one row per project with its permit link. No hard-coded searches or places. Fixture tests. Commit.
- [ ] **L5 `project-details` (new).** One web lookup per project: street address, units,
  developer, expected opening, news link, website. Never guess; blank if not found. Fixture tests.
  Commit.
- [ ] **L6 `find-sales-news` (new).** News search for apartment sales in the state's cities, last
  24 months: building, buyer, date, units, link. Fixture tests. Commit.
- [ ] **L7 Software + who to call, any area.** Make `find-website`, `detect-software` and
  `contact-scrape` take any area (remove Plano paths); drop RealPage leads; contact = developer or
  new owner office phone + website, named person only from a permit/news page. Commit.
- [ ] **L8 `score-leads`, any area.** Remove Plano bits; rank soonest opening → units → not picked
  yet above competitor; one-line "why" per lead. Fixture tests. Commit.
- [ ] **L9 Small test run (💲 ~20 searches).** Run the whole chain on **one city** of the picked
  state, capped at 5 projects. Show Drew the 5 leads in plain words. **Stop -- Drew says go before
  L10.**
- [ ] **L10 Full state run (💲 ~450 searches) -- only after Drew's go.** Whole state until 150
  projects or the search cap; save recipes; spot-check 10 software calls; log to
  `propertystack/runs/`. Commit.
- [ ] **L11 Site: area buttons.** `site/data/build_data.py` builds every area under
  `propertystack/data/`; Early Leads shows one button per area with its own table, a city filter
  for state areas; remove the sidebar area dropdown. Plano–Richardson unchanged. Check passes.
  Commit.
- [ ] **L12 Chat knows every area.** The chatbot loads each area's leads; `SOUL.md` stops naming
  one county; deep dives work for the new state. Rebuild; run `tooling/qa/check-answers.sh`.
  Commit. Tell Drew in plain words it's ready to try.
