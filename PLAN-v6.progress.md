
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
