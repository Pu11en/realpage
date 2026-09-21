# Masiate: Approved First Collection Pass

Check: python3 -m pytest -q propertystack/skills/lead-finder/tests

## Approved Outcome

Drew approved eight workers and roughly one hour on September 20, 2026; a little
under or over is acceptable. Deliver real sourced property candidates, useful
details on the strongest, a fixed first-pass PDF and explicit coverage gaps.
Stop after this package; another pass requires Drew's next instruction.
This supersedes the full-coverage completion condition for THIS pilot only.
The larger collection plan remains a backlog, not today's required checklist.

## Execution

Use the existing /api/spawn independent-session route with eight isolated git
worktrees, coordinated by thread 1551377360756940940. This is NOT /gowork and
does not change its three-worker limit, shared bot defaults, or running services.
Do not launch or resume the old stopped /gowork run. No additional agents beyond
these eight. Existing configured AI service only; no new provider or purchase.
The shared bot's ten-session limit still applies; record actual running/queued
workers instead of claiming all eight run when only their threads exist.

Start: around 2026-09-21 01:48 UTC (September 20, 8:48 PM Central).
Collection checkpoint: every 10-15 minutes, using per-worker files.
Collection wrap target: 2026-09-21 02:35 UTC.
Review/PDF delivery target: around 2026-09-21 02:45 UTC, flexible for honest checks.
These are targets, not an implemented kill switch or a guarantee of completeness.
Do not spend the hour building a general crawler framework. Use existing readers,
direct official documents, public searches, simple bounded scripts and evidence.

## Eight Independent Assignments

- [ ] Brazos: College Station permits and planning, Bryan planning/permit access, local bids and appropriate property-owner checks.
- [ ] Robertson: Hearne, Franklin, Calvert, Bremond and county project/bid sources.
- [ ] Burleson: Caldwell, Somerville, Snook and county project/bid sources.
- [ ] Grimes: Navasota, other cities, county development and current construction bids.
- [ ] Leon: Buffalo, Centerville, Jewett, Leona, Marquez, Normangee, Oakwood and county sources; verify Texas.
- [ ] Madison: Madisonville, relevant Normangee jurisdiction and county sources.
- [ ] Washington: Brenham, Burton, county project sources and local bids.
- [ ] Statewide: TDLR TABS across all seven counties, then TCEQ or other useful statewide sources if time allows; no local city or CAD crawling.

County workers do not crawl TDLR/TCEQ/TABC/Comptroller statewide services: only the
statewide worker owns those hosts. Workers never edit one another's outputs.
For shared non-government hosts or vendor domains, use an interprocess flock
under the run root, one request at a time and at least two seconds between
requests; respect longer server delays. No login bypass, rotating identities,
payment, supplier signup, agency messages or prospect outreach.
Jina/Brave keys are not verified allowances: no separately billed API calls
unless the existing allowance and no-overage behavior are actually verified.
Existing web tools and direct public documents are the default.

## Output Contract

Run root: /home/drewp/.local/state/cranesignal/masiate/pilot-20260920-2048
Each worker owns only its lowercase lane folder inside that root.
Use atomic checkpoints of records.json, coverage.json and summary.md.
Keep downloaded originals under that lane's evidence/ directory.
Read the exact record contract in masiate-pilot-worker-contract.md.
Mirror useful scripts and sanitized outputs in the worker's own git worktree
and commit there; never push or change main, live data, the site or live agent.
Shared runtime files survive worktree cleanup and are not a public export.

## Coordinator Review

The coordinator alone combines records, retains source IDs/units/phases, checks
shortlisted claims and business contact roles, and produces the PDF plus matching
agent-readable records. The agent-readable file is NOT live-agent integration.
No fixed lead quota, guessed contacts, invented availability or filler entries.
Expired bids and historical projects belong in watchlist/history, not open work.
If nothing qualifies, deliver an honest results/gaps report, not fabricated leads.
Show the exact run date, source dates, status uncertainty and partial coverage.
Finish with counts of source records, distinct projects, shortlisted profiles,
business contacts and unresolved sources; retain cursors for a later approved pass.

## How To Try It

1. Open the PDF and check a property's facts against its linked record.
2. Check the county coverage summary for missing sources and dates.
3. Check that a listed business contact has an evidenced role, not guessed ownership.
