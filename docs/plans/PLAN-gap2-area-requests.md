# Plan: Gap 2, honest front page + "request your area" (Software Sellers edition, 2026-09-18)

Decisions (Drew): no weekly list. Leads are added on demand. Front page says
"New leads added all the time" and "Don't see your area? Ask and we'll add it."
The Map page has a box where a visitor types the area they want; each request is logged and
posted to the Discord sign-ups channel (the same "New Crane Users" webhook used by
chatbot/signup_alerts.py, env SIGNUP_WEBHOOK_URL). Drew then fills those areas.

NOTE: the landing page and its server live in the nested `business/` git repo, which a gowork
copy of this repo cannot see. Do T1 and T2 directly in /home/drewp/main-projects/realpage/business,
commit there. Landing edits = change words only, keep the design.

Check: python3 -m pytest -q tooling/qa/fixes_tests/
Try: bash tooling/dev.sh
Open: http://localhost:8765/map.html

## Tasks
- [ ] T1 (business repo) Front page wording only: replace the "weekly list" promises with "New leads added all the time"; add one line "Don't see your area? Ask and we'll add it." linking to the app's map (#request-area). Keep "phone, website" (true via Find who to call, Gap 1).
- [ ] T2 (business repo) landing server.py: accept POST /api/signup with source=area-request (fields: area required, email optional; no role required); append to the signups CSV with metro=<area>, role="(area request)"; post a Discord message to SIGNUP_WEBHOOK_URL: "📍 Area request: <area> (email or 'no email')". Add a test; allow CORS from app.cranesignal.com and localhost:8765.
- [ ] T3 (this repo) Map page: small "Don't see your area?" box under the map (id request-area): one text field "City or county, state", optional email, button "Ask for it". Sends to the landing server (cranesignal.com/api/signup locally → http://localhost:8791). Shows "Got it — we'll add it" on success. Test that the box renders and posts the right fields.
- [ ] T4 Local end-to-end: submit "Tulsa, OK" on the local map; the row appears in the local signups CSV. (Discord post only fires where SIGNUP_WEBHOOK_URL is set — verify on live after Drew's OK.)

## How to try it
1. Front page no longer says "weekly list"; it says leads are added all the time.
2. On the Map page, type an area in "Don't see your area?" and click Ask for it: you see "Got it".
3. After going live, the request shows up in the Discord sign-ups channel.
