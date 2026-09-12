# PropertyStack v3 — Chat improvements

Written 2026-09-11. Goal: make the chat feel solid instead of fragile.
Run with: `Do the next unticked task in PLAN-v3.md, then tick it and stop.`

## Done already (2026-09-11)

- [x] **1. Conversation survives leaving the page.** Chat now persists in the
  browser (localStorage): reload, navigate away and back — messages and
  memory stay. "New chat" wipes it. Shipped and verified live.

## Part 1 — Reliability

- [ ] **2.1 Tell the user the chat is "remembering".** Small line under the
  chat ("Conversation saved in this browser · New chat to clear") so saved
  state is never a surprise.
  Check: line visible desktop + phone in headless screenshot.
- [ ] **2.2 Better error recovery.** If the chatbot is unreachable, show a
  clear message with a Retry button that keeps the typed question (already
  partly there — verify the retry keeps conversation order and add a
  "chatbot is waking up" note for slow first answers).
  Check: kill network in headless test, error + retry works.
- [ ] **2.3 Old conversations age out.** If a saved conversation is older
  than 7 days, start fresh instead of restoring something stale.
  Check: unit-testable in headless with a faked old timestamp.

## Part 2 — Feel

- [ ] **3.1 Copy button on answers.** One click copies the bot's answer text.
  Check: headless click, clipboard content matches.
- [ ] **3.2 Suggested follow-ups.** After each answer, show 2-3 clickable
  follow-up chips based on the answer (e.g. after a software list: "which of
  these is biggest?"). Static heuristics first, no model calls.
  Check: chips render and clicking sends the question.

## Part 3 — Bigger (ask Drew before starting, may cost)

- [ ] **4.1 Chat on every page.** The Ask button currently exists only on the
  Master Table. Make it a shared widget on all pages, same saved conversation.
  Check: sweep visits property/software/under-the-hood pages and chats once.
- [ ] **4.2 Streaming answers.** Show words as they arrive instead of waiting
  up to a minute. Needs a change in `chatbot/proxy.py` (streaming) + Railway
  redeploy. Makes the bot feel 10x faster.
  Check: headless chat shows partial text before completion.
- [ ] **4.3 Freshness.** Today the data is baked in at deploy; the bot can't
  know a scrape ran yesterday. Decide later whether worth rebuilding the
  data pipeline to auto-refresh.
