# Lead data cleanup, done safely (redo)

Goal: bad lead rows are fixed without losing a single real phone number or a real project.
Done when: the quality report shows 0 broken phones and 0 duplicates, every phone with 10 real
digits is still present (just reformatted), and no row was merged unless its street address
matches another row exactly.

Written 2026-09-15 (thread 1549506016125911081). The first cleanup run went too far:
- It blanked good numbers written as `319-217-8136` because they were not in `(319) 217-8136`
  style. Real phones must be **reformatted, never deleted**.
- It merged 7 different Arizona projects because they all share the placeholder name
  "Unnamed project" in the same city, even though their unit counts differ.
Start from the current branch of the previous run (it already has
`tooling/leadcheck/report.py`, `clean.py` and the tests); fix the rules, then re-run the clean
over data restored from git so nothing stays lost. Localhost only; **never push**.

Run with: `Do the next unticked task in PLAN-lead-data-quality-redo.md, then tick it and stop.`
Check: `python3 -m pytest -q tooling/qa/fixes_tests/test_lead_data_quality.py chatbot/tests`
Try: `python3 tooling/leadcheck/report.py`
Open: no page; the report prints and is saved to `tooling/leadcheck/report.md`

## How to try it (30 seconds)
1. Run `python3 tooling/leadcheck/report.py`: 0 broken phones, 0 duplicates.
2. Search the Texas lead file for "Richardson Ridge": it still has a phone, now written as (319) 217-8136.
3. Search the Arizona lead file for "Unnamed project": all the separate Mesa/Maricopa rows are still there.

## Tasks

- [ ] **R1 Restore the data, fix the phone rule.** `git checkout` the lead CSVs from the commit
  before the first clean, so every original row and phone is back. In `tooling/leadcheck/clean.py`:
  a phone with exactly 10 digits (any punctuation, or a leading 1) is **reformatted** to
  `(XXX) XXX-XXXX`; only a phone that cannot make 10 digits is blanked. Add tests for
  `319-217-8136`, `+1 512 610 4016`, `8-773-367-2410` (the only one that should be blanked).
  Run Check. Commit.
- [ ] **R2 Fix the duplicate rule.** Two rows are duplicates **only** when their street address
  matches exactly (case/spacing ignored) and they are in the same city; a shared name is never
  enough, and a placeholder name ("Unnamed project", "Apartments at ...") never merges anything.
  When merging, keep the row with more filled-in fields. Add a test proving the 7 Arizona
  "Unnamed project" rows stay separate and a true same-address pair merges. Run Check. Commit.
- [ ] **R3 Re-run and prove it.** Run `clean.py` over every area, then `report.py`. Write in
  `PLAN-lead-data-quality-redo.progress.md`: rows before/after per area, how many phones were
  reformatted, how many blanked, how many rows merged (with their addresses). Confirm the Texas
  and Arizona checks in "How to try it" by hand and record the exact lines. Run Check. Commit. Do not push.
