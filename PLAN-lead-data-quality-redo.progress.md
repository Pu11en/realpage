## **R1 Restore the data, fix the phone rule.** `git checkout` the lead CSVs from the commit (built alongside other steps)
- — the step is finished and committed

## **R2 Fix the duplicate rule.** Address + city only, no placeholder merges
- Removed name/city-based grouping from `find_duplicate_groups()`; now only groups by exact address + city match
- Rows without addresses (like the "Unnamed project" entries) are never grouped
- Placeholder names like "Unnamed project" or "Apartments at ..." no longer trigger merging
- Added tests: `test_arizona_unnamed_projects_stay_separate()` proves 7 AZ rows stay separate
- Added tests: `test_true_duplicate_pair_merges()` proves same-address pairs still merge
- All 68 tests pass (tooling/qa/fixes_tests/test_lead_data_quality.py + chatbot/tests)
- Commit: a57a105

## R2 fix (reviewer follow-up)
report.py's find_duplicates was still grouping by name+city, so the report kept flagging
the 7 Arizona "Unnamed project" rows even though clean.py no longer merges them. Fixed
find_duplicates to use the exact same rule as clean.py's find_duplicate_groups: address +
city only, no name-based grouping. Also collapsed internal whitespace before comparing
addresses/cities in both clean.py and report.py (e.g. "123  Main   St" now matches "123 Main St").
Added tests: report.py duplicate rule matches clean.py's (Arizona rows not flagged, true
address+city pair is flagged), and whitespace-collapsed address matching.
Commit: f709791. Checked: `python3 -m pytest -q tooling/qa/fixes_tests/test_lead_data_quality.py chatbot/tests` — 71 passed.

## **R3 Re-run and prove it.** Full cleanup, verify zero broken phones and duplicates

Ran `clean.py` over all areas (AZ, NY, TX). Results:
- **Rows before/after:** AZ 279→279, NY 2→2, TX 592→592 (total 873→873)
- **Phones reformatted:** 3
  - 319-217-8136 → (319) 217-8136 (Richardson Ridge, Fort Worth, TX)
  - 512-610-4016 → (512) 610-4016 (The Bloom at Lamar Square, Austin, TX)
  - 440-263-0406 → (440) 263-0406 (Cottages on Independence, Port Lavaca, TX)
- **Phones blanked:** 1 (8-773-367-2410 in South Lamar Multifamily, Austin, TX — truly invalid)
- **Rows merged:** 0 (no duplicate rows with same address+city found)
- **Verification checks passed:**
  - Texas "Richardson Ridge" still has phone: (319) 217-8136 ✓
  - Arizona "Unnamed project": 9 separate rows confirmed (different units: 36, 36, 29, 260, 290, 140, 24, 44, 36) ✓
- **Quality report:** 0 broken phones, 0 duplicates ✓
- **Tests:** 71 passed ✓
- Commit: (waiting to commit this entry)

## Next time (from how this build went)
- **Split the duplicate-rule fix into two coordinated steps, not one.** The cleanup tool (clean.py) got fixed, but the report tool (report.py) kept the old logic — they should have been updated together or the second one flagged explicitly as a follow-up, so the reviewer caught it faster.
- **Mark task checkboxes as soon as they're done.** Sonnet's retry didn't tick the box, so the plan thought R2 was still pending even after it ran — this caused confusion and made Haiku redo the work.
- **Run code review before retry, not after.** Haiku's review found the incomplete fix, but by then Sonnet had already tried and "finished." Catching the two-file split upfront would have saved a retry loop.
