
## W0 Self-contained check script — done
- Added `tooling/qa/fake-webui/index.html`: a stand-in for Open WebUI with a
  fake login button (opens a popup, posts `signed-in` back like the real
  Google flow will) and a fake message list, for tests to use instead of the
  real chat app.
- Added `tooling/qa/check-panel.sh`: serves `site/` and the stand-in chat page
  on their own ports (8766 / 3001, overridable via CHECK_SITE_PORT /
  CHECK_CHAT_PORT), runs `quick-check.py` (not the slower `sweep.py`, which
  checks every external link on the internet and can't finish in 2 minutes
  offline) plus the new `panel_test.py`, then kills both servers. Exits
  non-zero on any bug.
- Added `tooling/qa/panel_test.py`: a stub Playwright check that loads all 5
  pages with `window.PS_CHAT_URL` pointed at the stand-in chat page and fails
  on any console/page error. Later W-tasks will add the real panel-open /
  sign-in / reload checks here.
- `site/js/app.js`: `CHAT_APP_URL` now reads `window.PS_CHAT_URL` first (set
  by tests), falling back to the existing localhost/live URLs.
- Checked: `bash tooling/qa/check-panel.sh` passes clean in ~8s with no env
  vars set, on ports 8766/3001.
- Commit: (see git log after this entry).
- Left open: default ports 8766/3001 can collide with a leftover server from
  a previous run if one was killed uncleanly; CHECK_SITE_PORT/CHECK_CHAT_PORT
  env vars work around that if it ever happens.

## W1 Panel shell on every page — done
- Added `site/js/chat-panel.js` + `site/css/chat-panel.css`: a right-side
  slide-out panel (480px desktop, full width under 600px) with a header
  (✦ Ask PropertyStack, "Open in full page" link, close button), a loading
  message, an `<iframe>` pointed at `CHAT_APP_URL`, and a friendly error
  message if the frame doesn't load within 8s. Open/closed state persists via
  sessionStorage so it survives tab switches and reloads within the session.
  ESC closes it; the sidebar's Chat link is marked active while it's open.
- Loaded the two new files on all 5 pages (index, master-table,
  software-share, under-the-hood, property) right after styles.css/app.js.
- `site/js/app.js`: the sidebar "Chat" link and the floating "Ask" button now
  have `data-chat-toggle` and open the panel instead of navigating away;
  `renderShell` calls `window.initChatPanel()` after building the shell.
- Removed the PLAN-v5 B2 locked "Ask PropertyStack" card and its two-column
  layout from `master-table.html` — the shared panel replaces it. That page's
  `.ask-fab { display: none; }` override is gone too, so the floating Ask
  button now shows there like everywhere else.
- `tooling/qa/panel_test.py`: now actually opens the panel (via the Ask
  button) on all 5 pages at both 1440 and 390 widths, checks it survived a
  page switch (index → master-table with the panel open), and saves
  screenshots to `/tmp/qa/*-panel-open.png`.
- Checked: `bash tooling/qa/check-panel.sh` passes clean (0 sweep problems,
  panel_test.py clean). Manually reviewed `/tmp/qa/desktop-master-table-panel-open.png`
  — panel opens over the table, table stays visible, Chat tab shows active.
- Commit: (see git log after this entry).
- Left open: real Open WebUI framing/CSS fit (W2), Google sign-in flow (W3),
  and the hardening checklist (W4) are separate later tasks.

## W2 Open WebUI fits the frame — done
- Brought up the real stack (`docker compose -f chatbot/docker-compose.local.yml
  --env-file chatbot/.env.local -p ps-chat up -d --build`) and checked Open
  WebUI's response headers: no `X-Frame-Options` or `Content-Security-Policy`
  header at all, so it frames from the site with no changes needed.
- Added `chatbot/branding/custom.css`: compact-mode CSS mounted over Open
  WebUI's existing (empty) `/app/build/static/custom.css` override point
  (already linked from its `index.html`, same trick as the branding icons).
  Collapses the sidebar by default (toggle button stays visible to reopen
  it), hides the model picker and settings-modal trigger (not needed with
  one model and no per-user settings from inside the panel), and makes the
  message column fill the panel width. Selectors (`#sidebar`,
  `data-testid="model-selector-model-button"`, etc.) came from grepping the
  real built JS bundle inside the running container, not guessed.
