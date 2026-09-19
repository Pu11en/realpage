# Build C progress

## 2026-09-19 — T1 stable first-seen dates

- Added `firstSeen` to every built lead. Existing IDs retain their saved date, pre-field leads start at the current data date (`2026-09-15`), and newly appearing IDs use the build date.
- Rebuilt the current legacy, Arizona, New York, and Texas lead JSON files so every current row starts at `2026-09-15`.
- Added regression tests for date preservation, migration, new IDs, and complete coverage of built lead files.
- Implementation commit: `c1fc09f`.
- Checked with `python3 -m pytest -q tooling/qa/fixes_tests/` (`221 passed`) and the full project test command (`268 passed`).
- Build note: the first patch command was rejected before making changes because it targeted one file twice; the corrected patch applied cleanly.
- Left open: T2–T4 remain untouched.
