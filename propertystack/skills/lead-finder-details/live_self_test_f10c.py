"""Live self-test for F10c (find websites by project name, then address). Not
part of the offline pytest suite -- run by hand:
    python3 propertystack/skills/lead-finder-details/live_self_test_f10c.py

Runs fill_project_details for real against Jina/Brave on two of Tempe's real
leasing buildings, printing what website it finds for each so it can be
checked by hand.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEAD_FINDER = HERE.parents[0] / "lead-finder"
for p in (HERE, LEAD_FINDER, HERE.parents[1]):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from project_details import fill_project_details  # noqa: E402
from record import LeadRecord  # noqa: E402
from fetch import WebHelper  # noqa: E402

TEMPE_LEASING = [
    ("1020 Apache", "1020 W Apache Blvd"),
    ("La Victoria Commons on Apache", "1140 E Apache Blvd"),
]


def main() -> int:
    web = WebHelper()
    found_any = False
    for name, address in TEMPE_LEASING:
        rec = LeadRecord(area="az", city="Tempe", name=name, address=address, stage="leasing")
        out = fill_project_details(rec, lambda q, n: web.search(q, n), lambda u: web.fetch(u))
        website = out.website if out is not None else ""
        print(f"{name} ({address}): website={website!r}")
        if website:
            found_any = True
    if not found_any:
        print("\nFAILED: neither Tempe building got a website.")
        return 1
    print("\nAt least one of the 2 Tempe buildings got a real website.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
