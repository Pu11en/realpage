# PropertyStack v6 — Open WebUI inside a chat panel on every page

Written 2026-09-12. Drew's call: the chat lives **inside PropertyStack on every page** as a
slide-out panel beside the data, so you can switch dashboard tabs while the chat stays open.
Chosen for fewest bugs: the panel's insides are **Open WebUI** (the proven chat app from
PLAN-v5, already branded, Google-only login, $3/day cap via our proxy) shown in a frame,
not a hand-built chat. Everything from PLAN-v5 A1–A5 stays as is.

Run with: `Do the next unticked task in PLAN-v6.md, then tick it and stop.`
Check: `bash tooling/qa/check-panel.sh`
Try: `docker compose -f chatbot/docker-compose.local.yml --env-file chatbot/.env.local -p ps-chat up -d --build && python3 -m http.server 8765 -d site`
Open: http://localhost:8765/master-table.html → Ask button (bottom-right)

## How to try it (30 seconds)
1. Open any dashboard page, click Ask: a panel slides out on the right, the data stays visible.
2. Sign in with Google (opens a small Google window, then the panel shows the chat). Ask
   "Which vendor runs the most buildings?": a cited answer streams in.
3. Click another tab (Software share, Under the Hood): the panel and the conversation stay.
   Reload: still there.

Rules: everything runs locally until Drew says it's good; no push before C1. 💲 = real bot
calls (cents); everything else is free. Keep visuals minimal (green ✦, site colours); Drew
does the design pass himself later. Tests never need Google or the real bot: the check
script runs a **stand-in chat page** (`tooling/qa/fake-webui/`) in place of Open WebUI.

Known facts that shape the tasks (checked 2026-09-12):
- Google's sign-in pages refuse to load inside a frame, so login must open in a popup or
  a new tab, and the frame reloads once signed in (W3).
- A framed app's login cookie only works when the frame and the page are the same "site".
  Locally both are `localhost`, fine. Live, two `*.up.railway.app` addresses do **not**
  count as the same site (Safari/iOS block it), so C2 needs one address (custom domain
  with `chat.` subdomain, or one reverse proxy). Decide in C2, not before.
- The Google keys file `chatbot/.env.local` is gone from this computer; Drew re-enters the
  keys in W5. Old chats are still in the `ps-chat_open-webui` Docker volume.

## Part W — Panel

- [x] **W0 Self-contained check script.** `tooling/qa/check-panel.sh`: serves the site on
  8766 and the stand-in chat page (`tooling/qa/fake-webui/index.html`: fake login button,
  fake message list, posts `postMessage` events like the real one will) on 3001, runs
  `tooling/qa/sweep.py http://localhost:8766` and `tooling/qa/panel_test.py` (Playwright,
  starts as a stub that loads each page), kills both, exits non-zero on any bug. Under 2 min.
  `site/js/app.js` reads the chat address from `window.PS_CHAT_URL` if set (tests set it
  to :3001), else the existing local/live constant.
  Check: `bash tooling/qa/check-panel.sh` passes on a clean checkout with no env vars.
- [x] **W1 Panel shell on every page.** `site/js/chat-panel.js` + `site/css/chat-panel.css`
  loaded by all 5 pages via app.js: Ask button and the Chat tab open a right-side slide-out
  (480px desktop, full-screen on phone, page content still scrollable) with a slim header
  (✦ Ask PropertyStack, "open in full page" link, close) and an `<iframe>` of the chat
  address. Open/closed state and the frame's URL survive tab switches and reloads
  (sessionStorage). Loading shimmer until the frame loads; friendly note if it fails.
  Remove the B2 locked card from master-table.html.
  Check: sweep clean at desktop/tablet/phone; panel_test.py opens the panel on all 5 pages,
  switches page with it open → still open; screenshots at 1440 and 390 in `/tmp/qa/`.
- [x] **W2 Open WebUI fits the frame.** Verify Open WebUI's response headers allow framing
  from the site (if not, set them in compose or front it with the proxy); custom CSS
  (compact mode): sidebar collapsed by default but reachable (past chats, new chat), no
  model picker, no settings clutter, message column fills the 480px width, input pinned at
  the bottom on phone. No design polish beyond that.
  Check: free — compose up (no bot calls), Playwright loads the site with the real Open
  WebUI in the frame at 1440 and 390: no X-Frame/CSP errors, login page visible inside the
  panel, screenshots saved.
