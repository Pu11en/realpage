# Human release gate progress

## 2026-09-15 — H1: one clean release candidate

- Created the local-only `local-release-candidate-human-gate` branch from the Under the Hood work.
- Merged the tested product baseline (`local-test`, commit `99fd6bd`) and completed chat data
  (`gowork/plan-chat-data-20260915-090124`, commit `4a6ce22`) without conflicts.
- `bash tooling/qa/check-fixes.sh` passed: 125 focused checks, three page checks, and seven design
  page checks all passed.
- Attempted the broad `python3 -m pytest -q` suite. It is not a usable all-project command yet:
  its flat module imports collide between separate skills, and the client-map target test cannot
  locate its local `census` helper. The release-specific check above is passing; this existing test
  harness problem remains visible for later repair and does not make the human push gate pass.

## 2026-09-15 — H2: defensible Under the Hood evidence

- Replaced the inferred “passed first try” headline with four dated historical scorecard measures:
  1 of 6 checks passing, 92 of 100 saved answers meeting the rubric, 17 person-reviewed answers,
  and timing from 105 saved answers. The live agent remains the main action and the evidence details
  stay closed until opened.
- Added the saved 2026-09-15 recruiter scorecard to the candidate, so the page rebuilds without an
  old evaluation worktree or any machine-specific paths. It explicitly says the measurement is
  historical, gives the method and sample sizes, and lists why it is not release approval.
- Added four offline H2 regression checks proving the saved scorecard regenerates the public data,
  every headline has a matching sample, the old inferred headline is absent, and public evidence has
  no machine paths.
- Saved the implementation in local commit `bf8a8ed` (`H2: make Under the Hood evidence defensible`).
- Checked: `python3 -m pytest -q tooling/qa/fixes_tests/test_h2_under_the_hood_evidence.py` (4
  passed); `bash tooling/qa/check-under-the-hood.sh` passed; `bash tooling/qa/check-fixes.sh` passed
  (129 tests and 0 design problems). The broad `python3 -m pytest -q` still cannot collect the
  unrelated client-map test because its local `census` helper is missing; this existing H1 issue is
  recorded above and is not hidden or treated as a pass.
