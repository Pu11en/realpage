# Plan: Gap 1, "who to call" via Deep dive (Software Sellers edition, 2026-09-18)

Decision (Drew): no bulk lookup. When someone clicks Deep dive on a building, the chat finds the
management company, office phone and website for that one building, with sources. Costs credits only when used.
Local only until Drew OKs; edition = Software Sellers (main).

Check: python3 -m pytest -q tooling/qa/fixes_tests/ chatbot/tests
Try: bash tooling/dev.sh
Open: http://localhost:8765

## Tasks
- [ ] T1 Deep dive prompt (site/js/chat-panel.js deepDivePrompt): ask first for "Who to call: management company, office phone, website, and the role to ask for (with a source link for each)", then why now. Both upcoming and sold variants. For recently sold buildings with no buyer (the 24 Texas sales), also ask "who bought it (new owner)" — Gap 4, decided by Drew. Update/add a test.
- [ ] T2 Chat rules (chatbot/hermes-profile/SOUL.md + skills/query-propertystack): for a deep dive, start the answer with a short "Who to call" block; use the building's own data first (officePhone, website, developer), then web search (max ~6 searches); every phone/website must have a source link; if not found, say "not found" and never guess a number. For a recent sale, include "New owner" (from our data, else county/news search, with source).
- [ ] T3 Button label: rows and building pages show "Find who to call" instead of "Deep dive" (same action). Update tests that look for the old label.
- [ ] T4 Local check with the fake-free path: run 3 deep dives on the local chat (1 Texas upcoming, 1 Texas with phone, 1 Arizona sold) and save the answers to docs/plans/gap1-sample-answers.md for Drew. This uses ~3 real AI answers (cents).

## How to try it
1. Open Early Leads, click "Find who to call" on any building.
2. The chat answer starts with "Who to call": company, phone, website, each with a link.
3. On a building with nothing online, it says "not found" instead of making up a number.
