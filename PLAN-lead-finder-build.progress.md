# Progress log: PLAN-lead-finder-build

## 1.1 Skeleton + check + no-place-names test -- done

- Created `propertystack/skills/lead-finder/` with `SKILL.md` (describes all 6 parts,
  area-agnostic rule, caps) and a `run.py` stub (`--state`, `--run-id` args, not yet wired).
- Added `propertystack/skills/lead-finder/tests/test_no_place_names.py`: scans every
  `propertystack/skills/lead-finder*/**/*.py` (excluding fixtures and the test file itself)
  for literal US state names and a list of big cities/counties (including Plano, Richardson,
  Collin, Dallas); fails the check if any show up. Data files (csv/json) are exempt by design
  -- only code is scanned.
- Added `tooling/qa/check-lead-finder.sh`: runs pytest on every `lead-finder*/tests` dir plus
  `tooling/qa/check-panel.sh`, matching the pattern used by `check-client-map.sh`.
- Deleted the 4 old Plano-only skills: `propertystack/skills/{find-apartments,find-sales,
  build-table,scout-areas}` (code only -- checked first that nothing else in the repo imports
  their code; their historical run JSON files under `propertystack/runs/` and the Dallas data
  in `propertystack/data/dallas-parked/` were left alone since `site/data/build_data.py` reads
  those run files by skill name, not the skill code).
- Checked: `bash tooling/qa/check-lead-finder.sh` passes (2 tests + panel check clean).
  Also ran `python3 site/data/build_data.py` directly to confirm the site still builds after
  the deletions -- it does (properties, leads, pipeline, client-map all wrote fine).
- Nothing left open for this task. Next task (1.2) adds the actual lead record format and
  `docs/LEAD-FORMAT.md`.

## 1.2 One lead format -- done

