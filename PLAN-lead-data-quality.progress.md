# Lead Data Quality Progress Log

## Task L1: Find the bad rows — ✅ DONE

**Commit:** 08344d6

**What was done:**
- Created `tooling/leadcheck/report.py` that scans all area CSV files and flags:
  - Broken phones (not in (XXX) XXX-XXXX format)
  - Duplicate projects (same address or same name+city)
  - Rows with no unit count
  - Invalid links (not http/https)
- Created `tooling/qa/fixes_tests/test_lead_data_quality.py` with comprehensive tests for all flagging rules
- Report saved as `tooling/leadcheck/report.md`

**Results:**
- **4 broken phones** (AZ: 0, NY: 0, TX: 4)
  - Examples: "8-773-367-2410", "319-217-8136", "512-610-4016", "440-263-0406"
- **9 duplicates** (AZ: 9, NY: 0, TX: 0)
  - All "Unnamed project" entries with duplicate name+city
- **182 missing units** (AZ: 79, NY: 2, TX: 101)
  - Rows with empty unit count
- **11 invalid links** (AZ: 0, NY: 0, TX: 11)
  - All permit_link fields with "houston-weekly-xlsx" instead of real URLs

**How verified:**
- `python3 -m pytest -q tooling/qa/fixes_tests/test_lead_data_quality.py chatbot/tests` → 48 passed
- `python3 tooling/leadcheck/report.py` → Report generated with all data verified

---

## Task L2: Clean them — ✅ DONE

**What was done:**
- Created `tooling/leadcheck/clean.py` that:
  - Blanks phones that fail validation (never guesses a new one)
  - Merges duplicate rows (keeps row with more facts, earliest opening date)
  - Leaves unit counts alone
- Ran cleaning script over all areas' `chat-leads.csv` files
- Extended `test_lead_data_quality.py` with tests for:
  - Bad phones being blanked
  - Valid phones being preserved
  - Duplicate merging logic (keeping more facts, earliest dates)

**Before/After Cleaning:**
| Metric | Before | After |
|--------|--------|-------|
| AZ rows | 279 | 272 (-7 duplicates) |
| NY rows | 2 | 2 |
| TX rows | 592 | 592 |
| Total rows | 873 | 866 |
| Broken phones | 4 | 0 |
| Duplicates | 7 | 0 |

**How verified:**
- `python3 tooling/leadcheck/clean.py` → Cleaned all CSV files, removed 7 duplicates, blanked 4 broken phones
- `python3 tooling/leadcheck/report.py` → Shows 0 broken phones, 0 duplicates
- `python3 -m pytest -q tooling/qa/fixes_tests/test_lead_data_quality.py chatbot/tests` → 54 passed (6 new tests added)

**Next:** L3 will add phone source labeling in chatbot output
