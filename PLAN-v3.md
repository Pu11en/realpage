# PropertyStack v3 — Chat improvements

Written 2026-09-11. Goal: make the chat feel solid instead of fragile.
Run with: `Do the next unticked task in PLAN-v3.md, then tick it and stop.`
Check: `python3 tooling/qa/sweep.py http://localhost:8765` (plus the task's own Check line below)

## Done already (2026-09-11)

- [x] **1. Conversation survives leaving the page.** Chat now persists in the
  browser (localStorage): reload, navigate away and back — messages and
  memory stay. "New chat" wipes it. Shipped and verified live.

## How to check (applies to every task)

- Serve locally: `python3 -m http.server 8765 -d site` → `http://localhost:8765/master-table.html`.
- All chat code lives inline in `site/master-table.html` (the second `<script>` block, ~line 318).
- Headless checks use Playwright with `page.route("**/chat", ...)` to **fake the bot's
  reply** — no real chatbot calls, no cost. Only 4.2 needs the real bot.
- Rule for every new button in chat messages (Retry, Copy, chips): messages are saved as
  raw HTML and re-created on reload, so click handlers must use **one listener on
  `#chat-log`** (event delegation), not per-button listeners — otherwise buttons go dead
  after a reload.

## Deep Chat decision (added 2026-09-11, see `CHAT-OPEN-SOURCE-OPTIONS.md` on main)

Checked against deepchat.dev docs: Deep Chat (MIT web component) **does** ship saved
conversations (`browserStorage`), streaming, suggestion buttons (HTML with
`deep-chat-suggestion-button`), and it would drop onto every page easily. It does **not**
ship a copy button, a Retry button, or ageing-out of old chats. Adopting it also means
rebuilding our citation chips and table repair (via `responseInterceptor` returning HTML)
and restyling. So it mainly pays off for 4.1 (every page) and 4.2 (streaming), not for the
small fixes.

- [x] **D1 Deep Chat trial page (no change to the real site).** Build
  `site/chat-trial.html` with `<deep-chat>` wired to our chatbot's `/chat` via a `connect`
  handler, `browserStorage` on, citation chips + table repair ported, site colours.
  Check: headless with a faked reply — answer renders with citation chips and a table,
  survives reload, screenshots at 1280 and 390 look on-theme.
- [ ] **D2 Drew decides.** Drew tries `chat-trial.html` next to the Master Table chat on
  localhost. Yes → replace 4.1a/4.1b/4.2b with "swap Master Table to Deep Chat" + "add to
  every page", and redo 2.1–3.2 as Deep Chat settings/add-ons. No → delete the trial page
  and carry on below.

Task 2.0 is done first either way: it fixes a live bug in 5 minutes.

## Part 1 — Reliability (do in this order)

- [x] **2.0 Don't save half-finished messages.** (New — found in code review.) The
  "Thinking..." bubble and error bubbles get saved to localStorage. Reload mid-answer →
  "Thinking..." sits there forever; reload after an error → a dead Retry button. Fix:
  `saveChat()` skips `.typing` and `.error` messages.
  Check: headless — fake a slow reply, reload during "Thinking", confirm no stuck bubble;
  fake a 500, reload, confirm no dead Retry.
- [ ] **2.1 Tell the user the chat is "remembering".** Small line under the chat form
  ("Conversation saved in this browser · New chat to clear") so saved state is never a
  surprise. Must show on the phone full-screen chat too.
  Check: line visible in headless screenshots at 1280 and 390 wide (phone: after tapping Ask).
- [ ] **2.2 Better error recovery.** Verified today: Retry already keeps the question and
  conversation order (removes the error, re-asks). Missing: (a) no time limit in the
  browser — add a ~90s abort with a clear "took too long" message + Retry; (b) the
  "Thinking" note should switch to "Chatbot is waking up, first answer can be slow" after
  ~15s.
  Check: headless — fake a network failure → error + Retry → Retry succeeds with correct
  order; fake a 20s delay → waking-up note appears.
- [ ] **2.3 Old conversations age out.** Nothing is timestamped yet. Save a `savedAt` time
  with the chat; on load, if older than 7 days, clear it and show the empty state.
  Check: headless — write a saved chat with an 8-day-old `savedAt`, load page, empty
  state shows; a 1-day-old one restores.

## Part 2 — Feel

- [ ] **3.1 Copy button on answers.** One click copies the bot's answer as plain text
  (keep the raw answer in a `data-` attribute so the copy is the text, not HTML). Button
  shows "Copied" briefly. Must still work after reload (see delegation rule).
  Check: headless with clipboard permission — click Copy, clipboard matches the faked
  answer; reload, click again, still works.
- [ ] **3.2 Suggested follow-ups.** After each answer, show 2-3 clickable chips picked by
  simple keyword rules (software list → "Which of these is biggest?"; building list →
  "Show their recent sales"; etc.). No model calls. Only the newest answer shows chips.
  Check: headless — faked software answer shows chips; clicking one sends it as a new
  question; reload keeps chips clickable.

## Part 3 — Bigger (ask Drew before starting, may cost)

- [ ] **4.1a Move chat into its own files (no visible change).** (New — 4.1 was too big
  for one task.) Move the chat JS/CSS/HTML out of `master-table.html` into
  `site/js/chat.js` + `site/css/chat.css`; the script builds the panel itself. Master
  Table must look and behave exactly as before.
  Check: headless before/after screenshots of Master Table at 1280 and 390 match; a faked
  chat round-trip works.
- [ ] **4.1b Chat on every page.** Add the shared chat (plus the marked/DOMPurify
  scripts) to index, property, software-share and under-the-hood. On pages without the
  side panel, use the floating Ask button everywhere. Same saved conversation across
  pages.
  Check: sweep visits every page, sends a faked question on each, and the conversation
  from one page shows up on the next.
- [ ] **4.2a Streaming in the chatbot proxy.** 💲 `chatbot/proxy.py` currently asks
  Hermes with `"stream": False`. Add a streaming reply (Server-Sent Events), keep the old
  non-streaming reply working so the live site doesn't break. Needs Railway redeploy —
  ask Drew first (GitHub-last rule).
  Check: `curl -N` against the proxy (local Docker) shows text arriving in pieces.
- [ ] **4.2b Streaming in the chat panel.** Show words as they arrive; fall back to the
  old wait-for-everything reply if streaming fails.
  Check: headless with a faked streamed reply shows partial text before completion.
- [ ] **4.3 Freshness.** Today the data is baked in at deploy; the bot can't know a
  scrape ran yesterday. Decision only, no build: ask Drew whether it's worth
  auto-refreshing the data.
