# Version 1 — what "fully working" means

Everything below already runs locally; the list is the whole v1, so we both know exactly what "done" is.

## ✅ The dashboards (the data side)

- **Master Table**: every property, every vendor, searchable, sortable, filterable, CSV export.
- **Software Share**: which software runs where, with share charts per vendor.
- **Under the Hood**: the evidence behind the data — sources, confidence, freshness.
- **Property pages**: one page per building with its vendors, reviews and history.
- All of it built from public evidence only (reviews, Reddit, news, filings), every claim citable.

## ✅ The AI chat (the ask-anything side)

- **Ask panel on every page**: click Ask (or the Chat tab) and the chat slides in beside the data — docked, nothing covered, full-screen on phone.
- **Real answers with citations**: it checks the live data first, then answers with sources, e.g. "Which vendor runs the most buildings?"
- **Memory in a conversation**: follow-ups like "and what year was the biggest one built?" work.
- **Chat history survives**: switch tabs or reload, the panel and conversation stay.
- **One assistant, no model picker**, no settings clutter.
- **Sign-in with Google** (your account), or no sign-in at all in local dev mode.

## ✅ Safety and running gear

- **$3/day spend cap** per user through our proxy, so nobody can run up a bill.
- **One command to start it all locally**: `bash tooling/dev.sh` → site, chat app and bot all up.
- **Automated checks**: a sweep that clicks every button, filter and page at desktop/tablet/phone widths, plus chat-panel tests — all green.

## ⬜ Not in v1 (later)

- Going live on Railway with one address (started, needs your domain decision).
- Multi-user admin screen, usage dashboards, anything password-managed.
- Design polish pass (you said you'd do that yourself).

## ⚠️ One honest caveat

- The local site server can die when my session restarts — if the page suddenly won't load, tell me and I'll bring it back up in seconds (or run `bash tooling/dev.sh` yourself).
