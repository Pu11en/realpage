# Task Plan: T9 Landing Summary

## Goal
Make the marketing landing page show the same data-driven summary as the app, refresh it hourly with a last-good fallback, remove state coverage claims, and prove the behavior offline.

## Next Step
Commit the completed T9 plan record and verify both repositories are clean.

## Current Phase
Phase 1

## Phases

### Phase 1: Requirements & Discovery
- [x] Understand user intent
- [x] Identify constraints
- [x] Document in findings.md
- **Status:** complete

### Phase 2: Planning & Structure
- [x] Define approach
- [x] Create project structure
- **Status:** complete

### Phase 3: Implementation
- [x] Execute the plan
- [x] Write to files before executing
- **Status:** complete

### Phase 4: Testing & Verification
- [x] Verify requirements met
- [x] Document test results
- **Status:** complete

### Phase 5: Delivery
- [x] Review outputs
- [x] Deliver to user
- **Status:** complete

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| Work only on T9 | The build-worker contract forbids starting the next task. |
| Test summary fetching without live network | T9 explicitly requires a fake-summary test and reliable offline checks. |
| Keep the existing landing layout and add one concise hero proof line | The redesign audit found no T9-scoped reason for a broader visual rewrite. |
| Cache validated JSON beside the signups volume | Railway already persists that directory, giving the last good summary survival across process restarts. |
| Use the app's existing generic hero copy only when no valid live or cached summary has ever existed | A first boot should remain readable even if the app endpoint is temporarily unavailable. |
| Keep implementation and plan records in separate local commits | The landing page is a separate local Git repository nested outside the product repo's tracking. |

## Errors Encountered
| Error | Resolution |
|-------|------------|
| `init-session.sh` was not executable | Invoked the installed helper through `bash` without modifying the skill. |
| Planned `business/marketing/landing` path is absent from this outer worktree | Locate the nested business repo before editing; do not invent a replacement. |
| First combined implementation patch missed two exact sample-building lines | No files changed; inspect the precise table markup and apply smaller targeted patches. |
| First offline landing run passed 51/52 checks; CTA assertion still expected the old button copy and old `/map.html` destination | Updated the existing CTA test to recognize “See the leads free” and the current `/index.html` destination. |
