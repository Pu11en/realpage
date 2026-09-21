# Masiate Pilot: Parallel Review And Report Work

Check: python3 -m pytest -q propertystack/skills/lead-finder/tests

## Latest Instruction

Drew explicitly requested closing finished sessions and keeping multiple workers
productive to finish this pilot quickly. Archive completed threads only after
their turn is idle, files are saved and local work is committed; preserve chat,
git history and raw evidence. Do not delete sessions' data or resurrect the old
50-task loop. Maintain at most eight active pilot workers, excluding coordinator.
Replace finished collection tasks with independent review/report tasks below,
not another county crawl. Existing Codex settings and no-new-purchases rules stay.

Six original collection threads were archived after confirming idle/clean state;
Grimes and Washington were left open while their final turns were still active.
Finish archiving them when idle, before filling all eight review slots.

## Timing And Inputs

Aim to finish these bounded tasks by 2026-09-21T02:38:00Z, with coordinator PDF
delivery around 02:45 UTC, flexible for final checks. This is the remaining
first-pass work, not a new hour. Checkpoint useful output early; do not idle.
No new source inventory or general-purpose infrastructure build.

Collection root:
/home/drewp/.local/state/cranesignal/masiate/pilot-20260920-2048

Use immutable review-input/<lane>/{records,coverage,status}.json copies from that
root, while local_path evidence remains in the original lane's evidence folder.
Never edit collection outputs. Write only to finish/<your-role>/ and your own
isolated worktree. Atomic JSON checkpoints plus status.json (real current UTC,
state, started_at, finished_at, output_paths) and summary.md.

## Eight Small Outcomes

- [ ] review-brazos: assess Brazos records across local and statewide inputs, verify strongest projects against preserved originals, correct claims and recommend detailed PDF entries.
- [ ] review-west: same for Robertson, Burleson and Washington; preserve lots, suites, distinct permits and project phases.
- [ ] review-east: same for Grimes, Leon and Madison; distinguish approved work from agenda requests, denials, past awards and speculative needs.
- [ ] contacts: verify useful BUSINESS contact routes for strongest near-term trade-fit candidates across all counties, prioritizing actual owners/GCs rather than treating architects as buyers.
- [ ] dedup: conservative source-ID/address/project matching, output canonical project groups and member IDs without losing evidence or incorrectly merging units/phases; focused offline tests.
- [ ] coverage: reconcile all source receipts and counts, identify genuinely complete source/windows versus partial county coverage, and write the report's coverage summary.
- [ ] evidence-qa: independently flag missing evidence files, mismatched source IDs/facts, future retrieval/checkpoint dates, expired bids, past estimated dates, unsupported active-stage claims and private-contact exposure; no rewriting of source data.
- [ ] pdf-renderer: build and test a local static PDF renderer using installed WeasyPrint, with readable source-linked property profiles, county coverage, uncertainty, page numbers and an empty-results state.

## Review Output Contract

Three county reviewers each write reviewed_records.json (array) and decisions.json.
For every proposed PDF record, preserve the original worker-contract fields plus:
member_ids (all source record IDs supporting this project), review_decision
(include/watchlist/exclude), priority_reason (service-fit/evidence/recency, not
largest-budget sorting), reviewed_at (actual current UTC), evidence_checked
(list of source URLs/local paths inspected), corrections (explicit list).
Do not call unreviewed records validated. decisions.json accounts for original
IDs reviewed or not yet reviewed and the reason for each disposition.
Detailed PDF inclusion requires an identifiable location/project, concrete
Masiate fit and dated evidence. Work availability may be unknown and must be
stated. Past expected completion is not evidence of current work.
No fixed lead quota. Keep business participants separate from private homeowners.

contacts writes contacts.json entries with record_ids, verified_business_name,
role, phone/email/website as supported, source_url, retrieved_at and role_basis.
No guessed emails, homeowner phone numbers, inferred purchasing authority or
outreach. Existing source contact fields can be verified from preserved originals;
use bounded official business-site checks only when useful. Unknown paid API
allowances mean disabled, not permission to use them.

dedup writes groups.json with canonical_id, member_ids, match_basis and
conflicts, plus duplicate_tests.json. Ambiguous matches stay separate.
coverage writes coverage.json (all source receipts plus audit notes),
counts.json and coverage.md; do not equate records, distinct projects and leads.
evidence-qa writes findings.json with record_ids, severity, issue, source/check
and recommended_action, plus checked_ids and unchecked_ids.

## Renderer Interface

Create render_report.py in your finish/pdf-renderer runtime folder and mirror it
in your worktree with tests. CLI:
python3 render_report.py --records REVIEWED_JSON --coverage COVERAGE_JSON
--output OUTPUT_PDF --title "Masiate Construction: First-Pass Property Research"

Input records are the reviewer arrays above (original fields plus review fields).
Only review_decision=include may enter detailed primary profiles. Unknown fields
must show unknown; watchlist separate if included. Source local_path must not be
printed publicly. Allow missing fields gracefully, escape text/links, disallow
remote/file asset loading in untrusted input, avoid overflowing long URLs.
PDF sections: honest first-pass scope/counts, detailed property profiles, county
coverage/gaps and limitations. Whole-project budget is not Masiate contract value.
No claim of open work without bid/status evidence; no outreach scripts.
Test with clearly synthetic fixtures, NEVER mix fixtures into real records.
Generate a clearly labeled QA draft from available reviewed inputs if present;
the coordinator approves final selection and attaches final files.

## Completion

Commit local changes only; no push, live-site or agent changes, accounts, outreach,
paid-provider calls with unverified allowances, new agents or bot restarts.
Do not write other workers' files or shared plans. Finish with exact runtime paths.
The pdf-renderer worker alone watches these eight finish statuses and sends one
queued relay to parent thread 1551377360756940940 when all finish or 02:38 UTC
arrives. That wakes the coordinator for final assembly, corrections, visual/text
QA and attachment delivery; do not independently publish a draft as final.
Other workers must not send extra completion relays or ask Drew questions.
The coordinator archives finished review threads after verifying idle/saved state.

## How To Try It

1. Confirm the PDF labels unknown availability and dates honestly.
2. Open a property's source link and compare its address and scope.
3. Check each county's coverage gaps and match the PDF to reviewed JSON.
