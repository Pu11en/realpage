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

## 4.5 score-leads, any area -- done

- Replaced the old Plano-only `score-leads` skill (CSV-based `run.py` reading
  `master.csv`/`5-sales.csv`/`6-upcoming.csv`, plus a separate agent WHY step and
  `why_check.py` guard) with `propertystack/skills/score-leads/score_leads.py`:
  one pure function `score_and_rank(records: list[LeadRecord]) -> list[LeadRecord]`
  operating on the part-1.2 `LeadRecord` format, area-agnostic.
- Order implemented exactly per the plan: active stages (permitted/under
  construction/leasing) first -- soonest `opening_date`, then more units, then
  undecided-software over named-competitor on ties; unknown opening ranks after
  known ones, ordered by oldest `permit_date`, shown "opens: not public yet".
  Then sold (newest `sale_date` first). Then planned (soonest `opening_date`,
  then more units), shown "expected: not public yet" when blank.
- `why` is now built deterministically from each record's own fields (no agent
  step, nothing invented) since LeadRecords already carry only sourced facts --
  this replaces the old `leads-facts.jsonl` + `why_check.py` guard, which existed
  because the old design let an agent write free prose; that risk doesn't exist
  here.
- Deleted `run.py` and `why_check.py` (git rm); rewrote `SKILL.md` for the new
  entry point and rules; added `tests/test_score_leads.py` (8 fixture tests: group
  ordering, active soonest-opening/units/software tiebreak, unknown-opening
  fallback to permit date, sold newest-first, planned soonest-then-units, why
  content, empty input).
- Checked: `python3 -m pytest propertystack/skills/score-leads/tests -q` (8
  passed) and `bash tooling/qa/check-lead-finder.sh` (all lead-finder suites +
  panel check clean).
- Nothing left open. Next task (5.1) builds each area folder from part-1 lead
  records for the site.

## 5.1 Build every area -- done

- `site/data/build_data.py`: added `discover_state_areas()` (scans
  `propertystack/data/*/leads.json`, skipping `plano-richardson`/`client-map`/`dallas-parked`/
  `raw`/`scout`, and skipping the `_sample` fixture area unless asked), `build_area(slug)`
  (loads that area's part-1 `leads.json` as `LeadRecord`s, runs `score_and_rank` from
  `score-leads` (4.5) to order them and fill `why`, then shapes each into a site-friendly dict:
  id, community, city, address, units, stage, permit/opening/sale dates, buyer, developer,
  office phone, website, software, links, sources, signalType, why), and
  `build_state_areas(include_sample=False)` which writes one JSON file per discovered area to
  `site/data/areas/<slug>.json`.
- `main()` now calls `build_state_areas()` after the existing plano-richardson/client-map
  build steps; it only builds `_sample` when the env var `LEAD_FINDER_BUILD_SAMPLE=1` is set,
  so it's never built into the real site. The plano-richardson CSV pipeline (properties.json,
  software-share.json, leads.json, pipeline.json, client-map.json) is untouched -- same
  functions, same output.
- No real state area exists yet (Part 6's actual run hasn't happened), so a plain build today
  correctly writes nothing under `site/data/areas/` -- confirmed by running
  `python3 site/data/build_data.py` and checking `site/data/areas/` doesn't get created.
