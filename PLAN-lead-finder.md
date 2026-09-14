# PropertyStack: lead finder (any area, new buildings first)

Rewritten 2026-09-13 with Drew (all answers: `/home/drewp/main-projects/handoffs/2026-09-13-area-finder-plan-answers.md`).
**NOT approved to run yet** -- planning with Drew. This file is now the **rules + map**; the work is
split into 6 plans (below) so several `/gowork` runs can build at the same time. Runs after `PLAN-client-map.md` (done).
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
- **Early signals (added 2026-09-13):** city council / planning agendas (Legistar first, then
  civic-scraper platforms) → projects shown as **"Planned (not permitted yet)"**, ranked **below**
  permitted ones, upgraded when a permit appears. **HUD FHA loan list** (221(d)(4) = new building,
  223(f) = likely sale/refi). **State housing agency award lists** (found via NCSHA / Novogradac;
  saved as per-state recipes). Skip: HUD LIHTC list (years stale), NHPD (non-commercial),
  Google Maps scraping, email guessing. Later: job posts as timing signal, HUD owner/manager list.
- **Software check:** our own fingerprint rules file (Wappalyzer-style format, our own rules for
  RealPage / Yardi / Entrata / AppFolio / ResMan / MRI …); cheap HTML check first, browser only if
  unclear; a **double check** before any "RealPage" or "competitor" verdict.
- **Phones:** `phonenumbers` finds and de-duplicates numbers; office lines above fax/cell.
- **Resume:** every step writes to a run folder; a stopped run picks up where it left off.
- **Tools (all local, run only in harness sessions in this folder, never the deployed chatbot):**
  this Claude session, **SearXNG first** (`tooling/searx_search.py`, `127.0.0.1:8888`), **Jina only
  as fallback** (paid, capped), crawl4ai (`localhost:11235`), Scrapling (stubborn sites, before Playwright), Playwright + stealth, Claude web
  search/fetch, Socrata/ArcGIS catalog APIs (find city permit data), GDELT (sale news), usaddress +
  Census batch geocoder (matching). No Ollama. `tooling/pms_detect.py`, Census data, optional
  Reddit/X (read-only). No LinkedIn.

## The 6 plans (build order)
1. **`PLAN-lf-1-core.md`** -- shared base: skeleton, one lead format, web helper, run folder +
   resume, caps. **Must finish first.**
2. Then these four can run **at the same time** (each only touches its own folders):
   - **`PLAN-lf-2-permits.md`** -- cities → permit sources → new apartment projects → details.
   - **`PLAN-lf-3-early-signals.md`** -- meeting agendas, HUD loan list, state award lists.
   - **`PLAN-lf-4-software-contacts.md`** -- software check, sale news, who to call, ranking.
   - **`PLAN-lf-5-site-chat.md`** -- Early Leads area buttons + city filter, chat knows every area
     (built on sample data).
3. **`PLAN-lf-6-run.md`** -- after 1-5 are merged: wire the chain, small test run (**stops for
   Drew's go**), full state run, fill the site.

Every plan runs on its own safe copy and is merged into `local-test`. Nothing is pushed until
Drew has tried it on localhost and said OK.

Check (all lead-finder plans): `bash tooling/qa/check-lead-finder.sh`
