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

## D2 Map numbers in the chat — done

What I did:
- Added `tooling/chat-data/build_map_summary.py`, which flattens `site/data/client-map.json`
  (the site's leads-by-state map, itself built from `propertystack/data/client-map/counts.json`)
  into one row per state/top-city pair: `state, abbr, state_total, city, city_count`.
- Ran it once and committed its output at `propertystack/data/map-summary/kb/map-summary.csv`
  (20 states, 46 data rows).
- Updated `chatbot/Dockerfile`'s `kb` stage to also copy `propertystack/data/map-summary/kb/*.csv`
  into `/kb/data`, landing as table `map_summary`.
- Updated `chatbot/hermes-profile/plugins/propertystack/__init__.py`: added `map_summary` to
  `SOURCE_NAMES` and a `ps_schema` note saying to use `map_summary` (not `state_leads`) for
  "which state/city has the most leads" so the answer matches the map, and that `state_total`
  repeats per city row (don't sum it across a state's own rows).
- Updated `chatbot/hermes-profile/skills/query-propertystack/SKILL.md`'s table with the same row.
- Added a check_answers question: "Which state has the most leads, and what are its top cities?"
  (not run — costs money, Drew runs it).
- Added `tooling/qa/fixes_tests/test_d2_map_summary.py`: rebuilds the kb the Dockerfile way into a
  temp dir, runs the plugin's real `_build_db()`, asserts the `map_summary` table loads, and
  asserts every state's `state_total` in the built table exactly matches `client-map.json`'s
  `total` for that state (fails without the fix — table wouldn't exist / numbers could drift).

Commit: see git log (message "D2: ship the site's lead map into the chat as map_summary").

How I checked it: `bash tooling/qa/check-fixes.sh && python3 -m pytest -q chatbot/tests` — both
pass (114 fixes_tests + design check, 35 chatbot tests).

Anything left open: none for this task. Like D1, the chat container wasn't rebuilt/tried live
(D7 does that).
