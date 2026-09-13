## S1 Skeleton + tests — done (2026-09-13)
- Added propertystack/skills/scout-areas/: SKILL.md (contract + scoring formulas), metros.csv (25 metros TX/FL/AZ/NC/SC + Boise, no DFW), run.py (load_metros, SearchBudget cap<=1500 raising CapReached, score_metro, run_metros stops cleanly at cap, render_cards), tests/ with saved fixtures.
- Commits: b7ef02c (failing tests first), 11ad2fc (skeleton).
- Checked: `python3 -m pytest -q propertystack/skills/scout-areas/` -> 6 passed. Try command parses args and exits "skeleton only" (gather() is NotImplemented until S2-S4).
- Open: CBSA codes/lat-lon typed from memory; S2 should verify CBSA codes against Census files.
