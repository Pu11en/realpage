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
