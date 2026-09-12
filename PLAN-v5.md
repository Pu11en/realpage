# PropertyStack v5 — Chat via Open WebUI, locked behind Google sign-in

Written 2026-09-11. Drew's call: use a proven open-source chat app instead of closing
holes one by one. **Open WebUI** is the frontend Hermes' own code and docs are built for.
Dashboards stay open to everyone; the chat needs a one-click Google sign-in; signed-in
people get unlimited chat with their own saved history. The chat is reached from a
"Chat" tab in the PropertyStack sidebar and the Ask button on every page (full-screen,
branded to match). Under the Hood gets its own plan in another session.

Run with: `Do the next unticked task in PLAN-v5.md, then tick it and stop.`
Check: `python3 tooling/qa/sweep.py http://localhost:8765` (plus the task's own Check line)
Try: `docker compose -f chatbot/docker-compose.local.yml --env-file chatbot/.env.local -p ps-chat up -d --build && python3 -m http.server 8765 -d site`
Open: http://localhost:8765 (dashboards) → Chat tab → http://localhost:3000 (chat, Google sign-in)

## How to try it (30 seconds)
1. Open http://localhost:8765, click the green ✦ Chat tab (or the Ask button bottom-right).
2. Click "Continue with Google", sign in, ask: "Which vendor runs the most buildings?" — a cited answer should stream in.
3. Reload the chat page: the conversation is still there in the left list.

Status 2026-09-12: A1, A2, B1 done locally. Next unticked task: A3.

Supersedes PLAN-v4 Parts A5–A6, B1, B3–B6, Z1–Z2. Keeps: A1 (server chats), A3 (streaming
proxy) — still used by the site's quick "Ask" panel until step C3 removes it.
Rules: everything runs on Drew's computer (Docker) until he says it's good; no push, no
Railway change before C1. 💲 = real bot calls (cents).

## Part A — Run it locally

- [x] **A1 Open WebUI talks to the local bot.** _(Done 2026-09-11: `docker compose -f chatbot/docker-compose.local.yml -p ps-chat up -d --build`; http://localhost:3000, admin = kidquick360@gmail.com / local-trial-pass. Headless: cited streamed answer, same-chat memory, auto chat title, follow-up suggestions, copy/regenerate present. Noted for A4: warm-up lines "I'll check the schema first." show in the answer; no progress line seen.)_ `chatbot/docker-compose.local.yml`: the
  existing `ps-chatbot` image + `ghcr.io/open-webui/open-webui` pointed at Hermes'
  OpenAI-style API (`/v1`, bearer = `API_SERVER_KEY`). Hermes must listen on the Docker
  network, not only 127.0.0.1 (env `API_SERVER_HOST`). Sign-up off except the first admin.
  Check: 💲 open http://localhost:3000, log in as admin, ask "Which vendor runs the most
  buildings?" → cited answer streams; "what did I ask?" in the same chat → remembers.
- [x] **A2 Google sign-in.** _(Done 2026-09-12 locally: keys in git-ignored `chatbot/.env.local`; login page shows only "Continue with Google" (verified headless, redirects to accounts.google.com); password login/sign-up off in Open WebUI's DB (see GOOGLE-SIGNIN.md note). Still to confirm by Drew: real Google login with his account and a second account seeing an empty chat list.)_ Create the Google OAuth client (Drew does the Google console
  part with a written 6-step guide in `chatbot/GOOGLE-SIGNIN.md`); set Open WebUI's Google
  OAuth vars, OAuth sign-up on, password sign-up off, new users get the "user" role.
  Check: a second Google account can sign in with one click and sees an empty chat list;
  it cannot see the admin's chats.
- [ ] **A3 Brand it PropertyStack.** Name, logo/favicon, dark theme in PropertyStack's
  colours (custom CSS), only the `hermes-agent` model shown, default model set, welcome
  text with 3 example questions, no model picker/settings clutter for users.
  Check: screenshots at 1280 and 390 look like PropertyStack; a user sees no model picker.
- [ ] **A4 Agent bits show properly.** Confirm tool progress ("Checking what data there
  is…") shows in Open WebUI, Stop works and interrupts Hermes (logs), citations render.
  Also make sure `[3-software.csv]` citations don't get eaten by markdown — if they do,
  adjust the bot's prompt (`hermes-profile/SOUL.md`) to write them as `\[file\]` or code.
  Check: 💲 one question with a lookup shows a progress line, Stop mid-answer stops it,
  citation chips visible.
- [ ] **A5 Limits & safety.** Per-user rate limit in Open WebUI admin (or leave unlimited
  per Drew's wish, but set a daily cap so a bot can't run up the bill), tools stay
  read-only, Hermes API not reachable from the internet (only from Open WebUI).
  Check: the Hermes port is not published; a user with 40 messages in a minute is throttled.

## Part B — Link it into PropertyStack

- [x] **B1 "Chat" tab + Ask button everywhere.** _(Done 2026-09-12: green ✦ Chat tab in the sidebar + floating Ask button on all 5 pages (Master Table keeps its own quick panel), opening localhost:3000 locally / Railway live. The "← PropertyStack" link inside the chat is part of A3.)_ Add a `Chat` tab to the sidebar
  (`site/js/app.js` NAV_TABS) and a floating Ask button on every page; both open the chat
  URL (env-style constant: `http://localhost:3000` locally, Railway URL live). The
  chat's own top bar gets a "← PropertyStack" link back.
  Check: sweep shows the tab and button on all 5 pages; clicking opens the chat.
- [ ] **B2 Locked-chat message.** On the Master Table, the old side panel is replaced by a
  small card: "Ask PropertyStack — sign in with Google to chat" + 3 example questions;
  clicking any goes to the chat with the question prefilled (`?q=`), if Open WebUI
  supports it, else just to the chat.
  Check: screenshots at 1280 and 390; click → chat page.

## Part C — Ship

- [ ] **C1 Drew tries it on localhost.** Sign in with Google, chat, reload, phone size.
  After "good" and "Put it on GitHub?": deploy.
- [ ] **C2 Railway.** New `propertystack-chat` service (Open WebUI) with a volume; chatbot
  service exposes Hermes only on Railway's private network; Google OAuth redirect URL
  updated to the live domain; site's chat URL switched to live.
  Check: live site → Chat tab → Google sign-in → answer streams; redeploy → chats still there.
- [ ] **C3 Clean up.** Delete `site/chat-trial.html`, the old side-panel JS in
  `master-table.html`, and `/chat/stream` if nothing uses it; update `chatbot/README.md`.
  Check: sweep clean; README describes the Open WebUI setup.

## Later (separate plans)
- Under the Hood overhaul — own session and plan.
- Memory of who the visitor is (PLAN-v4 A2 trial) — only if Drew still wants it after C2.
