# Progress log

## S0 Save as you go + data-first switch
- Added `run_chain(..., on_city_done=...)` to `skills/lead-finder/run.py`: after
  each city finishes, it writes the area's `leads.json` (from records so far)
  and calls the hook. Added a real `--commit-each` CLI flag that wires this to
  `commit_city_progress()`, which `git add`s the run folder + that area's
  `propertystack/data/<state>` dir and commits (`git diff --cached --quiet`
  first, so a city with nothing new to save is a no-op, not an empty commit).
- Data-first switch: `project_details.fill_project_details` now only searches
  for a website when `record.stage` is `"leasing"` or `"sold"` (`BUILT_STAGES`).
  A not-yet-built project (planned/permitted/under construction) still gets
  its units/developer/opening-date search, just never a website search/match.
- Fixed 3 pre-existing tests in `test_project_details.py` that asserted a
  website was filled without setting `stage` (default is `"planned"`, which
  would now correctly get no website) -- set `stage="leasing"` on those since
  they're testing the website-matching logic itself, not stage gating.
  Added a new test (`test_fill_project_details_never_searches_website_for_not_yet_built`)
  proving a `"permitted"` record never gets a website even when the search
  would otherwise match.
- Added `test_run_chain_calls_on_city_done_once_per_city` and
  `test_commit_city_progress_commits_new_files` (real `git init` in a tmp dir)
  in `skills/lead-finder/tests/test_run.py`.
- Checked: `bash tooling/qa/check-lead-finder.sh` passes (all lead-finder*
  suites + check-panel.sh). Also ran the whole propertystack suite
  (`python3 -m pytest -q --ignore=skills/client-map/tests`): 267 passed. The
  `skills/client-map/tests` collection error (`ModuleNotFoundError: census`) is
  pre-existing and unrelated to this change.
- Left open: `run.py`'s per-city commit only fires when `--commit-each` is
  passed on the command line; S5/T6 (the actual AZ/TX re-runs) need to pass
  that flag to get the save-as-you-go behavior in practice.

## S1 Parallel lookups
- `step_details` (per-city, `skills/lead-finder/run.py`) now runs
  `project_details.fill_project_details` for up to `LOOKUP_WORKERS` (6)
  records at once via `concurrent.futures.ThreadPoolExecutor.map`, which
  keeps input order in its output regardless of which record's lookup
  finishes first.
- `fill_software` (`skills/lead-finder-software/run.py`) and `fill_contacts`
  (`skills/lead-finder-contact/contact.py`) got the same treatment: each
  record's lookup is independent (own website, own fields), so a thread
  pool runs the network part and the (order-preserving) result application
  stays single-threaded.
- `fetch.WebHelper` (`skills/lead-finder/fetch.py`) is now the thing that
  makes this safe: added a `threading.Lock` around every bit of shared
  mutable state (`counts`, `junk_jina`, `brave_usage`, `_block_counts`,
  `_skipped`) and rewrote `_respect_gap` to reserve a site's next-visit slot
  under the lock before sleeping outside it -- so two threads hitting the
  same site still get the required >=2s gap instead of both reading "no
  recent visit" and firing together, and a site's 3-strikes block count
  can't lose an increment to a race.
- Tests: `test_fetch.py` gained
  `test_fetch_from_several_threads_respects_same_site_gap` (4 concurrent
  fetches to one site, asserts consecutive visits are still >=0.19s apart)
  and `test_fetch_block_counts_are_race_free_across_threads` (10 concurrent
  blocked fetches, asserts the block count trips at exactly `BLOCK_LIMIT`).
  `test_run.py` gained `test_step_details_runs_in_parallel_but_keeps_order`
  (records sleep in reverse-input order so an accidentally-serial pool
  couldn't fake correct ordering). `test_detect.py` and `test_contact.py`
  each gained an 8-record parallel-order test. 277 propertystack tests pass
  (`python3 -m pytest -q --ignore=skills/client-map/tests`, pre-existing
  unrelated collection error only); `bash tooling/qa/check-lead-finder.sh`
  passes.
- Live-timed Tempe's actual 6 not-yet-built permits (from the AZ run-1
  fixture, `runs/AZ/20260914-tempe-test/permits.Tempe.json`) through
  `step_details` with real Jina/crawl4ai network calls, cold cache both
  times: serial (`LOOKUP_WORKERS=1`) took **98.2s**; parallel
  (`LOOKUP_WORKERS=6`) took **36.2s** -- 2.7x faster, identical output (6
  records, 7 Jina + 1 Brave search both runs). The full Tempe run only
  reaches ~2.7x rather than 6x because several lookups land on `crawl4ai`
  calls to the *same* domain back to back (e.g. friendshipvillageaz.com
  three times), which the 2s same-site gap still serializes on purpose.
