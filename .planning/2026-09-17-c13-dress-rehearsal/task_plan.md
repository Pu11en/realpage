# Task Plan: C13 dress rehearsal and recovery card

## Goal
Prove the case-study service can process, export, and recover through the local HTTP stack, then leave concise interview instructions and reproducible evidence.

## Next Step
Repeat the rehearsal against the containerized local stack, then run all required tests and record evidence.

## Current Phase
Phase 3

## Phases

### Phase 1: Requirements & Discovery
- [x] Read the C13 requirements and prior progress
- [x] Inspect the service, browser tests, fixtures, and current README
- [x] Document findings
- **Status:** complete

### Phase 2: Rehearsal tooling and docs
- [x] Add a repeatable local HTTP rehearsal
- [x] Expand the README with run/export/recovery steps
- [x] Write a one-page interview card
- **Status:** complete

### Phase 3: Full rehearsal
- [x] Run both goldens and a 12-record batch through the Python HTTP service
- [x] Parse configured-mode, offline-mode, and malformed-middle exports
- [x] Repeat the Python-service rehearsal twice
- [ ] Repeat the full rehearsal against the containerized local stack
- **Status:** in_progress

### Phase 4: Verification
- [ ] Run the plan Check command and project checks
- [ ] Record commands and actual results in the canonical progress log
- **Status:** pending

### Phase 5: Delivery
- [ ] Add C13 decision-log entry
- [ ] Tick C13, commit all work, and leave the worktree clean
- **Status:** pending

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| Rehearse over the HTTP API with the actual web service | Exercises the same service boundary as the demo without requiring an authorized live-model call. |
| Use the first 12 practice records as the rehearsal batch | The actual 12 interview hold-outs are not stored in the repository; the workbench remains ready for arbitrary live JSONL. |
| Treat configured mode without credentials as a required template fallback | It proves graceful recovery and obeys the prohibition on new keys or paid calls. |

## Errors Encountered
| Error | Resolution |
|-------|------------|
| `resolve-plan-dir.sh` was not executable | Invoked the skill scripts through `bash`. |
| First rehearsal test rejected the `none` engine on a consent-suppressed practice row | Allowed the deterministic no-send engine while continuing to reject any model/unknown engine. |
