"""Live self-test for the county sales recipes saved under
propertystack/recipes/<state>/ (F5). Not part of the offline pytest suite
(check-lead-finder.sh stays network-free) -- run by hand:
    python3 propertystack/skills/lead-finder-sales/live_self_test.py az
Downloads each recipe's real sales + parcel zip files and asserts find_sold()
returns at least 10 real 20+ unit apartment sales in the last 24 months.
"""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from find_sold import default_fetch_rows, find_sold  # noqa: E402

RECIPES_ROOT = Path(__file__).resolve().parents[2] / "recipes"


def main() -> int:
    state_dir = sys.argv[1] if len(sys.argv) > 1 else "az"
    recipes_dir = RECIPES_ROOT / state_dir
    today = datetime.date.today()
    failures = []
    found_any = False
    for path in sorted(recipes_dir.glob("*sales*.json")):
        recipe = json.loads(path.read_text())
        try:
            records = find_sold(state_dir, recipe, default_fetch_rows, today=today)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{path.name}: error {exc!r}")
            continue
        if len(records) < 10:
            failures.append(f"{path.name}: only {len(records)} sales rows returned (need >= 10)")
            continue
        found_any = True
        print(f"{path.name}: {len(records)} apartment sales, e.g.:")
        for r in records[:5]:
            print(f"  {r.address}, {r.city} -- {r.units} units, sold {r.sale_date}, buyer={r.buyer!r}, price via why={r.why!r}")
    if not found_any and not failures:
        failures.append(f"no *sales*.json recipes found under {recipes_dir}")
    if failures:
        print("\nFAILED recipes:")
        for f in failures:
            print(f" - {f}")
        return 1
    print("\nAll sales recipes returned at least 10 real rows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
