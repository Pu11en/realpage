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
