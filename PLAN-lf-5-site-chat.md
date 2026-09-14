# PropertyStack lead finder, part 5: site and chat for any area

Part of the lead finder. **Read the rules in `PLAN-lead-finder.md` first** (area-agnostic: no place
names in code; Plano is never rerun; never guess facts; SearXNG first, Jina fallback; localhost only,
no push). **NOT approved to run yet.** Starts after part 1 is merged; can run **at the same time as parts 2, 3 and 4**. Built on the sample area; real data arrives in part 6.

Run with: `Do the next unticked task in PLAN-lf-5-site-chat.md, then tick it and stop.`
Check: `bash tooling/qa/check-lead-finder.sh`
Try: `bash tooling/dev.sh`
Open: http://localhost:8765 → Early Leads

## How to try it (30 seconds)
1. Early Leads has a row of area buttons (Plano–Richardson plus the sample area while testing); each button shows its own table; the sidebar area dropdown is gone.
2. In the sample area, pick a city in the filter: only that city's leads show; planned projects say "Planned (not permitted yet)".
3. Ask the chat about a sample-area lead: it answers, and its deep dive works.

## Tasks

- [ ] **5.1 Build every area.** `site/data/build_data.py` builds each area folder under
  `propertystack/data/` from the part-1 lead format (sample area only when a test flag is set, never
  in the real build). Plano–Richardson unchanged. Tests. Commit.
- [ ] **5.2 Area buttons.** Early Leads: one button per area, each its own table; remove the
  sidebar area dropdown. Check passes. Commit.
- [ ] **5.3 City filter + labels.** State areas get a city filter above the table; rows show
  "Planned (not permitted yet)", "Opens: not public yet", "Sold <date>" and the why line. Commit.
- [ ] **5.4 Chat knows every area.** The chatbot loads every area's leads; `SOUL.md` stops naming one
  county; deep dives work for a new area (links incl. 📋 Agenda when present). Rebuild with
  `bash tooling/dev.sh`; run `tooling/qa/check-answers.sh`. Commit.
