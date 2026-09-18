# Progress Log

## Session: 2026-09-17

### Current Status
- **Phase:** 3 - Full rehearsal
- **Started:** 2026-09-17

### Actions Taken
- Read the full build plan and canonical progress log.
- Confirmed C13 is the only unchecked task.
- Inspected the web service, browser/export tests, sample and practice data, and existing operating README.
- Chose an HTTP rehearsal that makes no live model call and uses a 12-record practice slice because the live hold-outs are not stored here.
- Added the repeatable HTTP rehearsal client, its focused test, expanded operating/recovery README, interview card, and decision-log entry.
- Ran the full rehearsal twice against a credential-free local Python service; each run checked 31 results across five exports (2 configured goldens, 12 configured practice rows, 2 offline goldens, 12 offline practice rows, and 3 rows with malformed JSON in the middle).
- Reparsed all 62 exported results and confirmed every object had only `next_message` and `next_action`.

### Test Results
| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| Initial worktree | No pre-existing task changes | Clean before planning files were initialized | pass |
| Focused rehearsal test | Full five-case HTTP rehearsal passes | 1 passed | pass |
| Rehearsal run 1 | Five exports parse with counts 2/12/2/12/3 | 31 results checked; all passed | pass |
| Rehearsal run 2 | Five exports parse with counts 2/12/2/12/3 | 31 results checked; all passed | pass |

### Errors
| Error | Resolution |
|-------|------------|
| `resolve-plan-dir.sh: Permission denied` | Ran skill shell scripts using `bash`. |
| Rehearsal test expected every record to use `template`, but a no-consent row correctly used engine `none` | Updated the assertion to accept deterministic no-send outcomes and still reject model/unknown engines. |
