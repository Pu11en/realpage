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
