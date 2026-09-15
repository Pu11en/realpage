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
