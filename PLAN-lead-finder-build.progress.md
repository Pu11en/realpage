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

## 2.1 Rank the state's cities (free) -- done

- Added `propertystack/skills/lead-finder-cities/rank.py`: for any state (two-letter code),
  ranks cities -- and unincorporated-county permit areas -- by new 5+ unit apartment permits,
  using the free Census Building Permits Survey **place-level** region files
  (`Place/<Region> Region/<rg>YYMMc.txt`), summed over the last N months (12 default, `--months`
  for up to 24). Self-contained: I found that `client-map/targets.py` (which already had very
  similar place-file parsing logic from client-map's C2 task) imports `scout-areas/census.py`,
  but `scout-areas` was one of the 4 skills deleted in 1.1 -- that import is already broken on
  this branch (confirmed by running client-map's own tests, which fail the same way,
  independent of my change). Rather than depend on that dangling import, `rank.py` has its own
  small cached `fetch()` and place-file parser, kept in `lead-finder-cities/` only.
  - Unlike `targets.py` (which drops rows matching "county"), `parse_places_all()` keeps them
    and tags `is_county_area=True`, per the plan's "add unincorporated county areas as cities
    when the county issues the permits."
  - `realpage_counts()` reads `propertystack/data/client-map/counts.json` for that state's
    per-city RealPage building counts (0 if the state or city isn't listed yet).
  - `build()` writes `propertystack/data/<state-slug>/cities.json` (state-slug = lowercase
    2-letter code), sorted by permits descending, each row: city, is_county_area, permits_5plus,
    realpage_count.
- Tests: `tests/test_rank.py` -- ranks and sorts a fixture with two cities + one county area +
  one out-of-state city (filtered out), county area kept and tagged, RealPage counts read from a
  fixture counts.json (including missing-state and missing-file cases), and `build()` writes to
  the right `<state-slug>/cities.json` path. Used fictional place names in the fixture (not real
  Texas cities) since the 1.1 no-place-names test scans every `.py` file under `lead-finder*/`
  (not just non-test code) for banned literals.
- Checked: `bash tooling/qa/check-lead-finder.sh` -- lead-finder-cities' own 4 tests pass, plus
  lead-finder's existing 34 (unaffected) and the panel check, all clean. Also reran
  `python3 site/data/build_data.py` to confirm the site still builds unaffected.
- Left open (pre-existing, not part of this task): `client-map/targets.py` still imports the
  deleted `scout-areas/census.py` and its own tests (`propertystack/skills/client-map/tests/
  test_targets.py`) currently fail to collect for the same reason -- this predates my change
  (task 1.1 deleted scout-areas) and isn't covered by `check-lead-finder.sh` (which only runs
  `lead-finder*` dirs), so it wasn't caught until now. Flagging here since a later task may want
  to either restore a small shared census-fetch helper or point `targets.py` at
  `lead-finder-cities/rank.py`'s self-contained version instead.
- Next task (2.2) adds permit recipes (Socrata/ArcGIS catalog lookup) per city.

## 2.2 Permit recipes + catalog lookup -- done

- New skill `propertystack/skills/lead-finder-sources/find_sources.py`:
  - `find_sources(city, state, http_get, recipes_dir=...)`: tries the free **Socrata
    Discovery API** first (`https://api.us.socrata.com/api/catalog/v1?q=<city>+building+permits`),
    then the **ArcGIS Hub search** API (`https://hub.arcgis.com/api/search/v1/collections/dataset/items?q=<city>%20building%20permits`)
    if Socrata has nothing. For each catalog candidate whose name mentions "permit", it pulls
    a small sample of rows (`$limit=20` for Socrata, `features` for an ArcGIS FeatureServer
    query) and runs `test_dataset(rows)`, which only accepts the dataset if the sample has a
    units-like or date-like field and reports how many of the sampled rows look multifamily
    (matching "multifamily"/"apartment"/"dwelling" across the row's values) -- an empty or
    clearly irrelevant dataset is rejected, never saved as a recipe.
  - A working recipe is written to `propertystack/recipes/<city-slug>.json`: city, state,
    system (`socrata`/`arcgis`), endpoint, guessed field-name mapping (permit_type, issue_date,
    units, address -- guessed by matching column names, since real catalogs don't standardize
    field names), `date_tested` (today), and a `completeness` note describing what the test
    found. No catalog hit -> returns `None` and writes nothing, so 2.3's portal-search fallback
    has something to do.
  - Both catalog calls and the sample-row fetch go through one injectable `http_get(url) ->
    dict|list` so tests never touch the network (per the plan's fixture-test rule); `run.py`
    (2.2's real caller, wired in later at 6.1) will pass a real HTTP GET.
  - Used fictional city names (Rivertown, Cedarville, Oakford) in the fixtures/tests, matching
    2.1's convention, since the 1.1 no-place-names test scans every `.py` file under
    `lead-finder*/`.
- Tests: `tests/test_find_sources.py` -- Socrata catalog hit saved as a recipe with guessed
  fields and the right completeness count; ArcGIS Hub used when Socrata returns nothing; no
  catalog hit anywhere returns `None` and saves no file; a dataset with no units/date-like
  field is rejected even though its catalog entry matched; `test_dataset()` and `slugify()`
  exercised directly.
- Checked: `bash tooling/qa/check-lead-finder.sh` -- lead-finder-sources' own 6 tests pass,
  plus all other lead-finder* tests (34 lead-finder + 4 lead-finder-cities, unaffected) and the
  panel check, all clean.
- Nothing left open. Next task (2.3) adds the `find-sources` fallback for cities with no
  catalog hit: search for the city's permit portal, identify the system by URL/markup pattern,
  test on 5 permits, save the recipe the same way.

## 2.3 `find-sources` fallback -- done

- Added `propertystack/skills/lead-finder-sources/find_sources_fallback.py`, used only after
  2.2's catalog lookup (`find_sources.find_sources`) returns `None`. Takes injectable
  `search_fn`/`fetch_fn` (real callers will pass `WebHelper.search`/`WebHelper.fetch` from
  1.3's `fetch.py`, matching its search/cache/block-limit behavior for free).
  - `find_sources_fallback(city, state, search_fn, fetch_fn, recipes_dir)`: searches for the
    city's permit portal, and for each result tries to identify the system from the URL, then
    from the fetched page's HTML if the URL alone doesn't match -- patterns cover Accela
    Citizen Access, Tyler EnerGov/CSS, OpenGov, CentralSquare, and MyGovernmentOnline (regexes
    in `SYSTEM_PATTERNS`). A recognized system's page is "tested on 5 permits" by counting
    permit-number-like rows (`count_sample_permits`); fewer than 5 and that result is skipped,
    not saved.
  - If no portal result passes, it falls back to a city-published report file (PDF/XLSX/CSV
    matched by extension in the search results) and applies the same 5-permit test to its text.
  - Nothing usable anywhere -> returns `{"skipped": True, "reason": "no permits online"}` and
    saves no recipe file, per the plan ("nothing online -> city skipped: no permits online").
  - A working hit is saved as a recipe the same way as 2.2:
    `propertystack/recipes/<city-slug>.json` with system, endpoint, date_tested, and a
    completeness note (permits sampled, how many look multifamily).
- Tests: `tests/test_find_sources_fallback.py` -- Accela portal identified from the URL and
  saved; a system identified from page HTML when the URL itself doesn't match (Tyler EnerGov);
  a portal that matches a known system but has too few sample permit rows is rejected, and the
  search falls through to a monthly PDF report which passes instead; nothing online at all
  returns the skip note and writes no file; `identify_system`/`count_sample_permits`/
  `count_multifamily_hits` exercised directly; `slugify`.
- Checked: `bash tooling/qa/check-lead-finder.sh` -- lead-finder-sources now has 12 tests (was
  6, +6 for this task), all lead-finder* dirs total 50 passing, panel check clean. Also reran
  `python3 site/data/build_data.py` to confirm the site still builds unaffected (204 properties,
  42 leads, 20 states in the client map).
- Nothing left open. Note: this task only covers the fallback *lookup*; wiring 2.2's
  `find_sources()` and this fallback together into one "try catalog, then fallback" entry point
  for a city happens at 6.1 when the whole chain is assembled, per the plan's own ordering.
- Next task (2.4) rebuilds `find-upcoming` for any city: city + recipe -> new apartment permits
  with stage inferred from issue date / certificate of occupancy.

## 2.4 `find-upcoming` rebuilt for any city -- done

- Added `propertystack/skills/lead-finder-permits/find_upcoming.py`:
  `find_upcoming(city, state, area, recipe, http_get, today=None)` takes a 2.2/2.3 recipe
  (endpoint + guessed field mapping) and returns one `LeadRecord` per apartment project.
  - Keeps a row if its permit-type/description field matches multifamily/apartment, or (if
    that's unclear) any field on the row does, or units >= 20.
  - Stage comes only from dates found on the row, never guessed: looks for a
    certificate-of-occupancy-like field by regex (since 2.2's recipe fields don't include one)
    -- CO within the last 6 months -> `leasing`; CO older -> dropped (past the "upcoming"
    window). No CO: permit issued within the last 24 months -> `permitted`; older, or no
    usable date at all -> dropped. `today` is injectable so tests are deterministic.
  - Units stay `None` when the row's units field is blank/unparseable, per the plan ("unknown
    units kept for 2.5 to fill" -- 2.5 isn't built yet, so this task doesn't drop them).
  - Several permit rows for the same address are merged into one record by reusing 1.2's
    `merge.merge_records` (imported from `lead-finder/`), keeping the permit link.
  - Handles both response shapes from 2.2 (`http_get` returning a raw list for Socrata, or a
    dict with `features`/`attributes` for ArcGIS); a missing endpoint or a raised exception from
    `http_get` (site down) returns an empty list rather than guessing.
- Tests: `tests/test_find_upcoming.py` -- recent permit with no CO -> permitted; recent CO ->
  leasing; old CO -> dropped; old permit with no CO -> dropped; a low-unit non-apartment permit
  -> dropped; a large unit count counts as apartment even when the type field is ambiguous;
  blank units field kept as `None` (not dropped, not guessed); two permits at the same address
  merge into one record; no endpoint / an `http_get` exception both return `[]`; the ArcGIS
  `features`/`attributes` response shape works the same as Socrata's flat list. Used a fictional
  city ("Rivertown") and state code ("ZZ"), matching 2.1-2.3's convention.
  - First draft of the module docstring/SKILL.md said "Plano-only" describing the *old* skill
    being replaced -- the no-place-names test in 1.1 scans every `.py` file under `lead-finder*/`
    regardless of context, so that failed the check; reworded to "single-city" instead (same
    meaning, no banned literal) and reran clean.
- Checked: `bash tooling/qa/check-lead-finder.sh` -- lead-finder-permits' own 11 tests pass, all
  other lead-finder* dirs unaffected (4 + 12 + 34 = 50 total before this task, still passing),
  panel check clean. Also reran `python3 site/data/build_data.py` to confirm the site still
  builds unaffected (204 properties, 42 leads, 20 states).
- Left alone (out of scope for this task): the old single-city `find-upcoming` skill still lives
  at `propertystack/.claude/skills/find-upcoming/` (Legistar-only) -- 1.1 only deleted
  `find-apartments`/`find-sales`/`build-table`/`scout-areas`, and the plan doesn't ask to delete
  this one yet. The new chain (wired at 6.1) will use `lead-finder-permits/find_upcoming.py`
  instead; the old skill can be removed once nothing depends on it, but that's not this task.
- Nothing left open for this task. Next task (2.5) adds `project-details`: clean addresses
  (Census batch geocoder) and one web lookup per project for units/developer/opening
  date/news/website, dropping any project whose units are still unknown after that lookup.

## 2.5 `project-details` (new) -- done

- Added `propertystack/skills/lead-finder-details/project_details.py`:
  - `geocode_address(address, city, state, geocode_fn)`: looks up lat/lon via the free Census
    one-line/batch geocoder (`geocoding.geo.census.gov/geocoder/locations/onelineaddress`),
    taking an injectable `geocode_fn(query) -> parsed JSON` so tests never hit the network.
    Blank address, no match, or a raised exception (site down) all return `None` rather than
    guessing -- callers keep whatever lat/lon they already had.
  - `fill_project_details(record, search_fn, fetch_fn, geocode_fn=None)`: the one web lookup per
    project the plan asks for. Geocodes the address first (if `geocode_fn` given) to make later
    75m merge matching (1.2) reliable, then does one `search_fn` call for the address + city +
    "apartments" and walks the results: picks a non-news result as `website`, a news-domain
    result (matched by hostname keywords: news/journal/times/tribune/herald/business/press) as
    `links["news"]`, then fetches results in order with `fetch_fn` and pulls units (regex like
    "220-unit"/"220 units"), developer ("developed by X" / "developer: X"), and opening date
    ("now leasing March 2026" style) from the first page that has them -- never guessing, only
    ever using what's actually on the page, and each fact filled gets a `sources` entry with the
    URL it came from. Stops fetching once units are found. A project whose units are still
    `None` after the lookup returns `None` (dropped), per the plan ("still-unknown units ->
    drop"). Units already known (e.g. from 2.4's permit data) are never overwritten by a lower-
    confidence web guess.
  - Handles both a dataclass-like `FetchResult` (from 1.3's `fetch.py`, `.ok`/`.html`) and a
    plain dict shape for `fetch_fn`'s return, so tests can use either.
- Tests: `tests/test_project_details.py` -- geocode success/no-match/blank-address/exception
  cases; a full fill (units + developer + opening date + website) from one page; picking a news
  link separately from the website when both are in the search results; dropping when units stay
  unknown after search+fetch; not overwriting units that were already known; no search results
  at all still drops when units are unknown; geocode results applied to lat/lon when a
  `geocode_fn` is passed; a blocked/not-ok fetch result is skipped and the next search result is
  tried instead. Found and fixed two regex bugs while writing these tests: the developer regex
  wasn't matching text right after "developed by" (needed an explicit optional-space + lazy stop
  at the next `.`/newline), and the opening-date regex's greedy gap quantifier was letting a
  bare year ("2026") win over "March 2026" during backtracking -- made it lazy (`{0,20}?`) so it
  prefers the shortest gap and the full month+year match wins.
- Checked: `bash tooling/qa/check-lead-finder.sh` -- lead-finder-details' own 11 tests pass, all
  other lead-finder* dirs unaffected (4 + 11 + 12 + 34 = 61 before this task, all still passing;
  72 total now), panel check clean. Also reran `python3 site/data/build_data.py` to confirm the
  site still builds unaffected (204 properties, 42 leads, 20 states).
- Nothing left open for this task. Next task (3.1) starts Part 3: the HUD FHA multifamily loan
  list (firm commitments/endorsements spreadsheet, filtered by state/units/age, 221(d)(4) vs
  223(f)).

## 3.1 HUD FHA loan list -- done

- Added `propertystack/skills/lead-finder-hud/hud_loans.py`. Downloaded the real workbook
  from `https://www.hud.gov/sites/default/files/Housing/documents/FHA-MF-Firm-Commitments-and-Endorsements-Database-FY01-FY26-Q3.xlsx`
  (linked from https://www.hud.gov/hud-partners/multifamily-data) and printed its real
  header row first, per the plan: `FHA Number, Project Name, Project City, Project State,
  Program Type, Program Category, Activity Description, Activity Group, Facility Type,
  Program Subcategory, Firm Activity, Lender Name for Firm Activity, Mortgage Amount,
  Total Units, Firm Activity Date, Fiscal Year at Firm Activity, MAP or TAP, LIHTC, Tax
  Exempt Bonds, Home, CDBG, Refi 202, IRP Decoupling, Hope VI, Current Status`. The header
  sits at row 9 (there's a 8-row title block above it), and the program code lives in
  "Program Subcategory" (e.g. "221(d)(4) NC/SR", "223(f) Refi/ Purchase Apts") -- matched
  with a loose regex since HUD's own docs show it written a few ways ("221(d)(4)", "221D4").
  - `fetch_workbook_bytes()`: downloads once into `propertystack/data/raw/hud/` (already
    covered by that directory's own `.gitignore`, so the ~8MB file never gets committed),
    reads from cache after that -- same pattern as 2.1's Census fetcher.
  - `load_sheet_rows(bytes)`: opens the "Firm Commitments" sheet with `openpyxl` (added as
    a dependency -- the repo had no xlsx reader yet; installed with
    `pip install --user --break-system-packages openpyxl` since the system Python is
    externally managed), skips the title block, returns one dict per row keyed by the real
    column names.
  - `parse_hud_rows(rows, state, min_units=20, months=36, today=None)`: the pure filtering
    logic (state match, units >= 20, Firm Activity Date within the window, program code ->
    stage). 221(d)(4) -> `permitted` ("HUD FHA 221(d)(4) firm commitment for new
    construction"); 223(f) -> `sold` ("HUD refi or sale (FHA 223(f))"); any other program
    code dropped. Missing units or missing/future date -> dropped, never guessed. Takes
    plain dicts so tests never need openpyxl or the network.
  - `find_hud_loans(state, ...)`: the end-to-end entry point (download -> load -> filter).
  - HUD gives city/state but no street address, so `address` stays blank on these records --
    1.2's merge only works off name/geocode for these until an address shows up from
    another source (permits, agenda, news).
- Bug caught by a real-data smoke test, not by the unit tests: my first header-row constant
  (9) was off by one -- running `find_hud_loans("TX")` against the real cached workbook
  returned 0 rows for a state that clearly has hundreds. Traced it to reading one row too
  far as the header (columns came out as a jumble of two data rows' values). Fixed to 8 and
  reran against the real file -- 211 Texas leads came back correctly (211 total; a mix of
  permitted/new-construction and sold/refi rows). Left the real xlsx cached at
  `propertystack/data/raw/hud/` for reuse by 6.x's real run (that directory is gitignored).
- Tests: `tests/test_hud_loans.py` (13 tests, all against a fictional state code "ZZ" and
  city "Rivertown") -- 221(d)(4) -> permitted with the right why/units/city
  (title-cased)/permit_date/HUD link; 223(f) -> sold with "HUD refi or sale" in the why;
  wrong state dropped; missing/too-low units dropped; missing/older-than-36-months/future
  date dropped; an unrelated program code (542(c) HFA Risk Sharing) dropped; the "221D4"
  no-punctuation spelling still matches; the `_program_stage` helper returns `None` for
  unrelated or blank text; `find_hud_loans` with an injected fetcher/loader and
  case-insensitive state matching.
- Checked: `bash tooling/qa/check-lead-finder.sh` -- lead-finder-hud's own 13 tests pass,
  every other lead-finder* dir unaffected (72 before this task, 85 total now, all passing),
  panel check clean. Also reran `python3 site/data/build_data.py` to confirm the site still
  builds unaffected (204 properties, 42 leads, 20 states in the client map) and
  `git status --short` shows only the new `lead-finder-hud/` directory as untracked (the
  cached xlsx is excluded by `propertystack/data/raw/.gitignore`).
- Nothing left open for this task. Note for whoever wires 6.1: `find_hud_loans` needs the
  `openpyxl` package installed (not previously a repo dependency) -- if a fresh environment
  is missing it, install with `pip install --user --break-system-packages openpyxl` before
  running the real chain.
- Next task (3.2) is the state housing agency awards list (NCSHA/Novogradac tax-credit and
  bond award PDFs/spreadsheets, per-state recipe, new-construction only).

## 3.2 State housing agency awards (2026-09-14)
Added `propertystack/skills/lead-finder-awards/` (`awards.py` + `SKILL.md` + tests).
- `find_award_recipe()`: searches `"<agency>" housing tax credit awards 2025/2026` and
  `"<agency>" "bond" "awards"`, saves the first PDF/xlsx hit as `propertystack/recipes/awards-<state>.json`.
  No hit -> `{"skipped": True, "reason": "no award list online"}`.
- `load_pdf_table_rows()` (pdfplumber) / `load_xlsx_rows()` (openpyxl) are dumb table readers.
- `parse_award_rows()`: rows -> LeadRecords (stage "planned"), keyed off loose column-name
  matching (any header containing "unit"/"date"/"project"/"city"/"developer"). Drops rows with
  no units or date, under 20 units, older than 36 months, or whose type/activity column matches
  rehab/preservation.
- `find_awards()` wires it end to end; CLI entry point mirrors lead-finder-hud's.
Checked: `bash tooling/qa/check-lead-finder.sh` (34 lead-finder-awards+existing tests pass,
no-place-names test passes, check-panel.sh clean). Fixture-only tests, no network used.
Nothing left open for this task; a real state/agency's exact award-list column names will only
be confirmed at the 6.x full-run steps.
Commit: (see git log)

## 3.3 Which meeting system does a city use? (done)
Built `propertystack/skills/lead-finder-agendas/agendas.py`: `find_meeting_system(city, state, search_fn, fetch_fn)`
searches `"<city>" "<state>" planning commission agenda`, matches the first result's URL
(or fetched HTML if the URL doesn't give it away) against known system fingerprints
(legistar, agendacenter, granicus, primegov, civicclerk, boarddocs, escribemeetings, iqm2),
and caches the identified system + agenda URL as `propertystack/recipes/agendas-<city>.json`.
No online hit -> `{"skipped": True, "reason": "no agenda system identified"}`, never guessed.
Followed the same shape as lead-finder-sources (2.3) fallback code for consistency.
Checked: `python -m pytest propertystack/skills/lead-finder-agendas/tests -q` (5 passed) and
`bash tooling/qa/check-lead-finder.sh` (all green, no place-name test still clean).
Nothing left open for this task.

## 3.4 Legistar reader -- done

- Added `propertystack/skills/lead-finder-legistar/legistar.py`: `find_legistar_matters(city,
  state, area, client, http_get, today=None)` -- calls the free Legistar Web API
  (`https://webapi.legistar.com/v1/<client>/`): `bodies` to find Planning/Zoning/Council body
  IDs by name match, `events?$filter=EventDate ge datetime'<12mo ago>'` for those bodies'
  meetings, then `events/<id>/eventitems` per meeting for agenda items. Keeps only items whose
  matter title matches multifamily/apartment/unit-count/rezoning/site-plan; dedupes matters seen
  across multiple meetings; pulls an address and unit count out of the title with regex when
  present, folds a case number into the `why` line, and builds the agenda link as
  `https://<client>.legistar.com/LegislationDetail.aspx?ID=<matterId>`. Returns merged
  `planned`-stage `LeadRecord`s via `merge.py` (1.2).
- Any city whose Legistar API call raises (token-required instances, or unreachable) or that has
  no Planning/Zoning/Council body returns a skip-note dict (`{"skipped": True, "reason": ...}`),
  never guessed at, matching the 3.3 agendas skill's pattern.
- `tests/test_legistar.py`: 5 fixture tests (fake `http_get`, no network) -- multifamily matter
  becomes a planned record with address/units/case parsed out; non-matching body and non-keyword
  items dropped; token-required/unreachable API returns the skip note; no planning/zoning/council
  body returns the skip note; the same matter appearing at two meetings is deduped to one record.
- Checked: `bash tooling/qa/check-lead-finder.sh` passes -- all lead-finder* skill test dirs
  (including the new one) plus the no-place-names scan and `check-panel.sh` are clean.
- Nothing left open. Next task (3.5) covers non-Legistar systems (CivicPlus/Granicus/PrimeGov/
  CivicClerk) plus raw PDF agendas via civic-scraper.

## 3.5 Other systems + PDFs -- done

- Added `propertystack/skills/lead-finder-civic/civic_agendas.py`, covering the four
  systems 3.3 can identify that 3.4's Legistar reader doesn't handle: AgendaCenter
  (CivicPlus), Granicus, PrimeGov, CivicClerk. `civic-scraper` (named in the plan) isn't
  installed in this environment (`pip show civic-scraper` -> not found) and there's no
  requirements file in the repo to add it to (same situation 1.2 hit with `usaddress`);
  since these four systems' listing pages all reduce to "find agenda/packet document
  links on an HTML page, then read the PDF", a small self-contained reader does the same
  job without a new dependency.
  - `find_civic_agenda_items(city, state, recipe, fetch_fn, ocr_fn=None)`: takes a 3.3
    recipe (`system` + `agenda_url`); unsupported system (legistar -- 3.4 already covers
    it) or a recipe missing `agenda_url` returns a skip note immediately. Fetches the
    listing page, pulls agenda/packet links with `find_agenda_links()` (href ending
    .pdf/.html whose href or link text mentions "agenda" or "packet", resolved to an
    absolute URL). No links found -> skip note ("no agenda documents found").
  - For each linked packet: **packets over 25 MB are skipped** by checking
    `len(content)` before ever calling PyMuPDF on it (per the plan, "packets over 25 MB
    skipped"); a non-PDF link (bare `.html` agenda page, no page structure to window
    around) is skipped too, since this task's job is packet PDFs specifically -- an HTML
    agenda page's structure is too system-specific to generalize safely without guessing.
  - `extract_pdf_pages(pdf_bytes, ocr_fn=None)`: one text string per page via PyMuPDF
    (`fitz`, already installed -- confirmed with `import fitz` before writing this).
    A page with no extractable text at all runs through the caller's `ocr_fn` (rendered
    to a PNG via `page.get_pixmap()`) if one was given; no OCR engine ships with this
    repo, so real runs will need to supply `ocr_fn`, but nothing here guesses or fakes
    OCR when it's absent -- the page just stays blank and won't match a keyword.
  - `keyword_hit_windows(pages_text, window=5)`: same keyword regex as 3.4's Legistar
    reader (multifamily/apartment/unit count/rezoning/site plan); only pages within 5
    pages of a hit are kept (**"at most the 10 pages around a keyword hit"**), not the
    whole packet -- matches the plan's page-budget instruction directly rather than
    reading every page of a 200-page packet.
  - This part only returns raw `AgendaHit(url, page, text)` objects (the packet URL +
    page number + nearby text) -- per the plan's own split, turning a hit into a
    planned-project LeadRecord (address/case number required) is task 3.6, not this one.
- Tests: `tests/test_civic_agendas.py` (14 tests, no network) -- link extraction filters
  to agenda/packet links and resolves relative URLs; `is_pdf` magic-bytes check;
  keyword-window keeps only nearby pages and returns empty with no hit; real PDF text
  extraction against tiny in-memory PDFs built with PyMuPDF itself (`fitz.open()` +
  `new_page()` + `insert_text()`, no fixture files needed); OCR fallback used only when a
  page truly has no text; unsupported system / missing agenda_url / unreachable listing /
  no links found all return the right skip note; an end-to-end fetch_fn fake finds a
  keyword hit inside a fake packet and returns its URL+text; an oversized packet and a
  non-PDF link both return no hits without crashing.
- Checked: `bash tooling/qa/check-lead-finder.sh` -- lead-finder-civic's own 14 tests
  pass, every other lead-finder* dir unaffected (85 before this task, 99 total now, all
  passing), panel check clean. Also reran `python3 site/data/build_data.py` to confirm
  the site still builds unaffected (204 properties, 42 leads, 20 states).
- Nothing left open for this task. Next task (3.6) turns agenda hits (from 3.4's
  Legistar matters and this task's civic hits) into planned-project LeadRecords: keep an
  item only if it has an address or case number, pull name/address/developer/units/case
  number, merge P&Z + council into one project per case.

## 3.6 Agenda hits -> Planned projects -- done

- Added `propertystack/skills/lead-finder-agenda-projects/agenda_projects.py`: the shared
  step that turns 3.4's Legistar matters and 3.5's civic `AgendaHit`s into planned-stage
  LeadRecords. `hit_to_project()` takes anything with `.url`/`.text`, requires an address
  or case number (bare keyword mentions with neither are dropped), and pulls out
  name/address/developer/units/case number with regex. `agenda_hits_to_projects()` merges
  hits for the same case number (or same address when there's no case number) into one
  project, so a rezoning discussed at both Planning & Zoning and Council becomes one
  record, not two.
- Tests: `tests/test_agenda_projects.py` (9 tests, no network) -- kept when address
  present, kept when case number present, dropped when neither, project name extraction,
  merge across two meetings by case number, merge by address with no case number, two
  distinct cases stay separate, empty input, all-weak-hits-dropped.
- Checked: `bash tooling/qa/check-lead-finder.sh` -- new skill's 9 tests pass, all other
  lead-finder* dirs unaffected (99 before, 108 total now, all passing), no-place-names
  scan and panel check clean.
- Nothing left open. Next task (4.1) starts software fingerprinting (RealPage/OneSite/etc)
  with our own Wappalyzer-format rules file.

## 4.1 Software fingerprints -- done

- Added `propertystack/skills/lead-finder-software/`: `rules.json` (our own Wappalyzer-format
  vendor rules -- url + html regex per vendor: RealPage, Yardi, Entrata, AppFolio, Buildium,
  ResMan, MRI, Knock, SightMap, Yotta, plus in-house UDR/Camden -- written from scratch, not
  copied from the GPL webappanalyzer technologies file), `detect.py` (portal -> hop-portal ->
  asset -> text -> in-house -> unknown, merging the proven approach from `tooling/pms_detect.py`),
  and `run.py` (`fill_software(records, web)` batch entry point over `LeadRecord`s, plus a
  standalone `in.json out.json` CLI).
- "Cheap page check first, full browser only if unclear" comes from reusing the shared
  `WebHelper.fetch()` (part 1.3), which already tries crawl4ai before Scrapling/Playwright and
  only falls back when a page looks blocked -- this skill never opens a browser directly, so no
  new code was needed for that rule.
- Area-agnostic: no place names in `detect.py`/`run.py`; rules.json has no place names either
  (checked by hand -- it's data, and the no-place-names test only scans code files anyway).
- Tests: `tests/test_detect.py`, 11 cases with a `FakeWeb` fixture (no network) -- link
  classification (portal wins over asset), text fallback, in-house fallback, hop-portal,
  no-website short-circuit (never fetches), blocked-site unknown_reason, and
  `fill_software` writing `links["software_proof"]` + a `sources` entry and skipping records
  with no website.
- Checked: `bash tooling/qa/check-lead-finder.sh` passes (glob already picks up the new
  `tests/` dir; 11/11 new tests plus every other lead-finder* skill's tests and check-panel.sh
  all green).
- Nothing left open. Next task (4.2) adds the second-check-before-verdict rule and drops
  RealPage buildings from the leads list.

## 4.2 Double check + drop RealPage -- done

- `lead-finder-software/detect.py`: added `_second_page_url` and `_confirm_on_second_page`.
  A `portal`, `asset` or `text` verdict now fetches a second page (the resident-portal link
  itself, or another link found on the homepage) and requires it to still show the same
  vendor before the verdict is final; no agreement, no second page to check, or a failed
  fetch all drop the verdict to `unknown` with `unknown_reason=unconfirmed`. `hop-portal`
  already involves two pages agreeing (the homepage link + the page it points to), so it's
  left as-is.
- `lead-finder-software/run.py` `fill_software`: a confirmed `"RealPage"` verdict now drops
  the record from the output entirely (not a lead). A confirmed competitor keeps its name;
  a record whose website was actually fetched but never confirmed a vendor becomes
  `"not picked"` (matches the `docs/LEAD-FORMAT.md` enum); a record with no website stays
  `"unknown"`.
- Updated `SKILL.md` to describe the second-page check and the RealPage-drop/not-picked
  rule.
- Tests added/updated in `tests/test_detect.py`: portal verdict needs the second page to
  confirm (added a confirming second page to the existing portal/hop-portal/fill_software
  fixtures so they still pass); new tests for an unconfirmed second page, a missing second
  page, `fill_software` dropping a confirmed RealPage record while keeping a Yardi one, and
  the unknown-after-fetch -> "not picked" / no-website -> "unknown" split.
- Checked: `python3 -m pytest propertystack/skills/lead-finder-software/tests -q` (16
  passed) and `bash tooling/qa/check-lead-finder.sh` (all suites + panel check clean).
- Nothing left open. Next task (4.3) is `find-sales-news`.

## 4.3 find-sales-news -- done

- Added `propertystack/skills/lead-finder-sales-news/sales_news.py`: `news_query()`
  builds the SearXNG news query (`"<city>" apartments sold OR acquires OR acquisition
  units`) covering the full 24-month window; `gdelt_url()` builds the GDELT DOC API
  URL (`mode=artlist&format=json`) as a freshness add-on queried in addition to, not
  instead of, SearXNG (GDELT DOC only indexes roughly the last 3 months). `hit_to_record()`
  turns one title/snippet/date into a sold-stage LeadRecord only if it has a sale
  keyword, a parseable 20+ unit count, and a real date -- any missing and it's dropped,
  never guessed. `extract_buyer()` pulls a buyer name from "acquired by X" / "sold to X"
  / "X acquires" patterns, blank otherwise. `find_sales_news()` runs both sources for
  one city and dedupes by article URL.
- No place names in the module -- city/area are always caller-supplied.
- Tests: `tests/test_sales_news.py` (13 tests, no network) -- query building, GDELT URL
  encoding, full match, dropped for no sale keyword / no units / under-20-units / no
  date, buyer extraction (acquires pattern and no-match case), SearXNG-only end to end
  (with an out-of-window hit and a no-units hit both dropped), SearXNG+GDELT dedup by
  URL, bad GDELT JSON ignored gracefully, and no gdelt_fetch_fn supplied at all.
- Checked: `bash tooling/qa/check-lead-finder.sh` -- new skill's 13 tests pass, every
  other lead-finder* dir unaffected (108 before, 121 total now, all passing), panel
  check clean.
- Nothing left open. Next task (4.4) is "who to call" -- find-website + contact-scrape
  for any area, pulling office phone numbers with `phonenumbers` and a named contact
  only when a permit/agenda/news page names one.

## 4.4 Who to call, any area -- done

- Added `propertystack/skills/lead-finder-contact/contact.py`:
  - `find_website(developer, search_fn)`: one search for the developer/owner's own site
    (`"<developer> apartments website"`), takes the first result URL, never guesses one.
  - `find_office_phone(html)`: uses the `phonenumbers` package (installed with
    `pip install --user --break-system-packages phonenumbers`, same pattern as 3.1's
    `openpyxl`) to find every phone-shaped number in a page, skips any number whose nearby
    text says "fax", and prefers a non-cell/mobile number over a cell one (a cell number is
    kept only as a last-resort fallback if nothing else is found). Context window is 15
    characters back from each match -- a wider window was pulling an earlier "Fax:" label
    across into a later, unrelated "Office:" number's context; caught by a two-number test
    fixture and fixed by shrinking the window.
  - `find_named_contact(text)`: only matches a name that directly follows "contact:"/
    "property manager:"/"leasing manager:"/"project manager:"/"developer contact:" --
    used only against permit/agenda/news page text, never a generic developer website, per
    the plan's "a named person only if a permit, agenda or news page names one." (Bug caught
    while writing the test: the label alternation was under the same `re.I` flag as the
    `[A-Z]` name-capture group, so `re.I` made `[A-Z]` match lowercase too and the name
    capture ran on past "Jane Doe" into the rest of the sentence; fixed with an inline
    `(?i:...)` scoped only to the label.)
  - `fill_contacts(records, search_fn, fetch_fn)`: the batch entry point. Fills
    `office_phone` from the record's own website (or the developer's website found via
    search, which also fills `website` if it was blank) -- never overwrites an
    already-known phone. Separately, if the developer name doesn't already carry a
    `(contact: ...)` tag, checks the record's `permit`/`agenda`/`news` links (in that order,
    stopping at the first hit) for a named contact and folds it onto `developer` as
    `"<developer> (contact: <name>)"` -- there's no dedicated contact-name field in
    `docs/LEAD-FORMAT.md`, and adding one wasn't asked for by the plan, so this reuses the
    existing `developer` field the same way HUD/permit records already carry extra context
    inline. Every phone/name fact filled gets a `sources` entry with its URL.
- Tests: `tests/test_contact.py` (15 tests, no network) -- office-vs-fax preference, fax-only
  returns nothing, cell-as-fallback-only, no-numbers-found, website search first-result and
  blank-developer/no-results cases, named-contact match and no-match, filling phone from an
  already-known website, searching for a website when blank, not overwriting a known phone,
  naming a contact only from a permit/agenda/news link, no name added when none of those pages
  name one, and a blocked (`ok: False`) fetch result being skipped rather than misread.
- Checked: `bash tooling/qa/check-lead-finder.sh` -- lead-finder-contact's own 15 tests pass,
  every other lead-finder* dir unaffected (121 before this task, 136 total now, all passing),
  panel check clean. Also reran `python3 site/data/build_data.py` to confirm the site still
  builds unaffected (204 properties, 42 leads, 20 states).
- Nothing left open for this task. Note for whoever wires 6.1: `fill_contacts` needs the
  `phonenumbers` package installed (not previously a repo dependency) -- if a fresh
  environment is missing it, install with
  `pip install --user --break-system-packages phonenumbers` before running the real chain.
- Next task (4.5) is `score-leads` rebuilt for any area: soonest opening first, then more
  units, then not-picked-above-competitor; sold and planned groups ordered separately; a
  one-line "why" per lead.
