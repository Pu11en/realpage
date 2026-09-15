# CraneSignal: fix everything the Sep 15 audit found

Written 2026-09-15 from the audit handoff (`handoffs/2026-09-15-audit-fix-handoff.md`, read it first).
**Starts only when Drew says "go work".** Localhost only: never push, never deploy, never change
Railway settings. The live chat fix (CORS) is done by the orchestrating session with Drew's OK, not here.

Ground rules for every task:
- User-facing name is **CraneSignal**. Never show "PropertyStack" or "Hermes" to users; internal code,
  folders, table names and the model id `hermes-agent` stay as they are.
- The app now uses the landing look (white, navy, blue, amber; Plus Jakarta Sans headings, Inter body).
  Any new UI uses the existing classes in `site/css/styles.css`; the design check must keep passing.
- Every fix adds one small offline test in `tooling/qa/fixes_tests/test_<task>.py` (no network, no paid
  AI calls) that fails without the fix. Never weaken an existing test to make the Check pass.
- Data fixes happen upstream (lead finder / build scripts), then rebuild with
  `python3 site/data/build_data.py` and the chat's `chat-leads.csv`, and commit the rebuilt files.
- **Never touch anything AI Visibility** (`site/ai-visibility.html`, `site/data/*ai*`, `09-ai-visibility/`, its build scripts or plans; Drew 2026-09-15: another session owns it), nor `tooling/street-talk/`. At merge, local-test's AI Visibility files win.
- `check_answers.py` questions may be added but never run (they cost money); Drew runs them.
- Tech choices are yours. Anything only Drew can do goes in the final report, not a question.

AI for the build: same as the planning session (`"harness": "same"`).

Run with: `Do the next unticked task in PLAN-audit-fixes.md, then tick it and stop.`
Check: `bash tooling/qa/check-fixes.sh`
Try: `bash tooling/dev.sh` (site plus chat; or `python3 -m http.server 8765 -d site` for the site only)
Open: http://localhost:8765/index.html

## How to try it (30 seconds)
1. Open Early Leads on your phone: it fits the screen, pick a Region and the number boxes change.
2. Click any Texas or Arizona building: it opens a detail page; search "zzzz" shows "Nothing found".
3. Ask the chat "How many leads in Dallas–Fort Worth?": it says 311 and names CraneSignal as the source.

## Tasks

### Part A: site pages
- [x] **A1 Phones.** Add `<meta name="viewport" content="width=device-width, initial-scale=1">` to
  `index.html`, `under-the-hood.html`, `property.html`, `ai-visibility.html` (that one line only).
  In `tooling/qa/sweep.py` and `quick-check.py` phone runs use `is_mobile=True, has_touch=True`; fix
  any page that now overflows. Test: every `site/*.html` has the viewport tag.
- [x] **A2 Early Leads: stat boxes follow the Region pick, and "Nothing found".** In `index.html`
  `renderPage`, the number boxes use the rows currently shown (state + region + city + search). An
  empty result shows one row "Nothing found. Clear the search or pick another region." with a
  clear-search button.
- [x] **A3 Chat panel no longer hides Software and Why.** With the panel open on desktop the table
  gets narrower (hide low-value columns first, or let it scroll sideways inside its own box), never
  covering Software/Why. Also fix both "Early Leads" and "Chat" showing as selected in the menu.