- Wired the mount into `chatbot/docker-compose.local.yml` next to the other
  branding volume mounts.
- Checked (free, no bot calls): a one-off Playwright script loaded the site
  with `window.PS_CHAT_URL` pointed at the real `http://localhost:3000` Open
  WebUI, opened the panel at 1440 and 390 widths — no frame-related console
  or request errors, the real (already Google-only) login page rendered
  correctly inside the 480px panel at both sizes, screenshots saved and
  reviewed by eye (`/tmp/qa/desktop-webui-frame.png`,
  `/tmp/qa/phone-webui-frame.png`). Also reran `bash tooling/qa/check-panel.sh`
  (stand-in chat page) — still green.
- Commit: (see git log after this entry).
- Left open: the compact CSS above only touches elements reachable from the
  login page and the real JS bundle's known selectors — it hasn't been
  visually confirmed against the *signed-in* chat interface yet, since that
  needs a real Google sign-in (W3/W5). If it looks off once signed in, adjust
  `chatbot/branding/custom.css` then. Docker stack was torn down after
  testing (`docker compose ... down`) since nothing needs to stay running
  between tasks.

## W3 Sign-in from inside the panel — done
- Checked the real Open WebUI image for a custom-JS mount point (it already has
  one for CSS, `custom.css`, used in W2) — there isn't one, so Open WebUI's own
  "Continue with Google" button can't be intercepted from inside the framed
  page. Used the plan's documented fallback instead: `site/js/chat-panel.js`
  now shows its own "Sign in with Google" button over the frame, which opens
  the chat app as a normal top-level popup (Google is willing to load there,
  just not inside an iframe) and reloads the framed copy once the popup
  closes, so it picks up the newly-signed-in session.
- The panel knows whether to show that button via a small postMessage
  contract: the framed chat app posts `{type: "auth-state", signedIn}` on
  load. `tooling/qa/fake-webui/index.html` (the stand-in) now sends this
  correctly and shares its signed-in flag via `localStorage` (not
  `sessionStorage`) so the popup and the framed copy — separate browsing
  contexts, same origin — see the same flag, standing in for the real cookie
  Open WebUI's backend sets once signed in.
- Added the sign-in flow to `tooling/qa/panel_test.py`: opens the panel,
  waits for the Sign in button to appear, clicks it, catches the popup,
  signs in inside the popup, confirms the popup closes on its own, confirms
  the framed copy then shows the chat view, and confirms the Sign in button
  disappears.
- Left open (real Open WebUI, deferred to W5 on purpose): the real app
  doesn't send an `auth-state` postMessage today (no custom-JS hook), so
  right now the Sign in button would always show even once actually signed
  in against the real app. W5's real run needs a different signal for that
  (e.g. the panel or proxy checking the session via a small `fetch`) — noted
  here so it isn't missed, not solved now since W3's Check only covers the
  stand-in.
- Checked: `CHECK_SITE_PORT=8792 CHECK_CHAT_PORT=8793 bash tooling/qa/check-panel.sh`
  passes clean. Note: the plan's exact `bash tooling/qa/check-panel.sh` (no
  env vars) currently fails on this shared machine only because something
  unrelated is already listening on port 3001 (not started by this task,
  still there after this session ends) — nothing to do with this change;
  confirmed by re-running on alternate ports.
- Commit: (see git log after this entry).

## W3 follow-up: fixed the port collision (2026-09-12)
- The reported "sign-in button didn't show" failure wasn't a panel bug: an
  unrelated server on this shared machine was already listening on the
  plan's default port 3001 (and 8766), so check-panel.sh's fixed ports
  sometimes served someone else's app instead of ours. Confirmed the real
  sign-in flow works correctly when run on non-colliding ports.
- Fixed `tooling/qa/check-panel.sh` to ask the OS for a free port by default
  (CHECK_SITE_PORT/CHECK_CHAT_PORT still override if set), and to verify the
  server's response body actually looks like our site/fake-webui before
  treating it as "up" (previously any 200 response was accepted).
