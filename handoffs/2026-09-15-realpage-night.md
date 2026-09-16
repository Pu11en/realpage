# Handoff — RealPage / CraneSignal (2026-09-15, ~22:05 CDT)

Previous handoff: `handoffs/2026-09-15-realpage.md` (still accurate for background and decisions).
This one records what changed after it. Thread: 1549610069765918800.

## Shipped tonight (pushed to GitHub, Railway deploying)

`main` and `origin/main` are identical. Tip: `8aba7b6`.

1. **Lead data cleanup redo merged** (`7f9dee8`, `05b35c6`). Main had been left with the BAD cheap
   cleanup (7 Arizona "Unnamed project" rows squashed into one, valid phones blanked). The good
   redo lived only on `gowork/plan-lead-data-quality-redo-20260915-204734`. Merged, conflicts
   resolved in favour of the redo, and the 7 AZ rows restored by hand (`git merge` had kept main's
   deletion). Verified: AZ 279 rows with 9 distinct Unnamed rows, TX 592 rows, Richardson Ridge
   phone `(319) 217-8136`, report says 0 broken phones / 0 duplicates. 35 lead tests pass.
2. **🔍 Find contact** link — was already on main from an earlier session; went out with this push.
3. **55 RealPage product cards** (`2de82c9`) in `02-products/realpage/`, built by
   `tooling/realpage-library/cards.py` from the 2,195-page crawl in `raw/realpage-site/`.
4. **RealPage key-facts sheet** (`8aba7b6`) — `01-company/realpage-key-facts.md`, 66 facts, 67
   realpage.com links, plus `tooling/realpage-library/facts.py`.

The chatbot Dockerfile already copies `01-company` … `09-ai-visibility` into the agent's
`/kb/research`, so 3 and 4 reach the agent with no rule change. SOUL.md was deliberately NOT
touched (the answer-fix build owns it right now).

**Known, still true:** 3 tests in `tooling/qa/fixes_tests/` fail (`test_e1_signin`,
`test_h7_novice_browser_dry_run`, `test_t5_logo_links_home`). They fail identically on the
previously deployed `70bdac8`, so they are stale tests, not a regression from tonight.

## In flight — the four failed answers

Plan `PLAN-agent-answer-fixes.md`, rewritten tonight into five right-sized tasks; a check test file
`tooling/qa/fixes_tests/test_agent_answer_fixes.py` was created so `Check` passes from task one.

Build loop running in worktree
`/home/drewp/.local/state/ccdb/gowork/realpage-plan-agent-answer-fixes-20260915-214243`
(branch `gowork/plan-agent-answer-fixes-20260915-214243`), reporting into this thread.

- [x] A1 offer to check instead of "I don't have that" (Austin)
- [x] A2 right region for sales questions (Dallas–Fort Worth, not Plano-only)
- [x] A3 Reddit claims carry their post link + post count
- [x] A4 RealPage news / lawsuit / funding claims carry a readable link
- [ ] A5 ask the four questions locally with Playwright and save the real answers

**Next session must**: read A5's saved answers, judge them by reading (not by the summary), then
merge that branch into main and push. It is told never to push itself.

## Still open / next

1. Confirm the live agent now answers RealPage product questions from the new cards
   (e.g. "what does RealPage Lumina do?", "what is RealPage Analytics?").
2. Re-ask the four fixed questions on the live agent and update the frozen shipcheck numbers.
3. Build the Under the Hood "Tested with shipcheck" section (`site/under-the-hood.html`,
   `site/data/evals.json`): frozen 36/40, honest open-issues list, shipcheck GitHub link beside the
   build-bot link.
4. Prepare the public shipcheck repo in `/home/drewp/main-projects/drew's eval`, then ask Drew the
   single yes/no "Put it on GitHub?".
5. Backlog: sweep SOUL.md for other over-strict rules; 182 lead rows with no unit count; 11 invalid
   links; DOJ rent-pricing case is absent from RealPage's own site (a finding for AI Visibility —
   the 15 hand-checked facts cover it from outside sources).

## Other sessions tonight

- Thread 1549501531273961543 ("realpage ai visibility") built the cards + facts sheet.
- Thread 1549506016125911081 is the shipcheck thread the first handoff came from.

## Agreed with Drew (end of night)

Leave the answer-fixes loop running. When it reports, Drew says "check it"; then read A5's four
saved answers, merge `gowork/plan-agent-answer-fixes-20260915-214243` into `main` and push.
Drew then opens a fresh session for the to-do list.

## Done after that: the four answer fixes are live

A5 finished and I read its four captured answers (Austin offers a `🔍 Check` link as the Next line;
DFW returns Arlington/Tarrant rows and names the region; the Entrata answer says "from 1 Reddit
post" and carries the real reddit.com link; the lawsuit answer carries the justice.gov release).
Branch `gowork/plan-agent-answer-fixes-20260915-214243` merged into `main` and pushed (`7b0f404`).
62 checks pass. Frozen shipcheck numbers still need re-asking those four questions on the LIVE agent.
