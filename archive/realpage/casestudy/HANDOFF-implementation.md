# Implementation handoff back to the original session

Status: REVIEW COMPLETE — READY TO RESUME IN THE ORIGINAL BUILDING SESSION.
Drew clarified that this session was a second opinion and wants to return to the original session
to build, test the result himself, and iterate. The optional change-by-change walkthrough is no
longer a prerequisite. The original session remains the implementation owner; this review session
has not written app code, sent this handoff to another session, or pushed anything.

Requested provider/model: DeepSeek V4 Flash for the case-study application. Verify its exact API
model identifier and existing configuration during setup; the reviewer has made no live provider
call and cannot claim that integration already works. Astra Advisor concerns coding coordination,
not a replacement for the application's DeepSeek API. Its hypothetical API cost comparison is
unrelated to the application's DeepSeek bill and need not clutter the product walkthrough.

## Resume instruction

Read this handoff and the active plan, implement the reviewed case-study bot, verify it, and show
Drew a working preview for feedback. Preserve the established workflow and existing authorization
for provider-backed tests; do not infer a new spending budget. Deployment/push still follows Drew's
existing explicit authorization boundary.

## Delivery sequence

1. Make one complete path work: input record -> decision/message -> visible explanation -> export.
2. Extend it to both supplied examples and an ordered 12-record batch; verify the required checks,
   offline fallback, and handling of one malformed record.
3. Demonstrate the working page and give Drew a short, repeatable test sequence.
4. Fix what Drew finds, rerun the relevant checks, and prepare the agreed live deployment.
5. Rehearse the actual interview flow: paste the 12 records, run, inspect, export, and recover offline.

Use the plan's remaining tasks to complete the deliverable; checkpoints are engineering checks,
not requests for Drew to approve each small implementation step.

## Inputs and precedence

1. `data/problem_statement.txt` and both lines of `data/sample.jsonl`.
2. `../PLAN-casestudy-bot.md` — active requirements, including the self-review corrections.
3. `REVIEW-astra.md` — use the dated self-review correction block over earlier contradictory claims.
4. `CHANGES-explained.md` and Drew's subsequent walkthrough answers.
5. `DECISION-LOG.md` and the three research files — history and citations, not replacement requirements.

## First bounded implementation milestone

Implement C0 plus the input/output contracts needed for C1, entirely offline, within `casestudy/`.
Read both supplied records; retain exact structure/null/CTA/action checks, but score message prose
by meaning. Define a clean submission object and separate diagnostics. Demonstrate that changing
or removing a held-out `expected` block cannot affect inference. Return the complete diff and
checks to the original session's coordinator, then continue the active plan within the approved scope.

## Acceptance and routing

Astra Advisor was used for this review session and is available to an Astra coordinator; this
handoff does not require the original session to switch its previously confirmed workflow/model.
Installed and independently verified by the parent: `astra-advisor@astra-advisor` v0.2.0,
commit `c72d3280551f118eba51a5884e3971a0c0058aa6`, status `installed, enabled` in `codex plugin list`.
Skill: `/mnt/c/Users/drewp/.codex/plugins/cache/astra-advisor/astra-advisor/0.2.0/skills/orchestration/SKILL.md`.
The skill and operations reference were read and applied in this session; future tasks can discover
the registered plugin. Upstream: https://github.com/DannyMac180/astra-advisor.

Choose a bounded implementer dynamically from supported lower-cost models; there is no automatic
team launch or fixed worker count. Parent owns the contract and integration, inspects the complete
diff and runs relevant checks; substantial implementation receives a fresh read-only review.

Required invariants: no real sends/bookings, no property-data access, no expected-answer leakage,
no fabricated facts for unseen properties, explicit uncertainty for inferred rules, no fake metric
passes, valid ordered batch export, and offline fallback. Preserve existing product decisions and
unrelated working-tree changes. Do not push.

Setup delegation: `/root/advisor_setup`, requested `gpt-5.6-luna` / `medium`, completed. Native
metadata did not expose realized model/effort or token usage. The worker reported 15 source-checkout
verification tests passed; the installed-copy verifier assumes a repository layout and is not a
valid installed-plugin check. Parent checked registration, enabled state, manifest and skill path.
API-equivalent cost receipt: unavailable because observed parent/delegate token usage is absent;
no dollar savings or subscription-cost claim is made.

## Decisions still requiring evidence or interviewer clarification

- Timing reference and meaning of `dayN`; both samples share Dec 9, but no evaluation clock is given.
- Personalization formula and reply label/schema definition; our metrics are explicit proxies.
- Missing property links/availability; supplied-example facts need provenance and narrow scope.
- Public legal citations: research contains conflicting statute numbers and Sunday claims; verify
  primary authorities before publishing them as legal facts.
- Submission schema beyond the two examples; default export mirrors those examples.

These uncertainties can be represented in code and explained; do not ask Drew to invent the
employer's answers. Continue with the working assumptions recorded in the active plan.
