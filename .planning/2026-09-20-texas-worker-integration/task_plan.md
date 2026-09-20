# Task Plan: Texas Worker Integration

## Goal
Merge the finished Texas worker branches, verify the integrated result, push the approved work, and summarize what changed.

## Current Phase
Phase 3

## Phases

### Phase 1: Inventory
- [x] Confirm all worker sessions are finished.
- [x] Identify the worker commits to integrate.
- **Status:** complete

### Phase 2: Merge
- [x] Merge the five worker branches into the coordinator branch.
- [x] Resolve conflicts only within the approved worker scope.
- **Status:** complete

### Phase 3: Verify
- [ ] Run the relevant test and lead-data checks.
- [ ] Confirm the worktree is clean.
- **Status:** pending

### Phase 4: Push & Cleanup
- [ ] Push the integrated branch.
- [ ] Release stale claims and close/archive threads where tooling allows.
- [ ] Summarize results for Drew.
- **Status:** pending

## Worker Commits
- `4042f13` Fort Worth audit.
- `aad6506` San Antonio and San Marcos audit.
- `e800cd3` Houston city permit feed audit.
- `8628506` healthy Texas source proof.
- `8e14e31` buyer-facing Texas counts and lead labels.

## Decisions
- Drew explicitly approved pushing after workers finished.
- No GitHub push happens until local merge and verification are complete.
