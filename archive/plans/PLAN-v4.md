> **Superseded by PLAN-v5.md (Open WebUI + Google sign-in), 2026-09-11.** A1/A3/B2/B7 done and kept; the rest is replaced.

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
| Remembers the person | `memory_enabled` + `user_profile_enabled` | Off | **A2** trial first (built-in memory is shared by everyone) |
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

## Holes in today's chat (found by reading the code, 2026-09-11)

Drew's real goal: **no holes** — the chat never breaks, loses things, confuses or
surprises you, the way Eve feels solid on Telegram. Every hole below gets fixed by a task,
and task Z1 turns each one into an automatic test so it can't come back.

| # | What goes wrong for the user | Fixed by |
|---|---|---|
| H1 | Reload or leave the page while it's thinking → the answer is lost, your question sits there unanswered with no note | ✅ note added (B2); answer itself still lost until B3 |
| H2 | Two tabs open → each overwrites the other's saved chat | A1 + B3 |
| H3 | After ~10 questions the bot silently forgets the start of the chat, but you can still see it | A1 + A4 |
| H4 | Screen shows the last 40 messages but saves 20 turns; long chats lose older messages without saying so | A1 + B3 |
| H5 | Errors show robot words: "Something went wrong: agent error." / "agent timed out" | ✅ H-fix task B7 |
| H6 | Hit the hourly limit (30 questions) → vague error, no "try again in X minutes" | ✅ A6 + B7 |
| H7 | First question after the bot has slept is very slow, nothing explains why | ✅ B2 (hint after 15s) |
| H8 | While reading a long answer, a new answer yanks you to the bottom; long answers open at their end, not their start | ✅ B7 |
| H9 | No way to stop a slow or wrong answer | ✅ A3 + B2 |
| H10 | Press Enter while it's still answering → nothing happens, no hint why | ✅ B7 |
| H11 | Collapsed chat panel pops open again after reload | ✅ B7 |
| H12 | Chat exists only on the Master Table | B1 |
| H13 | Phone: keyboard may cover the input box (unverified) | B5 |
| H14 | The bot's warm-up words ("I'll check the schema first.") flash in the answer for a moment before a lookup | ✅ B7: show them in the grey status line instead |

## Rules for every task

- Backend tasks run the chatbot in **local Docker first** (`chatbot/README.md` → Local
  test, port 18080). No Railway deploy until Drew has tried it on localhost (task A8).
- 💲 = real DeepSeek calls (small cost). Website tests use faked bot replies via
  Playwright `page.route`, which costs nothing.
- Each visitor gets a random ID saved in their browser. No login, no names.
- Public-site safety stays: read-only tools, rate limit, length caps.

## Part A — Backend (chatbot/, local Docker)

