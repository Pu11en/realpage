# Plan: first-time-user fixes (from the 5-persona browser-use test, 2026-09-19)

Evidence: tooling/first-user-test/out/1-5.md (avg score 5.2/10). Re-run the test after fixes; target 8/10.
Business repo (landing) edits are done by hand, not in gowork.

## Decisions
- P1 sign-up surprise (Drew: A): say it up front everywhere: "Browse every lead free. A free account unlocks who to call, the agent and your Lead Pack." Buttons read "Get contact (free account)" when signed out. Simpler sign-up box wording. The panel stops re-opening over the list after the visitor closes it (this visit). Landing: remove "no sign-in needed" claims that contradict this.
- P2 confusing controls (Drew: A): remove the "View as" vendor menu; add a small ⓘ with a one-line plain explanation next to "Signal", "Units in play", "Score" (and "Opening soon"); prefix the example chips with the label "Ask the agent:" so they don't read as filters; make each state on the Map clickable (opens Early Leads for that state) and simplify the legend to one key.
- P3 findability (Drew: A): top of Early Leads shows "Covered now: Texas, Arizona. Don't see yours? Ask for it" (link to map.html#request-area). Three always-visible quick filter buttons "New builds" / "Opening soon" / "Recently sold" that filter the list instantly (no account, no agent). Recently sold rows show sale date + buyer visibly.
