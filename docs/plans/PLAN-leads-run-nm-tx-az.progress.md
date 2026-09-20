# Progress: one-command lead runs — New Mexico + fresh Texas and Arizona

- 2026-09-19 — T1 complete: replaced positional lead IDs with deterministic state/address/name content IDs, added content-based `firstSeen` migration, and rebuilt the checked-in lead snapshots so Texas and Arizona kept their 2026-09-15 dates. Added tests for normalization, row reordering, ID uniqueness, and legacy migration.
  - Commit: `770ed4e` (implementation and rebuilt data)
  - Checks: `python3 -m pytest -q tooling/qa/fixes_tests/ propertystack -x -q` (570 collected, all passed); `python3 site/data/build_data.py`; `python3 -m py_compile site/data/build_data.py`; `git diff --check`.
  - Open: the separate `tooling/qa/check_lead_data.py` gate is introduced by T2 and does not exist yet.
