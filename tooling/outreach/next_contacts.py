#!/usr/bin/env python3
"""Which buildings still need a contact, and the exact query to search for each.

Phase 4 of docs/plans/PLAN-texas-only-6h.md. The CSV is the source of truth, not anyone's
memory: a six-hour run outlasts one conversation, so the only reliable answer to "what is
left" is the difference between the target list and what has been written down.

    python3 tooling/outreach/next_contacts.py            # the next 4
    python3 tooling/outreach/next_contacts.py 10         # the next 10
    python3 tooling/outreach/next_contacts.py --progress # how far along
    python3 tooling/outreach/next_contacts.py --add id,name,phone,mgmt,email,url
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGETS = ROOT / ".phase4-targets.json"
FOUND = ROOT / "propertystack" / "data" / "tx" / "contacts-found.csv"
COLS = ["id", "found_name", "phone", "management_company", "email", "source_url", "found_on",
        "notes"]

# The counties bake clerical codes into their own name fields. Stripped for the query only --
# the stored record keeps whatever the county published.
JUNK = re.compile(r"\s*[-(]?\s*TDHCA#?\s*\d+\s*\)?|\(\s*\d+\s*units?\s*\)|\s*-\s*\d+\s*Units?\b", re.I)


def targets() -> list[dict]:
    return json.loads(TARGETS.read_text(encoding="utf-8"))


def found() -> dict[str, dict]:
    if not FOUND.exists():
        return {}
    with FOUND.open(encoding="utf-8", newline="") as fh:
        return {row["id"]: row for row in csv.DictReader(fh)}


def query_for(row: dict) -> str:
    """The search that worked on all ten of the feasibility sample.

    A name that starts with a digit is the street address doing duty as a name, which is most
    of the sold rows. Those resolve anyway -- Apartments.com, HAR and Yelp all index by
    address -- so the query leads with the address and lets the aggregator supply the name.
    """
    name = JUNK.sub("", row.get("name") or "").strip(" -,")
    address = (row.get("address") or "").title()
    city = (row.get("city") or "").split("(")[0].strip().title()
    if not name or re.match(r"^\d", name):
        return f'apartments "{address}" {city} TX leasing office phone'
    return f'"{name}" apartments {address} {city} TX leasing phone'


def main() -> int:
    args = sys.argv[1:]
    have = found()
    todo = [t for t in targets() if t["id"] not in have]

    if "--progress" in args:
        total = len(targets())
        with_phone = sum(1 for r in have.values() if r.get("phone"))
        with_mgmt = sum(1 for r in have.values() if r.get("management_company"))
        print(f"searched {len(have)} of {total}   found a phone on {with_phone}   "
              f"management company on {with_mgmt}   still to do {len(todo)}")
        if have:
            print(f"hit rate so far: {with_phone * 100 // len(have)}%")
        return 0

    if "--add" in args:
        payload = args[args.index("--add") + 1]
        parts = next(csv.reader([payload]))
        # The 7th field is optional: a note, used to record a search that found nothing so
        # the work is not repeated and a reader can see we looked rather than skipped.
        assert len(parts) in (6, 7), f"want 6 or 7 fields, got {len(parts)}: {parts}"
        new = dict(zip(["id", "found_name", "phone", "management_company", "email",
                        "source_url", "notes"], parts))
        new.setdefault("notes", "")
        new["found_on"] = "2026-09-26"
        write_header = not FOUND.exists()
        with FOUND.open("a", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=COLS, lineterminator="\n")
            if write_header:
                w.writeheader()
            w.writerow(new)
        print(f"recorded {new['id']}")
        return 0

    count = int(next((a for a in args if a.isdigit()), 4))
    # The id goes on the same line as the query on purpose. Printed on its own line it gets
    # skipped when the output is filtered, and then the id gets *guessed* from the address --
    # which put four contacts against rows that do not exist on 2026-09-26.
    for row in todo[:count]:
        print(f"ID: {row['id']}  ({row['units']}u {row.get('metro') or 'Rest of Texas'})")
        print(f"    QUERY: {query_for(row)}")
    print(f"\n({len(todo)} left)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
