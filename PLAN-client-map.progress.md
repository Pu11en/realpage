# Progress: PLAN-client-map

## C1 Skeleton + tests — done (commit 7356a24)
- Added `propertystack/skills/client-map/` with `SKILL.md`, `run.py` (SearchBudget capped at 150, `search_targets` stops cleanly at the cap, `vendor_of` via pms_detect VENDORS, `is_realpage_proof` = loftliving/activebuilding/onesite.realpage.com only, `dedupe` by portal host or normalized address, `counts` per state/city) and `tests/test_client_map.py` (12 fixture-only tests).
- Checked: tests failed with an empty run.py (12 failed), then 12 passed; `check-panel.sh` clean (0 problems, panel clean).
- Open: `run.py` main is a stub until C3.
