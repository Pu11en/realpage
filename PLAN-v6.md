# PropertyStack v6 — Chat panel inside the site

Written 2026-09-12. Drew's call: the chat lives **inside PropertyStack on every page** as a
slide-out panel, not a separate app. It knows all the data (same bot as before), helps with
sales tasks, and must not be buggy. Google sign-in and the $3/day cap are handled by **our
own proxy** (`chatbot/proxy.py`), not Open WebUI. Open WebUI stays parked (not deleted) until
the panel is proven, then goes in C3.

Run with: `Do the next unticked task in PLAN-v6.md, then tick it and stop.`
Check: `bash tooling/qa/check-panel.sh`
Try: `python3 chatbot/proxy.py` (with `FAKE_HERMES=1` for free fake answers) and `python3 -m http.server 8765 -d site`
Open: http://localhost:8765/master-table.html → Ask button (bottom-right)

## How to try it (30 seconds)
1. Open any dashboard page, click Ask: a panel slides out over the right side, the data stays visible.
2. Click "Sign in with Google", then ask "Which vendor runs the most buildings?": words stream in with source tags.
3. Reload the page: the panel remembers you and the conversation. Close it and open it on another page: same chat.

Rules: everything runs locally until Drew says it's good; no push before C1. 💲 = real bot calls.
Keep visuals minimal and on-theme (green ✦, site colours); Drew does the design pass himself later.
Every new button inside chat messages uses one delegated listener on the log, never per-button listeners.

Kept from PLAN-v5 (already on main): proxy per-user daily cap + rate limit (A5), Hermes internal
only, `/chat/stream` (streaming), branding assets in `chatbot/branding/`.

## Part P — Panel

- [ ] **P0 Self-contained check script.** `tooling/qa/check-panel.sh`: starts the proxy with
  `FAKE_HERMES=1` (a built-in fake Hermes that streams a canned cited answer with a table, no
  key needed) on port 8791 and the site on 8766, runs `tooling/qa/sweep.py http://localhost:8766`
  plus `tooling/qa/panel_test.py` (Playwright, created here as a stub that just loads a page),
  kills both servers, exits non-zero on any bug. Must finish in under 2 minutes.
  Check: `bash tooling/qa/check-panel.sh` passes on a clean checkout with no env vars set.
- [ ] **P1 Google sign-in in the proxy.** `GET /auth/config` (client id), `POST /auth/google`
  takes a Google ID token (Google Identity Services button), verifies it against Google's
  tokeninfo endpoint, sets a signed httpOnly cookie (email + expiry, HMAC with `CHAT_COOKIE_SECRET`),
  `GET /auth/me`, `POST /auth/logout`. `/chat` and `/chat/stream` require the cookie; usage cap
  keyed by email (reuse the A5 gateway code; admin email unlimited). `FAKE_GOOGLE=1` accepts
  the token `test:<email>` so tests never touch Google. CORS with credentials for localhost:8766/8765.
  Check: panel_test.py — unsigned `/chat` → 401; sign in with `test:a@b.com` → `/auth/me`
  returns the email; 41st message in a minute → 429.
- [ ] **P2 Panel shell on every page.** `site/js/chat-panel.js` + `site/css/chat-panel.css`,
  loaded by all 5 pages via app.js: the existing Ask button opens a right-side slide-out
  (420px desktop, full-screen on phone) with header (✦ Ask PropertyStack, close), message log,
  input form, and a "Sign in with Google" state when not signed in (real button when
  `/auth/config` has a client id, a test button when `FAKE_GOOGLE`). Remove the Open WebUI
  link and the B2 locked card from master-table.html; the Chat tab opens the panel too.
  Check: sweep clean at desktop/tablet/phone; panel_test.py opens the panel on all 5 pages,
  screenshots at 1440 and 390 in `/tmp/qa/`.
- [ ] **P3 Ask and stream.** Send via `/chat/stream` with a per-person server session id;
  words stream into the bubble; progress line ("Checking what data there is…") shows while
  the bot works; Stop button aborts; `[file.csv]` citations become chips; markdown tables
  render; errors show a Retry that re-asks the same question.
  Check: panel_test.py with FAKE_HERMES — streamed answer has chips and a table; Stop
  mid-stream leaves a "Stopped" note; a faked 500 shows Retry, Retry succeeds.
- [ ] **P4 Saved conversation per person.** Proxy keeps a small SQLite (`chats.db`, path from
  `CHAT_DB`) of messages per email + session; `GET /chats` (list), `GET /chats/<id>`,
  `POST /chats/new`. Panel restores the last chat on load and on every page, has "New chat"
  and a small "Past chats" list. Nothing in localStorage except the current chat id.
  Check: panel_test.py — ask, reload, message still there; open another page, same chat;
  New chat → empty; Past chats lists both; a second signed-in email sees none of them.
- [ ] **P5 Not buggy.** Hardening pass with an explicit list: double-submit while streaming,
  very long answers, 1000+ char question rejected with a message, cookie expired mid-chat
  (re-shows sign-in, keeps the draft), phone keyboard doesn't hide the input, panel state
  survives tab switch, no console errors on any page. Fix everything found and extend
  panel_test.py with a case per item.
  Check: `bash tooling/qa/check-panel.sh` green; zero console errors in the sweep.
- [ ] **P6 Local Google keys + docker.** `chatbot/docker-compose.local.yml` runs only
  Hermes + proxy (Open WebUI service removed from compose, volumes left alone);
  `chatbot/GOOGLE-SIGNIN.md` updated for the panel (JavaScript origin = site URL, no redirect
  URI needed); `.env.local.example` lists `GOOGLE_CLIENT_ID`, `CHAT_COOKIE_SECRET`.
  Check: 💲 with real keys in `chatbot/.env.local`, compose up, real Google sign-in works
  on http://localhost:8765 and a real cited answer streams.

## Part C — Ship

- [ ] **C1 Drew tries it on localhost.** Panel on every page, Google sign-in, ask, reload,
  phone size. After "good" and "Put it on GitHub?": deploy.
- [ ] **C2 Railway.** Proxy env (`GOOGLE_CLIENT_ID`, `CHAT_COOKIE_SECRET`, `CHAT_DB` on a
  volume); Google console origin = live site URL; drop the `propertystack-chat` service if
  it was created.
  Check: live site → Ask → Google sign-in → answer streams; redeploy → chats still there.
- [ ] **C3 Clean up.** Remove Open WebUI from PLAN-v5 leftovers (compose, branding no longer
  used, `CHAT_APP_URL` in app.js, gateway `/v1/*` routes in proxy if unused); update
  `chatbot/README.md`; archive PLAN-v5.
  Check: sweep clean; README describes the panel setup.
