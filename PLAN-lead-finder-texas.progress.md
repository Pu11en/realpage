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
