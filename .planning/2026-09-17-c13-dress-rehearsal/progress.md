# Progress Log

## Session: 2026-09-17

### Current Status
- **Phase:** Complete
- **Started:** 2026-09-17

### Actions Taken
- Read the full build plan and canonical progress log.
- Confirmed C13 is the only unchecked task.
- Inspected the web service, browser/export tests, sample and practice data, and existing operating README.
- Chose an HTTP rehearsal that makes no live model call and uses a 12-record practice slice because the live hold-outs are not stored here.
- Added the repeatable HTTP rehearsal client, its focused test, expanded operating/recovery README, interview card, and decision-log entry.
- Ran the full rehearsal twice against a credential-free local Python service; each run checked 31 results across five exports (2 configured goldens, 12 configured practice rows, 2 offline goldens, 12 offline practice rows, and 3 rows with malformed JSON in the middle).
- Reparsed all 62 exported results and confirmed every object had only `next_message` and `next_action`.
- Built the real slim container and repeated the full five-case rehearsal twice against it; both runs checked 31 results successfully, health returned OK, and the runtime user was `casestudy`.
- Ran the complete case-study suite (223 passed), related project suites (254 passed), Python compile, JavaScript syntax, and whitespace checks.
- Committed the implementation as `320e981`, then ticked C13 and recorded the final evidence in the canonical progress log.

### Test Results
| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| Initial worktree | No pre-existing task changes | Clean before planning files were initialized | pass |
| Focused rehearsal test | Full five-case HTTP rehearsal passes | 1 passed | pass |
| Rehearsal run 1 | Five exports parse with counts 2/12/2/12/3 | 31 results checked; all passed | pass |
| Rehearsal run 2 | Five exports parse with counts 2/12/2/12/3 | 31 results checked; all passed | pass |
| Container build | Deployment image builds with current source | Image `cranesignal-case-study-c13` built | pass |
| Container rehearsal runs 1 and 2 | Five exports and 31 results pass per run | Both runs passed; health OK; non-root user `casestudy` | pass |
| Plan check | Complete case-study suite passes | 223 passed in 8.04s | pass |
| Related project tests | Existing site/library/fixes checks pass | 254 passed in 4.60s | pass |
| Static checks | Python, JavaScript, and diff checks pass | All passed | pass |

### Errors
| Error | Resolution |
|-------|------------|
| `resolve-plan-dir.sh: Permission denied` | Ran skill shell scripts using `bash`. |
| Rehearsal test expected every record to use `template`, but a no-consent row correctly used engine `none` | Updated the assertion to accept deterministic no-send outcomes and still reject model/unknown engines. |