- Checked: `bash tooling/qa/check-panel.sh` (no env vars, as the plan
  specifies) now passes clean, run 3 times in a row.

## W4 Not buggy — done
- Reviewed the hardening checklist against the current code:
  - Rapid double-click, ESC close, Chat-tab-active, panel close/open not
    reloading the chat, and console errors were already correct by
    construction (buildPanel() is idempotent by id, closePanel() never
    clears the iframe's src, markChatTabActive is called from both
    open/closePanel).
  - Found one real bug: `site/css/chat-panel.css` used a fixed `100vh` for
    the phone panel height, so when the on-screen keyboard opens on a real
    phone, the visual viewport shrinks but the panel doesn't, hiding the
    chat input behind the keyboard. Fixed by adding `height: 100dvh;` after
    the `100vh` fallback (dynamic viewport height tracks the keyboard;
    browsers without `dvh` support silently keep using the `100vh` line
    above it).
- Added explicit `tooling/qa/panel_test.py` checks for the checklist items
  that weren't covered yet: rapid double-click (Ask clicked twice fast)
  leaves exactly one `#chat-panel-frame` and ends closed, not doubled;
  sign in, send a message, close, reopen — the message is still there
  (proves the frame wasn't reloaded); ESC closes the panel on desktop and
  clears the Chat nav link's active state.
- Checked: `bash tooling/qa/check-panel.sh` passes clean (0 sweep problems,
  panel_test.py clean, all new checks included).
- Commit: (see git log after this entry).
- Left open: the "open in full page" link still points at the static chat
  app URL, not the exact open conversation — real Open WebUI has no
  custom-JS hook (confirmed in W3) to tell the parent page which
  conversation is open across origins, so there's no safe way to read that
  from the iframe. Not fixable without a server-side change; noted here in
  case it matters later, not attempted now since it's out of scope for a
  hardening pass. Also noted in W3: the sign-in postMessage flow only works
  with the stand-in today — the real Open WebUI signed-in detection is
  W5's job.

## W5 — Local Google keys + real run (partial, needs Drew)
- Found `chatbot/.env.local` already has real `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`
  filled in (Drew must have done this earlier), so that part of the task is done.
- Added `chatbot/.env.local.example` (blank template, safe to commit) listing the four
  keys the real file needs: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, ENABLE_SIGNUP,
  ENABLE_LOGIN_FORM.
- Added the missing "Authorized JavaScript origins: http://localhost:8765" step to
  `chatbot/GOOGLE-SIGNIN.md` step 4 (the plan's known-facts note said this was needed but
  the doc didn't have it yet).
- Started the real stack (`docker compose ... up -d --build`): both containers came up
  healthy, Open WebUI answered 200 on http://localhost:3000/ with Google OAuth configured
  (log confirms "OAuth providers configured (Google)"). Then stopped the stack again.
- Did NOT do the last part of the check (actually signing in with a real Google account in
  a browser and sending a message that triggers a real paid bot call) — that needs a human
  to click through the Google popup, and it costs real money, so it needs Drew. Leaving the
  W5 box unchecked for that reason.
- Commit: (see git log after this entry).
- Left open: same as before — full W5 check (sign in as kidquick360@gmail.com, ask a
  question, see a cited streamed answer, reload and confirm the conversation persists)
  still needs Drew to do it by hand, then this box can be ticked.
- Drew's answer to the last ask ("yes-leave-it"): leave W5 unticked for now, move on to
  the next task instead of waiting for him to test sign-in.

## W6 Docked, never covering — done
- `site/css/chat-panel.css`: on desktop/tablet (>= 900px) opening the panel now adds
  `margin-right` to `.shell` (480px, or 400px between 900–1199px, matching the panel's own
  width at that size) instead of just floating the panel on top. `.shell`'s grid keeps the
  220px sidebar fixed and the main column shrinks to fill what's left.
- Found the shrink alone caused a real horizontal scrollbar at 1024px: `.main` had no
  `min-width: 0`, so its grid track wouldn't actually shrink below its content's natural
  width (a CSS grid default). Added `min-width: 0` and `table { overflow-x: auto }` for
  `.main` while the panel is docked, matching the pattern already used for the phone
  layout further down the same file.
- `tooling/qa/panel_test.py`: added a W6 check pass at 1440px and 1024px across all 5
  pages — opens the panel, waits for the slide/margin transition to settle, then asserts
  the page content's right edge never crosses the panel's left edge (no overlap) and that
  `document.documentElement.scrollWidth` never exceeds the viewport (no horizontal scroll).
- Checked: `bash tooling/qa/check-panel.sh` passes clean (0 sweep problems, panel_test.py
  clean, including the new W6 checks).
- Commit: (see git log after this entry).
- Left open: only verified against the stand-in chat page per the plan's Check line; the
  real Open WebUI iframe's own internal layout at 400px (tablet) wasn't separately
  eyeballed, since W2 already confirmed its compact CSS fits a 480px column and 400px is
  narrower still — worth a quick look if it looks cramped once W7/W8 wire up the real app.

## W7 One model, no picker — done
- Brought up `chatbot/docker-compose.local.yml` (already running from earlier work) and
  found two real problems on top of Drew's original complaint:
  1. Open WebUI's OpenAI connection had been persisted (in its SQLite `config` table)
     pointing at the old port `chatbot:8642` with the connection disabled — a leftover
     from before this repo's proxy moved to port 8080. That's why `/api/models` was
     returning nothing. Open WebUI stores these as "PersistentConfig": once written to
     the DB, env vars in the compose file no longer take effect on restart. Fixed via
     the admin `/openai/config/update` API to point at `http://chatbot:8080/v1` with
     `enable: true` — matches what the compose file already intends.
  2. The custom.css rule meant to hide the model picker (`[data-testid='model-selector-
     model-button']`) never matched: this Open WebUI build (v0.11.3) renders that button
     with `id="model-selector-model-button"`, not a `data-testid` attribute, so the
     dropdown was fully visible and clickable the whole time. Added the `#id` selector
     alongside the old one in `chatbot/branding/custom.css` (kept both so it survives
     either attribute style across versions).
  3. Also found the built-in "Arena Model" pseudo-model showing up in the model list
     (the plan's "clutter" to hide) — turned it off via the admin
     `/api/v1/evaluations/config` endpoint (`ENABLE_EVALUATION_ARENA_MODELS: false`),
     and set the default new-user permission `chat.controls: false` via
     `/api/v1/users/default/permissions` so future signed-up users don't get per-chat
     controls exposed either.
- All three fixes are server-side admin settings persisted in Open WebUI's own database
  (the volume the compose file already mounts), not code changes to this repo, except
  the custom.css selector fix.
- Checked with a new Playwright script, `tooling/qa/w7_real_webui_check.py`: signs in as
  a throwaway admin and a throwaway normal user (created via Open WebUI's own signup API
  with `ENABLE_SIGNUP` temporarily flipped on for setup only, then flipped back off and
  both throwaway accounts deleted — Drew's real `kidquick360@gmail.com` admin account
  was never touched), loads the real app at 480px, and asserts the model-selector button
  and "Arena Model" text are not visible for either account. Passed for both, before and
  after restoring the real Google-only sign-in settings. Screenshots saved under
  `tooling/qa/shots/` (gitignored, not committed).
- Also reran `bash tooling/qa/check-panel.sh` (the plan's existing check) — still clean,
  0 problems, panel_test.py clean.
- Commit: (see git log after this entry).
- Left open: the real compose stack's OpenAI connection and Arena/permission settings
  live in the Open WebUI database volume, not in a config file this repo tracks — if
  that volume is ever recreated from scratch (fresh `docker volume rm` or a new
  environment), these three admin settings will need to be reapplied once by hand or
  scripted, since Open WebUI ignores the compose file's env vars once its own DB has a
  value. Worth a short one-time setup script if this comes up again for Railway (C2).

## W8 Sign-in button that actually shows — done (commit pending, see note)
- `site/js/chat-panel.js`: the panel no longer waits for an `auth-state`
  postMessage the real Open WebUI never sends. It now decides sign-in state
  itself: on every frame load (and on reopen of an already-loaded frame) it
  calls `GET <chat>/api/v1/auths/` with `credentials: "include"`; 401 or a
  failed fetch shows a clear "Sign in to ask a question" card **over the
  frame** with one Sign in with Google button (opens the popup as before;
  popup close reloads the frame, which re-runs the check and hides the card).
- `chatbot/docker-compose.local.yml`: added `CORS_ALLOW_ORIGIN` (default
  `http://localhost:8765`) to the open-webui service — with the default
  wildcard, a credentialed cross-origin fetch is refused by the browser, so
  the panel could never learn the real sign-in state. Verified live: the
  endpoint answers 401 with `access-control-allow-origin: http://localhost:8765`
  and `access-control-allow-credentials: true`.
- Stand-in upgraded to match the real contract: `tooling/qa/fake-webui/server.py`
  (new) serves the stand-in page plus `GET /api/v1/auths/` (401 without the
  cookie, 200 with it) and `POST /api/v1/auths/signin` (sets the cookie);
  `check-panel.sh` now serves the stand-in with it; the fake page's sign-in
  button hits the POST so the popup and the panel agree on state via the
  cookie, exactly like the real app.
- `tooling/qa/panel_test.py`: W3/W8 section updated — signed out → card with
  button visible; click → popup; popup closes → frame reloads to the chat;
  card disappears (now waited-for properly instead of an immediate racy check).
- New `tooling/qa/w8_real_check.py` (free, no bot calls): loads the real Open
  WebUI in the panel — the sign-in card shows on first open, as the plan's
  Check requires. Ran it against the live local stack: PASS.
- Checked: `bash tooling/qa/check-panel.sh` green (0 problems, panel_test.py
  clean); real check above PASS.
- Commit: BLOCKED this round — the sandbox denied writes to the worktree's
  shared .git (outside the session workspace) and no approval channel was
  available. All changes are saved in the worktree; the commit must be made
  with wider file access (`git add -A && git commit -m "PLAN-v6 W8: panel
  decides sign-in state itself via /api/v1/auths/"`).
- Left open: the signed-in half of the real check (card hides when actually
  signed in) was verified only against the stand-in — creating a throwaway
  account needs signup temporarily re-enabled; the logic is identical
  (200 → hide) and C1's real Google run will cover it.

## W8 follow-up: live answers were broken by the W8 CORS value — fixed
- Drew's local try showed the panel chat signed in and accepted a question but
  never showed an answer. Root cause found by driving the real stack in a
  browser (Playwright) and reading Open WebUI's own source:
  - W8 set `CORS_ALLOW_ORIGIN=http://localhost:8765` (only the site) so the
    panel's credentialed `GET /api/v1/auths/` would work. But Open WebUI also
    derives `SOCKETIO_CORS_ORIGINS` from that same value
    (`socket/main.py:62`), so the chat app's **own** origin `http://localhost:3000`
    was no longer allowed. Every socket.io handshake from inside the frame (and
    even top-level :3000) was refused with HTTP 403, and Open WebUI delivers
    streaming answers and error events over that socket. Result: the model ran,
    the answer was saved, but the UI showed an empty assistant bubble forever.
  - Verified the mechanism: exact browser request body replayed with curl
    returned `null` (the endpoint's error path, `main.py:1691`), while the
    saved chat already contained the correct assistant answer; direct curl to
    `/api/chat/completions` streamed fine.
- Fix: `CORS_ALLOW_ORIGIN` default is now the semicolon-separated list
  `http://localhost:8765;http://localhost:3000` (Open WebUI splits on `;`), with
  a comment explaining that the chat app's own origin must stay in the list.
- Checked (real stack, no Google needed — sign-in state simulated by seeding the
  chat origin's `token` exactly as the popup does after OAuth):
  - top-level :3000 chat: completion response now `{"status":true,...}`, not
    `null`; live text renders.
  - panel on the site: sign-in card → popup → close → chat loads → ask
    "which vendor runs the most buildings?" → **live cited answer visible in the
    panel in ~6s** ("Yardi runs the most buildings — 66 of 204, ahead of
    RealPage (36) and Entrata (22) [3-software.csv]"), zero socket/console
    errors, and the same answer saved server-side.
- The real Google popup click-through (needs Drew's account) is still C1's job;
  everything up to and after the popup is now verified.
