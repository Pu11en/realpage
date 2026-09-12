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
- [ ] **W1 Panel shell on every page.** `site/js/chat-panel.js` + `site/css/chat-panel.css`
  loaded by all 5 pages via app.js: Ask button and the Chat tab open a right-side slide-out
  (480px desktop, full-screen on phone, page content still scrollable) with a slim header
  (✦ Ask PropertyStack, "open in full page" link, close) and an `<iframe>` of the chat
  address. Open/closed state and the frame's URL survive tab switches and reloads
  (sessionStorage). Loading shimmer until the frame loads; friendly note if it fails.
  Remove the B2 locked card from master-table.html.
  Check: sweep clean at desktop/tablet/phone; panel_test.py opens the panel on all 5 pages,
  switches page with it open → still open; screenshots at 1440 and 390 in `/tmp/qa/`.
- [ ] **W2 Open WebUI fits the frame.** Verify Open WebUI's response headers allow framing
  from the site (if not, set them in compose or front it with the proxy); custom CSS
  (compact mode): sidebar collapsed by default but reachable (past chats, new chat), no
  model picker, no settings clutter, message column fills the 480px width, input pinned at
  the bottom on phone. No design polish beyond that.
  Check: free — compose up (no bot calls), Playwright loads the site with the real Open
  WebUI in the frame at 1440 and 390: no X-Frame/CSP errors, login page visible inside the
  panel, screenshots saved.
- [ ] **W3 Sign-in from inside the panel.** In the frame, the "Continue with Google" click
  must open Google in a popup (or new tab on phone); after it finishes, the frame reloads
  signed in. Implement in Open WebUI custom JS/CSS if it allows, else the panel intercepts:
  shows its own "Sign in with Google" button when the frame is on the login page, opens
  the chat app's Google route in a popup, and reloads the frame when the popup closes.
  Stand-in page mimics the same flow for tests.
  Check: panel_test.py with the stand-in — click sign in → popup opens → close it → frame
  shows the chat; real check in W5.
- [ ] **W4 Not buggy.** Hardening checklist, fix all, one test each in panel_test.py:
  panel open on reload keeps the same chat; phone keyboard doesn't hide the input; panel
  close/open doesn't reload the chat; two rapid Ask clicks don't double the frame; no console
  errors on any page; Chat tab is marked active while the panel is open; ESC closes on
  desktop; the "open in full page" link goes to the same conversation.
  Check: `bash tooling/qa/check-panel.sh` green; zero console errors in the sweep.
- [ ] **W5 Local Google keys + real run.** Drew re-enters `GOOGLE_CLIENT_ID` /
  `GOOGLE_CLIENT_SECRET` in `chatbot/.env.local` (guide in `chatbot/GOOGLE-SIGNIN.md`,
  updated: authorised origin also = `http://localhost:8765`); add `chatbot/.env.local.example`.
  Check: 💲 compose up, open http://localhost:8765, Ask → sign in with Google in the popup →
  a cited answer streams inside the panel; reload → conversation still there.

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
