# Progress: PLAN-client-map

## C1 Skeleton + tests — done (commit 7356a24)
- Added `propertystack/skills/client-map/` with `SKILL.md`, `run.py` (SearchBudget capped at 150, `search_targets` stops cleanly at the cap, `vendor_of` via pms_detect VENDORS, `is_realpage_proof` = loftliving/activebuilding/onesite.realpage.com only, `dedupe` by portal host or normalized address, `counts` per state/city) and `tests/test_client_map.py` (12 fixture-only tests).
- Checked: tests failed with an empty run.py (12 failed), then 12 passed; `check-panel.sh` clean (0 problems, panel clean).
- Open: `run.py` main is a stub until C3.

## C1 fix — check command (plan check failed)
- The bot runs `Check:` without a shell, so `&&` reached pytest as a filename. Moved both steps into `tooling/qa/check-client-map.sh` and pointed the plan's `Check:` line at it.
- Checked: `bash tooling/qa/check-client-map.sh` → 12 passed, 0 problems, panel clean, exit 0.
