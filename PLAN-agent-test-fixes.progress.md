# Progress log

## T1 Chat loads every time — done
Raised the chat panel's load timeout from 8s to 30s (`site/js/chat-panel.js`), changed the loading
message to "Waking up the chat…", and added one automatic reload of the iframe before showing the
manual "Couldn't load the chat." error with its Try again button. Added
`tooling/qa/fixes_tests/test_t1_chat_load_timeout.py` (checks the 30s default, the wording, and that
one auto-retry happens before the error is shown). Checked with `bash tooling/qa/check-fixes.sh`
(60 tests pass, design check 0 problems). Commit: see git log.
