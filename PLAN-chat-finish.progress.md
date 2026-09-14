# Progress: PLAN-chat-finish

## T1 Tidy the rulebook — done 2026-09-13
- Rewrote `chatbot/hermes-profile/SOUL.md` (161 → 124 lines; Never-do list kept word for word): one "two fixed layouts" section (deep dive + normal answer) replaces the tables-for-3+, `###` headings, "say how many more exist" and old Bottom line leftovers.
- `check-readable.sh` part 1 now looks for `**Next:**` / `**Sources:**` (it was failing before: SOUL.md no longer said "Bottom line").
- `PLAN-deep-dive.md`: D4 marked dropped (replaced by the 4-line deep dive).
- Checked: `bash tooling/dev.sh` rebuild, then curl'd "Which buildings sold recently?", "Which 3 leads should I call first this week?", "Deep dive on Orchards Market Plaza Senior Apts, Plano" — all ~40 words, bold, correct layout, plain source names, no codes. Check line passes.
- Open: nothing.

## T2 Answer checker — done 2026-09-13
- New `tooling/qa/check-answers.sh` + `tooling/qa/check_answers.py`: exits with "start the local stack" if the bot is down; asks the 5 set questions in parallel (~55 s); fails >60 words (Sources line and link URLs not counted), raw codes, file names, "opener"/"objection", or no `**` bold; prints each answer with PASS/FAIL.
- First run 3/5: the leads list was 67 words (unit count repeated in each name), and the Grand At Legacy West software answer had no bold at all.
- `SOUL.md` fix: list items use a short name (never repeat the unit count), first line max 10 words, plus a tiny bolded one-fact example. Rebuilt with `tooling/dev.sh`.
- Then 5/5 twice in a row. Check line passes.
- Open: "Which buildings sold recently?" hit 59 words on the second pass — close to the limit; the bot also sometimes skips bold on unit counts/dates (T3's auto-bold will cover that).

## T3 Auto-bold safety net — done 2026-09-13
- New `chatbot/autobold.py`: `bold()` wraps plain phone numbers, "N units", month-day-year dates (Sep 13, 2026 / 9/13/2026) and the labels Next:/Sources:/Why now:/Size:/Software:/Ask for: (plus "Call" at the start of a line or bullet) in `**`. Existing bold, links, bare URLs and `code` are never touched; only `**` is ever added, and running it twice changes nothing.
- `StreamBolder` holds back at most ~40 characters (never splits a pattern, an open `**`, or a link), so a phone split across two chunks is still bolded.
- `chatbot/proxy.py` uses it on all paths: site `/chat` and `/chat/stream`, Open WebUI gateway non-streamed and streamed (SSE lines rewritten; held text sent before finish/[DONE]), and saved deep-dive replays. Dockerfile copies `autobold.py`.
- Checked: `chatbot/tests/test_autobold.py` 13 passed (plain→bold, already-bold untouched, URLs untouched, split chunks, 600 random splits equal whole-text result, gateway SSE rewrite). Rebuilt with `tooling/dev.sh`; `check-answers.sh` 5/5 passed; Check line passes.
- Open: month-year only dates ("July 2026") are not bolded (plan asked for month-day-year).
