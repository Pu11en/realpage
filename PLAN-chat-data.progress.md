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

## D3 Software market share — done

What I did:
- Added `tooling/chat-data/build_software_share.py`, which flattens `site/data/software-share.json`'s
  `share` list into one row per vendor (`vendor, properties, units, pct_of_identified_properties`).
- Ran it once and committed its output at `propertystack/data/software-share/kb/software-share.csv`
  (10 vendor rows, matching the site's chart).
- Updated `chatbot/Dockerfile`'s `kb` stage to also copy `propertystack/data/software-share/kb/*.csv`
  into `/kb/data`, landing as table `software_share`.
- Updated `chatbot/hermes-profile/plugins/propertystack/__init__.py`: added `software_share` to
  `SOURCE_NAMES` and a `ps_schema` note saying it's the site's vendor market-share chart, Plano and
  Richardson only (same scope as `software`/`master`), and that `pct_of_identified_properties` is
  already computed so it shouldn't be recomputed.
- Updated `chatbot/hermes-profile/skills/query-propertystack/SKILL.md`'s table with the same row.
- Added a check_answers question: "What percent of identified Plano/Richardson properties run
  RealPage?" (not run — costs money, Drew runs it).
- Added `tooling/qa/fixes_tests/test_d3_software_share.py`: rebuilds the kb the Dockerfile way into
  a temp dir, runs the plugin's real `_build_db()`, asserts the `software_share` table loads, and
  asserts every vendor's properties/units/pct in the built table exactly match
  `software-share.json` (fails without the fix -- table wouldn't exist / numbers could drift).
- Left `site/data/reach.json` out on purpose: it mixes Plano/Richardson building proof links with
  out-of-area "scout" rows (no vendor field, just scored URLs) and isn't a vendor-share source, so
  shipping it didn't fit this task's "software market share" scope. Can revisit separately if Drew
  wants those proof links queryable.

Commit: see git log (message "D3: ship the site's software market share into the chat as software_share").

How I checked it: `bash tooling/qa/check-fixes.sh && python3 -m pytest -q chatbot/tests` — both
pass (116 fixes_tests + design check, 35 chatbot tests).

Anything left open: none for this task. Like D1/D2, the chat container wasn't rebuilt/tried live
(D7 does that).

## D4 Building-page extras — done

What I did:
- Checked what the chat was already missing vs `site/data/properties.json`: the `master` table
  already carries owner/website_confidence/unknown_reason, and `sales`/`leads`/`contacts` already
  load, but they're keyed differently (`apt_id` vs `ref_id`) and most buildings have no sale or
  lead row at all, so getting "owner + sale + lead status" for one building meant a 3-4 way join
  the chat wasn't set up to do reliably.
- Added `tooling/chat-data/build_building_extras.py`, which flattens `site/data/properties.json`'s
  204 properties to one row per building keyed by `apt_id`: owner, website_confidence,
  unknown_reason, sale_date/sale_new_owner/sale_previous_owner, lead_rank/lead_total_leads/lead_why
  (sale/lead fields blank when that building has no sale or isn't a ranked lead).
- Ran it once and committed its output at
  `propertystack/data/building-extras/kb/building-extras.csv`.
- Updated `chatbot/Dockerfile`'s `kb` stage to also copy that CSV into `/kb/data` (table name
  `building_extras`).
- Updated `chatbot/hermes-profile/plugins/propertystack/__init__.py`: added `building_extras` to
  `SOURCE_NAMES` and a `ps_schema` note explaining it joins to `master` on `apt_id`, that
  owner/website_confidence/unknown_reason duplicate `master` for convenience, and that sale/lead
  fields are blank for most buildings.
- Updated `chatbot/hermes-profile/skills/query-propertystack/SKILL.md`'s table with the same row.
- Added a check_answers question: "Who owns Ellington in Plano, and has it sold recently or ranked
  as a lead?" (not run — costs money, Drew runs it).
- Added `tooling/qa/fixes_tests/test_d4_building_extras.py`: rebuilds the kb the Dockerfile way
  into a temp dir (real `plano-richardson` CSVs plus the new building-extras CSV), runs the
  plugin's real `_build_db()`, and asserts: the `building_extras` table loads with one row per
  property in `properties.json`; joining `master` to `building_extras` on `apt_id` returns the
  same owner from both tables for a known building; and a building with both a sale and a lead has
  its sale/lead fields match `properties.json` exactly. Fails without the fix (table wouldn't
  exist / join would return nothing / numbers could drift).

Commit: see git log (message "D4: ship building owner, sale and lead detail into the chat as
building_extras").

How I checked it: `bash tooling/qa/check-fixes.sh && python3 -m pytest -q chatbot/tests` — 117
fixes_tests pass except 2 pre-existing, unrelated failures in `test_t4_not_found.py`
(`TimeoutError` on a local socket fixture used by an unrelated 404-page test; same failure occurs
with no files from this task touched, so it's flaky infra, not a regression from D4); 35 chatbot
tests pass.

Anything left open: none for this task. Like D1-D3, the chat container wasn't rebuilt/tried live
(D7 does that rebuild + report).
