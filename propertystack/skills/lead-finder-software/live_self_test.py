"""Live self-test for software detection (F7), against the 5 answer-key AZ
buildings that have a hand-verified vendor (propertystack/answer-keys/az.json).
Not part of the offline pytest suite (check-lead-finder.sh stays network-free)
-- run by hand:
    python3 propertystack/skills/lead-finder-software/live_self_test.py
Fetches each building's real website and asserts detect_software() finds the
same vendor a human confirmed by hand in the answer key.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEAD_FINDER = HERE.parents[0] / "lead-finder"
for p in (HERE, LEAD_FINDER):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from detect import detect_software, load_rules  # noqa: E402
from fetch import WebHelper  # noqa: E402

# name -> (website, expected vendor), read off each answer-key entry's
# software_verified_from field (the building's own site, not a listing page).
BUILDINGS = [
    ("Lumara", "https://www.lumaraphoenix.com/", "Yardi"),
    ("Navona", "https://www.navonamesa.com/", "Entrata"),
    ("The Stately Avondale", "https://thestatelyavondale.com/residents/", "Yardi"),
    ("Marquee on 5th", "https://www.themarqueeon5th.com/", "Yardi"),
    ("Bella Victoria", "https://www.bellavictoria.com/", "Yardi"),
]


def main() -> int:
    web = WebHelper()
    rules = load_rules()
    failures = []
    for name, url, expected in BUILDINGS:
        result = detect_software(url, web, rules)
        got = result["software"]
        status = "OK" if got == expected else "MISMATCH"
        print(f"{name}: expected={expected} got={got} signal={result['signal']} ({status})")
        if got != expected:
            failures.append(f"{name}: expected {expected}, got {got} ({result['unknown_reason']})")
    if failures:
        print("\nFAILED:")
        for f in failures:
            print(f" - {f}")
        return 1
    print("\nAll 5 answer-key buildings correctly identified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
