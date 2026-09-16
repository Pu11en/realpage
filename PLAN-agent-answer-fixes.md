# CraneSignal agent: fix the four answers Drew failed

Goal: the four question types Drew graded as fails come back good: an offer to go check when our
data doesn't know, real Reddit post links when asked about Reddit, links on RealPage news, and
the right area for a "just sold in Dallas–Fort Worth" question.
Done when: the Check tests pass and a local run of the four questions shows the four behaviours.

Written 2026-09-15 (thread 1549506016125911081). From Drew's own grading of the live run:
- **r03** "Any new Austin buildings that haven't picked software yet?" → it said "I don't have
  that" (software is only checked in Plano/Richardson). Drew: *"have it ask person if they want
  to check"* — it should list the Austin buildings and offer to check one now.
- **r04** "Show me buildings that just sold in Dallas–Fort Worth" → it returned Plano-only rows.
- **r24** "Where is RealPage losing customers to Entrata?" → no actual Reddit posts. Drew: *"not
  horrible, but fail"*.
- **r31** "What's going on with the RealPage lawsuit?" → Drew: *"give links too"*.
Localhost only; **never push** (Drew pushes after trying it). Do not touch AI Visibility.

Run with: `Do the next unticked task in PLAN-agent-answer-fixes.md, then tick it and stop.`
Check: `python3 -m pytest -q chatbot/tests tooling/qa/fixes_tests/test_agent_answer_fixes.py`
Try: `bash tooling/dev.sh`
Open: http://localhost:8765 → Ask (no sign-in locally)

## How to try it (30 seconds)
1. Ask "Any new apartment buildings opening in Austin that haven't picked software yet?" — it lists
   Austin buildings and offers to check one building's software now.
2. Ask "Where is RealPage losing customers to Entrata?" — every claim from Reddit carries that post's link.
3. Ask "What's going on with the RealPage lawsuit?" — the answer carries at least one link to read.

## Tasks

Each task is one small change to the agent's rules plus its own check. Do them in order.

- [x] **A1 Offer to check instead of "I don't have that".** In `chatbot/hermes-profile/SOUL.md`:
  when our data can't answer for an area (e.g. software isn't checked outside Plano/Richardson),
  the answer leads with what we DO have (the buildings), says in one short line what isn't checked,
  and ends with an offer to check one now, as a clickable
  `[🔍 Check <building>](#ask:Deep dive on <name>, <city>)`. Never open with "I don't have that"
  when we have rows to show. Add a test for this rule to
  `tooling/qa/fixes_tests/test_agent_answer_fixes.py`. Run Check. Commit.
- [x] **A2 Right area for sales.** In `SOUL.md`: a question naming a region (Dallas–Fort Worth,
  Houston, Austin, San Antonio) must filter `state_leads` by that `region` column, never fall back
  to the Plano/Richardson `leads` tables, and must say the region it used in the first line.
  Add its test to the same file. Run Check. Commit.
- [x] **A3 Reddit claims carry their post link.** In `SOUL.md` and the `query-propertystack`
  skill notes: any claim drawn from `street_talk` must show that row's `url` as a link on the same
  line, and the answer must say how many posts it is based on (e.g. "from 2 posts"). If no post
  link exists, the claim is left out. Add its test. Run Check. Commit.
- [x] **A4 RealPage news carries a link.** In `SOUL.md`: RealPage news, lawsuit or funding claims
  must include at least one readable link (from the research folders or a page read this turn);
  if none exists, say plainly that the summary has no link yet. Add its test. Run Check. Commit.
- [x] **A5 Ask the four questions locally and save the answers.** Start `bash tooling/dev.sh`,
  ask the four questions from "How to try it" with Playwright, paste the four real answers into
  `PLAN-agent-answer-fixes.progress.md`, and say for each whether the behaviour is there.
  Stop the stack. If one still fails, note exactly what it said and leave A5 unticked. Run Check.
  Commit. Do not push.
