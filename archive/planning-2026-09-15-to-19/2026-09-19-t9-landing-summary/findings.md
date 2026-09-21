# Findings & Decisions

- T9 is the first unchecked build task.
- The landing source is expected at `business/marketing/landing`, but that nested repo is absent from this gowork checkout.
- Existing handoff notes identify the canonical nested repo as `/home/drewp/main-projects/realpage/business/` and its landing tests as `python3 business/tools/test_landing.py`.
- The outer repo's T8 output is `site/data/summary.json`; the landing server must fetch its deployed equivalent at `https://app.cranesignal.com/data/summary.json`.
- The business source is a separate local-only Git repository. A dedicated worktree and branch now exist at this worker's `business/` path, so T9 can be committed without touching the original checkout.
- The landing server already dynamically renders `/` when a local app URL is selected, so root rendering can consistently inject the summary in both production and local preview.
- The current page explicitly names Texas and Arizona in a coverage sentence and uses `TX` in the hero/sample copy; those claims must be removed for T9.
- The app already defines the exact formatter contract: `Last check Sep 19, 2026: 972 buildings just filed permits, 498 just sold. 1,470 tracked.`
- Design diagnosis: preserve the existing asymmetric job-site hero and CTA flow; add the current counts as a proof line beside the existing proposition. No wider redesign belongs in this task.

## Requirements
-

## Research Findings
-

## Technical Decisions
| Decision | Rationale |
|----------|-----------|

## Issues Encountered
| Issue | Resolution |
|-------|------------|

## Resources
-
