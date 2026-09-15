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
