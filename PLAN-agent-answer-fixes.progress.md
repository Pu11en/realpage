# Progress: agent answer fixes

## A1 Offer to check instead of "I don't have that" — done 2026-09-15
- Sharpened the SOUL.md rule: when data has rows but not the detail (e.g. Austin
  software), lead with the buildings, one line saying software isn't checked there,
  end with `[🔍 Check <building>](#ask:Deep dive on <name>, <city>)` for the #1 building.
  Scoped "I don't have that" to no-matching-rows-at-all only.
- Tests: 3 new tests in tooling/qa/fixes_tests/test_agent_answer_fixes.py.
- Check: `python3 -m pytest -q chatbot/tests tooling/qa/fixes_tests/test_agent_answer_fixes.py` → 40 passed.
- Commit: see `git log` (A1 commit). Note: the previous attempt died on a bad model id ("each"), nothing was lost.
- Open: real live-answer check happens in A5.

## A2 Right area for sales — done 2026-09-15
- New SOUL.md rule "Right area for sales and leads": a question naming a region
  (Dallas–Fort Worth, Houston, Austin, San Antonio, any `region` value) filters
  `state_leads` by `region` (+ `status='Sold'` for sales), never falls back to the
  Plano/Richardson `leads`/`sales`/`master` tables, and names the region in the
  first line. No rows → say so and offer the nearest region.
- Tests: 3 new A2 tests in tooling/qa/fixes_tests/test_agent_answer_fixes.py.
- Check: `python3 -m pytest -q chatbot/tests tooling/qa/fixes_tests/test_agent_answer_fixes.py` → 43 passed.
- Note: the previous attempt died on a bad model id ("each") before doing anything; redone from scratch.
- Open: live answer check happens in A5.

## A3 Reddit claims carry their post link — done 2026-09-15
- New SOUL.md rule "Reddit claims carry their post link": every claim from
  `street_talk` shows that row's `url` as a link on the same line, the query
  always selects `url`, the first line says how many posts it is based on
  ("From 2 posts"), a row without a real thread link is left out, and posts are
  framed as "a Reddit user says". Same rule added to the query-propertystack
  skill's street_talk row.
- Checked the data: all 23 saved posts have a real reddit.com/r/ thread link,
  so the strict rule never empties an answer. A test now guards that.
- Tests: 5 new A3 tests in tooling/qa/fixes_tests/test_agent_answer_fixes.py.
- Check: `python3 -m pytest -q chatbot/tests tooling/qa/fixes_tests/test_agent_answer_fixes.py` → 48 passed.
- Commit: 398ec5d. Note: the previous attempt died on a bad model id ("each") before doing anything; redone from scratch.
- Open: live answer check happens in A5.

## A4 RealPage news carries a link — done 2026-09-15
- New SOUL.md rule "RealPage news carries a link": any answer about RealPage
  news, the lawsuit, DOJ case, settlement, funding, layoffs or an acquisition
  must carry at least one readable link (a URL from the research folders read
  this turn, or a page read with ps_web_read), on the same line as the claim
  and repeated on the Sources line. A bare address in research gets `https://`
  in front. No URL anywhere → `**Sources:** RealPage research (no link yet)`,
  never a made-up link.
- Fixed the DOJ timeline research file: its justice.gov press-release address
  had no `https://`, so it wasn't a clickable link. Now it is.
- Tests: 3 new A4 tests (rule present, no-link wording, DOJ timeline has a
  real justice.gov link).
- Check: `python3 -m pytest -q chatbot/tests tooling/qa/fixes_tests/test_agent_answer_fixes.py` → 51 passed.
- Commit: f3c584d. Note: the previous attempt died on a bad model id ("each") before doing anything; redone from scratch.
- Open: live answer check happens in A5.

