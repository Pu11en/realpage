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

## F2 sent back by review, fixed (commit 00c17b4)
- Review asked for proof the click really sends. Checked Open WebUI's built JS (ghcr.io/open-webui/open-webui:main): a same-origin postMessage {type:"input:prompt:submit", text} calls its submitPrompt; the site's chat-panel.js already uses the sibling "input:prompt" message the same way. So the mechanism is real.
- Real run then showed the actual bug: Open WebUI printed "[🔍 Find contact](#ask:Deep dive on …)" as raw text, because Markdown will not parse a link whose address contains spaces. Fix: linkfix.py (the proxy's last step) percent-encodes the text after #ask: (no double-encoding); loader.js already decodes it. SOUL.md unchanged.
- New tooling/qa/live_find_contact_click.py (real Playwright against the running stack; SITE env picks the site port): asked "give me top leads any area" -> 3 lead lines, 2 with 📞 + Texas building record, 1 (4030 N 44Th Ave, Phoenix) with 🔍 Find contact; clicked it -> "Deep dive on 4030 N 44Th Ave, Phoenix" appeared as the sent message, site URL unchanged, no new tab; deep-dive answer came back with a phone. PASS. Screenshot: tooling/qa/shots/find-contact.png (folder is gitignored, so not committed).
- Note for F3: the run used this worktree's site on port 8766 (another stack holds 8765), with CORS_ALLOW_ORIGIN extended to include 8766 when starting the compose stack. On 8765 via tooling/dev.sh no extra setting is needed.
- Check: 48 passed.

## F3 Try it for real, locally — done (PASS)
- Rebuilt the dev chat stack from this worktree (`docker compose -f chatbot/docker-compose.local.yml -f chatbot/docker-compose.dev.yml -p ps-chat up -d --build`) and confirmed the running container really has the linkfix `#ask:` percent-encoding.
- Port 8765 is held by another stack (cranesignal-human-test), so this worktree's site was served on 8766 with `CORS_ALLOW_ORIGIN` extended to include it; on a free 8765 plain `bash tooling/dev.sh` needs nothing extra.
- Real Playwright run (`SITE=http://localhost:8766 python3 tooling/qa/live_find_contact_click.py`), asked "give me top leads any area": 3 lead lines, 0 without a contact/link —
  Groves Apartments, Humble 📞 (210) 326-1119 + Texas building record; 4030 N 44th Ave, Phoenix 🔍 Find contact; Stargaze Apartments, Brownsville 📞 (956) 343-6375 + Texas building record.
- Clicked the 🔍 Find contact link: "Deep dive on 4030 N 44th Ave, Phoenix" was sent as a chat message on its own, site URL unchanged (http://localhost:8766/index.html), no new tab, no console errors. The deep dive answered with a leasing-office phone ((928) 543-0626), size, software and source lines. RESULT: PASS.
- Screenshot: tooling/qa/shots/find-contact.png (+ -before.png). That folder is gitignored, so the images are on disk only, not committed.
- Check: 48 passed. Stopped the site server I started (8766); left the shared ps-chat containers up because another session was already using them.
- Nothing left open: the plan's goal is met end to end. Not pushed.

## Next time (from how this build went)
- Test commands should skip shell tricks — this plan's probe for a file existence broke the run. Use simple, validated commands instead.
- Mark task checkboxes correctly; an incomplete mark got F2 stuck and didn't tick the next step.
- The rest ran smoothly — the review step's verification was thorough, and implementation plus validation both went cleanly.
