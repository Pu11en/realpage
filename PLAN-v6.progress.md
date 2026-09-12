
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
