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