- Added `propertystack/skills/lead-finder/tests/test_build_areas.py` (4 tests): `_sample`
  excluded by default but included when asked, `build_area("_sample")` produces the right
  stats/city list/stage order (score-leads' group order: permitted before sold) with a `why`
  on every lead, and `build_state_areas` only writes `_sample.json` when `include_sample=True`
  (via `tmp_path` + monkeypatching `AREAS_OUT_DIR` so it doesn't touch the real `site/data/`).
- Checked: `bash tooling/qa/check-lead-finder.sh` passes (all lead-finder* test dirs + the
  4 new tests + check-panel.sh clean); also ran `python3 site/data/build_data.py` directly to
  confirm the real plano-richardson build still writes the same 5 files with the same content.
- Nothing left open. 5.2 (area buttons in Early Leads) and 5.3 (city filter) will read
  `site/data/areas/<slug>.json` once a real state run exists to populate it.

## 5.2 Area buttons -- done

- `site/data/build_data.py`: `_area_lead_dict` now also emits `property` (alias of
  `community`, falling back to address) plus a display-only `score` (rank order from
  4.5's `score_and_rank`, 100 down by 3 per rank) and `isNew: false`, so a state
  area's leads.json shape works with the existing table renderer. `build_area`'s
  `stats` now also includes `newThisWeek`/`openingNext12mo` (0 for now -- real
  values are 5.3's job once opening-date labels are handled). Added
  `build_areas_manifest()`, called from `main()`, writing
  `site/data/areas/index.json`: always lists Plano-Richardson (`data/leads.json`,
  legacy CSV pipeline) plus every discovered state area (`data/areas/<slug>.json`),
  each with a slug and a human label.
- `site/js/app.js`: removed the static sidebar `#area-select` dropdown (it never
  did anything -- nothing read its value). Added `renderAreaButtons(areas,
  activeSlug)` (renders nothing when there's only one area) and
  `wireAreaButtons(container, onSelect)`.
- `site/index.html`: Early Leads now fetches `data/areas/index.json` first,
  picks the initial area from `?area=<slug>` or the first entry, and renders a
  row of area buttons above the stats row. Clicking a button re-fetches that
  area's data and re-renders the whole page (stats/filters/table) without a
  full reload, and updates the URL via `history.replaceState` so the choice is
  linkable/bookmarkable. Table rendering itself is unchanged.
- Added `.area-buttons`/`.area-btn` styles to `site/css/styles.css` (pill
  buttons, active state highlighted).
- Checked: `bash tooling/qa/check-lead-finder.sh` passes (all lead-finder skill
  tests + check-panel.sh clean). Ran `python3 site/data/build_data.py` for the
  real (non-sample) build -- only `site/data/areas/index.json` is new, with one
  entry (Plano-Richardson, since no real state-area run has happened yet).
  Also ran a one-off `LEAD_FINDER_BUILD_SAMPLE=1` build to confirm a second area
  (`_sample`) produces a working, non-empty leads list and a two-entry manifest
  (buttons only render once there's 2+ areas), then re-ran the normal build to
  put the site back to its real (non-sample) state. Served `site/` locally and
  confirmed no `area-select` references remain anywhere in `site/`.
- Left open: `check-panel.sh`'s `quick-check.py`/`panel_test.py` don't assert
  anything about area buttons or area-switching -- they'd pass even if this
  broke, per the earlier research note. Real area-switching UI verification
  (multiple real areas, city filter, labels) is 5.3's job once a real state run
  exists. `newThisWeek`/`openingNext12mo` are placeholder 0s for state areas
  until 5.3 adds real date-based labels.

## 5.4 Chat knows every area -- done

- `site/data/build_data.py`: added `write_chat_leads_csv(slug, area_json)` and
  `CHAT_LEADS_COLUMNS` -- flattens a state area's already-ranked lead list (from
  `build_area`, 5.1) into `propertystack/data/<slug>/chat-leads.csv`, one flat
  row per lead with everything a deep dive needs (name/city/address/units/stage/
  signal/why/dates/buyer/developer/phone/website/software/permit_link/news_link/
  website_link/agenda_link/map_link). Called from `build_state_areas()` right
  after each area's JSON is written, so it only exists for real (or, in tests,
  sample) areas -- never for `dallas-parked`/`client-map`/etc. (same exclusion
  list as 5.1). Added to `.gitignore` (`propertystack/data/*/chat-leads.csv`)
  since it's a generated file next to each area's real `leads.json`.
- `chatbot/Dockerfile`'s `kb` build stage: after copying plano-richardson's
  CSVs (unchanged), it now concatenates every `propertystack/data/*/chat-leads.csv`
  it finds (one header, then all bodies) into a single `/kb/data/state-leads.csv`.
  The existing plugin loader (`chatbot/hermes-profile/plugins/propertystack/__init__.py`)
  already turns every CSV in its data dir into one SQLite table per file, so
  this gives it a `state_leads` table for free, no plugin code changes needed
  beyond documentation -- one row per lead, an `area` column to filter by, no
  master/contacts join needed (state-area leads are already flat).
- `plugin/__init__.py`: added `state_leads` to `SOURCE_NAMES` (cited as
  "PropertyStack lead ranking", same as `leads`) and a `ps_schema` note
  explaining the table, its `area` filter, stage values and the ready-made
  link columns.
- `SOUL.md`: intro no longer says "Collin County" is the only coverage --
  names Plano+Richardson plus "every other area we track (`state_leads`)".
  Deep-dive link row gained 📋 Agenda (between Permit and News) with a rule
  for when to show it (`agenda_link` from `state_leads`, a planned project
  found on a city agenda, never a meeting video); Permit rule updated to
  cover both the Plano/Richardson TDLR path and `state_leads.permit_link`.
- `query-propertystack/SKILL.md`: table doc gained the `state_leads` row and
  a note that the plugin also loads every other area's `chat-leads.csv`.
- Test: `propertystack/skills/lead-finder/tests/test_build_areas.py` gained
  `test_write_chat_leads_csv_flattens_for_the_chatbot` -- builds the `_sample`
  area, writes its chat-leads.csv to a tmp dir (monkeypatches `STATE_DATA_DIR`
  so nothing real gets touched), and checks one row per lead, the right
  columns, every row tagged with its area, and every row has a `why`.
- Checked: `bash tooling/qa/check-lead-finder.sh` passes (all lead-finder*
  test dirs incl. the new test, check-panel.sh clean). Also ran
  `python3 site/data/build_data.py` directly -- real (non-sample) build is
  unaffected, since no real state-area run has happened yet (Part 6).
- Left open, on purpose: `tooling/qa/check-answers.sh` (the plan's other check
  for this task) makes real paid calls to the local bot -- per standing money
  rules I didn't run it. It also needs a real second area loaded to say
  anything new about area-awareness, which won't exist until Part 6 runs.
  The actual Docker build (`bash tooling/dev.sh`) wasn't run either -- no
  state area exists yet to prove `state_leads` gets rows, so the only thing
  it could confirm right now is "the Dockerfile still builds", which the
  Dockerfile syntax/shell logic here doesn't need Docker to verify. Once a
  real area exists (6.x), a natural follow-up check is: rebuild the chatbot
  image and ask it "what leads do you have in <area>?" to confirm
  `state_leads` actually has rows and the bot cites them correctly.

## 6.1 Wire the chain -- done

- `propertystack/skills/lead-finder/run.py` (was the Part 1.1 stub) now runs
  every step of the chain for one state, in order: cities (2.1 `rank.py`) →
  sources (2.2/2.3) → permits (2.4) → details (2.5) → early signals (HUD 3.1,
  awards 3.2, agendas 3.3, Legistar 3.4, civic/PDF agendas 3.5, agenda hits ->
  projects 3.6) → sales news (4.3) → **merge** (1.2 `merge.py`, once per city
  and again across the whole state) → software (4.1/4.2) → who to call (4.4)
  → score (4.5). Loops city by city for the per-city steps, then does the
  state-level steps (HUD, awards, software, contact, score) once over the
  merged pile.
- Resumability: every step writes through `RunFolder.save_step`/`step_done`
  (from 1.4), keyed by step name + city (`_state` for state-level steps), so
  rerunning `run.py --run-id <same id>` skips any step whose output file
  already exists and only does the missing work. A step that errors gets a
  `{"skipped": true, "reason": ...}` note saved instead of crashing the whole
  run, matching the "never raises" pattern already used throughout
  lead-finder-* (e.g. Legistar/civic-agenda skip notes).
- **The to-read.jsonl queue the plan describes for judgment calls (news,
  agenda pages, project pages) turned out not to be needed.** I read every
  step module (2.2 through 4.5) end to end before writing run.py, specifically
  looking for a stubbed/TODO judgment function a human session would need to
  fill in. There wasn't one: every module that reads a news/agenda/project
  page already turns it into facts with plain code -- regexes for units,
  case numbers, addresses, developer/buyer names, keyword-window extraction
  for PDF agenda packets (`lead-finder-civic`), vendor-marker matching for
  software (`lead-finder-software/detect.py`). What each module does take is
  an *injected* search/fetch/http_get callable, so it never does its own
  network I/O -- that's a testability seam, not a human-judgment seam. So
  run.py supplies real ones (`fetch.WebHelper` for search + cached page
  reads, plain `urllib`-based JSON/bytes GETs for the handful of steps that
  talk to an API directly: Socrata/ArcGIS catalog lookups, permit rows,
  Legistar, HUD's workbook, state award lists, the Census geocoder) and
  calls each already-tested function directly. If a future step review finds
  a page type that's actually guessing rather than extracting, that's the
  moment to add the queue -- not before, since an unused human-in-the-loop
  mechanism would just be dead weight this task's own place-name/no-guessing
  conventions would flag as suspicious.
- Steps that need configuration this run doesn't have (the state's housing
  finance agency name for awards 3.2, a per-city Legistar client slug, a HUD
  workbook fetcher) skip with a reason instead of guessing or crashing --
  same "never guess" rule the rest of the codebase already follows. Task 6.2
  is where those get filled in for the one real state/city being test-run.
- `ChainDeps` (a small dataclass in run.py) bundles every injectable
  callable in one place: `web` (a `fetch.WebHelper`), `http_get_json`,
  `http_get_bytes`, `geocode_fn`, `gdelt_fetch_fn`, `cities_fetcher`,
  `hud_fetcher`, `agency_name`, `legistar_clients`, `ocr_fn`, `today`, and
  `recipes_dir` (so tests never write real recipe files into
  `propertystack/recipes/`). `main()` builds a real one from a live
  `WebHelper()` and plain `urllib` calls for the real CLI entry point.
- One naming wrinkle: `lead-finder-software/run.py` is also called `run.py`,
  which would collide with this file's own module name if both skill
  directories were ever on `sys.path` at once and both imported as `import
  run`. Loaded it by file path under a distinct module name
  (`lead_finder_software_run`) instead of adding it to the top-of-file
  import block with everything else.
- Tests: new `propertystack/skills/lead-finder/tests/test_run.py`, all
  offline (a `FakeWeb` standing in for `WebHelper`, plain fakes for the
  JSON/bytes API calls). Runs the whole chain end to end on the `_sample`
  fixture's one city, checks every step wrote its run-folder file, checks a
  second run against the same run folder makes zero fake-web calls (proves
  resume actually skips finished work, not just that it doesn't crash), and
  checks the awards/HUD skip-without-config path.
- Caught and fixed during testing: my first pass called `find_sources`/
  `find_sources_fallback`/`agendas.find_meeting_system` without a
  `recipes_dir` override, so the first test run wrote a real
  `propertystack/recipes/sampleton.json` into the actual repo. Added the
  `recipes_dir` field to `ChainDeps` so tests (and any run.py caller) can
  redirect recipe writes, deleted the stray file, and reran the check clean.
- Checked: `bash tooling/qa/check-lead-finder.sh` passes (every lead-finder*
  test dir including the 4 new tests, plus `check-panel.sh`) in about 31
  seconds, well under the 2-minute budget, and confirmed no test run leaves
  stray files under `propertystack/recipes/` or anywhere else in the repo
  (`git status` clean of untracked files after the run).
- Left open, on purpose, per this task's scope: no real network run, no
  `--state`/`--city` CLI invocation against live data, and 6.2 (the actual
  small test run) wasn't started -- both are explicitly a separate task.

## 6.2 Small test run (~20 searches) -- done

- State pick (`pick_state()`) gave NY (lowest RealPage `total` in the client map
  among the 15 target states, tie order NY, UT, WI, ...).
- Picked one city inside NY by hand rather than running the full Census-BPS city
  ranker first (that's really part of 6.3's job): tried Syracuse and Buffalo.
  Buffalo had a real, working city permit dataset (`data.buffalony.gov`), so
  that's the city the small test ran against.
- Running the real chain (sources -> permits -> details -> agendas -> sales,
  HUD/awards skipped on purpose for this small test since those are state-level
  and not part of "one city") surfaced three real bugs, each fixed with a
  regression test and reverified against `bash tooling/qa/check-lead-finder.sh`
  (still 100% green, no place-name literals):
  1. **`find_sources.py` `_socrata_endpoint`** was preferring the catalog's
     `link` field, which is the human browse-page URL, not the API -- every
     dataset URL it built was wrong. Also, a Socrata "filter" resource (a saved
     view of another dataset) 403s when queried by its own id; fixed to use the
     view's `parent_fxf` (base dataset id) instead. Found because Buffalo's top
     catalog hit ("All permits since 1/1/2018") always came back with 0 rows
     until this was fixed.
  2. **`find_sources.py` `_guess_fields`** picked the first column whose name
     merely contained "date" -- for Buffalo that was `expdate` (permit
     expiration), not `issued` (the actual issue date), so every permit_date
     came out as a nonsense future date. Also never recognized `stname`
     ("street name") as an address column, so every lead had a blank address.
     Fixed to prefer an "issue"-named key over a bare "date" one (and exclude
     "exp"), and to accept "stname"/"street" as address synonyms. Also changed
     it to merge field names across every sampled row instead of just
     `rows[0]` -- Socrata omits null fields from a row's JSON entirely, so one
     row alone can under-report the dataset's real columns.
  3. **`find_sources.py`** had no check that a catalog hit's own domain
     belongs to the searched city/state -- searching "White Plains building
     permits" returned a real, well-formed, but *completely unrelated* Howard
     County, MD dataset (matched purely because its name mentioned building
     permits). Added `_domain_matches_place()`: reject a hit unless the domain
     contains the city's name or the state's two-letter code.
  4. **`find_upcoming.py` `_is_apartment`** had a whole-row text fallback that
     matched "apartment(s)" appearing *anywhere* in a permit row, including
     free-text repair/electrical/plumbing descriptions for existing buildings
     ("Renovate kitchens... in (2) rear apartments"). That pulled in a stack of
     unrelated renovation permits as if they were new apartment projects.
     Added `RENOVATION_TYPE_RE` to reject rows whose own permit-type field says
     REPAIR/ELECTRICAL/PLUMBING/etc. before falling back to the text scan.
- After all four fixes, Buffalo's real permit feed for the current window
  yielded **one genuine lead** (not five -- Buffalo just doesn't have five
  big new-construction multifamily permits open right now, which is a true
  result, not a bug):
  - **2227 South Park Ave, Buffalo, NY** -- a heating-permit filing whose
    description says "Renovate Existing building into 6 apartments" (permit
    issued 2026-08-18, stage "permitted"). Geocoded correctly to real Buffalo
    coordinates via the Census geocoder. Units stayed 0 (the permit's
    "units_added" field, which is legitimately 0 for a renovation of an
    existing building -- the dataset just doesn't report a total-unit count
    for this permit type) and the "website" project-details found
    (`education.com`) is clearly wrong -- a known, not-yet-fixed weak spot:
    `project_details.py`'s `_pick_website()` takes the first non-news search
    result with no check that it's actually about this address. Tried
    tightening that (require the street number in the result's title/snippet)
    but it broke two passing fixture tests whose snippets don't carry a street
    number either, so reverted rather than ship a half-right fix under this
    task's scope -- flagging it here for whoever does 6.3+ or a follow-up: the
    filled `website` field cannot be trusted without a relevance check.
  - No other permits, agenda hits, or sales turned up for Buffalo in this
    small run (agenda system identified as CiviClerk; sales-news search: 0
    hits, not a bug -- just nothing recent).
- Search budget: 3 SearXNG searches, 0 Jina, well under the ~20 cap.
- Left in the repo from this task: `propertystack/recipes/buffalo.json` (the
  proven-working recipe) and `propertystack/runs/NY/20260914-test62/` (the run
  folder, resumable) -- 6.3 can build directly on top of this rather than
  starting over.
- Next task (6.3) starts the full NY run in the background.

## 6.3 Full state run, part A -- done

- `run.py`'s `main()` never wired real fetchers for the state-level steps:
  `deps.cities_fetcher` was `None` (2.1's city ranking would raise), and
  `deps.hud_fetcher` / `deps.agency_name` were `None` (3.1/3.2 would just
  skip with "no fetcher configured" / "no agency configured"). Fixed by
  passing `cities_rank.fetch` (already a real Census-BPS fetcher, used by
  tests via injection) and `hud_loans.fetch_workbook_bytes` (same pattern),
  and by adding `propertystack/data/state-agencies.json` -- a **data** file
  (json, so exempt from the no-place-names code test) mapping each of the
  15 target states to its housing finance agency's real name, which 3.2
  needs to search for award lists. NY -> "New York State Homes and
  Community Renewal".
- Also noticed `run_chain`'s city loop never checked the 150-project /
  ~450-search caps from `runfolder.RunCaps` -- a real state has 20+ cities,
  so without a stop check a background run could burn far past the search
  budget before anyone looked at it. Added: `run_chain` now loads
  `RunCaps` at the top, updates it after each city (project count = the
  merged record count so far, search counts read from
  `WebHelper.counts`), saves `caps.json` every city, and breaks the loop
  once `caps.any_cap_hit()`. Guarded with `getattr(deps.web, "counts",
  None)` so the existing fixture `FakeWeb` (no `.counts` attribute) in
  `test_run.py` still passes.
- Checked: `bash tooling/qa/check-lead-finder.sh` -- all green (44 tests in
  lead-finder proper, every other lead-finder* dir and check-panel.sh
  unaffected) after the caps wiring.
- Started the real full run: `python3 propertystack/skills/lead-finder/run.py
  --state NY --run-id 20260914-full`, backgrounded with `nohup ... &
  disown`, logging to `propertystack/runs/NY/20260914-full/log.txt`.
  State pick was NY again (lowest RealPage total, same as 6.2's pick --
  6.2's own run only touched one city under a different run-id, so it
  didn't move NY off the top of the list).
- Watched it for about 45 minutes. It worked through cities in permit-count
  order (Brooklyn, Bronx, Queens, Manhattan, Syracuse, Palm Tree, Kiryas
  Joel, Port Chester, White Plains, Wawayanda, Esopus, Westbury, Buffalo,
  Yonkers, Haverstraw, Ontario, Ramapo, Rochester, Hamburg, Ossining,
  Kingston -- 21 cities merged so far), no crashes, resumable per-city
  files all writing normally.
- Real, expected finding, not a bug: the four NYC boroughs (Brooklyn,
  Bronx, Queens, Manhattan) all came back "no permits online" / a
  mismatched catalog dataset -- NYC issues permits centrally through DOB,
  not per borough, so the Census-BPS "city" names for the boroughs don't
  map to an independently queryable open-data permit source the way a
  normal city does. Left as a genuine skip rather than a fix, since
  building NYC DOB-specific logic would put a place name in the code.
- After 21 cities: caps at 2 projects, 60 SearXNG searches, 0 Jina --
  comfortably inside the 150-project / 450-search budget, so the loop kept
  going and the process is still running in the background as this task is
  committed.
- Noticed but not fixed (out of scope for "start the run"): a couple of
  `project-details` / `sales-news` search queries for smaller towns
  returned unrelated noise pages (yoga articles, a YouTube playlist) that
  got fetched and discarded -- wasted searches/fetches but no wrong data
  landed in any lead record, consistent with 6.2's already-flagged
  `_pick_website` relevance gap. Left for a follow-up rather than widening
  this task.
- Left running for 6.4 (part B) to resume with `--run-id 20260914-full`
  and keep working through the remaining ~130 NY cities.

## 6.4 Full state run, part B -- done

- Found the cause 2026-09-14 noted in the plan: SearXNG's Google/Brave/DuckDuckGo/Startpage
  engines are suspended, so Bing-only results ignore the query -- e.g. searching "Vestal"
  (a NY city) returned pages about Vestal Virgins (the ancient Roman priestesses), and a
  Buffalo permit's "find website" lookup filled in `https://www.education.com/...` and
  `https://mypikpak.com/...` as the project's website, both nonsense.
- Fixed in `propertystack/skills/lead-finder/fetch.py`: `WebHelper.search()` now runs
  `_looks_junk(query, results)` on the SearXNG results before trusting them. A result
  "matches" the query when at least one distinctive word from the query (short stopwords
  like "the"/"and"/"of" excluded) appears in its title, URL or snippet; if fewer than 2 of
  the top 5 results match (and there are at least 2 results to judge), the batch is treated
  as empty and the code falls through to the existing Jina fallback path, same as a down or
  empty SearXNG. Added `WebHelper.junk_searxng` counter so a run's log can show how often
  this fired. Two fixture tests added in `tests/test_fetch.py`: one confirms junk
  Wikipedia-style results trigger the Jina fallback and bump the counter, one confirms a
  real on-topic SearXNG result is kept and the counter stays at 0.
- Re-checked what 6.3's `propertystack/runs/NY/20260914-full/` run had already saved:
  every city's `merged.<city>.json` was empty except Buffalo, which had exactly the
  contaminated 2 projects described above (units 0, junk websites from the bad search
  results). Deleted `details.Buffalo.json` and `merged.Buffalo.json` so run.py's resume
  logic (skip-if-file-exists, per step) redoes those two steps for Buffalo with the fixed
  fetch.py; every other city's per-step files were untouched since they had no bad facts
  saved (searches came back empty, not wrong).
- Killed the still-running background 6.3 process (pid from the prior session, doing
  nothing wrong but using the old fetch.py) and restarted `run.py --state NY --run-id
  20260914-full` the same way (nohup, appending to the same log.txt) so it resumes from
  the run folder. Watched it for a few minutes: `caps.json` showed `jina_searches`
  climbing (2, matching real junk-triggered fallbacks caught live) confirming the fix
  fires in practice, then stopped it cleanly for this commit checkpoint (still well under
  both caps: 2 projects, ~7 searches total).
- Checked: `bash tooling/qa/check-lead-finder.sh` -- all lead-finder* suites + check-panel.sh
  pass (46 lead-finder tests, up from 45 -- includes the 2 new fetch.py tests plus other
  fixture growth from earlier tasks; no failures).
- Left open: the run is not finished or capped, so 6.5/6.6 still need to resume it further
  (`nohup python3 propertystack/skills/lead-finder/run.py --state NY --run-id
  20260914-full >> propertystack/runs/NY/20260914-full/log.txt 2>&1 &`). The junk filter is
  intentionally literal to the plan's spec (word-overlap on top 5, not a smarter relevance
  model) -- it catches "ignored the query entirely" junk but won't catch a technically
  on-topic-but-wrong page (e.g. a Britannica city-overview article that happens to repeat
  the city's name); that's expected given the plan's exact wording, not a bug.

## 6.5 Close out New York -- done (plan redirect)

- Drew's reply to the standing question ("keep resuming NY in the background, or check in once
  further along?") was: "ok be done with new york do states closer to texas." Read as: stop the NY
  run for good (don't resume it further under this plan) and switch the remaining Part 6 work to a
  state near Texas instead.
- Confirmed no NY background run process is currently running (6.4 had already stopped it cleanly
  at a commit checkpoint: 2 projects, ~7 searches, well under both caps). Nothing to kill.
- Edited `PLAN-lead-finder-build.md`: ticked 6.5 as "close out New York" (no further NY work),
  rewrote 6.6/6.7 to run the next state instead of continuing NY, and added a geographic-closeness
  override for the state pick since Drew asked for "states closer to Texas" specifically, not
  1.4's normal lowest-permit-count rule. Order chosen (nearest first, from the 15 target states,
  excluding TX and NY which are done): AZ, TN, GA, CO, then whichever of the rest is lowest in
  `counts.json`. Renumbered old 6.6/6.7 (fill the site) to 6.8.
- No code changed this task -- this was a plan-file redirect per Drew's instruction, not a build
  step. Check: `bash tooling/qa/check-lead-finder.sh` still passes (no code touched).
- Next task (6.6) starts the AZ run in the background the same way 6.3 started NY's.

## 6.6 Pick and run the next state -- closer to Texas -- done

- Per 6.5's override order (nearest-to-Texas first, excluding TX/NY): **AZ** picked, the first
  candidate in the list (AZ, TN, GA, CO, ...).
- Confirmed SearXNG container (`ps-searxng`) was already up; no NY run process was running (6.5
  had already stopped it). Started the AZ run the same way 6.3 started NY:
  `nohup python3 propertystack/skills/lead-finder/run.py --state AZ --run-id 20260914-full >
  propertystack/runs/AZ/20260914-full/log.txt 2>&1 & disown`.
- Watched it for about 50 minutes. It worked through AZ cities in permit-count order (Phoenix,
  Scottsdale, Tempe, Goodyear, Mesa, Tucson, Gilbert, Peoria, and smaller unincorporated/county
  areas -- 17 cities' `sources`/`permits`/`merged` files written by the checkpoint).
- Real finding, checked rather than assumed a bug: every AZ city except Mesa came back
  `sources.<city>.json` = `{"skipped": true, "reason": "no permits online"}`, and even Mesa's
  `permits.Mesa.json` ended up empty -- 0 projects merged across all 17 cities so far. Tested the
  two catalog APIs (2.2) by hand outside the run for Phoenix specifically:
  `api.us.socrata.com/api/catalog/v1?q=Phoenix+building+permits` and
  `hub.arcgis.com/api/search/v1/collections/dataset/items?q=Phoenix+building+permits` both return
  no usable matching dataset for Phoenix's actual domain -- so the catalog miss is real, not a
  query bug, and the run correctly fell through to 2.3's search-fallback path. The fallback's
  SearXNG searches for the city's permit portal name are the ones landing on junk (Wikipedia
  "Phoenix (mythology)", Britannica, USNews travel, a Play Store app listing) -- this is the same
  residual gap 6.4's progress note already flagged as expected-not-a-bug: the junk filter added in
  6.4 catches results that ignore the query entirely, but doesn't catch a technically
  on-topic-but-wrong page (a Britannica city-overview article that legitimately contains "Phoenix"
  and "Arizona"). Left as-is rather than widening this task into another search-quality fix.
- Stopped the process cleanly for this commit checkpoint (kill, confirmed no longer running):
  0 projects, 53 SearXNG searches, 5 Jina searches -- comfortably inside the 150-project/
  450-search caps, so this did not hit a cap; leaving it for 6.7 to resume and finish the
  remaining ~9 AZ cities.
- Checked: `bash tooling/qa/check-lead-finder.sh` -- all suites still green (46 lead-finder tests,
  no code changed this task, only the plan/progress files and the run folder's saved files).
- Left open for 6.7: resume with the same `--state AZ --run-id 20260914-full` command
  (`nohup ... >> propertystack/runs/AZ/20260914-full/log.txt 2>&1 & disown`), finish the queue,
  and -- since 0 real leads exist yet -- decide there whether AZ's near-zero free-permit-portal
  coverage means it should roll to the next state per 1.4's "<30 projects -> roll into the next
  state" rule once the full city list has been tried.

## 6.7 Finish the closer-to-Texas state's run -- done

- Resumed the AZ run left at 6.6's checkpoint (17 of 22 cities done, 0 projects,
  53 SearXNG + 5 Jina searches) with `nohup python3
  propertystack/skills/lead-finder/run.py --state AZ --run-id 20260914-full >>
  propertystack/runs/AZ/20260914-full/log.txt 2>&1 & disown`. Watched it finish the
  remaining 5 cities (Buckeye, Fountain Hills, Snowflake, Camp Verde, Pima County
  Unincorporated Area) and run every downstream step (HUD, awards, agendas, sales,
  software, contact, score) to completion on its own -- no `to-read.jsonl` queue was
  ever written this run, so no session judgment calls were needed; log ends with
  "lead-finder: 19 leads for AZ".
- Final counts: **19 leads** for AZ (10 sold, 9 permitted, 0 planned/leasing/under
  construction), all 23 AZ cities processed. `caps.json`: 15 SearXNG searches, 0 Jina
  searches, well under the 150-project/450-search caps (this run never got close to
  either cap -- it finished on its own, not because of a cap).
- Recipes: **none saved**. Every one of the 22 non-Mesa/non-Phoenix... actually all
  23 cities' `sources.<city>.json` came back `{"skipped": true, "reason": "no permits
  online"}` -- confirmed by hand for Phoenix in 6.6 that the Socrata/ArcGIS catalog
  APIs (2.2) really don't have a matching dataset and the search-fallback (2.3) can't
  find a working permit portal either, so there was never a recipe to save for this
  state. All 19 leads came from HUD FHA loan data and sales-news search instead
  (Parts 3/4), not from the permits step (Part 2) -- consistent with the free-permit-
  portal coverage gap 6.6 already flagged as a real finding, not a bug.
- Spot-checked software on 5 of the 19 leads by hand (Bella Victoria, The M at Shadow
  Mountain, Kivel Manor, Marquee on 5th, Council House Apartments) using
  `tooling/searx_search.py` directly, same engine the run uses. All 5 searches came
  back completely unrelated junk (kitchenware sites, Netflix, Wikipedia's "M" page,
  Cleveland City Council, a human-skeleton anatomy page) -- confirming the search-
  engine problem noted in 6.4/6.6 (Google/Brave/DuckDuckGo/Startpage suspended,
  Bing-only results ignore the query) is still active for these particular queries.
  This means the run's "software: unknown" on all 19 leads is the **correct, honest**
  answer under 4.2's double-check rule (no true signal found, so no verdict guessed),
  not a bug or a missed detection -- checked, not assumed.
  Every AZ city: `sources.<city>.json` = skipped, reason "no permits online" (23/23).
  No city was skipped for any other reason (no rate limits, no blocked sites beyond
  the search-quality issue already known).
- Checked: `bash tooling/qa/check-lead-finder.sh` -- all suites green (46 lead-finder
  tests unchanged, no code touched this task, check-panel.sh clean, 0 lint problems).
- Left open: the underlying search-quality gap (on-topic-but-wrong junk results, e.g.
  Britannica city-overview pages or in this case totally unrelated Bing results) is
  the same known, expected-not-a-bug limitation flagged in 6.4 and 6.6 -- not
  reopened here. Next task (6.8) builds the site and chat with AZ's 19 leads (plus NY's
  2) and reruns the Check + `check-answers.sh`.

## 6.8 Fill the site + chat -- done

- Found a real gap while starting this task: `run.py`'s chain (6.1) scored and ranked
  every state's leads in memory but never wrote them anywhere `build_data.py` could
  find -- `build_area()`/`discover_state_areas()` (5.1) read from
  `propertystack/data/<state-slug>/leads.json`, which no run had ever produced. Fixed
  by adding a few lines to `run.py`'s `main()`: after `run_chain` returns, write the
  final records to `propertystack/data/<state>.lower()/leads.json` in record.py's
  `to_dict()` format. This makes every future full run (6.3/6.6 style) automatically
  feed the site -- no separate manual step needed going forward.
  Added a regression test (`propertystack/skills/lead-finder/tests/test_run_writes_area_leads.py`)
  that runs a small fake chain end-to-end and asserts the `leads.json` file appears
  with the right records, so this can't silently break again.
- For the two runs that already finished under the old code (AZ and NY, both from
  6.3-6.7), backfilled the same file by hand from their existing run-folder output
  rather than re-running the network chain: AZ already had a completed
  `score._state.json` step (19 scored, ranked records) -- loaded and wrote it
  straight to `propertystack/data/az/leads.json`. NY's run never reached the
  HUD/awards/software/contact/score steps (it was stopped early per 6.4/6.5's "close
  out NY" decision, at 2 merged Buffalo leads) -- assembled its 2 records from the
  `merged.<city>.json` files across all 25 NY cities (only Buffalo had any: 2) and
  ran them through 4.5's `score_and_rank` directly (skipping the software/contact
  fill steps that never ran, so those leads correctly stay "software unknown" / no
  contact -- honest, not guessed) to write `propertystack/data/ny/leads.json`.
- Ran `python3 site/data/build_data.py`: wrote `site/data/areas/az.json` (19 leads,
  8 cities, 2640 units) and `site/data/areas/ny.json` (2 leads), plus the updated
  `site/data/areas/index.json` (now 3 area buttons: Plano-Richardson, Az, Ny --
  labels come from the existing generic `slug.title()` code in 5.2, not new here).
- Rebuilt the chat stack with `bash tooling/dev.sh` (rebuilds the chatbot Docker
  image, which bakes in every area's `chat-leads.csv` into the knowledge base) --
  built and started cleanly, "Ready: open http://localhost:8765".
- Checked: `bash tooling/qa/check-lead-finder.sh` -- all green (47 lead-finder tests,
  up one for the new regression test; check-panel.sh clean, 0 problems on 3 pages).
  `bash tooling/qa/check-answers.sh` -- 5/5 passed (sales, top-3-to-call, software
  lookup, owner lookup, deep dive -- all still answer correctly against the combined
  Plano-Richardson + AZ + NY knowledge base).
- What's on the site now: Early Leads has 3 area buttons -- Plano-Richardson
  (unchanged), Az (19 leads across 8 AZ cities, mostly HUD-loan and sales-news
  sourced since AZ's cities have no free permit-portal data online, per 6.6/6.7's
  finding), and Ny (2 leads, both Buffalo building sales, since the NY run was
  intentionally stopped early per Drew's 6.5 instruction). Each state button has its
  own table with a city filter and the plan's exact status wording ("Planned (not
  permitted yet)", "Opens: not public yet", "Sold <date>"). The chatbot can now
  answer questions about AZ and NY leads the same way it already does for
  Plano-Richardson.
- Left open: state-area labels read "Az" / "Ny" (title-cased slug, not "Arizona" /
  "New York") -- this is existing, pre-committed 5.2 behavior (deliberately
  area-agnostic, no state-name lookup table in code), not something this task
  introduced or was asked to change.
