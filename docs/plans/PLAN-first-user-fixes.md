# Plan: first-time-user fixes (from the 5-persona browser-use test, 2026-09-19)

Evidence: tooling/first-user-test/out/1-5.md (avg score 5.2/10). Re-run the test after fixes; target 8/10.
Business repo (landing) edits are done by hand, not in gowork.

## Decisions
- P1 sign-up surprise (Drew: A): say it up front everywhere: "Browse every lead free. A free account unlocks who to call, the agent and your Lead Pack." Buttons read "Get contact (free account)" when signed out. Simpler sign-up box wording. The panel stops re-opening over the list after the visitor closes it (this visit). Landing: remove "no sign-in needed" claims that contradict this.
- P2 confusing controls (Drew: A): remove the "View as" vendor menu; add a small ⓘ with a one-line plain explanation next to "Signal", "Units in play", "Score" (and "Opening soon"); prefix the example chips with the label "Ask the agent:" so they don't read as filters; make each state on the Map clickable (opens Early Leads for that state) and simplify the legend to one key.
- P3 findability (Drew: A): top of Early Leads shows "Covered now: Texas, Arizona. Don't see yours? Ask for it" (link to map.html#request-area). Three always-visible quick filter buttons "New builds" / "Opening soon" / "Recently sold" that filter the list instantly (no account, no agent). Recently sold rows show sale date + buyer visibly.
- P4 front page (Drew: A; business repo, done by hand): one main button everywhere "See the leads free →" (book-a-call stays as a small text link); a subline under the headline "Leads for companies that sell to apartment buildings."; a small trust line "Built by Drew Pullen · Free during early access · No card"; the Lead Pack line and steps say the free account unlocks who to call, the agent and the Lead Pack (no "no sign-in needed" claims).

Check: python3 -m pytest -q tooling/qa/fixes_tests/
Try: bash tooling/dev.sh
Open: http://localhost:8765/index.html

## Tasks (site only; P4 is done by hand in business/)
- [ ] T1 (P1) Signed-out copy: one line at the top of Early Leads "Browse every lead free. A free account unlocks who to call, the agent and your Lead Pack."; signed-out buttons read "Get contact (free account)" and "Download Lead Pack (free account)"; sign-up box text becomes "Make a free account to see who to call. Takes 20 seconds with Google or email." Tests.
- [ ] T2 (P1) Once a visitor closes the agent panel, nothing re-opens it on its own for the rest of the visit (only their own clicks do). Building pages must not show a phone that Early Leads hides: make contact display consistent (show known phones everywhere, or nowhere). Tests.
- [ ] T3 (P2) Remove the "View as" vendor menu and its code; add ⓘ one-line explanations for Signal, Units in play, Score, Opening soon; prefix example chips with "Ask the agent:". Tests.
- [ ] T4 (P2) Map: each covered state is clickable (opens index.html?area=<state>); one simple legend. Tests.
- [ ] T5 (P3) Top of Early Leads: "Covered now: Texas, Arizona. Don't see yours? Ask for it" (map.html#request-area); three always-visible quick buttons New builds / Opening soon / Recently sold that filter instantly without the agent; Recently sold rows show sale date and buyer visibly. Tests.
- [ ] T6 Re-run the 5-persona test (~/.venvs/bu/bin/python tooling/first-user-test/run.py) against a LOCAL copy is not possible (it uses the live site) — instead save before/after screenshots of Early Leads, Map and a building page (desktop + phone) to docs/plans/first-user-fixes-shots/ for Drew.

## How to try it
1. Early Leads says up front what's free and what needs a free account.
2. "Recently sold" is one click; Arizona sales show the buyer.
3. No "View as" menu; the ⓘ explains each number; clicking Texas on the map opens its leads.
