"""Live self-test for F10b (developer + phone for brand-new permits). Not
part of the offline pytest suite -- run by hand:
    python3 propertystack/skills/lead-finder-contact/live_self_test_f10b.py

Takes 3 of Tempe's real new-permit projects (no contractor field filled in
yet, per propertystack/runs/AZ/20260914-tempe-test/permits.Tempe.json),
downloads Maricopa County's real parcel file, looks up each address's owner,
then a real news search for the project's own name -- printing what
find_developer_for_new_permit actually finds for each so it can be checked
against public news by hand.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SALES = HERE.parents[0] / "lead-finder-sales"
LEAD_FINDER = HERE.parents[0] / "lead-finder"
for p in (HERE, SALES, LEAD_FINDER):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from contact import find_developer_for_new_permit  # noqa: E402
from find_sold import default_fetch_rows  # noqa: E402
from record import LeadRecord  # noqa: E402
from fetch import WebHelper  # noqa: E402

RECIPE_PATH = HERE.parents[1] / "recipes" / "az" / "maricopa-county-sales.json"

# 3 of Tempe's real new permits with no contractor filled in (from the
# 2026-09-14 test run), address taken straight from the permit row.
TEMPE_PERMITS = [
    ("REVELRY [NEW MIXED-USE]", "965 E UNIVERSITY DR"),
    ("AVENUE 5/TROVITA RIO", "701 W RIO SALADO PKWY"),
    ("THE SAMUEL (COLLEGE + 7TH) [NEW MIXED-USE]", "712 S COLLEGE AVE"),
]


def main() -> int:
    recipe = json.loads(RECIPE_PATH.read_text())
    web = WebHelper()
    found_any = False
    for name, address in TEMPE_PERMITS:
        rec = LeadRecord(area="az", city="Tempe", name=name, address=address, stage="permitted")
        developer, source = find_developer_for_new_permit(
            rec, recipe, default_fetch_rows, lambda q: web.search(q)
        )
        print(f"{name} ({address}): developer={developer!r} source={source}")
        if developer:
            found_any = True
    if not found_any:
        print("\nFAILED: none of the 3 Tempe permits got a developer name.")
        return 1
    print("\nAt least one of the 3 Tempe permits got a real developer name.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
