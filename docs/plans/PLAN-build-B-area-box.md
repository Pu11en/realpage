# Build B: Map page "request your area" box (Software Sellers edition, 2026-09-18)

From PLAN-gap2-area-requests.md (read it for the decisions). Only site/map.html (+ its own small JS/CSS and tests).
Do NOT touch site/index.html, site/js/app.js, site/js/chat-panel.js (Build A) or business/ (separate repo).
The landing server endpoint (POST /api/signup with source=area-request, fields area + optional email) is built separately;
locally it runs at http://localhost:8791, live at https://cranesignal.com. Test the form with a mocked fetch.

Check: python3 -m pytest -q tooling/qa/fixes_tests/
Try: bash tooling/dev.sh
Open: http://localhost:8765/map.html

## Tasks
- [ ] T3 (this repo) Map page: small "Don't see your area?" box under the map (id request-area): one text field "City or county, state", optional email, button "Ask for it". Sends to the landing server (cranesignal.com/api/signup locally → http://localhost:8791). Shows "Got it — we'll add it" on success. Test that the box renders and posts the right fields.
- [ ] T4 Local end-to-end: submit "Tulsa, OK" on the local map; the row appears in the local signups CSV. (Discord post only fires where SIGNUP_WEBHOOK_URL is set — verify on live after Drew's OK.)

## How to try it
1. The Map page shows "Don't see your area?" under the map.
2. Type "Tulsa, OK" and click Ask for it: it says "Got it".
3. The request lands in the sign-ups list.
