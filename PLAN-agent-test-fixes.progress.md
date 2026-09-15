# Progress log

## T1 Chat loads every time — done
Raised the chat panel's load timeout from 8s to 30s (`site/js/chat-panel.js`), changed the loading
message to "Waking up the chat…", and added one automatic reload of the iframe before showing the
manual "Couldn't load the chat." error with its Try again button. Added
`tooling/qa/fixes_tests/test_t1_chat_load_timeout.py` (checks the 30s default, the wording, and that
one auto-retry happens before the error is shown). Checked with `bash tooling/qa/check-fixes.sh`
(60 tests pass, design check 0 problems). Commit: see git log.

## T2 One chat header bar — done
Hardened `site/js/chat-panel.js` against double-init: the whole script now guards itself with
`window.__chatPanelLoaded` so it only runs once even if the `<script>` tag is ever duplicated;
`wireTriggers()` now marks each Ask/Chat button (`dataset.chatWired`) so a repeat `initChatPanel()`
call can't attach a second click listener (which would open-then-immediately-close the panel and
briefly show a second header while the first was torn down); and `buildPanel()` now defensively
drops any stray extra `#chat-panel` nodes instead of building yet another one. Added
`tooling/qa/fixes_tests/test_t2_chat_panel_single_header.py` (3 tests, checks all three guards are
present in the source). Checked with `bash tooling/qa/check-fixes.sh` (63 tests pass, design check
0 problems). Commit: see git log.

## T3 Sign-out button — done
Added a "Sign out" link to the shared sidebar shell (`site/js/app.js`'s `renderShell()`), next
to Privacy, hidden by default. `site/js/chat-panel.js` now shows/hides it using the same
sign-in check it already does for the chat panel's sign-in card (`checkAuth()`): hidden locally
(chat app auth off) and hidden until someone is actually signed in live. Clicking it posts to
the chat app's `/api/v1/auths/signout`, clears the panel's local session flag, and sends the
browser to the chat app's `/auth` sign-in page. Added
`tooling/qa/fixes_tests/test_t3_sign_out.py` (5 tests: link present on all 5 app pages, hidden
by default, calls the right sign-out endpoint and lands on `/auth`, only shown once signed in,
wiring doesn't double-bind). Checked with `bash tooling/qa/check-fixes.sh` (68 tests pass,
design check 0 problems). Commit: see git log.

## T4 Real "page not found" — done
Added `site/404.html` (a CraneSignal-styled not-found page with a link home) and reworked
`site/Caddyfile` so unknown addresses get a real 404 instead of the chat app's leads page:
gave the chat app's own routes (`/auth`, `/oauth`, `/api/*`, `/ws`, `/_app/*`, `/static/*`,
`/c/*`, and `/` only when it's the chat panel's iframe) an explicit matcher, and everything
else now hits `error * 404` then `handle_errors` serves `404.html` with a real 404 status.
The sign-in gate is untouched — signed-out app pages still 302 to `/auth`, the iframe home
and the chat API still reach the chat app. Added
`tooling/qa/fixes_tests/test_t4_not_found.py` (4 tests, reuses the E1 test's real-Caddy
fixture): unknown page is a real 404 with CraneSignal wording, the sign-in gate still works,
chat app routes still reach the chat app, and the 404.html file exists. Verified manually
with the cached Caddy binary before writing the test (curl showed `HTTP/1.1 404 Not Found`
with the CraneSignal page body, `/auth` still 200, `/api/v1/auths/` still 401, signed-in
`/index.html` still 200). Checked with `bash tooling/qa/check-fixes.sh` (72 tests pass,
design check 0 problems). Commit: see git log.

