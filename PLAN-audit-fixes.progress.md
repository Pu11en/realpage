## A1 Phones — done (7f8a73b)
- Added the viewport tag to index, under-the-hood, property, ai-visibility (one line only) and the master-table redirect page, so every site/*.html has it.
- sweep.py and quick-check.py phone runs now use is_mobile=True, has_touch=True.
- Test: tooling/qa/fixes_tests/test_a1_viewport.py (tag on every page; QA scripts emulate phones).
- Checked: check-fixes.sh passes (2 tests, design check 0 problems); every page at 390px phone emulation has no sideways scroll (Under the Hood's wide table scrolls inside its own box).
- Note: port 8791 had a stale server serving old pages; use another port if checks look odd.
