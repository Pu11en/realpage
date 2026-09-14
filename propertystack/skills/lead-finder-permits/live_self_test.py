"""Live self-test for the permit recipes saved under propertystack/recipes/<state>/
(F4). Not part of the offline pytest suite (check-lead-finder.sh stays
network-free) -- run by hand:
    python3 propertystack/skills/lead-finder-permits/live_self_test.py <state-dir>
Hits each recipe's real endpoint and asserts find_upcoming() returns at least
one multifamily row from it.
"""
from __future__ import annotations

import datetime
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from find_upcoming import find_upcoming  # noqa: E402

RECIPES_ROOT = Path(__file__).resolve().parents[2] / "recipes"


def http_get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "propertystack-live-self-test"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def main() -> int:
    state_dir = sys.argv[1] if len(sys.argv) > 1 else "az"
    recipes_dir = RECIPES_ROOT / state_dir
    today = datetime.date.today()
    failures = []
    for path in sorted(recipes_dir.glob("*.json")):
        recipe = json.loads(path.read_text())
        try:
            records = find_upcoming(recipe["city"], recipe["state"], state_dir, recipe, http_get, today=today)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{path.name}: error {exc!r}")
            continue
        if not records:
            failures.append(f"{path.name}: 0 multifamily rows returned")
            continue
        print(f"{path.name}: {len(records)} multifamily rows, e.g. {records[0].address!r} units={records[0].units}")
    if failures:
        print("\nFAILED recipes:")
        for f in failures:
            print(f" - {f}")
        return 1
    print("\nAll recipes returned at least one multifamily row.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
