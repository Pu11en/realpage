# CraneSignal agent: one-tap "Find contact" on leads with no contact

Goal: A sales rep never has to type the next step: every lead in a chat lead list shows a phone, a link, or a 🔍 Find contact link that sends the deep dive in one tap.
Done when: The Check tests pass and a local Playwright run of "give me top leads any area" shows every lead line with a phone, link or 🔍 Find contact link, and clicking one sends "Deep dive on …" and gets an answer (screenshot saved to tooling/qa/shots/find-contact.png).

Written 2026-09-15 (thread 1549506016125911081, Drew). In a lead list, a lead with no phone or
link currently ends with plain text "ask me for a deep dive", so a sales rep has to type the
next question. Drew wants every lead to show the rep exactly what to do: a phone/link, or a
clickable **🔍 Find contact** link *inside the chat answer* that sends "Deep dive on <name>,
<city>" for them. The #1 lead also gets one quick web lookup for a phone/website when it has
none. Localhost only; **never push** (Drew pushes after trying it). Do not touch AI Visibility.

Run with: `Do the next unticked task in PLAN-find-contact-link.md, then tick it and stop.`
Check: `python3 -m pytest -q chatbot/tests tooling/qa/fixes_tests/test_h4_grounded_answers.py tooling/qa/fixes_tests/test_find_contact.py`
Try: `bash tooling/dev.sh`
Open: http://localhost:8765 → Ask (no sign-in locally)

## How to try it (30 seconds)
1. Open http://localhost:8765, click Ask, type "give me top leads any area".
2. Every lead line shows a 📞 phone and/or a link, or a **🔍 Find contact** link.
3. Click a **🔍 Find contact** link: the chat sends "Deep dive on <that building>" by itself and the deep dive answer appears.

## Tasks

- [x] **F1 Agent rule + its tests.** In `chatbot/hermes-profile/SOUL.md` (lead list section),
  replace the "ask me for a deep dive" ending with
  `[🔍 Find contact](#ask:Deep dive on <name>, <city>)`, and add: if the **#1** lead has no
  `office_phone`, do one `ps_web_search` for its phone or website (only for #1, never more) and
  show it only if a result actually names that building. Make `chatbot/linkfix.py` leave `#ask:`
  links untouched while still stripping fake `https://` links. Add
  `tooling/qa/fixes_tests/test_find_contact.py` (offline) checking the SOUL rule and the linkfix
  behaviour. Run Check. Commit.
- [x] **F2 Clickable in the chat.** In `chatbot/branding/loader.js` (runs inside Open WebUI),
  catch clicks on links whose href starts with `#ask:`, put the decoded text in the chat input
  and send it (same way the site's deep-dive buttons send a prompt); no page jump or navigation.
  Keep existing loader behaviour. Add a test to `test_find_contact.py` that loader.js has the
  `a[href^="#ask:"]` handler. Run Check. Commit.
- [x] **F3 Try it for real, locally.** Start `bash tooling/dev.sh`, then with Playwright on
  http://localhost:8765: ask "give me top leads any area", confirm every lead line has a phone,
  a link or a 🔍 Find contact link, click one Find contact link and confirm a "Deep dive on …"
  message is sent and a deep-dive answer comes back. Save a screenshot to
  `tooling/qa/shots/find-contact.png` and write the result in `PLAN-find-contact-link.progress.md`.
  Stop the stack. Commit. Do not push.
