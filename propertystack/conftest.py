"""Root pytest conftest for the propertystack tree.

`live_self_test.py` scripts (one per lead-finder-* skill that has a hand-run,
network-touching live check -- see F4/F5 in PLAN-lead-finder-fix.md) are meant
to be run directly (`python3 .../live_self_test.py <area>`), never collected
by pytest: `check-lead-finder.sh` only runs each skill's `tests/` directory,
but a whole-tree run (`pytest propertystack`) would otherwise try to collect
every `live_self_test.py` as a test module, and since none of these skill
directories are Python packages (no `__init__.py`), two files sharing the
same basename in different directories collide ("import file mismatch").
Skipping them here keeps a whole-tree pytest run both network-free and
collision-free without renaming the hand-run scripts.
"""
collect_ignore_glob = ["*/live_self_test.py"]