- Added `propertystack/skills/lead-finder/record.py`: `LeadRecord` dataclass with every field
  from the plan (area, city, name, address, lat/lon, units, stage, permit_date, opening_date,
  sale_date, buyer, developer, office_phone, website, software, links, sources, why),
  `STAGE_ORDER`/`stage_rank` for planned < permitted < under construction < leasing < sold,
  `save_records`/`load_records` for JSON round-trips, `normalize_address` (self-contained --
  no `usaddress` dependency, since it's not installed and there's no venv/requirements file in
  this repo to add it to; wrote a small suffix/unit-word normalizer instead that passes the
  plan's example: "123 Main St" and "123 Main Street Bldg B" normalize the same), and
  `haversine_meters` for the 75m geocode check.
- Added `propertystack/skills/lead-finder/merge.py`: `same_building()` (normalized address
  match, or within 75m + shared developer/name word) and `merge_records()` (one record per
  building, keeps the most advanced stage, keeps every source and link from both records --
  a planned project that gets a permit is upgraded in place, not duplicated).
- Added `docs/LEAD-FORMAT.md` describing every field and the merge rules.
- Added `propertystack/data/_sample/leads.json` (+ README marking it clearly fake) -- two
  fixture records for later parts' tests, never built into the real site.
- Tests: `tests/test_record.py` (stage ordering, address normalization incl. the tricky
  "123 Main St" vs "123 Main Street Bldg B" pair, save/load round-trip, sample fixture loads)
  and `tests/test_merge.py` (address match, geocode+name match, geocode-without-shared-name
  stays separate, far-apart stays separate, stage upgrade keeps all sources/links, distinct
  buildings stay distinct, planned-then-permitted upgrades not duplicates).
- Checked: `bash tooling/qa/check-lead-finder.sh` -- 17 tests pass (was 2), panel check clean.
  Also reran `python3 site/data/build_data.py` to confirm the site still builds unaffected.
- Nothing left open. Next task (1.3) adds the web helper (SearXNG/Jina search + cached page
  reads).

## 1.3 Web helper -- done

- Added `propertystack/skills/lead-finder/fetch.py`: `WebHelper` class wrapping search and
  page reads for every later part.
  - `search()`: calls `tooling/searx_search.py` (free, local) first; falls back to Jina
    (`https://s.jina.ai/<query>`, key read from `/home/drewp/main-projects/realpage/.env`
    `JINA_API_KEY`, never hardcoded/committed) only when SearXNG raises (down) or returns no
    results. `SearchCounts` tracks `searxng` vs `jina` call counts separately so a run's search
    budget can tell free from paid calls apart, matching the plan's "every search counted
    (Jina logged separately)".
  - `fetch()`: page reads go through a fallback chain -- crawl4ai first, Scrapling if the
    result looks blocked, Playwright last (all three are installed in this environment, so no
    stub was needed). Every fetched page is cached on disk under
    `propertystack/runs/cache/<sha256(url)>.html` and never re-read (cache hit returns
    `from_cache=True`, fetcher never called again). Visits to the same site (by netloc) are
    spaced >= 2 s apart. A page whose HTML matches common block markers ("access denied",
    "captcha", "403 forbidden", etc.) counts as a block for that site; after 3 blocks the site
    is marked skipped with a reason and every later `fetch()` for that site returns immediately
    without calling any fetcher again.
  - `propertystack/runs/cache/` added to `.gitignore` (only result JSON from later steps gets
    committed, per the plan).
- Tests: `tests/test_fetch.py`, all with fake `searx_search`/fetcher callables injected via
  `WebHelper(..., searx_search=..., page_fetchers=...)` -- no real network, SearXNG, Jina, or
  browser calls. Covers: SearXNG-has-results (no Jina call), SearXNG down (OSError) falls back
  to Jina, SearXNG returns empty falls back to Jina, no Jina key configured returns nothing
  instead of guessing, cache hit skips the fetcher entirely, 3 blocks in a row skip the site and
  a 4th URL on that site never reaches any fetcher, and the crawl4ai-fails -> scrapling-blocked
  -> playwright-succeeds fallthrough chain.
- Checked: `bash tooling/qa/check-lead-finder.sh` -- 24 tests pass (was 17), panel check clean.
  Also reran `python3 site/data/build_data.py` to confirm the site still builds unaffected.
- Nothing left open. Next task (1.4) adds the run folder, resume, caps, and state pick.

## 1.4 Run folder, resume, caps, state pick -- done

- Added `propertystack/skills/lead-finder/runfolder.py`:
  - `pick_state()`: reads `propertystack/data/client-map/targets.json` (the 15 states) and
    `counts.json` (RealPage counts per state), picks the state with the lowest `total` in
    counts.json (a state missing from counts.json counts as 0), ties broken by more permits
    (`permits_5plus_12mo`) winning. Returns the pick plus the full ordered backup list, so a
    caller can roll to the next state on the list if the first one nets too few projects.
  - `RunCaps`: tracks `project_count`, `searxng_searches`, `jina_searches` separately (so Jina
    usage stays visible per the fetch.py counting from 1.3); `project_cap_hit()` (150),
    `search_cap_hit()` (~450 total searches), `any_cap_hit()`, and `below_minimum()` (<30
    projects -> roll into next state).
  - `RunFolder`: `propertystack/runs/<state>/<run-id>/` with `step_file(step, city)` giving one
    JSON file per step per city (spaces in city names replaced so paths stay simple);
    `step_done()`/`load_step()` let a later run skip any step whose output file already exists
    (resume); `save_state_pick()` writes the pick + backup order into the run folder;
    `save_caps()`/`load_caps()` persist the running totals so a resumed run continues counting
    instead of resetting to zero.
  - Wired into `run.py`: with no `--state` given it calls `pick_state()` and prints the pick and
    backup order; `--run-id` resumes an existing folder, otherwise a UTC timestamp names a new
    one; the folder is created and its path printed. The actual chain steps (2.1 onward) still
    need to be plugged in -- this task only builds the folder/resume/caps/pick scaffolding the
    plan asked for.
- Tests: `tests/test_runfolder.py` -- `pick_state` (lowest total wins, missing-from-counts
  treated as 0, tie broken by more permits), `RunFolder` resume (step file doesn't exist until
  saved, then loads back the same data), one file per step per city (two cities' files don't
  collide), state-pick and caps round-trip through disk, and all four `RunCaps` cases (project
  cap hit, search cap hit, below-minimum roll-into-next-state, under all limits).
- Checked: `bash tooling/qa/check-lead-finder.sh` -- 34 tests pass (was 24), panel check clean.
  Also ran `python3 propertystack/skills/lead-finder/run.py --state ZZ_TEST --run-id testrun1`
  by hand to confirm the folder gets created and printed correctly (then deleted the test
  folder), and reran `python3 site/data/build_data.py` to confirm the site still builds
  unaffected.
- Nothing left open. Next task (2.1) starts Part 2: ranking a state's cities from the free
  Census Building Permits Survey place-level files.
