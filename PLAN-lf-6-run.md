# PropertyStack lead finder, part 6: the real run

Part of the lead finder. **Read the rules in `PLAN-lead-finder.md` first** (area-agnostic: no place
names in code; Plano is never rerun; never guess facts; SearXNG first, Jina fallback; localhost only,
no push). **NOT approved to run yet.** Starts only after parts 1-5 are merged into `local-test`. **6.2 stops and waits for Drew's go.**

Run with: `Do the next unticked task in PLAN-lf-6-run.md, then tick it and stop.`
Check: `bash tooling/qa/check-lead-finder.sh`
Try: `bash tooling/dev.sh`
Open: http://localhost:8765 → Early Leads → the new state's button

## How to try it (30 seconds)
1. Early Leads: click the new state's button -- its own table, soonest openings on top.
2. Pick a city in the filter: only that city's leads; each row says why it's a lead.
3. Click ✦ Deep dive on the top lead: address, opening date and real links.

## Tasks

- [ ] **6.1 Wire the chain.** `lead-finder/run.py` runs every step in order (cities → sources →
  permits → details → early signals → sales → software → who to call → score), resumable, on
  the sample area end to end. Tests. Commit.
- [ ] **6.2 Small test run (💲 ~20 searches).** Whole chain on **one city** of the picked state,
  capped at 5 projects. Show Drew the 5 leads in plain words. **Stop -- Drew says go before 6.3.**
- [ ] **6.3 Full state run (💲 ~450 searches) -- only after Drew's go.** Whole state until 150
  projects or the cap (roll into next state if <30); save recipes; spot-check 10 software calls;
  log to `propertystack/runs/`. Commit.
- [ ] **6.4 Fill the site + chat.** Build the site and rebuild the chat with the new area; run the
  Check and `check-answers.sh`. Commit. Tell Drew in plain words it's ready to try.
