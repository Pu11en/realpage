# Task Plan: CraneSignal human release gate

## Goal
Produce one clean localhost release candidate, remove known trust and safety blockers, and require a real first time human test before any GitHub push.

## Next Step
Ask Drew whether to run the eight preparation tasks through GPT 5.6 Terra or in this normal session.

## Current Phase
Phase 2

## Phases

### Phase 1: Requirements & Discovery
- [x] Understand user intent
- [x] Identify constraints
- [x] Document in findings.md
- **Status:** complete

### Phase 2: Planning & Structure
- [x] Define the preparation loop and real human release gate
- [x] Write a small task per outcome in PLAN-human-release-gate.md
- [ ] Record Drew's execution choice
- **Status:** in_progress

### Phase 3: Preparation implementation
- [ ] Integrate the completed local branches
- [ ] Correct recruiter proof and known answer failures
- [ ] Close the two container findings
- [ ] Build an isolated sign in enabled preview
- [ ] Run an automated novice dry run
- **Status:** pending

### Phase 4: Human verification
- [ ] Drew tests with a fresh account and his own words
- [ ] Fix and retest every release blocking observation
- [ ] Verify the exact tested commit is clean and all checks pass
- **Status:** pending

### Phase 5: Release decision
- [ ] State ready to push only if every human and automated gate passes
- [ ] Ask Drew whether to put the exact tested commit on GitHub
- **Status:** pending

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| Human test is a hard release gate | Automated browser and cached answer checks do not prove first time comprehension or reasonable use. |
| Drew uses a fresh isolated account | Existing history and familiarity would hide onboarding and sign in problems. |
| One combined candidate precedes testing | Testing separate branches cannot validate the commit that would be published. |
| No paid calls in preparation | Saved evidence and deterministic fixtures are enough to prepare cheaply; the real human questions are the only necessary live sample. |
| No GitHub work before the gate | Global project rule and Drew's request both require localhost approval first. |

## Errors Encountered
| Error | Resolution |
|-------|------------|
