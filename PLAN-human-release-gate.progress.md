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

## 2026-09-15 — H3: predictable off-topic boundary

- Added one exact, calm off-topic reply to the CraneSignal Agent instructions: it says the request is
  outside CraneSignal, states the product's sales-research purpose, and suggests asking about a Texas
  building. It explicitly covers small talk, unrelated facts, writing requests, and attempts to change
  the agent's role or bypass its rules; none of these requests uses a tool.
- Added seven saved offline fixtures for the scorecard's scope-creep class: normal small talk,
  unrelated factual questions, and role-redirect attempts. The focused test verifies all three classes
  retain the same useful boundary and that the agent instructions still require it.
- Checked: `python3 -m pytest -q tooling/qa/fixes_tests/test_h3_off_topic_behavior.py` (2 passed);
  `bash tooling/qa/check-fixes.sh` passed (131 tests and 0 design problems). The broad
  `python3 -m pytest -q` still cannot collect the unrelated client-map test because its local `census`
  helper is missing; this existing H1 issue remains visible and is not treated as a pass.

## 2026-09-15 — H4: grounded factual answers

- Added a deterministic final answer guard to every public chat response path, including the
  streamed Open WebUI path. A factual answer now keeps only a readable URL that came from an
  approved tool result; otherwise people see a plain statement that CraneSignal could not verify
  the claim. The streamed path holds the completed text until that check finishes, so an unsupported
  claim cannot flash on screen first.
- Kept honest unknowns and the fixed off-topic / read-only boundaries unchanged. Added the exact
  final-verification instruction to the agent profile; it tells the agent never to invent a
  citation to avoid the check.
- Added two saved offline regression fixtures: an unapproved source link and a plain source name
  with no link. Both become the unverified reply; an approved readable source remains visible and
  an honest "I don't have that" stays unchanged. Updated the gateway cache and free-limit test
  doubles so their intentionally factual sample answers include an approved readable source.
- Checked: the focused H4 + chat test suite passed (38 tests); an explicit offline streamed-answer
  check passed; and `bash tooling/qa/check-fixes.sh` passed (134 focused tests and 0 design
  problems). The broad `python3 -m pytest -q` still cannot collect the unrelated client-map test
  because its local `census` helper is missing; this existing H1 issue remains visible and is not
  treated as a pass.