## T5 Logo goes home — done
Made the CraneSignal wordmark in the shared shell (`site/js/app.js`'s `renderShell()`) an
`<a href="index.html">` instead of a plain `<div>`, and added `text-decoration: none` to
`.sidebar .wordmark` in `site/css/styles.css` so it still looks like a wordmark, not a
typical link. Added `tooling/qa/fixes_tests/test_t5_logo_links_home.py` (2 tests: the
wordmark markup is an anchor to index.html, and every app page still calls renderShell()).
Checked with `bash tooling/qa/check-fixes.sh` (74 tests pass, design check 0 problems).
Commit: see git log.

## T6 Saved deep dive comes back — done
`chat-panel.js`'s `deepDive()` used to always reopen the panel and re-fill the same unsent
question, so a second click on the same building looked like nothing was remembered.
It now takes the building's id as well as the prompt text, remembers the last deep dive
sent per building in `localStorage` (`propertystack.deepDive.<id>` -> `{text, ts}`), and
on a repeat click with the same id and the same question shows a
"Saved deep dive from <date>. Press ↻ to redo it." notice in place of the chat frame,
with a Redo button that actually resends the question and refreshes the saved timestamp.
A genuinely new question (different prompt text, e.g. the building's stage changed) still
goes straight through as before. Updated the three deep-dive call sites
(`site/index.html`, `site/property.html` x2) to pass the lead/property id. Added
`tooling/qa/fixes_tests/test_t6_saved_deep_dive.py` (4 tests: the per-building memory
functions exist, the saved-notice path in `deepDive()` doesn't fall through to
re-sending the question, the redo button is wired, and all three call sites pass an id).
Checked with `bash tooling/qa/check-fixes.sh` (78 tests pass, design check 0 problems).
Commit: see git log.

## T7 No broken "Sources: )" line — done
Found it: `chatbot/linkfix.py`'s `_fix_line()` strips out a citation link whose URL was never
returned by a tool (unseen/bad), and when that leaves a "Sources:" line with nothing real on
it, a separate check is supposed to drop the whole line. That check only recognized whitespace,
`*`, `·`, `:`, `,`, `;` and the word "Sources" as "nothing" — it didn't know about stray
parentheses. So a line like `Sources: [Bad record](http://fake)` lost its link but kept the
`()` wrapper around where the link used to sit, leaving exactly the broken `Sources: )` (or
`Sources: ()`) the live test saw. Fixed by adding `()` to that check's "nothing to cite"
character class, so the line is dropped entirely once every citation on it is gone. Added
`tooling/qa/fixes_tests/test_t7_sources_line.py` (3 tests: a dropped citation no longer
leaves dangling parens, an already-empty `Sources: ()` line is dropped, and a Sources line
with a real seen citation still survives with its link). Also added a "broken Sources line"
check to `tooling/qa/check_answers.py`'s `problems()` (not run — it needs the live bot) so a
future live answer with a dangling `Sources: )`/`()` fails that check too; "Which buildings
sold recently?" (the question that showed the bug) is already in its question list. Checked
with `bash tooling/qa/check-fixes.sh` (81 tests pass, design check 0 problems). Commit: see
git log.

## T8 Duplicate building — done
Found it: `dedupe_leads.py` only compared candidate duplicates within the same
(name, city) group, but "Torrington Wilmer" appeared once labeled city
"Dallas" and once as the annexed suburb "Wilmer" (slightly different address
spelling, same 300 units) -- so the two records never got compared and both
survived. Changed the grouping key to name alone, and tightened
`same_project()`'s loose "one planned, one further along" fallback to require
a matching city too (real address/street/unit evidence is still enough to
merge two same-named records across differing city labels, so unrelated
projects that happen to share a name in different cities still stay separate).
Added `tooling/qa/fixes_tests/test_t8_duplicate_building.py` (2 tests: same
name + different city label + matching address/units merges to one row;
same name + different city + nothing else in common stays two rows). Rebuilt
site data with `python3 site/data/build_data.py` (TX leads count dropped
597 -> 593, matching the duplicates that merged). Checked with
`bash tooling/qa/check-fixes.sh` (83 tests pass, design check 0 problems).
Commit: see git log.

## T9 Arizona names cleaned — done
`site/data/build_data.py`'s `_nice_name()` only recognized a fixed set of
generic permit-feed labels ("apartments", "building permit", ...), so a raw
plat/lot label like "South Pier Lot 6" (developer City of Tempe, Tempe AZ)
kept showing as the project name instead of becoming "Apartments at <address>".
Added `_LOT_LABEL_RE` (matches a plat name ending in "Lot/Parcel/Tract <number>",
case-insensitive) and widened `_nice_name()` to also clean names matching it.
Added `tooling/qa/fixes_tests/test_t9_arizona_names.py` (4 tests: the Tempe
example becomes "Apartments at 1314 E Vista Del Lago Dr", Parcel/Tract labels
are also cleaned, a real project name is left alone, and a lot label with no
address falls back to "Unnamed project" like the existing generic-name rule).
Rebuilt site data with `python3 site/data/build_data.py`; besides fixing the
Tempe row, it also caught a same-shaped Texas row ("ASTORIA ADDITION Block 2
Lot 34R" -> "Apartments at 3741 Stalcup Rd, Fort Worth"). Checked with
`bash tooling/qa/check-fixes.sh` (87 tests pass, design check 0 problems).
Commit: b403a97.

## T10 Table headers sort — done
The Early Leads table (`site/index.html`) already had a Sort dropdown
(score/size/newest) but the column headers (Score, Property, City, Units,
Signal, Software) just sat there looking clickable. Added `data-sort-key`
attributes to those headers, a click handler that sorts by that column
(numeric for Score/Units, alphabetical for the rest, missing software sorts
last) and toggles ascending/descending on a repeat click, with a small
▲/▼ arrow (CSS in `site/css/styles.css`) showing which column and
direction is active. Clicking the Score or Units header also flips the
existing Sort dropdown to match ("Sort: score" / "Sort: size"), and picking
anything from the dropdown clears the header-driven sort so the two never
fight over which one wins. Added
`tooling/qa/fixes_tests/test_t10_table_headers_sort.py` (5 tests: all six
sortable headers are declared, a repeat click reverses direction, a clicked
header takes priority over the dropdown's own sort branches, Score/Units
clicks sync the dropdown, and picking the dropdown clears the header sort).
Checked with `bash tooling/qa/check-fixes.sh` (92 tests pass, design check
0 problems on 7 pages) and a Node syntax check of the page's inline script.
Commit: see git log.

## T11 Map markers do what they say — done
Reproduced it first with a real Playwright click on the Arizona marker: the
click missed and landed on the Arizona state shape instead (it "intercepts
pointer events"), which only shows the blue-state hover tooltip -- exactly
the "only show a popup" the live testers saw. Cause: each marker's `<g>` in
`site/js/map.js` had no geometry of its own; its amber dot and its white
label pill are separate children with a visible gap between them, and a
click landing in that gap (which still looks like part of the marker) falls
through to the map state underneath instead of the marker's own click
handler. Fixed by adding an invisible `hit-area` rect as the first child of
each marker `<g>`, sized in `layoutLabels()` to cover both the dot and the
label pill (and the gap between them) so any click on the visible marker
navigates to that state's leads table. Re-ran the same live click and it now
lands on `index.html?area=az` as intended, so the existing "click opens the
table" wording stays accurate -- no copy change needed. Added
`tooling/qa/fixes_tests/test_t11_map_marker_click.py` (2 source checks for
the hit-area element and its sizing, plus a real headless-browser test that
clicks a marker and asserts the page navigates). Checked with
`bash tooling/qa/check-fixes.sh` (95 tests pass, design check 0 problems on
7 pages). Commit: see git log.

## T12 Fence permit gone — done
The Houston "MULTI-FAMILY NEW PERIMETER FENCE, FENCE" permit matched the
apartment-keyword regex (it literally contains "Multi-Family") before the
existing renovation-type filter ever ran, so it slipped through as a lead.
Added "fence"/"fences" to the shared `JUNK_PERMIT_RE` in
`propertystack/skills/lead-finder/junk_permits.py`, which both the live
permit fetch (`find_upcoming.py`) and the site rebuild
(`site/data/build_data.py`) already run against every lead's name — so this
one change drops fence permits from both new fetches and the existing saved
data. Ran `python3 site/data/build_data.py` to rebuild; the Houston fence
row is gone from `site/data/areas/tx.json` and `map-markers.json` counts
dropped accordingly. Added
`tooling/qa/fixes_tests/test_t12_fence_permit.py` (the real Houston permit
text is junk, other fence wording is junk, a real apartment permit is not,
and a street literally named "Fence Rd" is not caught by the false-positive
guard). Checked with `bash tooling/qa/check-fixes.sh` (99 tests pass, 0
design problems on 7 pages). Commit: see git log.

## T13 No duplicate source links — done
`sourceItems()` in `site/property.html` deduped saved sources by a
`label|url` key, so the same URL (e.g. a `tdlr.texas.gov` state project
record) showed twice when it appeared once as `p.website` (labeled
"Website" by the page's own `sourceLabel()`, which doesn't know about
tdlr.texas.gov) and once as a saved `{label: "State project record", url}`
source. Changed the dedup key to the URL alone when a source has one
(falling back to the label only for sources with no URL), and kept
`p.sources` ahead of `p.website` in the list passed to `sourceItems()` so
the saved, correctly-labeled entry wins and the plain website duplicate is
dropped. Added `tooling/qa/fixes_tests/test_t13_duplicate_source_links.py`
(4 tests: the old label-pair dedup key is gone and the new URL-based one is
in place, the website field still feeds the same dedup pass, a same-URL
pair under two labels collapses to one entry keeping the more specific
label, and two genuinely different URLs both still show). Checked with
`bash tooling/qa/check-fixes.sh` (103 tests pass, design check 0 problems
on 7 pages). Commit: see git log.

## T14 Shorter leads list — done
The Early Leads table (`site/index.html`) rendered every filtered/sorted row
at once (597, now 593, Texas rows). Added a `PAGE_SIZE = 50` /
`visibleCount` cap: `renderRows()` still computes and sorts the full
filtered `rows` list first (so the stat cards and rank numbers stay correct),
then slices to `pageRows = rows.slice(0, visibleCount)` only for what goes
into the table body. A "Show more (50 of 593)" button below the table adds
another 50 each click and hides itself once every row is shown.
`visibleCount` resets back to 50 whenever a filter, the sort dropdown, a
header-sort click, or a region/metro pick changes what's being shown, so a
new search always starts back at page one. Added
`tooling/qa/fixes_tests/test_t14_show_more_leads.py` (5 tests: page size is
50, the button exists and is wired to grow `visibleCount`, the table body
renders the sliced `pageRows` not the full list, stats run on the full
`rows` before slicing, and paging resets on filter/sort changes). Checked
with `bash tooling/qa/check-fixes.sh` (108 tests pass, design check 0
problems on 7 pages).
