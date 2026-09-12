# PropertyStack v4 — Chat that works like Eve

Written 2026-09-11. Drew's goal: the website chat should work like **Eve** (the Hermes
agent on Railway, `github.com/Pu11en/eve-agent`), just in a browser instead of
Telegram, with a UI that feels polished. It should also have all the backend a real
web chat needs.
Run with: `Do the next unticked task in PLAN-v4.md, then tick it and stop.`
Check: `python3 tooling/qa/sweep.py http://localhost:8765` (plus the task's own Check line)

This replaces PLAN-v3 items 2.1, 2.2, 2.3, 3.1, 3.2, 4.1 and 4.2. PLAN-v3 2.0 and D1 are
done. The trial page is `site/chat-trial.html`.

## Eve vs the site bot today (checked 2026-09-11)

| What | Eve (Telegram) | Site bot now | Plan |
|---|---|---|---|
| Remembers the conversation | Yes, server keeps each chat | Browser re-sends last 10 messages | **A1** server sessions |
| Remembers the person | `memory_enabled` + `user_profile_enabled` | Off | **A2**, one memory per visitor |
| Saved on Railway across redeploys | Persistent Hermes home | Wiped every deploy | **A1** Railway volume |
| Long chats squeezed, not cut off | `compression` 0.5 → 0.2 | Off | **A4** |
| Shows what it's doing | `tool_progress: true` | Off, just "Thinking..." | **A3 + B2** |
| Words arrive live | Yes (Telegram edits the message) | Waits up to a minute | **A3 + B2** |
| Steps per question | `max_turns: 90` | 8 | **A4** raise with a cost cap |
| Shows cost | `show_cost: true` | Shows seconds | **B6** ask Drew |
| Terminal, file writes, web, skill editing, sub-agents | Yes | No, read-only data tools | **Never on a public site.** Anyone on the internet can type into it. |

Hermes (the engine under both bots) supports all of this through its web API:
`X-Hermes-Session-Id` for server-side chats, `X-Hermes-Session-Key` for per-visitor
memory, `GET /api/sessions/{id}/messages` for history, and streaming with
`hermes.tool.progress` events. Docs: hermes-agent.nousresearch.com → API server.

## Rules for every task

- Backend tasks run the chatbot in **local Docker first** (`chatbot/README.md` → Local
  test, port 18080). No Railway deploy until Drew has tried it on localhost (task A8).
- 💲 = real DeepSeek calls (small cost). Website tests use faked bot replies via
  Playwright `page.route`, which costs nothing.
- Each visitor gets a random ID saved in their browser. No login, no names.
- Public-site safety stays: read-only tools, rate limit, length caps.

## Part A — Backend (chatbot/, local Docker)

- [ ] **A1 Server-side chats.** 💲 The browser sends a `session_id` it made up
  (a random ID); `proxy.py` checks it's a valid ID and forwards it as `X-Hermes-Session-Id`.
  The browser stops re-sending history. `HERMES_HOME` goes on a Railway volume so chats
  survive redeploys (volume set up in A8).
  Check: local Docker — two `curl` turns with the same session_id, the 2nd answer uses
  the 1st; a different session_id doesn't know it.
- [ ] **A2 Memory for each visitor.** 💲 Turn on `memory_enabled` + `user_profile_enabled`
  and forward a visitor ID as `X-Hermes-Session-Key`. **Isolation test before anything
  else:** if Hermes' built-in memory turns out to be one shared file for everyone, stop
  and ask Drew. Don't ship shared memory on a public site.
  Check: visitor A says "my company is Acme"; new chat for A still knows it; visitor B
  asked "what's my company?" does not know.
- [ ] **A3 Live words + "what it's doing".** New `POST /chat/stream` in `proxy.py` that
  passes Hermes' streamed text and `hermes.tool.progress` events through as
  Server-Sent Events. Tool names become plain labels ("Looking up buildings…"). Old
  `/chat` keeps working. If the visitor disconnects, stop the Hermes call.
  Check: `curl -N` shows progress lines then text arriving in pieces; killing curl
  mid-answer stops the Hermes request (logs).
- [ ] **A4 Long chats like Eve.** Turn on Eve's `compression` settings. Raise `max_turns`
  8 → 20 and cap answer time, so the cost per question stays bounded.
  Check: 💲 a 15-turn scripted chat in local Docker never errors and remembers turn 1.
- [ ] **A5 Chat history endpoint.** `GET /sessions?visitor=…` lists a visitor's past
  chats (title = first question, date), and `GET /sessions/{id}/messages` returns one chat.
  Only that visitor's chats are returned.
  Check: `curl` lists 2 chats for visitor A, none for visitor B.
- [ ] **A6 Safety pass.** Rate limit per visitor as well as per IP, reject malformed IDs,
  cap stored memory size, confirm the toolset is still read-only.
  Check: `curl` with a bad ID → 400; 31st request in an hour → 429; the tool list shows
  only propertystack tools.

## Part B — Chat UI (after Drew picks Deep Chat vs today's chat: PLAN-v3 D2)

- [ ] **B1 One chat on every page.** Shared chat files, mounted on all 5 pages, same visitor
  and same open chat everywhere.
  Check: sweep sends a faked question on each page; the chat carries over between pages.
- [ ] **B2 Live answers.** Words appear as they stream; a small grey line shows what the
  bot is doing ("Looking up sales…"); a Stop button ends it.
  Check: headless with a faked stream — partial text shows before the end, progress line
  shows then clears, Stop halts it.
- [ ] **B3 Past chats.** A "Chats" list (like Telegram's chat list): open, continue, delete
  old chats, and "New chat". Loads from the server (A5), so it works after clearing the
  page, on every page.
  Check: headless with faked history — list shows 2 chats; opening one shows its messages.
- [ ] **B4 Message actions.** Copy button, Retry on errors (keeps order), and 2–3
  follow-up chips after each answer (simple keyword rules, no extra model calls).
  Check: headless — clipboard matches; Retry succeeds; chip click sends the question.
- [ ] **B5 Polish pass.** Phone keyboard doesn't cover the input, a "jump to latest"
  button, focus and screen-reader labels, empty/loading/offline states, a "waking up"
  note after 15s.
  Check: screenshots at 390, 820 and 1280 of empty, mid-answer, error and long-chat states,
  each looked at.
- [ ] **B6 Drew's call: show cost per answer like Eve?** (Eve shows cost; the site shows
  seconds.) Ask, then apply.

## Part C — Ship

- [ ] **A8 Drew tries it on localhost, then deploy.** Drew tests the full chat against the
  local Docker bot. After his OK and "Put it on GitHub?": add the Railway volume for
  `HERMES_HOME`, push, redeploy the chatbot and the site.
  Check: live site — chat, reload, open on another page, the chat and memory are still there.