- [x] **W3 Sign-in from inside the panel.** In the frame, the "Continue with Google" click
  must open Google in a popup (or new tab on phone); after it finishes, the frame reloads
  signed in. Implement in Open WebUI custom JS/CSS if it allows, else the panel intercepts:
  shows its own "Sign in with Google" button when the frame is on the login page, opens
  the chat app's Google route in a popup, and reloads the frame when the popup closes.
  Stand-in page mimics the same flow for tests.
  Check: panel_test.py with the stand-in — click sign in → popup opens → close it → frame
  shows the chat; real check in W5.
- [x] **W4 Not buggy.** Hardening checklist, fix all, one test each in panel_test.py:
  panel open on reload keeps the same chat; phone keyboard doesn't hide the input; panel
  close/open doesn't reload the chat; two rapid Ask clicks don't double the frame; no console
  errors on any page; Chat tab is marked active while the panel is open; ESC closes on
  desktop; the "open in full page" link goes to the same conversation.
  Check: `bash tooling/qa/check-panel.sh` green; zero console errors in the sweep.
- [x] **W5 Local Google keys + real run.** _(Keys saved 2026-09-12; stack starts; the real sign-in click is part of C1. Drew's first try found the three problems fixed in W6–W8.)_ Drew re-enters `GOOGLE_CLIENT_ID` /
  `GOOGLE_CLIENT_SECRET` in `chatbot/.env.local` (guide in `chatbot/GOOGLE-SIGNIN.md`,
  updated: authorised origin also = `http://localhost:8765`); add `chatbot/.env.local.example`.
  Check: 💲 compose up, open http://localhost:8765, Ask → sign in with Google in the popup →
  a cited answer streams inside the panel; reload → conversation still there.

- [ ] **W6 Docked, never covering.** Drew's feedback: the panel floats over the top of
  the dashboard and hides content. On desktop/tablet (>= 900px) the panel must be **docked**:
  the page layout shrinks to make room (body gets a right margin / grid column equal to the
  panel width, header and tables reflow, sidebar untouched), nothing sits underneath it,
  no horizontal scroll. Slide animation is fine but the end state is side by side. On phone
  it stays full-screen. Keep the panel width 480px, allow 400px on tablet.
  Check: panel_test.py at 1440 and 1024 with the panel open — no page element's box
  intersects the panel's box, no horizontal scroll; sweep clean on all 5 pages.
- [ ] **W7 One model, no picker.** Drew saw a model picker inside the chat. Verify against
  the **real** Open WebUI (compose up, no bot calls): the model dropdown must not appear for
  a normal user or the admin; the single model is preselected. Do it with Open WebUI's own
  settings first (`DEFAULT_MODELS`, admin → Settings → Models: only one model, model
  selector off / user permissions `chat.controls` off), then custom.css only as a fallback.
  Also hide the "Arena"/temporary-chat/settings clutter if visible.
  Check: Playwright loads the real Open WebUI in the panel at 480px wide, signed in as the
  local admin via the API: no element matching the model selector is visible; screenshot saved.
- [ ] **W8 Sign-in button that actually shows.** Drew clicked and nothing happened: the
  panel's own "Sign in with Google" button only appears after an `auth-state` message that
  the real Open WebUI never sends (only the stand-in does), so the user is left with the
  framed Google button, which Google refuses. Fix: the panel decides sign-in state itself
  by calling the chat app's `GET /api/v1/auths/` with `credentials: "include"` (enable
  `CORS_ALLOW_ORIGIN` for the site address in compose); if not signed in, show a clear
  "Sign in with Google" card **over the frame** with one button that opens the popup;
  when the popup closes, re-check and reload the frame. If the fetch itself fails, show
  the button anyway. Stand-in page gets the same endpoint so tests still run free.
  Check: panel_test.py — not signed in → card with button visible; click → popup;
  popup closes → card gone, frame reloaded. Free real check: compose up, open the site,
  the card shows on first open.

## Part C — Ship

- [ ] **C1 Drew tries it on localhost.** Panel on every page, Google sign-in, ask, switch
  tabs, reload, phone size. After "good" and "Put it on GitHub?": deploy.
- [ ] **C2 Railway, one address.** Pick with Drew: (a) custom domain, site at the root and
  chat at `chat.` (same site, cookies work), or (b) one reverse proxy service serving the
  site and forwarding `/chat/` to Open WebUI. New `propertystack-chat` service (Open WebUI)
  with a volume; Hermes private; Google console origins/redirect = live addresses; app.js
  live chat address updated.
  Check: live site → Ask → Google sign-in → answer streams inside the panel on desktop and
  iPhone Safari; redeploy → chats still there.
- [ ] **C3 Clean up.** Remove the old `/chat` + `/chat/stream` JSON routes from the proxy
  if nothing uses them; `chatbot/README.md` describes the panel + Open WebUI setup; archive
  PLAN-v5.
  Check: sweep clean; README current.