## A5 Ask the four questions locally — done 2026-09-15
- Ran `bash tooling/dev.sh` (rebuilds the bot with this checkout's SOUL.md), then a
  Playwright script (`tooling/qa/ask_four_live.py`, new) typed each question into the real
  Ask panel on http://localhost:8765 and captured the streamed answer + links. Stack stopped after.
- First run: 3 of 4 right. The Austin answer listed buildings and said "Software isn't checked
  in Austin yet" but ended on a phone-call Next line and had no `🔍 Check` link, because the
  A1 rule said "end with the link" while the layout rule says every answer ends with
  **Next:** + **Sources:**. Fix: the A1 rule now makes the `🔍 Check <building>` link the
  **Next:** line itself. Rebuilt, re-asked the Austin question: link present.
- Check: `python3 -m pytest -q chatbot/tests tooling/qa/fixes_tests/test_agent_answer_fixes.py` → 51 passed.

### 1. "Any new apartment buildings opening in Austin that haven't picked software yet?" — ✅ (after fix)
```
Upcoming in Austin: 3 new buildings, permits filed.
Apartments at 3525 Far West Blvd, Austin -- 115 units, permitted, no open date · abc.austintexas.gov
Apartments at 2610 Hume Pl, Austin -- 142 units, permitted, no open date · abc.austintexas.gov
Apartments at 8700 Shoal Creek Blvd, Austin -- 93 units, permitted, no open date · abc.austintexas.gov
Software isn't checked in Austin yet, so I can't say who's unclaimed.
Next: 🔍 Check Apartments at 3525 Far West Blvd      ← link: #ask:Deep dive on Apartments at 3525 Far West Blvd, Austin
Sources: City permit records · CraneSignal lead ranking
```
Behaviour: lists Austin buildings, one line on what isn't checked, clickable offer to check one. Present.
(First run before the fix: same shape, buildings 7333 Bluff Springs Rd / Belmont / Dessau, but
"Next: Call Belmont Apartments — 348 units, 9 months before it opens." and no Check link.)

### 2. "Show me buildings that just sold in Dallas–Fort Worth" — ✅
```
Sold recently in Dallas–Fort Worth:
The Park At Ashford, Arlington -- 144 units, sold Aug 2025 · tad.org
Bella Vida, Tarrant County -- 84 units, sold May 2025 · 🔍 Find contact
Westland Estates, Tarrant County -- 192 units, sold May 2025 · thelifeatwestlandestates.com
Next: Open Westland Estates' site — new owner, 192 units, no software check yet.
Sources: County sales records · City permits and news
```
Behaviour: DFW rows (Arlington, Tarrant County), region named in the first line, no Plano rows. Present.

### 3. "Where is RealPage losing customers to Entrata?" — ✅
```
From 1 Reddit post: no RealPage-to-Entrata switch in our data.
A manager with ~1,000 units in Texas and California is "considering making the switch from AppFolio to Entrata" (reddit.com)
    ← link: https://www.reddit.com/r/PropertyManagement/comments/1g676mt/seeking_advice_transitioning_from_appfolio_to/
No post names a building or city leaving RealPage for Entrata.
Next: Ask a DFW building that just sold what software it runs — 2-minute call.
Sources: reddit.com · Reddit posts
```
Behaviour: says how many posts, the one Reddit claim carries its real post link on the same
line, and it is honest that no post shows RealPage losing to Entrata. Present.

### 4. "What's going on with the RealPage lawsuit?" — ✅
```
RealPage settled with the DOJ; it must stop sharing competitor rent data.
Aug 2024: DOJ and state AGs sued over rent-pricing data.
Nov 24-25, 2025: proposed settlement -- no real-time competitor data in pricing (justice.gov)
    ← link: https://www.justice.gov/opa/pr/justice-department-requires-realpage-end-sharing-competitively-sensitive-information-and
Mar 26, 2026: settlement entered by the court; DOJ answered comments May 2026.
Next: Read the DOJ release before your next RealPage call -- 2 minutes.
Sources: justice.gov · RealPage research
```
Behaviour: at least one readable link (justice.gov press release). Present.

- Open: nothing. Not pushed (Drew tries it first).

## Next time (from how this build went)
- The AI model name ("each") wasn't available or was misconfigured, which made the first four tasks fail immediately. Test the AI on one quick task first before running a batch of five.
- Once you switched to a working model (fable), everything ran smoothly and finished in 2–4 minutes per task. The task sizes themselves were fine.
- The five tasks had similar goals (add a rule, run a check, save answers). Grouping them into one batch worked well, but catch the model issue earlier so you don't redo the same setup five times.
