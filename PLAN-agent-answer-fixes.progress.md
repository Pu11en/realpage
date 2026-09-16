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
