# PropertyStack: finish the chat (rules, checker, bold, panel, past chats, redo)

Written 2026-09-13 with Drew, one question at a time (answers saved in
`/home/drewp/main-projects/handoffs/2026-09-13-chat-build-plan-answers.md`). Starting point:
branch `local-test` at 39dd14b -- answers are ~40 words, simple words, sales-only, ADHD shape
always on, 4-line deep dive, no call script unless asked, deep dives saved per building in
`chatbot/proxy.py`. Uses the shared local stack (`tooling/dev.sh`, ports 8765/3000/18080).
Tasks 1-3 all touch the bot's answers: run them in order, never in parallel. Localhost only
until Drew says it's good; no push, no deploy.

Not in this plan (Drew's calls): no Script button and no call scripts; no shared team memory
(own plan later); no speed work; saved deep dives never expire on their own.

Run with: `Do the next unticked task in PLAN-chat-finish.md, then tick it and stop.`
Check: `bash tooling/qa/check-panel.sh && bash tooling/qa/check-readable.sh`
Try: `bash tooling/dev.sh`
Open: http://localhost:8765 → Ask (no sign-in locally)

Bot changes only take effect after `bash tooling/dev.sh` (it rebuilds the image; a plain
`docker restart` keeps the old rules). Talk to the bot with `curl` on
`http://localhost:18080/v1/chat/completions`, headers `Authorization: Bearer
local-trial-key-change-me` and `X-OpenWebUI-User-Email: admin@localhost`, model `hermes-agent`.

## How to try it (30 seconds)
1. Open http://localhost:8765 and click Ask: the chat stays in the side panel, there is no
   "Open in full page" link, and a clear **Past chats** button opens your saved chats inside it.
2. Ask "Which buildings sold recently?": about 40 words, 3 bold bullets, a **Next:** line and
   **Sources:**, with no codes or file names.
3. Click Deep dive on any Early Leads row twice: the second time is instant and says it was
   saved; the chat's own regenerate (↻) button redoes it fresh.

## Tasks

- [x] **T1 Tidy the rulebook.** Rewrite `chatbot/hermes-profile/SOUL.md` into one clean,
  non-contradicting version of today's rules (keep every rule's meaning, delete the leftovers):
  the old "Bottom line" block rule, the "tables for 3+ items" rule, the "`###` headings on long
  answers" rule and "say how many more exist" all fight the ~40-word fixed layouts -- the two
  fixed layouts (deep dive, normal answer) win. Keep: Never-do list, data rules, sources at the
  end in plain words, no codes, only this building's facts, simple words, sales-only, ADHD
  shape. Target under ~110 lines. Update `tooling/qa/check-readable.sh` part 1 to look for the
  `**Next:**` / `**Sources:**` layout instead of "Bottom line". In `PLAN-deep-dive.md`, mark D4
  dropped (replaced by the 4-line deep dive). Rebuild with `bash tooling/dev.sh`, ask the 3
  "How to try it" questions once by curl and read the answers. Commit.
- [x] **T2 Answer checker (💲 a few cents per run).** `tooling/qa/check-answers.sh` (+ a small
  Python helper): with the local stack up (exit with a clear message if it isn't), asks 5 set
  questions in parallel -- "Which buildings sold recently?", "Which 3 leads should I call first
  this week?", "What software does Grand At Legacy West Apartments run?", "Who owns Ellington
  in Plano?", and a "Fresh deep dive on Orchards Market Plaza Senior Apts, Plano (178 units,
  Entrata): who runs it, and why would they switch now?" -- and fails any answer that is over
  60 words (not counting the Sources line), contains a raw code (`SWDNL`, `WDNL`, `hop-portal`,
  `no-portal-link`, `apt_id`, `score_`), a file name (`.csv]`, `.csv`, `.md]`), a call script
  ("opener", "objection") or has no `**` bold at all. Prints each answer with PASS/FAIL. Under
  ~2 minutes. Run it; fix `SOUL.md` until it passes twice in a row. Commit. (Not in the Check
  line because it costs money; run it in any later task that changes answers.)
- [x] **T3 Auto-bold safety net.** In `chatbot/proxy.py`, before an answer leaves the proxy
  (both the streamed and non-streamed paths, and saved deep-dive replays), bold anything the
  bot left plain: phone numbers like `(682) 418-2225` / `469-829-7591`, unit counts
  (`178 units`), month-day-year dates, and the labels `Next:`, `Sources:`, `Call`, `Why now:`,
  `Size:`, `Software:`, `Ask for:`. Never double-bold (`****`), never touch text inside links
  or URLs, never change any other characters. For streaming, hold back only as much text as a
  pattern needs (a phone number split across chunks must still be bolded). Unit tests in
  `chatbot/tests/test_autobold.py` (plain → bolded, already-bold untouched, URL untouched,
  pattern split across two chunks). Rebuild, run `check-answers.sh`. Commit.
- [x] **T4 Panel only, never pop out.** In `site/js/chat-panel.js` (and its CSS), remove the
  header's "Open in full page" link and the load-error "Open it in a new tab" link; the error
  state instead shows "Couldn't load the chat." with a **Try again** button that reloads the
  iframe. Keep the Google sign-in pop-up (Google blocks sign-in inside a frame; it closes by
  itself). Update `tooling/qa/panel_test.py` / `sweep.py` so they assert no full-page/new-tab
  link exists and Try again reloads. Check passes. Commit.
- [x] **T5 Past chats button.** Every chat is already saved per user by Open WebUI; the list
  is hidden because `chatbot/branding/custom.css` squeezes `#sidebar` to width 0, leaving only
  a tiny toggle icon. Make the chat list reachable inside the panel: label the sidebar toggle
  clearly as **Past chats** (big enough to see at 480px wide), and when opened show the saved
  chat list as an overlay over the full panel width, with an obvious way back to the current
  chat (picking a chat or pressing the button again closes it). Only CSS / branding changes
  if at all possible (the site and chat are different origins locally, so the site page can't
  reach into the frame). Rebuild the chat app image if branding is baked in; screenshot the
  panel closed and open to `/tmp/past-chats-*.png` and look at them. Check passes. Commit.
- [x] **T6 Redo a saved deep dive.** In `chatbot/proxy.py`: when Open WebUI's regenerate (↻)
  button is pressed on a saved deep dive, run it fresh and replace the saved copy. Detect it
  with the chat id Open WebUI forwards (`X-OpenWebUI-Chat-Id`, sent because
  `ENABLE_FORWARD_USER_INFO_HEADERS` is on): remember which chat ids were just served a saved
  deep dive for which building; the same chat asking the same deep dive again = redo. Change
  the saved note to say: "Saved deep dive from <date>. Press ↻ to redo it." Keep "Fresh deep
  dive on …" working. No automatic expiry. Unit tests in `chatbot/tests/test_deep_dive_cache.py`
  (first ask saves, second ask in a new chat replays, same chat again redoes, fresh prefix
  redoes). Rebuild; try it once in the real panel. Commit.
- [x] Fix: ok what are things i need to do
- [x] Fix: can i ask you questions here?
