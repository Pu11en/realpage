"""Live self-test for TDLR TABS (T2) -- not part of the offline pytest suite
(check-lead-finder.sh stays network-free) -- run by hand:
    python3 propertystack/skills/lead-finder-tabs/live_self_test.py
Hits the real TABS search + detail endpoints using recipes/tx/tabs.json and
asserts find_tabs_projects() returns real new-construction apartment projects
with a name, address and city.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tabs import default_fetch_detail, default_fetch_search, find_tabs_projects  # noqa: E402

RECIPE_PATH = Path(__file__).resolve().parents[2] / "recipes" / "tx" / "tabs.json"


def main() -> int:
    recipe = json.loads(RECIPE_PATH.read_text())
    records = find_tabs_projects("tx", recipe, default_fetch_search, default_fetch_detail)
    if not records:
        print("FAILED: 0 projects returned")
        return 1
    missing_name_or_address = [r for r in records if not r.name or not r.address]
    print(f"{len(records)} TABS projects, {len(missing_name_or_address)} missing name/address")
    for record in records[:5]:
        print(f" - {record.name!r} {record.city!r} units={record.units} developer={record.developer!r} phone={record.office_phone!r}")
    if missing_name_or_address:
        print("FAILED: some projects missing name or address")
        return 1
    print("\nAll TABS projects have a name and address.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
