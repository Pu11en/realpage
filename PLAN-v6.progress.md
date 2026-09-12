
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
