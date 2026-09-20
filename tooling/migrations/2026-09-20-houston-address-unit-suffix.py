#!/usr/bin/env python3
"""One-time: keep `firstSeen` when Houston addresses lose their unit suffix.

Harris County stores `site_addr_1` as the street address plus `str_unit`, so
every Houston lead used to read "9757 WINDWATER DR 150". Now that the runner
trims that suffix and reads it as the unit count, the lead's content identity
(state + address + name) changes, and the next build would stamp every one of
those buildings as first seen today -- a false "new this week" for buildings we
have tracked for months.

This rewrites the *previous built output* so the identity carry-over in
`build_data.add_first_seen` still matches. It only touches a lead whose old
address is exactly the new address plus a space and that lead's unit count, so
a street that legitimately ends in a number (NASA RD 1, HIGHWAY 3) is never
shortened. Safe to re-run: leads already migrated simply find no match.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "site" / "data"))
sys.path.insert(0, str(ROOT / "propertystack" / "skills" / "lead-finder"))

from build_data import content_id  # noqa: E402

AREA_FILE = ROOT / "site" / "data" / "areas" / "tx.json"
LEADS_FILE = ROOT / "propertystack" / "data" / "tx" / "leads.json"


def migrate(area_path: Path = AREA_FILE, leads_path: Path = LEADS_FILE) -> int:
    area = json.loads(area_path.read_text())
    new_leads = json.loads(leads_path.read_text())

    wanted: dict[str, str] = {}
    for lead in new_leads:
        units = lead.get("units")
        address = (lead.get("address") or "").strip()
        if not units or not address:
            continue
        wanted[f"{address} {units}".upper()] = address

    changed = 0
    for lead in area.get("leads", []):
        old_address = (lead.get("address") or "").strip()
        new_address = wanted.get(old_address.upper())
        if not new_address or new_address == old_address:
            continue
        suffix = old_address[len(new_address):]
        lead["address"] = new_address
        for field in ("property", "community"):
            value = lead.get(field)
            if isinstance(value, str) and value.upper().endswith(suffix.upper()):
                lead[field] = value[: -len(suffix)].strip()
        lead["id"] = content_id(
            "tx", new_address, lead.get("property") or lead.get("community") or ""
        )
        changed += 1

    if changed:
        area_path.write_text(json.dumps(area, indent=2) + "\n")
    return changed


if __name__ == "__main__":
    count = migrate()
    print(f"rewrote {count} Houston leads in the previous build so firstSeen survives")
