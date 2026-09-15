# Progress: find-contact-link

## F1 Agent rule + its tests — done (commit f0df219)
- SOUL.md lead-list rule: a lead with no phone/link now ends with `[🔍 Find contact](#ask:Deep dive on <name>, <city>)` instead of "ask me for a deep dive".
- SOUL.md: if the #1 lead has no office_phone, one ps_web_search (only for #1), shown only if a result names that building.
- linkfix.py already only checks http(s) links, so #ask: links pass through untouched; documented that in its docstring.
- New tooling/qa/fixes_tests/test_find_contact.py (5 offline tests: SOUL rule, #1-only lookup, linkfix keeps #ask:, still strips fake https next to it, streaming LineFixer).
- Check: 47 passed.
- Open: the link isn't clickable in chat yet (F2, loader.js); real run is F3.

## F1 check fix
- The bot runs Check without a shell, so `$(ls ...)` broke it. Check now names test_find_contact.py directly (it exists since F1). 47 passed.

## F2 Clickable in the chat — done (commit 985a83a)
- loader.js (inside Open WebUI): a capture-phase click handler on `a[href^="#ask:"]` decodes the text after `#ask:` and posts `{type:"input:prompt:submit", text}` to its own window. Open WebUI 0.11 (checked in the built JS of ghcr.io/open-webui/open-webui:main) accepts that same-origin and submits it at once. preventDefault + stopPropagation: no page jump, no new tab (Open WebUI renders links with target=_blank). Existing loader behaviour untouched.
- test_find_contact.py: new test that loader.js has the `a[href^="#ask:"]` handler, uses input:prompt:submit, preventDefault and decodeURIComponent.
- Check: 48 passed. Also a stand-alone Playwright check (fake page + loader.js): clicking the link posted exactly {type:"input:prompt:submit", text:"Deep dive on The Sherman, Richardson"}, URL unchanged, no new tab.
- Open: real end-to-end run against the dev stack is F3.
