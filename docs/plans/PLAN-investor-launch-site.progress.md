# Progress: investor launch site (2026-09-18)

## T1 ✅
Check script already passes with 0 violations. Only 1 RealPage reference in business/ (in vendor list, which is allowed). Ticked the box.

## T2 ✅
Created landing page at business/marketing/landing/index.html with:
- Investor headline: "See which apartment buildings just sold, who bought them, and what's being built"
- "Start free" CTA button linking to "/" (root will eventually redirect to /map.html when login gate is removed in T3)
- Example lead card (Legacy Arapaho building in Richardson, TX)
- Design matching screenshot: blueprint blue background, grid pattern, white cards, amber buttons
- Responsive for mobile
- Copy saved to site/landing.html for dev server
- Test suite created in business/tools/test_landing.py (validates headline, CTAs, no RealPage text, branding)
- All tests pass; check-no-realpage-target.sh still exits 0
- Commit: 94e17bd

## T3 ✅
Removed the sign-in check (forward_auth) from site/Caddyfile, so Map, Early Leads, building pages, Under the Hood, landing.html and their data load signed out. "/" still opens the Map, so the landing page's "Start free" link lands there with no login.
- Tests: test_e1_signin.py now runs the real Caddyfile and checks every page returns 200 signed out with content and no RealPage text; test_t4_not_found.py updated. 203 tests pass; check-no-realpage-target.sh exits 0.
- Commit: 6bb3343
- Open: the chat still asks for an account inside its panel (T4 reshapes that). Nothing pushed; the live site keeps its gate until this is deployed.

## T4 ✅
Chat panel now opens by default on every site page; the X closes it and it stays closed for the rest of the visit. Signed out it shows a big "Make a free account" button and a small "Already have one? Sign in" link (both use the existing sign-in popup), shown right away instead of after the chat app wakes up; signed in it shows the existing chat.
- Phones (under 900px wide): the panel covers the whole screen there, so it stays closed until the visitor taps Chat. Otherwise Reddit phone visitors would see only the account prompt, not the data.
- Tests: new test_l4_chat_open_by_default.py; 207 tests pass; check-no-realpage-target.sh exits 0. Browser check: open on Map, Early Leads, Under the Hood with the right wording; stays closed after X; closed by default at phone width.
- Commit: 5fc551d
- Open: not checked against the real chat app signed in (local dev has login off). Nothing pushed.

## T5 ✅
Hidden New York (2 leads) from the area picker and map using a flag in data/areas/index.json (data not deleted, just hidden).
- Added hidden: true to NY entry in areas/index.json
- Added visibleAreas(areas) helper function in app.js that filters out hidden areas
- Updated renderAreaButtons() to use visibleAreas, so state selector on Early Leads page only shows TX and AZ
- Updated findLead() to search only visible areas
- Updated index.html loadAreas() to return visibleAreas(m.areas)
- Updated map.js to load areas/index.json and filter out markers for hidden areas, so NY won't appear as a clickable marker on the map
- Tests: all 206 existing tests pass; check-no-realpage-target.sh exits 0
- Verified: NY is marked hidden; visible areas filter works; map markers correctly filtered
- Commit: 5609ea3
- Done: NY absent from area picker and map markers
