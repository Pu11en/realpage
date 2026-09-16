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