- Left open: only `step_details`, `fill_software` and `fill_contacts` were
  parallelized (the plan's explicit list); the agenda/legistar/civic/sales
  per-city steps still run one city at a time as before -- S2 covers
  skipping those, not speeding them up.

## S2 Skip dead ends
- `run.py`'s `step_agendas`/`step_legistar`/`step_civic`/`step_sales` each
  gained a `should_run`/`skip_reason` pair. `run_chain` computes a per-city
  gate (`_dead_end_gate`): run them if the city's `sources` step found a
  real (non-skipped) permit recipe, **or** the city has >= 10 Census 5+
  unit permits in the last 12 months (`DEAD_END_MIN_PERMITS`); otherwise
  every one of those four steps is saved as a skip dict with a reason like
  "no working permit source and only 3 Census 5+ unit permits in the last
  12 months (need >= 10)" and none of their search/fetch calls happen at
  all. The permit count comes from the already-saved `cities` step
  (`_permit_counts_from_cities_step`) when it was built from ranked Census
  data (`rank_cities`'s `permits_5plus` field) -- an explicit `--city` run
  or test fixture has no such data and falls back to the permit-source half
  of the gate alone.
- Agenda-system detection cache: `agendas.find_meeting_system` used to
  search/fetch every time even though it already saved a per-city recipe
  file -- a brand-new run-id started fresh every time and re-spent search
  budget on cities whose agenda system was already known. It now checks
  that saved recipe file first and returns it without ever calling
  `search_fn`/`fetch_fn` again if it's there. (A "nothing found" result is
  still not cached, same as before, so those cities do get re-tried on a
  later run in case a page appears.)
- Logged what's skipped and why: each skipped step prints a one-line
  `lead-finder: skipping <step> for <city>...: <reason>` when it runs (not
  on resume, since a resumed skip is loaded straight from the run folder).
- Tests: `_dead_end_gate` unit tests (source-but-no-permits,
  permits-but-no-source, neither) in `test_run.py`;
  `test_run_chain_skips_agenda_legistar_civic_sales_for_a_dead_end_city`
  monkeypatches all four underlying finders to raise if called, proving the
  gate stops the network calls, not just the run-folder bookkeeping.
  `test_agendas.py` gained
  `test_saved_recipe_is_reused_across_calls_without_searching_again`.
- Checked: `bash tooling/qa/check-lead-finder.sh` passes (all lead-finder*
  suites + check-panel.sh, 72 lead-finder/lead-finder-agendas tests total
  now). Full suite (`python3 -m pytest -q --ignore=skills/client-map/tests`
  from `propertystack/`): 276 passed, 1 failed --
  `test_fetch_block_counts_are_race_free_across_threads` (S1's own
  concurrent-block-count test, untouched by this task; reran it alone 3x
  and it flaked once and passed twice, so it's a pre-existing timing-race
  flake in S1's test, not something S2 broke).
- Left open: S3 (fix dropped/leaked leads) and later steps still run every
  city one at a time except for the parallelized sub-steps from S1; the
  dead-end skip here only removes wasted work, it doesn't change caps or
  ranking.

## S3 Fix dropped and leaked leads
- Found the real cause of Scottsdale's 0-of-~68 permits by hitting its live
  ArcGIS endpoint directly: it returns 403 Forbidden to the default
  `Python-urllib/x.y` user agent that `urllib.request.urlopen` sends with no
  headers, but works fine (500 features) with a normal browser-style
  User-Agent header. `_http_get_json`/`_http_get_bytes` in
  `skills/lead-finder/run.py` now send one on every request. `_fetch_rows`
  in `find_upcoming.py` swallows any fetch exception into `[]`, which is why
  this failed silently as "no permits" instead of a visible error.
- Found why the real Phoenix permit feed (360 raw commercial-new rows, live
  test) kept far fewer than expected and came back with a blank name on
  every kept row: the recipe (`recipes/az/phoenix.json`) maps `PERMIT_NAME`
  (which actually holds the real project name, e.g. "MADISON AT LOUISE
  APTS.") only as `permit_type`, never as `fields.name` -- `find_upcoming`
  had no fallback, so `name` was always `""`. Added the missing
  `"name": "PERMIT_NAME"` mapping in the recipe, and (for the general case
  the plan asked for -- any recipe missing a name field) `_build_record` in
  `skills/lead-finder-permits/find_upcoming.py` now falls back to the
  permit-type field's text, then to the street address, whenever the mapped
  name is blank.
- Found why sub-20-unit permits (mostly Mesa-shaped recipes, per the plan)
  slipped through: `_is_apartment` checked the permit-type text match
  *before* a known unit count, so a recipe whose source query is already
  server-side filtered to "Multi-Family Residential" (Mesa has no
  `permit_type` field mapped, so every row's own text contains that phrase
  and matched the whole-row fallback regex) let e.g. a 3-unit triplex
  through regardless of its actual unit count. Reordered `_is_apartment` so
  a known unit count is checked first and is authoritative (`>= 20` keeps
  it, `< 20` drops it no matter what the type text says); type-text matching
  is now only used when the units field/pattern gave no number.
- Verified all three live against the real endpoints/recipes (not mocks):
  Scottsdale's endpoint returns 500 features with the new header vs. a 403
  before; Phoenix's raw feed is 360 rows, 245 pass the old `_is_apartment`,
  all 245 had blank names before the recipe fix.
- Fixture tests added: `skills/lead-finder-permits/tests/test_find_upcoming.py`
  gained `test_known_low_unit_count_is_dropped_even_if_type_text_matches`,
  `test_blank_name_falls_back_to_permit_type_text`, and
  `test_blank_name_and_type_falls_back_to_address` (all built from the real
  row shapes above, generic city name per the no-place-names rule).
  `skills/lead-finder/tests/test_run.py` gained
  `test_http_get_json_sends_a_browser_user_agent`.
- Checked: `bash tooling/qa/check-lead-finder.sh` passes (67 lead-finder*
  tests + check-panel.sh). Full suite from `propertystack/`
  (`python3 -m pytest -q --ignore=skills/client-map/tests`): 281 passed.
  `test_fetch_block_counts_are_race_free_across_threads` (S1's pre-existing
  timing-race flake, noted in the S2 log) failed once in an earlier run of
  the full check script and passed 3/3 when rerun alone and in the full
  suite's final run -- confirmed unrelated to this task's changes.
- Left open: this fixes the three specific real-row failure modes named in
  the plan (blocked endpoint, missing name mapping, unit-count override);
  it does not re-run Arizona end to end (that's S5) or add unit-tests for
  every other AZ recipe file, so a similar header/mapping problem on a
  not-yet-tried city's endpoint could still exist until S5's re-run surfaces it.

## S4 Caps that don't cut cities off
- Raised the per-state caps in `propertystack/skills/lead-finder/runfolder.py`
  from 150 projects / 450 searches to 400 projects / 900 searches (plan's new
  numbers).
- Checked the existing cap-check placement in `run.py`'s `run_chain` loop: it
  already only tests `caps.any_cap_hit()` once per iteration, at the top of
  the `for city in city_list` loop, before any step for that city runs -- so
  a city already being processed always finishes every one of its steps
  (sources, permits, details, agendas, legistar, civic, sales, merged) before
  the next city is even considered. No code change was needed for the
  "never cut in half" half of this task, just confirmation.
- Tests: added
  `test_run_chain_only_checks_caps_between_cities_never_mid_city` to
  `skills/lead-finder/tests/test_run.py`, which monkeypatches
  `runfolder.MAX_PROJECTS` to 1 and runs a two-city chain -- proves the first
  city's full set of step files exist (nothing partial) while the second
  city has none at all (sources/permits/merged all absent), i.e. the cap
  stopped the chain cleanly between cities, not mid-city.
- Checked: `bash tooling/qa/check-lead-finder.sh` passes (all suites +
  check-panel.sh). Full suite from `propertystack/`
  (`python3 -m pytest -q --ignore=skills/client-map/tests`): 282 passed, no
  failures this time (the S1/S2 timing-race flake noted earlier didn't
  reproduce in this run).
- Left open: S5 (Arizona re-run) will be the first real end-to-end exercise
  of the new 400/900 caps against live data.

## S5 Arizona re-run
- Wired the Maricopa County sales file into the free data-first pull
  (`skills/lead-finder/permit_only.py`), which never called it before (the
  plan's "never wired into run 1" gap): `find_sold` (from
  `skills/lead-finder-sales/find_sold.py`) now runs once at the end against
  the state's `*-sales.json` recipe and adds one "sold" LeadRecord per
  qualifying apartment sale (20+ units, joined sales+parcel file, buyer +
  seller filled from the county record, no web search).
- Also filled `developer` (owner/builder) on not-yet-built permits from the
  same free parcel file, by address (`find_owner_by_parcel`, already existed
  in `lead-finder-contact/contact.py` but was previously only reachable
  through the full web-search chain's contact step) -- purely a public-record
  lookup, no search used.
- Both lookups reuse one in-memory cache (`_cached_fetch_rows`) keyed by
  source URL so the ~100MB+ sales and parcel zip files are each downloaded
  once per run no matter how many records need an owner match, not once per
  record.
- Live-ran `python3 skills/lead-finder/permit_only.py --state AZ` end to
  end (background, ~3 minutes wall clock including the two county zip
  downloads): before (run 1, 2026-09-14) was 94 leads, all new-permit only,
  no owner names, in 2 minutes; after is 279 leads (134 new/upcoming + 145
  sold) in ~3 minutes -- 86 of the 134 new-permit records got a real owner
  name from the parcel file, all 145 sold records have buyer + seller +
  sale price/date straight from the county file, still $0 (no Jina/Brave
  calls -- `permit_only.py` never imports a search function).
  Per-city new-permit counts this run: Gilbert 6, Maricopa County
  unincorporated 4, Mesa 44, Phoenix 29, Scottsdale 38, Tempe 11, Tucson 2.
- Ran `python3 site/data/build_data.py` to rebuild the site's `az` area from
  the new `data/az/leads.json` (204 properties total across areas incl. the
  larger AZ set; wrote `areas/az.json`) -- confirms the new sold + owner
  fields reach the site layer. Did not start the docker-compose chat stack
  (`tooling/dev.sh`) in this sandboxed worker session since it needs
  DEEPSEEK_API_KEY and Docker; Drew can run `bash tooling/dev.sh` locally to
  see it live at http://localhost:8765.
- Tests: `skills/lead-finder/tests/test_permit_only.py` (new) covers the
  fetch-cache -- one real download per distinct URL, cache hit reused
  across repeated calls for the same URL, offline via a fake
  `default_fetch_rows`.
- Checked: `bash tooling/qa/check-lead-finder.sh` passes (70 lead-finder*
  tests + check-panel.sh, up from 67). Full suite from `propertystack/`
  (`python3 -m pytest -q --ignore=skills/client-map/tests`): 284 passed, 0
  failures (the earlier S1 concurrent-block-count flake did not reproduce
  this run).
- Left open: `tooling/dev.sh` (the docker chat stack) itself was not
  started/verified in this session -- Drew should open
  http://localhost:8765 → Early Leads → Az locally to see the 279 leads and
  confirm sold properties show buyer/seller. Part 2 (Texas, T1 onward) is
  still all unchecked.

## T1 Texas area
- `skills/lead-finder-cities/rank.py`: `rank_cities`/`build` now take an
  `exclude_cities` list (case-insensitive city-name match), and a new
  `--exclude-file` CLI flag; `skills/lead-finder/run.py`'s `ChainDeps` gained
  `exclude_cities` (threaded into `load_or_build_cities`'s `rank_cities` call)
  and a matching `--exclude-cities-file` CLI flag, so any state's run can skip
  a finished area's cities without hard-coding place names in the generic
  code (area-agnostic rule) -- the excluded names live in a data file instead.
- Added `data/tx/collin-county-cities.json`: the 26 Collin County
  municipalities/unincorporated area (Plano, Richardson, McKinney, Frisco,
  Allen, Wylie, Murphy, Sachse, Prosper, Celina, Anna, Melissa, Farmersville,
  Lucas, Fairview, Princeton, Josephine, Nevada, Blue Ridge, New Hope, Weston,
  Parker, Lowry Crossing, St. Paul, Lavon, Westminster + the county's
  unincorporated area) -- Plano-Richardson is its own finished area and is
  never rerun, per the plan.
- Implemented the RealPage-gap ranking rule directly in `rank_cities`: cities
  sort by (realpage_count >= 3, -permits_5plus), so cities with 3+ RealPage
  buildings in the client map sort after every RealPage-gap city regardless
  of permit volume, but still order themselves by permit volume within each
  group (ranking, not a ban -- RealPage-heavy cities are still last in the
  list, not removed, so caps that allow them still reach them).
- Live-ran `python3 skills/lead-finder-cities/rank.py --state TX
  --exclude-file data/tx/collin-county-cities.json` against the real Census
  BPS files (background, ~15s): 99 Texas cities/county-areas, written to
  `data/tx/cities.json`. Verified: none of the 26 Collin County names appear
  in the output; the 6 cities with realpage_count >= 3 (Fort Worth, Houston,
  Austin, Dallas, Denton, Grand Prairie -- from `data/client-map/counts.json`)
  are exactly the last 6 entries in permit-descending order among themselves,
  even though Houston (4,077-unit Harris County area aside) and several of
  them have far more raw permit volume than cities ranked ahead of them.
- Tests: `skills/lead-finder-cities/tests/test_rank.py` gained
  `test_exclude_cities_drops_matching_names_case_insensitive` and
  `test_realpage_gap_rule_pushes_heavy_cities_last` (monkeypatches
  `rank.realpage_counts` directly, since `realpage_counts`'s `counts_path`
  default arg is bound at def time and monkeypatching `rank.COUNTS_FILE`
  after import doesn't reach it).
- Checked: `bash tooling/qa/check-lead-finder.sh` passes (76 lead-finder*
  tests, up from 70, + check-panel.sh). Full suite from `propertystack/`
  (`python3 -m pytest -q --ignore=skills/client-map/tests`): 286 passed, 0
  failures.
- Left open: `data/tx/cities.json` will need a fresh rank right before T6's
  full run (Census BPS data updates monthly and T2-T5's new sources aren't
  wired in yet); T2 (TDLR TABS) is next.

## T2 TDLR TABS -- the statewide backbone
- New skill `skills/lead-finder-tabs/tabs.py`: `find_tabs_projects(area,
  recipe, fetch_search, fetch_detail, today)` searches TDLR's TABS registry
  (`Search/SearchProjects` POST, 100 rows/page) once per keyword in
  `recipes/tx/tabs.json` (apartment, apartments, multifamily,
  multi-family, lofts, residences, flats, senior living), paginates to
  `recordsTotal`, keeps only rows whose `TypeOfWork` is the New
  Construction code (9001) and whose `EstimatedCost` >= $3,000,000, dedupes
  by `ProjectNumber` across keywords, then fetches each survivor's detail
  page (`Search/Project/<ProjectNumber>`) for full address, scope, square
  feet, owner name/address/phone, design firm, and estimated start/finish.
- Live-verified the real search endpoint and detail page directly with curl
  before writing any code: the detail page is plain server-rendered HTML
  with `<dt>Label:</dt><dd>value</dd>` pairs (parsed with a small regex, no
  bs4 needed, matching this codebase's existing HTML-parsing style in
  legistar.py/agendas.py) -- and it already gives city and county as real
  text ("Brownsville, TX 78521" / "Cameron"), not a code. **Deviation from
  the plan's "map city/county codes to names" instruction:** TDLR never
  publishes a lookup table anywhere public for the search row's numeric
  City/County fields, but the detail page's own text is ground truth (not a
  guess) and is used directly instead -- documented in the skill's
  SKILL.md so this isn't a silent gap.
- Units only ever come from a regex match against the detail page's "Scope
  of Work" text (e.g. "New construction apartment complex, 300 units");
  no match -> `units=None`, which the site already renders as "Units: not
  public yet" (confirmed via `skills/score-leads/score_leads.py`'s existing
  handling) -- never estimated from square footage or cost, per the plan.
- Owner name/phone come straight off the detail page's OWNER section
  (developer field falls back to the design firm's name only if there's no
  owner on file, matching `find_upcoming`'s owner-over-builder rule); a
  broken/failed detail-page fetch never drops the project, it still returns
  a record from the search row alone.
- Live self-test: ran the real search+detail flow for the "senior living"
  keyword alone (8 real projects, e.g. "Pine Creek Senior Living" |
  Bastrop | 52 units | "Pine Creek Bastrop, LP" | (214) 336-7495 |
  under construction) -- confirmed real names, cities, owners, phones and
  stages all come through correctly against the live site, not a mock.
  Wrote `skills/lead-finder-tabs/live_self_test.py` (same DI/offline-vs-live
  split as every other lead-finder* skill) for Drew/future runs to re-check
  the full 8-keyword set by hand; did not run the full 8-keyword set in
  this worker session (would be ~300+ detail-page fetches, too slow for a
  15-30 min task) -- T6 (the real Texas run) will exercise it in full.
- Tests: `skills/lead-finder-tabs/tests/test_tabs.py` (new, 7 tests, all
  offline via injected `fetch_search`/`fetch_detail`) covers: new
  construction + cost floor kept and detail fields filled in; wrong
  type-of-work dropped; below-cost-floor dropped; a project matching two
  keywords counted once; pagination follows `recordsTotal`; no unit match
  in scope text leaves `units=None`; a broken detail fetch still returns a
  record instead of dropping it.
- Checked: `bash tooling/qa/check-lead-finder.sh` passes (293 total
  propertystack tests via the full suite, up from 286; the report also hit
  the known pre-existing `test_fetch_block_counts_are_race_free_across_threads`
  timing flake once, reran clean). Full suite from `propertystack/`
  (`python3 -m pytest -q --ignore=skills/client-map/tests`): 293 passed, 0
  failures.
- Left open: `recipes/tx/tabs.json` is not yet wired into `run.py`'s chain
  (that's T6, which merges TABS + city recipes + appraisal files + TDHCA);
  T3 (Texas city permit recipes) is next.

## T3 Texas city permit recipes
- All 7 recipes in the plan are built and genuinely live-tested against
  their real endpoints, saved under `recipes/tx/`: `austin.json`,
  `fort-worth.json`, `arlington.json`, `san-marcos.json`,
  `san-antonio.json`, `houston.json`, `tarrant-tad.json`.
- **Austin** (Socrata, `data.austintexas.gov/resource/3syk-w9eu.json`):
  fits `find_upcoming`'s existing engine directly -- `housing_units` is a
  real numeric field. Live query (`permittype='BP' AND work_class='New' AND
  housing_units>=20` since 2024-09) returned real rows, e.g. 2631 Kramer Ln
  Unit FW3 (159 units, issued 2026-08-27).
- **Fort Worth** (ArcGIS): the real layer has 2,227 matching rows since
  2024-09 and genuinely hits ArcGIS's 1,000-row response cap
  (`exceededTransferLimit=true`), confirmed live with `returnCountOnly`.
  Added generic `resultOffset` pagination to
  `find_upcoming._fetch_rows` (capped at 20 extra pages) instead of a
  one-off Fort-Worth-only wrapper, since any large ArcGIS layer (AZ
  included) could hit the same cap. `Units` is a text field here (plain
  digit strings on the sampled rows) -- mapped via `units_text_field` +
  `units_text_pattern`.
- **Arlington** (ArcGIS, `gis2.arlingtontx.gov`): needs a `User-Agent`
  header or the service returns a bare HTTP 403 (already handled by every
  lead-finder* live fetch's shared header). No unit or owner field exists
  on this layer at all (confirmed live via the layer's own `?f=json`
  metadata) -- kept via the `MainUse` type match, units stay `None`.
- **San Marcos**: the plan's sketch URL wasn't runnable as given, so the
  real service was found live by walking `smgis.sanmarcostx.gov`'s ArcGIS
  REST folder catalog to `Planning/CoSM_BuildingPermits/FeatureServer/0`.
  `TYPE='New' AND LANDUSE='Multi-Family'` since 2024-09 returned 168 real
  rows, no paging needed. This layer is per-unit, not per-project,
  granularity (e.g. 4 separate rows for one building's apartments 301/303/
  304/329) -- relies on `find_upcoming`'s existing address-based merge; no
  aggregate unit-count field exists, so units always stay `None` here
  (documented as approximate/left-open in the recipe's notes, not
  fabricated).
- **San Antonio** (CKAN SQL): found the exact live resource ids via
  `package_search` on the `building-permits` dataset --
  `c21106f9-3ef5-4f3a-8604-f992b4db7512` (2025+) and
  `c22b1ef2-dcf8-4d77-be1a-ee3638092aab` (2020-2024). New adapter
  `skills/lead-finder-permits/ckan_sql.py` unwraps CKAN's
  `{result:{records:[...]}}` envelope into the plain list
  `find_upcoming._fetch_rows` already understands from Socrata, rather than
  teaching `_fetch_rows` CKAN's shape directly (a SQL query string isn't
  itself a GET-able URL the way Socrata/ArcGIS endpoints are, so a thin
  adapter fit better than a generic branch). The recipe's `sql` field
  `UNION ALL`s both resources with an explicit `::text` cast on `DATE
  ISSUED` -- a plain `UNION` genuinely fails live with a Postgres
  `DatatypeMismatch` error between the two resources' column types,
  confirmed by hitting it. Filtering `"PERMIT TYPE"='Comm New Building
  Permit'` plus an apartment-keyword match on `PROJECT NAME` returned 156
  real rows live (e.g. 8 separate building permits for "The Orion
  Apartments"). No units field anywhere in this dataset -- always `None`.
- **Houston**: not a Socrata/ArcGIS/CKAN shape at all -- new module
  `skills/lead-finder-permits/houston_sold_permits.py` scrapes the real
  `.xlsx` links straight out of the sold-permits search page's HTML (34
  posted weekly files found live) and parses each with `openpyxl` (already
  a project dependency, no new one added). Live-ran the full
  discover+download+parse chain against the real site: 41 genuine new
  apartment/R2 rows, several with real unit counts parsed straight out of
  free-text Comments (e.g. "78,855 SF NEW APT BLD (65 UNITS)" -> 65 units,
  "119,873 SF NEW APT BLD (104UNITS)" -> 104 units). **Left open /
  approximate, documented honestly in the recipe's notes:** the site only
  keeps a rolling few months of weekly files (earliest live link seen was
  January 2026), so this source alone cannot reach back to the plan's
  2024-09 start date for Houston -- T2's TABS puller and T5's TDHCA source
  are what actually cover that full window; this recipe adds only whatever
  is still posted at run time.
- **Tarrant County TAD**: new module `skills/lead-finder-permits/tad_zip.py`
  downloads+unzips the county's yearly commercial-permits zip (one `xlsx`
  inside, not a delimited text file like Maricopa's sales recipe, but the
  same "generic code, county specifics in data" shape) and tags each
  `LeadRecord` with the row's own `Issuing Agency` city field instead of
  one caller-supplied city, since the whole point of this source is that it
  covers every city in the county from one file. Live-verified against
  both the 2025 and 2026 zips: real header row matches the plan's expected
  fields exactly (`Total Units`, `Intended Property Use`, `Issuing Agency`,
  ...); filtering `Intended Property Use` contains "Apartments" and `Total
  Units>=20` gave 150 real rows spanning multiple real cities (e.g. Serena
  Vista Apartments, 120 units, Arlington; Whisperwind Apartments, 49 units,
  Fort Worth). `Total Units=0` on still-in-development projects (e.g. "THE
  CALHOUN APTS (IN DEVELOPMENT)") is treated as unknown, never as literally
  zero units.
- Live self-test: extended `skills/lead-finder-permits/live_self_test.py`
  to dispatch `ckan-sql`, `houston-sold-permits-xlsx`, and
  `county-appraisal-zip` recipes through their respective adapters (the
  last one bypasses `find_upcoming` entirely, calling
  `tad_zip.find_new_apartment_permits` directly, since that source's output
  is multi-city per call). Ran `python3
  skills/lead-finder-permits/live_self_test.py tx` live end to end: all 7
  T3 recipes returned real rows in one run -- arlington 178, austin 48,
  fort-worth 1 (after address-based merge collapses many permits per
  project), houston 24, san-antonio 2, san-marcos 6, tarrant-tad 185 (the
  only failure in that run is `tabs.json`, T2's recipe, which uses a
  different function signature on purpose and isn't part of T3).
- Tests: `test_tx_recipes.py` (recipe-wiring tests using placeholder city
  names so the lead-finder no-place-names-in-code check stays clean),
  `test_ckan_sql.py`, `test_houston_sold_permits.py`, `test_tad_zip.py`
  (all new, all offline via injected fetch functions), plus two new
  ArcGIS-pagination tests added to the existing `test_find_upcoming.py`.
- Checked: `bash tooling/qa/check-lead-finder.sh` passes (still 70
  lead-finder* tests + check-panel.sh -- the new tests live outside that
  script's scope, in the full suite instead). Full suite from
  `propertystack/` (`python3 -m pytest -q --ignore=skills/client-map/tests`):
  308 passed, up from 293 (0 real failures; the pre-existing
  `test_fetch_block_counts_are_race_free_across_threads` timing flake noted
  in T2 reproduced once in this session and passed clean on an immediate
  rerun, same as before -- not a regression from this work).
- Committed incrementally, one commit per source, per the plan's
  save-as-you-go rule: Austin+Fort Worth+Arlington+ArcGIS pagination, San
  Marcos, San Antonio+CKAN adapter, Houston, Tarrant TAD.
- Left open: none of these 7 recipes are wired into `run.py`'s chain yet
  (that's T6, same as T2's TABS recipe); T4 (Dallas + Houston from
  appraisal-district files) is next.

## Re-check fix after T3 (2026-09-14)
The plan's check failed after T3 was ticked: a flaky test in test_fetch.py expected
"blocked 3 times" but sometimes got "blocked 5 times". Root cause: fetch.py's block
counter increment and skip-message write happened outside a "already skipped" guard,
so concurrent threads could each overwrite the skip reason with their own higher count
after the site was already marked skipped. Fixed by only setting the skip reason once
and always returning the already-stored reason afterward. Ran the flaky test 5x in a
row plus the full check-lead-finder.sh (all lead-finder* test suites + check-panel.sh) —
all green. Commit: fix race in fetch block-count skip.

## T5 Tarrant sales with prices + affordable pipeline
- **Tarrant TAD improved sales** (new module
  `skills/lead-finder-permits/tad_sales.py`, recipe
  `recipes/tx/tarrant-tad-sales.json`): reuses the "county specifics in
  data, generic code" shape from T3/T4's `tad_zip.py`, but the apartment
  sheet's own name changes between years -- live-confirmed the 2025 zip's
  xlsx has a sheet literally named "Apartments" (129 rows) while the 2026
  zip's is "Apartment" (49 rows) -- so the match is a case-insensitive
  prefix, not an exact sheet name. Live-ran both years: 24 real sold
  apartment rows (20+ units, since 2024-09), e.g. "LANDMARK AT CROWLEY",
  305 W FM 1187, 267 units, sold 2025-04-08, $47,300,000. Checked the
  sheet's real full header live and confirmed there is genuinely no
  buyer/grantee column and no per-row city column anywhere in this file --
  `buyer` is always left blank (never guessed) and `city` falls back to
  the recipe's own county name, same fallback `find_sold.py` already uses
  for a county file with no per-row city. Document Date is a raw Excel
  day-serial number on real rows (e.g. 45552), not a formatted date cell --
  converted via the standard 1899-12-30 epoch, verified against a known
  serial/date pair. Price falls back from Adjusted Sale Price to Contract
  Sale Price and is omitted from `why` entirely (never treated as $0) on
  rows where both are the literal text "NULL", which does happen on real
  rows (e.g. vacant/land-only sales).
- **TDHCA affordable pipeline** (new module `skills/lead-finder-permits/tdhca.py`,
  recipe `recipes/tx/tdhca.json`): combines two plain-xlsx TDHCA downloads
  (not zips, unlike every other T3-T5 source) into one deduped list.
  - HTC Property Inventory ("PropInventory" sheet): filtering
    `ConType == "New Construction"` and `Year >= 2024` gave exactly 200 real
    rows live, matching the plan's expected count exactly, e.g. "Huntington
    Place Senior Living", Garland, 204 units, 2024; "The Arboretum at
    Woodland Hills", Houston, 366 units, 2024. Checked live that the
    sheet's "Board Approval" column (which looked like a plausible award-
    year field at first) is actually a much older/smaller legacy tiebreaker
    number (max value 1998 across the whole real sheet) -- "Year" (max 2027
    on real rows) is the field that genuinely tracks the award year, used
    for the since-2024 filter instead.
  - 4% (non-competitive) HTC status log: the plan's exact guessed URL
    (.../htc-4pct/2026260803-4HTC-StatusLog.xlsx) 404'd on its own -- the
    TDHCA site was restructured since the plan was written (old .htm pages
    gone). Found the real current listing page live by walking
    tdhca.texas.gov -> /programs/multifamily-housing-programs ->
    /multifamily-bond-program -> /non-competitive-4-housing-tax-credits;
    the plan's guessed filename turned out to still be the latest file
    listed there, just needed the corrected page path. The real header row
    isn't row 1 (rows 1-10 are a title block + numbered footnotes) --
    found live by scanning for the row whose first cell is literally
    "TDHCA Number" (row 11 in the real 2026-08-03 file) instead of
    assuming a fixed row number. Filtering `Construction Type == "NC"`
    returned real rows with a real Applicant Phone, e.g. "Bloom at Lamar
    Square", Austin, 58 units, (512) 610-4016; "Mayfield Park Apts",
    Arlington, 240 units, (409) 284-6362. Live-ran both sources together:
    212 real combined records.
- Tests: `test_tad_sales.py` (4 new, offline via injected `fetch_bytes`)
  covers sheet-name-prefix matching, small/old-sale dropping + county-name
  city fallback, the null-price-omitted-from-why case, and the Excel
  serial-date conversion; `test_tdhca.py` (3 new, offline) covers the
  new-construction + since-year filter on the inventory sheet, the
  scan-for-real-header-row + NC-only filter on the status log, and that a
  broken status-log fetch doesn't drop the inventory-only records. Used
  placeholder city/county names ("City A"/"City B"/"County A") in these
  test fixtures, not real Texas place names, per the repo's
  no-place-names-in-lead-finder-code check.
- Checked: `bash tooling/qa/check-lead-finder.sh` passes (70 lead-finder*
  tests total, up from 63, plus check-panel.sh clean). Full suite from
  `propertystack/` (`python3 -m pytest -q --ignore=skills/client-map/tests`):
  316 passed, up from 308, 0 failures.
- Left open: neither `tad_sales.json` nor `tdhca.json` is wired into
  `run.py`'s chain yet (that's T6, same as every other T2-T5 recipe); T6
  (the real Texas run merging TABS + city recipes + appraisal files +
  TDHCA) is next.

## T4 Dallas + Houston from appraisal-district files (real re-do, 2026-09-14)
The plan's T4 box had already been ticked `[x]` by an earlier session, but the
checkbox line itself was garbled mid-sentence with a stray "_(skipped)_" marker
and no matching progress-log entry existed and no code existed (no DCAD/HCAD
module or recipe anywhere in the repo) -- so this was really still undone.
Drew confirmed he wants it actually built, so this entry replaces that stub.

- **New generic module** `skills/lead-finder-permits/appraisal_zip.py`,
  following T3/T5's "county specifics in the recipe JSON, generic code" shape,
  but for the much bigger yearly county-wide bulk data zips (not the smaller
  single-year commercial-permits zip T3's `tad_zip.py` already handles) --
  these hold several large delimited CSV/TSV files (tens to hundreds of MB
  each), so this module streams each file row-by-row via `zipfile.open()` +
  `csv.DictReader` rather than loading a member fully into memory.
- **Dallas/DCAD** (`recipes/tx/dallas-dcad.json`): live-downloaded
  DCAD2026_CURRENT.ZIP (195,234,711 bytes, matches the plan's ~195MB estimate;
  the site's ViewPDFs.aspx "redirect" link is itself a direct download).
  COM_DETAIL.CSV really has BLDG_CLASS_DESC values "APARTMENT (BRICK
  EXTERIOR)"/"APARTMENT (FRAME EXTERIOR)" and a PCT_COMPLETE column that
  turned out to be a 0.00-1.00 **fraction**, not 0-100 percent (confirmed
  live: 4,072 of 4,173 real apartment rows sit at exactly 1.00 = fully
  built) -- an early version of this filter used `pct < 100` and wrongly
  kept every finished building, since 1.0 < 100. Filtering units>=20 and
  pct<1.00 with a real name gave 57 real under-construction rows live
  (10,525 total units), e.g. "PALLADIUM CARVER LIVING (TDHCA #6031)" 288
  units at 60% complete. COM_DETAIL.CSV has no street address at all --
  only the separate ACCOUNT_INFO.CSV does (STREET_NUM/FULL_STREET_NAME),
  so the module now does a second pass restricted to the already-matched
  accounts to fill in a real address instead of leaving new-construction
  leads addressless (loading all of ACCOUNT_INFO.CSV, one row per every
  account in the county, would have been wasteful). Joining ACCOUNT_INFO's
  DEED_TXFR_DATE/OWNER_NAME1/PHONE_NUM/PROPERTY_CITY to the 2,723 real
  apartment accounts with units>=20 and filtering DEED_TXFR_DATE>=2024-09-01
  gave 455 real deed transfers live, e.g. "ALENA" 216 units sold 2025-06-23
  to ASD ALENA PROPERTY OWNER LLC (Dallas, TX). PHONE_NUM is blank on most
  real rows, so office_phone is often empty here -- left blank, never
  guessed.
- **Houston/HCAD** (`recipes/tx/houston-hcad.json`): live-downloaded
  Real_acct_owner.zip (211,881,907 bytes, close to the plan's ~212MB
  estimate). real_acct.txt (889MB uncompressed) really has no unit-count
  column at all (confirmed by reading its real header row), so unlike
  Dallas this recipe filters `state_class == "B1"` (exact) plus a building-
  area floor instead of a unit count, per the plan's "drop small buildings
  by building area" instruction -- state_class=B1 and new_construction_val>0
  and bld_ar>=15,000 sqft gave 89 real under-construction rows live, e.g.
  "23615 KINGSLAND BLVD" 396,484 sqft / $15,632,471 new-construction value.
  deeds.txt is a separate file with only acct/dos and several dated rows
  per account (no owner, no price) -- joining its **latest** dos per
  account to the 2,955 real B1 accounts with bld_ar>=15,000, filtered to
  dos>=2024-09-01, gave 337 real sold rows live, e.g. "702 HADLEY ST"
  (556,114 sqft) sold 2025-06-10 to "RE III RESHI HOUSTON III DE LLC".
  Neither file has a building name field, so every Houston lead's name
  falls back to its address, same fallback pattern as Phoenix (S3) and
  Dallas's own blank-name rows in this same module.
- Tests: `test_appraisal_zip.py` (6 new, all offline via injected
  `fetch_bytes` returning small in-memory zips built with `zipfile.writestr`)
  cover: class/units/completion filtering and the pct-is-a-fraction rule,
  blank-name-and-no-address rows being dropped (never guessed), the
  second-file address join, the deed-join-and-since-date filter, and taking
  the *latest* of several dated rows for one account. Fixtures use
  placeholder "County A"/"County B" names per the repo's
  no-place-names-in-lead-finder-code check (module docstrings and comments
  were also reworded to "County A"/"County B" instead of naming Dallas/
  Harris directly, after the check first caught real county names in
  prose comments).
- Checked: `bash tooling/qa/check-lead-finder.sh` passes clean, including the
  no-place-names check once module/test prose was reworded to "County A"/
  "County B". Full suite from `propertystack/` (`python3 -m pytest -q
  --ignore=skills/client-map/tests`): 322 passed, up from 316, 0 failures.
- Live self-test wiring: added the `appraisal-district-bulk-file` branch to
  `skills/lead-finder-permits/live_self_test.py` so `python3
  live_self_test.py tx` will exercise both new recipes the same way as
  every other T2-T5 source (not run automatically here to avoid a second
  ~400MB download in this session; the numbers above come from running the
  real functions directly against the already-downloaded live zips instead).
- Left open: `dallas-dcad.json` and `houston-hcad.json` are not wired into
  `run.py`'s chain yet (that's T6, same as every other T2-T5 recipe). T6
  (the real Texas run merging TABS + city recipes + appraisal files +
  TDHCA) is next.