- [x] **A4 Every building opens a detail page.** `property.html` also works from a lead row with no
  `propertyId` (use the lead's own id): name, city, stage, units, software, why, sources, Deep dive
  button. All Texas/Arizona/New York rows become clickable. Test: every lead id in the built data
  opens without "not found".
- [x] **A5 Deep dive says the real stage.** `deepDivePrompt` in `site/js/chat-panel.js` passes the
  lead's real stage (planned / under construction / leasing) instead of calling every "Upcoming" row
  planned.
- [x] **A6 Menu footer honest.** "Last updated" comes from the built data's date, not the hard-coded
  "Sep 10, 2026" in `site/js/app.js`. The "View as" dropdown gets a short plain label and a tooltip
  ("Highlight the buildings a Yardi / Entrata / AppFolio seller would win"); "Neutral" becomes "Everyone".
- [x] **A7 Under the Hood cleaned for users.** Hide the raw bits: "area: plano-richardson",
  "propertystack/runs/*.json", the error row, the PLACEHOLDER box; make its lead count match the
  site. No other redesign (a rebuild is planned separately).
- [x] **A8 Privacy page.** Link it from the app menu footer and the landing footer
  (`business/marketing/landing/index.html`, its own git repo: commit there too). Mention email
  sign-up next to Google sign-in, what we store (email, chat history, sign-ups) and a contact line
  using the address already on the landing page (if none, write `CONTACT_EMAIL_TBD` and flag it).

- [x] **A9 Map labels easier to read.** State labels ("TX · 628 leads") no longer sit right on dark
  blue states: put them in a small white pill with navy text, or offset them; keep them readable on phone.

### Part B: the chat
- [x] **B1 No more "PropertyStack" in chat sources.** Rename the label to "CraneSignal lead ranking"
  in `chatbot/hermes-profile/plugins/propertystack/__init__.py`, the `query-propertystack` SKILL.md
  table and anywhere else in `chatbot/` a user could see it (SOUL.md, proxy.py messages, the
  sign-in popup title "CraneSignal (Open WebUI)" → "CraneSignal"). Test: grep of user-facing
  strings finds no "PropertyStack", "Hermes" or "Open WebUI".
- [x] **B2 Chat counts match the site.** Put Plano-Richardson's 42 leads into the Texas/DFW numbers
  the chat uses (data level: include them in Texas `chat-leads.csv` or make the skill count both
  tables), so Texas = site total and DFW = 320. Add a check_answers question "How many leads in
  Dallas–Fort Worth?" = 320 (don't run it). Offline test: the chat's SQL for DFW returns 320.
- [x] **B3 Vendor answers say their scope.** "Which vendor runs the most buildings?" must say which
  area the software data covers (today only Plano and Richardson). Fix in SOUL.md or the skill.
- [x] **B4 Saved deep dives are free.** In `chatbot/proxy.py` `gateway_chat`, serve a saved
  deep-dive replay before `_free_take`, so replays don't use one of the 3 weekly deep dives.

### Part C: lead data (merge with Texas cleanup; rebuild after each)
- [x] **C1 Junk permits out.** Lead finder filter drops pool, carport, stair/remodel, repair, roof and
  garage-apartment permits (tx-301, 305, 325, 327, 328, 335, 343). Look at tx-7 and tx-365 and keep
  them only if they are real apartment buildings. Test with those ids.
- [x] **C2 Duplicates.** Westdale Hills Apts (Hurst + Euless, 2,141 units, an old complex) is one
  existing building: drop it. For the 17 same-city name pairs, merge true duplicates (same
  address or same permit), keep real phases and label them "Phase 1 / Phase 2". Test: no two rows
  with same name + city unless labeled as phases.
- [x] **C3 Units and names.** New York's 0 units become "?". Arizona "Multi-Family Dwelling",
  "Commercial Multi-Family" and "Unnamed project" rows get a readable name from their address
  ("Apartments at 1234 E Main St"). Try to fill missing units (124 TX, 80 AZ) from data already
  saved in the source records; leave "?" when there's nothing.
- [ ] **C4 Source links a person can open.** Raw ArcGIS/Socrata API query URLs (279 AZ, 2 NY, 7 TX)
  become the dataset's public page (or the city's permit lookup page) with a plain label like
  "City of Mesa building permits". Bracket labels like "[houston-weekly-xlsx]" and "[county record]"
  become plain names ("Houston weekly permit list", "County property records").
- [ ] **C5 Arizona stage contradiction + Plano addresses.** Rows whose stage is leasing never show
  "Upcoming · opens not public yet" (e.g. az-1 La Victoria Commons). The 42 Plano-Richardson rows
  get their street address from the saved property data so the chat can give addresses.

### Part D: wrap up
- [ ] **E1 Sign-in for the whole app (Drew 2026-09-15).** Online, every app page (Early Leads, Map, property
  pages, AI Visibility, Under the Hood, data files) needs the same sign-in the chat uses (Google or email);
  only `privacy.html`, fonts, favicons and the sign-in pages themselves stay public. In `site/Caddyfile` use
  `forward_auth` to the chat app's current-user endpoint (Open WebUI reads the `token` cookie); not signed
  in = redirect to `/auth?redirect=<page>`, and after sign-in they land back on that page. Locally
  (`tooling/dev.sh`, no sign-in) nothing changes and the Check keeps working. Test offline with a fake
  upstream: signed-out request to `/index.html` and `/data/leads.json` redirects, `/privacy.html` doesn't,
  a request with a valid cookie gets the page. Don't deploy; note in the report that Drew must test the
  live sign-in after the push.

- [ ] **D1 Final check + report.** Run the Check, `bash tooling/qa/check-panel.sh` and
  `bash tooling/qa/check-lead-finder.sh`. Write `docs/audit-fixes-REPORT.md` in plain words: what
  changed per fix, the new lead counts per state, and the list of things only Drew can do:
  the live chat CORS setting, renaming the cal.com link `propertystack-intro` (then update
  `BOOK_CALL_URL` in proxy.py and the landing page), sign-up alerts, the contact email, and running
  `check_answers.sh`.
