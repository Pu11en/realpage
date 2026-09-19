# Build C progress

## 2026-09-19 — T1 stable first-seen dates

- Added `firstSeen` to every built lead. Existing IDs retain their saved date, pre-field leads start at the current data date (`2026-09-15`), and newly appearing IDs use the build date.
- Rebuilt the current legacy, Arizona, New York, and Texas lead JSON files so every current row starts at `2026-09-15`.
- Added regression tests for date preservation, migration, new IDs, and complete coverage of built lead files.
- Implementation commit: `c1fc09f`.
- Checked with `python3 -m pytest -q tooling/qa/fixes_tests/` (`221 passed`) and the full project test command (`268 passed`).
- Build note: the first patch command was rejected before making changes because it targeted one file twice; the corrected patch applied cleanly.
- Left open: T2–T4 remain untouched.

## 2026-09-19 — T2 downloadable Lead Pack

- Vendored pinned jsPDF 4.2.1 and jsPDF-AutoTable 5.0.8 browser bundles with their MIT license files; the Lead Pack runs entirely in the browser with no paid AI or CDN call.
- Added the Early Leads download action for the selected state or region. Its letter-size PDF has one row per lead with building, city, units, Hot/Warm/Early priority and reason, timing, available owner/developer/buyer and phone details, a why-now sentence, and a clickable free source; it also has the requested title, footer, and dated filename.
- Reused the chat panel's existing account check. Signed-out visitors see “Make a free account to download your Lead Pack,” and the queued download starts automatically after sign-in; local auth-off development and already signed-in visitors continue immediately.
- Added a regression test that builds all 307 Dallas–Fort Worth rows, checks every structured row, opens the resulting PDF, confirms letter dimensions, and counts 307 source-link annotations.
- Implementation commit: `d3d2384`.
- Checked with `python3 -m pytest -q tooling/qa/fixes_tests/` (`224 passed`) and the active project command from README (`271 passed`). JavaScript syntax and whitespace checks passed for the authored files.
- Browser smoke: Chromium downloaded `cranesignal-lead-pack-dallas-fort-worth-2026-09-19.pdf` with 307 leads across 27 pages, 307 source links, the correct success message, and no page errors; the first page was visually checked for readable layout.
- Build notes: a first temporary-package inspection command was rejected because it included prohibited cleanup, then succeeded without that cleanup. Bare repository-wide `pytest` still cannot collect archived projects with missing legacy imports, while the documented active suites pass. The first browser smoke timed out because its catch-all mock intercepted the auth-config request; a single corrected route then passed.
- Left open: T3–T4 remain untouched.
