## S1 Skeleton + tests — done (2026-09-13)
- Added propertystack/skills/scout-areas/: SKILL.md (contract + scoring formulas), metros.csv (25 metros TX/FL/AZ/NC/SC + Boise, no DFW), run.py (load_metros, SearchBudget cap<=1500 raising CapReached, score_metro, run_metros stops cleanly at cap, render_cards), tests/ with saved fixtures.
- Commits: b7ef02c (failing tests first), 11ad2fc (skeleton).
- Checked: `python3 -m pytest -q propertystack/skills/scout-areas/` -> 6 passed. Try command parses args and exits "skeleton only" (gather() is NotImplemented until S2-S4).
- Open: CBSA codes/lat-lon typed from memory; S2 should verify CBSA codes against Census files.

## S2 Census data — done (2026-09-13)
- Added census.py: sums the 12 latest monthly Census Building Permits CBSA files (5+ units, imputed; window 2025-08..2026-07) and reads renter households from the ACS 2024 1-year B25003 flat file (2025 not published yet; falls back automatically). api.census.gov now needs a key, so the keyless flat files are used instead.
- Raw files cached in propertystack/data/raw/census/ (git-ignored by existing raw/.gitignore). run.py gather() now returns Census numbers; Try command prints per-metro permits/renters/scores (churn/pain 0 until S3-S4).
- All 25 CBSA codes in metros.csv matched both files (verifies the S1 open item). E.g. Tucson 1,106 permits / 152,892 renter households; Boise 1,201 / 90,465.
- Commit: 61d1e27. Checked: pytest -> 11 passed (5 new, offline fixtures); live Try run OK, 0 searches used.