- [x] **A1 Server-side chats.** _(Done 2026-09-11, local Docker: same chat remembered across reload and bot restart, new chat/other ID doesn't know it, bad ID → 400. Railway volume still pending, A8.)_ 💲 The browser sends a `session_id` it made up
  (a random ID); `proxy.py` checks it's a valid ID and forwards it as `X-Hermes-Session-Id`.
  The browser stops re-sending history. `HERMES_HOME` goes on a Railway volume so chats
  survive redeploys (volume set up in A8).
  Check: local Docker — two `curl` turns with the same session_id, the 2nd answer uses
  the 1st; a different session_id doesn't know it.
- [ ] **A2 Memory trial (no build).** 💲 Drew's call 2026-09-11: saved chats ship first;
  "remembers who you are" waits for this trial. Hermes' built-in memory is **one shared
  memory for everyone**, so keep it OFF. In local Docker, try the free/self-hosted memory
  add-ons that list per-user separation (Hindsight local, Mem0 open-source, Supermemory
  self-hosted) with the visitor ID. For each, write down in
  `chatbot/MEMORY-OPTIONS.md`: works yes/no, keeps visitors apart yes/no, extra
  keys/accounts needed, monthly cost, storage needed on Railway.
  Check: `chatbot/MEMORY-OPTIONS.md` has a filled row per option, each with the isolation
  test (visitor A: "my company is Acme"; visitor B: "what's my company?" → doesn't know).
- [ ] **A2b Drew picks a memory option (or none).** If one is picked, add a build task here.
- [x] **A3 Live words + "what it's doing".** _(Done 2026-09-11: `/chat/stream` in proxy.py; tested with curl + disconnect → Hermes logs "interrupted".)_ New `POST /chat/stream` in `proxy.py` that
  passes Hermes' streamed text and `hermes.tool.progress` events through as
  Server-Sent Events. Tool names become plain labels ("Looking up buildings…"). Old
  `/chat` keeps working. If the visitor disconnects, stop the Hermes call.
  Check: `curl -N` shows progress lines then text arriving in pieces; killing curl
  mid-answer stops the Hermes request (logs).
- [ ] **A4 Long chats like Eve.** Turn on Eve's `compression` settings. Raise `max_turns`
  8 → 20 and keep the 120s answer-time cap, so the cost per question stays bounded.
  Check: 💲 a 15-turn scripted chat in local Docker never errors and remembers turn 1.
- [ ] **A5 Chat history endpoint.** `GET /sessions?visitor=…` lists a visitor's past
  chats (title = first question, date), and `GET /sessions/{id}/messages` returns one chat.
  Only that visitor's chats are returned.
  Check: `curl` lists 2 chats for visitor A, none for visitor B.
- [ ] **A6 Safety pass.** Rate limit per visitor as well as per IP, reject malformed IDs,
  cap stored memory size, confirm the toolset is still read-only.
  Check: `curl` with a bad ID → 400; 31st request in an hour → 429; the tool list shows
  only propertystack tools.

## Part B — Chat UI

Built on today's hand-built chat, not Deep Chat (decided 2026-09-11: the Eve-like parts,
like the progress line, chat list and Stop, are custom either way, and ours already
renders citations and tables).

- [ ] **B1 One chat on every page.** Move the chat out of `master-table.html` into
  `site/js/chat.js` + `site/css/chat.css`, mount it on all 5 pages, same visitor and same
  open chat everywhere. Delete the Deep Chat trial page `site/chat-trial.html`.
  Check: sweep sends a faked question on each page; the chat carries over between pages.
- [x] **B2 Live answers.** _(Done 2026-09-11 on Master Table, tested headless vs local bot: progress lines, partial text, Stop, reload note, fallback to old bot, errors. Also added the 15s "may be waking up" hint from B5.)_ Words appear as they stream; a small grey line shows what the
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
- [x] **B7 Plain-English errors and small annoyances (H5, H6, H8, H10, H11, H14).** _(Done 2026-09-11, tested headless: faked 504/429/502/400 show plain messages; collapse remembered; Enter while busy shows a hint and keeps the text; long answers open at their start; a reader who scrolled up isn't yanked; warm-up words stay in the grey line.)_ Errors say what
  happened and what to do ("The chatbot took too long. Try again." / "You've asked a lot
  this hour, try again in 12 minutes."). New answers scroll to their start, and don't yank
  you if you've scrolled up. Enter while busy shows "Still answering…". The panel remembers
  being collapsed.
  Check: headless with faked 502/504/429 replies shows the plain messages; scroll and
  collapse behave as written.
- [ ] **B6 Cost under each answer, like Eve.** Proxy returns the answer's cost (from
  Hermes' usage numbers); the chat shows it small and grey next to the seconds
  ("12s · $0.002").
  Check: headless with a faked reply shows "12s · $0.002"; `curl` against local Docker
  returns a cost field.

- [ ] **Z1 Hole test suite.** `tooling/qa/chat_holes.py`: one headless test per hole H1–H13
  (faked bot replies, no cost), each printing PASS/FAIL. Run it after every Part B task
  from now on.
  Check: `python3 tooling/qa/chat_holes.py http://localhost:8765` → all PASS.
- [ ] **Z2 Hands-on hole hunt.** Use the chat like a real person on desktop and phone
  size for 15 minutes (odd questions, fast clicking, reloads, bad network). Every new hole
  goes in the table above with a fix task.
  Check: the Holes table has a line dated today saying "hunt done: N new holes".

## Part C — Ship

- [ ] **A8 Drew tries it on localhost, then deploy.** Drew tests the full chat against the
  local Docker bot. After his OK and "Put it on GitHub?": add the Railway volume for
  `HERMES_HOME`, push, redeploy the chatbot and the site.
  Check: live site — chat, reload, open on another page, the chat and memory are still there.
