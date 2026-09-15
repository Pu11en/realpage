## A1 Phones — done (7f8a73b)
- Added the viewport tag to index, under-the-hood, property, ai-visibility (one line only) and the master-table redirect page, so every site/*.html has it.
- sweep.py and quick-check.py phone runs now use is_mobile=True, has_touch=True.
- Test: tooling/qa/fixes_tests/test_a1_viewport.py (tag on every page; QA scripts emulate phones).
- Checked: check-fixes.sh passes (2 tests, design check 0 problems); every page at 390px phone emulation has no sideways scroll (Under the Hood's wide table scrolls inside its own box).
- Note: port 8791 had a stale server serving old pages; use another port if checks look odd.

## A2 Early Leads stat boxes + Nothing found — done (46fde57)
- New leadStats(rows) in site/js/app.js; index.html renders the 4 number boxes from the rows currently shown (state, region, city, search, signal, software, hide-mine) on every filter change.
- "Opening soon" is now the count of shown, not-sold buildings opening in the next 12 months (same meaning the state builds already used).
- Empty result: one row "Nothing found. Clear the search or pick another region." with a Clear search button.
- Test: tooling/qa/fixes_tests/test_a2_stats_follow_filters.py (runs leadStats in node on the DFW rows).
- Checked: check-fixes.sh passes (5 tests, design 0 problems); in a browser Texas shows 628 leads, DFW 320 leads / 68,254 units, "zzzz" shows Nothing found, Clear search brings back 320 rows; no page errors.

## A3 Chat panel no longer hides Software and Why — done (7b801fc)
- With the chat docked on desktop (900px+), the Early Leads table turns into one card per lead (same layout as phones), so Software and Why are always visible; before, the table scrolled sideways inside its box and those two columns sat out of view.
- The Chat menu link no longer gets the selected look; while the panel is open it reads "Close chat". Only the current page's tab is selected.
- Test: tooling/qa/fixes_tests/test_a3_chat_panel_layout.py.
- Checked: check-fixes.sh passes (7 tests, design 0 problems); check-panel.sh clean; browser at 1000/1280/1440 wide with panel open: no sideways scroll, only "Early Leads" selected.

## A4 Every building opens a detail page — done (a5d938d)
- Every Early Leads row is now clickable: rows with no propertyId link to property.html?id=<lead id>&area=<state>.
- property.html: if the id isn't in properties.json, new findLead/pickLead (site/js/app.js) looks it up in the state files (asked state first) and shows name, address, city, state, units, developer/buyer, stage, signal, dates, software, score + why, phone, sources (plain labels for non-link sources) and the Deep dive button.
- Test: tooling/qa/fixes_tests/test_a4_every_lead_opens.py (all built lead ids resolve, via node).
- Checked: check-fixes.sh passes (10 tests, design 0 problems); browser: tx-1, az-1, ny-1, a Plano property and a click from the Arizona list all open, "zzz" still says not found, Deep dive opens chat, no page errors.
- Left for later tasks: Deep dive still calls non-sold rows "planned" (A5); raw ArcGIS source URLs shown as-is (C4); NY units 0 shows "units not stated" here.

## A5 Deep dive says the real stage — done (11b4f02)
- deepDivePrompt in site/js/chat-panel.js now takes the lead's stage/signalType and says it in plain words: "permit filed", "planned", "under construction", "leasing now" (asks who is leasing it / how full), or "recently sold". Plano property stages (zoning-filed, under-construction, ...) map too.
- Early Leads and the detail page pass stage + signalType instead of a guessed "upcoming" flag (before, TX "Planned"/"Leasing" rows got the existing-building prompt and every other upcoming row was called "planned").
- Test: tooling/qa/fixes_tests/test_a5_deep_dive_stage.py (fails on the old code).
- Checked: check-fixes.sh passes (12 tests, design 0 problems).

## A6 Menu footer honest — done (4118523)
- build_data.py now writes "updated" (the build day) into site/data/areas/index.json; the menu footer reads it and shows "Last updated: Sep 15, 2026" (rebuilt data committed; only index.json changed).
- "View as" dropdown has a plain "View as" label and tooltip "Highlight the buildings a Yardi / Entrata / AppFolio seller would win"; "Neutral" is now "Everyone" (an old saved "Neutral" choice reads as Everyone; index.html hide-mine filter updated).
- Test: tooling/qa/fixes_tests/test_a6_menu_footer.py.
- Checked: check-fixes.sh passes (16 tests, design 0 problems); browser on index/map/property/under-the-hood shows the date and label, no page errors.
- Note: the date changes whenever build_data.py is rerun (that is the point).

## A7 Under the Hood cleaned for users — done (92ed756)
- Removed "area: plano-richardson" and the "propertystack/runs/*.json" tag; the intro now says the step detail comes from the Plano and Richardson sample and the site has 909 leads across Texas, Arizona, New York (read live from areas/index.json).
- Run history only lists successful runs (the one build-reach error row and the status-less client-map row are hidden); no "(N errors)" text.
- The "Cost per area" card with the PLACEHOLDER box is gone.
- The last pipeline step now shows "909 leads on the site" (site total) instead of the Plano-only "49 ranked leads".
- Test: tooling/qa/fixes_tests/test_a7_under_the_hood.py.
- Checked: check-fixes.sh passes (19 tests, design 0 problems); browser shows 909, no PLACEHOLDER/error/plano-richardson, no page errors.
- Left: pipeline.json still carries costPerArea and error runs (page just hides them); skill names like find-apartments still show under each step.

## A8 Privacy page — done (a73ee37; landing repo 9b5b29f)
- site/privacy.html: sign-in section now covers Google sign-in and email sign-up (name, email, hashed password), early-access sign-up emails, chats; new Contact section; old "support email on the Google sign-in screen" line removed. Date bumped to Sep 15, 2026.
- App menu footer (site/js/app.js renderShell) has a "Privacy" link under Last updated.
- Landing footer (business/marketing/landing/index.html, its own repo) links to https://app.cranesignal.com/privacy.html; committed there (9b5b29f).
- ⚠️ No contact email exists on the landing page, so the page says CONTACT_EMAIL_TBD: Drew must pick one (for D1 report).
- Test: tooling/qa/fixes_tests/test_a8_privacy.py. Checked: check-fixes.sh passes (21 tests, design 0 problems).

## A9 Map labels easier to read — done (e6277c2)
- Each state label ("TX · 628 leads") now sits in a small white pill with navy text and a soft shadow, above its amber dot, so it no longer sits on dark blue.
- site/js/map.js layoutLabels() sizes label text (~12px on screen) and the dot to the drawn map width and refits the pill on resize, so on a phone the labels stay readable (before they shrank to ~5px) and dots are easier to tap.
- Test: tooling/qa/fixes_tests/test_a9_map_labels.py.
- Checked: check-fixes.sh passes (23 tests, design 0 problems); browser at 1280 wide and phone 390 wide (mobile/touch): pills readable, no sideways scroll, no page errors.

## B1 No more "PropertyStack" in chat sources — done (dff4f4c)
- Chat Sources now say "CraneSignal lead ranking" (plugin SOURCE_NAMES and the query-propertystack SKILL.md table); tool descriptions and the skill description say CraneSignal. Internal names (plugin/skill/toolset ids, hermes-agent) unchanged.
- proxy.py: no user-facing message had the old names; only its top docstring changed. SOUL.md only mentions the names in its "never say" rule, left as is.
- Sign-in popup: Open WebUI adds " (Open WebUI)" to WEBUI_NAME itself. webui.Dockerfile (Railway) patches that line out (checked against the real image: env.py line becomes pass); branding/loader.js also strips it from the page title and text, covering the local compose.
- ⚠️ For D1 report: the Open WebUI license only allows removing its name while we have 50 or fewer users in any 30 days; beyond that, restore it or buy their enterprise license. Takes effect live only after the chat app is redeployed (Drew).
- Test: tooling/qa/fixes_tests/test_b1_chat_names.py. Checked: check-fixes.sh passes (28 tests, design 0 problems); chatbot/tests 35 passed.

## B2 Chat counts match the site — done (c13eaa8)
- build_data.py now writes each state's chat-leads.csv after merging its included areas, so Texas chat-leads.csv holds the 42 Plano-Richardson leads (region Dallas–Fort Worth; stage sold/planned from Sold/Upcoming). Chat Texas = 628 (site total), DFW = 320. Rebuilt; only tx/chat-leads.csv changed.
- Skill table and ps_schema notes say Texas already includes Plano/Richardson: count from state_leads alone, never add the leads table on top.
- check_answers.py: new question "How many leads in Dallas–Fort Worth?" with an expected-number check (320). Not run (costs money; Drew runs it).
- Test: tooling/qa/fixes_tests/test_b2_chat_counts.py builds the chat database like the Dockerfile and runs the chat's SQL (fails on the old CSV).
- Checked: check-fixes.sh passes (30 tests, design 0 problems); chatbot + lead-finder tests 105 passed.
- Left: live chat picks this up only after redeploy (Drew).

## B3 Vendor answers say their scope — done (33d035c)
- Checked the data: only the Plano/Richardson rows have software (TX: Yardi 13, RealPage 4, Entrata 2, ResMan 2, AppFolio 1); every other TX/AZ/NY row is blank.
- SOUL.md: new rule "Software answers say their scope": vendor counts/rankings must say they cover Plano and Richardson only (with an example), never Texas-wide or nationwide.
- query-propertystack SKILL.md: "Software scope" note; ps_schema notes in the plugin say the same.
- check_answers.py: new question "Which vendor runs the most buildings?" that flags answers not naming Plano and Richardson. Not run (costs money; Drew runs it).
- Test: tooling/qa/fixes_tests/test_b3_vendor_scope.py (also checks the rule stays true in the data).
- Checked: check-fixes.sh passes (34 tests, design 0 problems); chatbot/tests 35 passed.
- Left: live chat picks this up only after redeploy (Drew).

## B4 Saved deep dives are free — done (8618b26)
- proxy.py gateway_chat: a saved deep-dive replay is served before _free_take, so it uses neither a daily question nor a weekly deep dive. "Fresh deep dive" / ↻ redos still count.
- chatbot/tests/test_usage_limits.py: test_replayed_deep_dive_counts replaced by test_replayed_deep_dive_is_free (5 replays free, 2 more fresh dives allowed, then the limit).
- Checked: chatbot/tests 35 passed; check-fixes.sh passes (34 tests, design 0 problems).
- Left: live chat picks this up only after redeploy (Drew).

## C1 Junk permits out — done (b0e6fc3)
- New shared filter propertystack/skills/lead-finder/junk_permits.py: pool, carport, stair/remodel, repair, roof and garage-apartment permits are not leads (a street like "Brentwood Stair Rd" is not caught). Used by the permit sources (find_upcoming.py by project name, houston_sold_permits.py by permit comments) and by build_data.py so already-saved leads are dropped on rebuild.
- Dropped exactly the 7 audit rows (old tx-301, 305, 325, 327, 328, 335, 343). Kept tx-7 (mixed-use with multifamily + parking garage, North Richland Hills) and tx-365 (1401 South Lamar Multifamily, Austin): both real apartment buildings.
- Rebuilt: Texas 628 -> 621 leads (DFW still 320; none of the 7 were in DFW). Lead ids are by rank, so Texas ids after the old positions shifted.
- Test: tooling/qa/fixes_tests/test_c1_junk_permits.py (fails on the old data).
- Checked: check-fixes.sh passes (36 tests, design 0 problems); lead-finder + permits tests 121 passed; chatbot/tests 35 passed.

## C2 Duplicates — done
- New shared pass `propertystack/skills/lead-finder/dedupe_leads.py`, applied in `build_data.py` on every rebuild: drops known existing complexes (Westdale Hills in Hurst and Euless), merges same-name same-city records when their base address/street/units match or one is only planned (a funding list) and the other further along, collapses separate building permits at one complex address (7900 Easthaven Blvd, 1415 Enclave Pky, 210 E 7th St), and labels the leftover same-name rows "Phase 1"/"Phase 2" in permit order.
- All 17 audit pairs resolved: 16 merged into one (keeping the further-along stage and the planned/funding units), Buena Vida Multifamily kept as two real phases (Ringgold St / E Tyler St). Westdale Hills dropped.
- Rebuilt: Texas 621 -> 597 leads; DFW 320 -> 311 (6 DFW duplicate pairs + Westdale's 2 rows + the Fort Worth Binyon-O'Keefe/Georgian Oaks same-address merge). Arizona 279 and New York 2 unchanged (their "Multi-Family Dwelling"/"Unnamed project" rows are told apart by address; C3 renames them).
- Updated the numbers C2 moved: check_answers.py DFW expectation 320 -> 311; test_b2_chat_counts.py now asserts DFW matches the site's built metro count instead of a hardcoded 320; test_a4's `> 900` sanity floor lowered to `> 850` (site total is now 878). Plan "How to try it" DFW 320 -> 311.
- Test: tooling/qa/fixes_tests/test_c2_duplicates.py (no same name+city pair unless phased; Westdale gone; audit pairs right; offline merge/phase rules).
- Checked: check-fixes.sh passes (40 tests, design 0 problems); check-lead-finder.sh + check-panel.sh clean; lead-finder + chatbot + score-leads tests 341 passed. Re-ran build_data.py and it reproduced the same files (no drift).

## C3 Units and names — done
- NY's 2 rows had units=0 (Buffalo's `units_added`=0, meaning "not recorded"); `build_data.py`'s new `_area_units` treats 0 like a blank, so both now show "?" instead of "0". No state shows a 0-unit building anywhere.
- AZ generic permit labels become "Apartments at <address>": 29 "Multi-Family Dwelling" (Scottsdale), 6 "Commercial Multi-Family" (Gilbert), 1 "Multifamily" (Phoenix) and 9 "APARTMENTS" (Scottsdale) — 45 rows now read "Apartments at 4251 N Marshall Wy" etc. ("multifamily" also added to dedupe_leads.GENERIC_NAMES).
- Units: recovered the one record whose count was already saved in its name ("8 UNIT MULTI-FAMILY APT." → 8 units); the other 79 AZ + 102 TX missing rows still have no unit data in any saved source (their permit layers have no unit field), so they stay "?" — never guessed.
- ⚠️ 9 "Unnamed project" rows (4 Mesa permits, 5 Maricopa County sales) have no name AND no address in any saved source, so "Apartments at <address>" cannot apply; they stay "Unnamed project". The 5 sold ones carry only LLC buyer/developer names (e.g. "WATERMARK AT PEORIA AZ LLC"), which I did not strip into a project name (no guessing).
- Rebuilt with build_data.py; deterministic (no drift). Lead counts unchanged: TX 597, AZ 279, NY 2.
- Test: tooling/qa/fixes_tests/test_c3_units_names.py (no units==0 anywhere; AZ generic labels gone; "Apartments at <address>" prefix matches the address; the "8 UNIT" recovery in both site JSON and chat CSV).
- Checked: check-fixes.sh passes (44 tests, design 0 problems); check-lead-finder.sh clean; chatbot/tests 35 passed; score-leads/tests 8 passed.

## C4 Source links a person can open — done
- `build_data.py` normalizes every source to `{label, url}`: the raw ArcGIS/Socrata query URLs (279 AZ, 7 TX, 2 NY) now open the dataset's public page (city permit search, open-data portal or ArcGIS item page) with a plain name like "City of Mesa building permits", "City of San Marcos building permits", "Maricopa County Assessor sales records". Plano CSV tags become plain names ("County property records", "Houston weekly permit list", "News coverage", "City permit record", "Building website"); links that are already human pages keep their URL with a label ("State project record", "City filing", "News").
- `site/index.html` and `site/property.html` render the label (no more `[tag]` brackets, no "source 1" for a named dataset). Every one of the new public pages was checked to return 200; no raw-API URL is left in any built lead.
- Rebuilt; only the `sources` fields changed (lead counts unchanged: TX 597, AZ 279, NY 2).
- Test: tooling/qa/fixes_tests/test_c4_sources.py.
- Checked: check-fixes.sh passes (52 tests, design 0 problems).

## C5 Arizona stage + Plano addresses — done
- A record whose own stage is "leasing" now counts as leasing even with no opening date: az-133 / az-134 (La Victoria Commons, 1020 Apache) read signalType "Leasing" and signal "Leasing now" instead of "Upcoming · opens not public yet", and their why no longer repeats "opens: not public yet".
- `_merge_included_areas` fills each Plano-Richardson row's street address from `site/data/properties.json` (the saved property data): 40 of the 42 rows now carry it in both `tx.json` and the chat's `tx/chat-leads.csv`. Two upcoming rows (Haggard Farm Townhomes, 360-unit project in downtown Plano) have no street address saved anywhere, so they stay blank rather than guess.
- Test: tooling/qa/fixes_tests/test_c5_stage_address.py.
- Checked: check-fixes.sh passes (52 tests, design 0 problems).
