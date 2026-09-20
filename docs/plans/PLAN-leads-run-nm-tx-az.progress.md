# Progress: one-command lead runs — New Mexico + fresh Texas and Arizona

- 2026-09-19 — T1 complete: replaced positional lead IDs with deterministic state/address/name content IDs, added content-based `firstSeen` migration, and rebuilt the checked-in lead snapshots so Texas and Arizona kept their 2026-09-15 dates. Added tests for normalization, row reordering, ID uniqueness, and legacy migration.
  - Commit: `770ed4e` (implementation and rebuilt data)
  - Checks: `python3 -m pytest -q tooling/qa/fixes_tests/ propertystack -x -q` (570 collected, all passed); `python3 site/data/build_data.py`; `python3 -m py_compile site/data/build_data.py`; `git diff --check`.
  - Open: the separate `tooling/qa/check_lead_data.py` gate is introduced by T2 and does not exist yet.

- 2026-09-19 — T1 reviewer repair complete: restored New York's `hidden: true` setting, made the area-manifest rebuild preserve existing hidden areas, and added a regression test proving a rebuild cannot reveal New York again.
  - Commit: `78962a2` (durable hidden-area preservation and regression test)
  - Checks: `python3 -m pytest -q tooling/qa/fixes_tests/test_build_c_first_seen.py -q` (5 passed); `python3 site/data/build_data.py` followed by an assertion that New York remains hidden; `python3 -m pytest -q tooling/qa/fixes_tests/ propertystack -x -q` (571 passed); `python3 -m py_compile site/data/build_data.py`; `git diff --check`.
  - Open: the separate `tooling/qa/check_lead_data.py` gate is introduced by T2 and does not exist yet.

- Reviewer still had concerns about T1 Stable ids + honest "new": give every lead a content id (state + normalised address + name), keep it across runs, and stamp `firstSeen` by that id in site/data/build_data.py (today it matches by list position, so a re-run mislabels new leads). Migrate existing tx/az leads so today's rows keep their first-seen date. Tests.: Make duplicate/sparse lead IDs depend only on durable source identity (or exclude rows without address/name), never score/rank or other changing display fields; add a test that reranking the same sparse leads preserves IDs and firstSeen.

- 2026-09-19 — T2 complete: added a reusable lead-data publishing gate that checks source URLs, duplicate normalized addresses, stable and unique built IDs, and lead-count losses over 20%. It accepts any state folder or leads JSON file, reports all problems in plain English, prefers a saved `leads.before-run.json` baseline, and otherwise compares with the currently published state snapshot.
  - Commit: `a974c29` (checker and four offline regression tests)
  - Checks: `python3 tooling/qa/check_lead_data.py` (3 states, 867 leads passed); `python3 -m pytest -q tooling/qa/fixes_tests/ propertystack -x -q` (all passed); targeted checker tests (4 passed); `python3 -m py_compile tooling/qa/check_lead_data.py tooling/qa/fixes_tests/test_check_lead_data.py`; `git diff --check`.
  - Open: T3 must preserve each state's pre-run file as `leads.before-run.json` (or pass `--previous`) so the loss guard still has the old count after site data is rebuilt. The earlier reviewer concern about sparse T1 IDs remains outside this task.
