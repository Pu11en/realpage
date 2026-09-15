# Progress log

## T1 Chat loads every time — done
Raised the chat panel's load timeout from 8s to 30s (`site/js/chat-panel.js`), changed the loading
message to "Waking up the chat…", and added one automatic reload of the iframe before showing the
manual "Couldn't load the chat." error with its Try again button. Added
`tooling/qa/fixes_tests/test_t1_chat_load_timeout.py` (checks the 30s default, the wording, and that
one auto-retry happens before the error is shown). Checked with `bash tooling/qa/check-fixes.sh`
(60 tests pass, design check 0 problems). Commit: see git log.

## T2 One chat header bar — done
Hardened `site/js/chat-panel.js` against double-init: the whole script now guards itself with
`window.__chatPanelLoaded` so it only runs once even if the `<script>` tag is ever duplicated;
`wireTriggers()` now marks each Ask/Chat button (`dataset.chatWired`) so a repeat `initChatPanel()`
call can't attach a second click listener (which would open-then-immediately-close the panel and
briefly show a second header while the first was torn down); and `buildPanel()` now defensively
drops any stray extra `#chat-panel` nodes instead of building yet another one. Added
`tooling/qa/fixes_tests/test_t2_chat_panel_single_header.py` (3 tests, checks all three guards are
present in the source). Checked with `bash tooling/qa/check-fixes.sh` (63 tests pass, design check
0 problems). Commit: see git log.

## T3 Sign-out button — done
Added a "Sign out" link to the shared sidebar shell (`site/js/app.js`'s `renderShell()`), next
to Privacy, hidden by default. `site/js/chat-panel.js` now shows/hides it using the same
sign-in check it already does for the chat panel's sign-in card (`checkAuth()`): hidden locally
(chat app auth off) and hidden until someone is actually signed in live. Clicking it posts to
the chat app's `/api/v1/auths/signout`, clears the panel's local session flag, and sends the
browser to the chat app's `/auth` sign-in page. Added
`tooling/qa/fixes_tests/test_t3_sign_out.py` (5 tests: link present on all 5 app pages, hidden
by default, calls the right sign-out endpoint and lands on `/auth`, only shown once signed in,
wiring doesn't double-bind). Checked with `bash tooling/qa/check-fixes.sh` (68 tests pass,
design check 0 problems). Commit: see git log.

## T4 Real "page not found" — done
Added `site/404.html` (a CraneSignal-styled not-found page with a link home) and reworked
`site/Caddyfile` so unknown addresses get a real 404 instead of the chat app's leads page:
gave the chat app's own routes (`/auth`, `/oauth`, `/api/*`, `/ws`, `/_app/*`, `/static/*`,
`/c/*`, and `/` only when it's the chat panel's iframe) an explicit matcher, and everything
else now hits `error * 404` then `handle_errors` serves `404.html` with a real 404 status.
The sign-in gate is untouched — signed-out app pages still 302 to `/auth`, the iframe home
and the chat API still reach the chat app. Added
`tooling/qa/fixes_tests/test_t4_not_found.py` (4 tests, reuses the E1 test's real-Caddy
fixture): unknown page is a real 404 with CraneSignal wording, the sign-in gate still works,
chat app routes still reach the chat app, and the 404.html file exists. Verified manually
with the cached Caddy binary before writing the test (curl showed `HTTP/1.1 404 Not Found`
with the CraneSignal page body, `/auth` still 200, `/api/v1/auths/` still 401, signed-in
`/index.html` still 200). Checked with `bash tooling/qa/check-fixes.sh` (72 tests pass,
design check 0 problems). Commit: see git log.

## T5 Logo goes home — done
Made the CraneSignal wordmark in the shared shell (`site/js/app.js`'s `renderShell()`) an
`<a href="index.html">` instead of a plain `<div>`, and added `text-decoration: none` to
`.sidebar .wordmark` in `site/css/styles.css` so it still looks like a wordmark, not a
typical link. Added `tooling/qa/fixes_tests/test_t5_logo_links_home.py` (2 tests: the
wordmark markup is an anchor to index.html, and every app page still calls renderShell()).
Checked with `bash tooling/qa/check-fixes.sh` (74 tests pass, design check 0 problems).
Commit: see git log.
