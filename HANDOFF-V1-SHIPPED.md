# HANDOFF — PropertyStack v1 is shipped (2026-09-10)

Read this first if you're starting the session after v1. It replaces nothing: `HANDOFF.md` is still
the repo bootstrap, and `PLAN-v1.md` is the v1 spec.

## Status in one line
v1 is done. All 10 build tasks in `PLAN-v1.md` are ticked, and the 5-point acceptance test passed on
the live site (auto-deploy, 204-building data, chatbot answers with citations, contact info on leads,
all 5 pages and click-throughs). **Don't keep building v1. The next session starts v2 planning.**

## What's live
| Thing | Where |
|---|---|
| Site (5 pages, static HTML/CSS/JS) | https://propertystack-production.up.railway.app, source in `site/` |
| Chatbot (Hermes + DeepSeek v4 flash, read-only) | https://propertystack-chatbot-production.up.railway.app/chat, source in `chatbot/` (see `chatbot/README.md`) |
| Data | `propertystack/data/plano-richardson/*.csv` → `python3 site/data/build_data.py` → `site/data/*.json` |
| Deploy | Push to `main` and Railway rebuilds both services (~30s for the site, a few minutes for the chatbot) |
| QA | `tooling/qa/sweep.py` (Playwright sweep, 3 widths, optional `--chat`); plan in `site/QA-PLAN.md`, bugs in `site/QA-BUGS.md` |

## Built after the core v1 tasks (same day)
- Page 2 chat panel: table ~2/3, chat ~1/3, collapsible; markdown via marked + DOMPurify; citation chips.
- Phones: a floating "Ask" button opens the chat full-screen.
- Chat memory within one conversation: the page sends its last 10 messages as `history`, and
  `proxy.py` forwards them. Nothing is kept across page reloads or stored on the server.
- Phone and tablet: the sidebar becomes a top bar, and wide tables scroll inside their own box.
- The property page Back link works when the page is opened directly. Two cut-off website URLs are fixed.

## Known issues / left open
- The 23Hundred @ Ridgeview website in the data is dead (404). Fix it at the next data refresh.
- The model sometimes writes tables without the `|---|` row. The page repairs this client-side
  (`repairTables` in `site/master-table.html`); a prompt tweak in `chatbot/hermes-profile/SOUL.md`
  would fix it at the source.
- There's no "New chat" button; reloading the page clears the chat.
- The chatbot allows 30 requests/hour per IP and 3 at once. That's fine for demos, but not for real traffic.
- Check `site/QA-BUGS.md` for anything the final QA pass (QA Task 3) left open.

## Candidate v2 directions (not decided — ask Drew)
1. Dallas County part of Richardson (explicitly deferred in PLAN-v1 "What NOT to do").
2. Scheduled data refresh (re-run the pipeline, rebuild JSON, auto-push) plus a "changed since last run" view.
3. Chatbot quality: fix the table format at the source, add a "New chat" button, answer-quality spot checks.
4. Outreach/lead workflow (v1 guardrail: no outreach writing). This needs a scope decision first.
5. Expand beyond Plano/Richardson.

## Rules for the next session
- Drew reads at most 5 sentences per reply and wants each reply to end with one multiple-choice question (4–5 options, recommendation first).
- Keep plans small: one outcome per task, checkbox list, and cut redundant re-checks. Work that runs longer than about 30 minutes gets split into tasks for separate tabs.
- Before any new paid or live model work, ask first.
