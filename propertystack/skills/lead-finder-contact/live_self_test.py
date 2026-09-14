"""Live self-test for phones/owners (F8), against 3 of the answer-key AZ
buildings (propertystack/answer-keys/az.json). Not part of the offline pytest
suite (check-lead-finder.sh stays network-free) -- run by hand:
    python3 propertystack/skills/lead-finder-contact/live_self_test.py
Fetches each building's real website and checks find_office_phone() pulls a
real, non-fax phone number off it; also runs find_website() live for one
developer name to confirm the F2 "is this really about them" check accepts
their real site.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEAD_FINDER = HERE.parents[0] / "lead-finder"
for p in (HERE, LEAD_FINDER):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from contact import find_office_phone, find_website  # noqa: E402
from fetch import WebHelper  # noqa: E402

# name -> the building's own website (same sites F7 confirmed have a real,
# non-blocked page behind them).
BUILDINGS = [
    ("Lumara", "https://www.lumaraphoenix.com/"),
    ("Navona", "https://www.navonamesa.com/"),
    ("The Stately Avondale", "https://thestatelyavondale.com/"),
]

DEVELOPER = "Toll Brothers Apartment Living"


def main() -> int:
    web = WebHelper()
    failures = []
    for name, url in BUILDINGS:
        result = web.fetch(url)
        html = result.html if result.ok else ""
        phone = find_office_phone(html)
        status = "OK" if phone else "MISSING"
        print(f"{name}: phone={phone or '(none found)'} ({status})")
        if not phone:
            failures.append(name)

    site = find_website(DEVELOPER, web.search)
    print(f"\n{DEVELOPER} website (F2-checked): {site or '(none found)'}")
    if not site:
        failures.append(f"{DEVELOPER} website")

    if failures:
        print("\nFAILED:")
        for f in failures:
            print(f" - {f}")
        return 1
    print("\nAll 3 answer-key buildings gave a real office phone, and the developer website lookup found a real, F2-checked site.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
