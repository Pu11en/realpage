# Progress log

## D1 Parked Dallas data in the chat — done

What I did:
- Added `tooling/chat-data/build_dallas.py`, a small build step that copies
  `propertystack/data/dallas-parked/*.csv` into `propertystack/data/dallas-parked/kb/*.csv`,
  adding an `area="dallas"` column, and renaming files so the plugin's table-naming rule turns
  them into `dallas_buildings`, `dallas_websites`, `dallas_software`, `dallas_sales`,
  `dallas_contacts` (no clash with the existing `apartments`/`websites`/`software`/`sales`/
  `contacts` tables).
- Ran the build step once and committed its output CSVs under `propertystack/data/dallas-parked/kb/`.
- Updated `chatbot/Dockerfile`'s `kb` stage to also copy `propertystack/data/dallas-parked/kb/*.csv`
  into `/kb/data` (the same flat dir the plugin loads every `*.csv` from).
- Updated `chatbot/hermes-profile/plugins/propertystack/__init__.py`: added the 5 new tables to
  `SOURCE_NAMES` and added a `ps_schema` note saying these are a separate Dallas-wide survey, not
  leads, and to never add them to Texas/DFW lead counts, and that `dallas_software` is almost
  entirely `unknown` so it shouldn't count toward vendor market share.
- Updated `chatbot/hermes-profile/skills/query-propertystack/SKILL.md` table with the same scope note.
- Added a question to `tooling/qa/check_answers.py` (not run — costs money, Drew runs it) asking
  about the Dallas-area survey size and whether it differs from the Dallas–Fort Worth lead count.
- Added `tooling/qa/fixes_tests/test_d1_dallas_parked.py`: rebuilds the kb the Dockerfile way into
  a temp dir, runs the plugin's real `_build_db()`, and asserts the 5 `dallas_*` tables load with
  an `area` column and that the `leads` table's row count is untouched (still equals `leads.csv`'s
  row count) — this test fails without the fix (tables wouldn't exist / Dockerfile wouldn't copy them).

Commit: see git log (message "D1: load the Dallas-area building survey into the chat, scoped and separate from leads").

How I checked it: `bash tooling/qa/check-fixes.sh && python3 -m pytest -q chatbot/tests` — both pass
(112 fixes_tests + design check, 35 chatbot tests).

Anything left open: none for this task. The chat container itself wasn't rebuilt/tried live (D7
does that rebuild + report); the local dev-server based tests above prove the data loading logic
without needing Docker.
