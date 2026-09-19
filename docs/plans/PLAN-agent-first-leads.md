# Plan: agent-first Early Leads (Software Sellers edition, 2026-09-18)

Decision (Drew): the value comes from the agent; Early Leads shows there's real data and gently steers
people to the agent without saying "don't use the filters".

Check: python3 -m pytest -q tooling/qa/fixes_tests/
Try: bash tooling/dev.sh
Open: http://localhost:8765/index.html

## Tasks
- [ ] T1 Top of the filter area on Early Leads: a wide search bar, placeholder "Describe the leads you want…". Enter sends the text to the agent panel (opens it, sends automatically; signed-out visitors see "Make a free account" first and the question sends after sign-up). Reuse the Get-contact send path from PLAN-gap1 T3.
- [ ] T2 Under the bar, 3 example chips built from the current state/region (e.g. "Dallas buildings opening in 2027", "Recently sold, 200+ units", "Not on any software yet near Austin"); a click sends that chip to the agent.
- [ ] T3 Fold the existing dropdowns (signal, city, software, sort, "hide properties already on my software") and the plain "Search property" box under a small "Filters" toggle button, closed by default; state and region pills stay visible. Filtering must still work exactly as before when opened.
- [ ] T4 Phone width (<900px): bar, chips and Filters button stack cleanly; screenshot desktop + phone for Drew. Tests for T1-T3.

## How to try it
1. Early Leads shows a big "Describe the leads you want…" bar with example chips; the dropdowns are hidden under "Filters".
2. Type "Dallas buildings opening next year" and press enter: the agent answers on the side.
3. Click "Filters": the old dropdowns appear and still work.
