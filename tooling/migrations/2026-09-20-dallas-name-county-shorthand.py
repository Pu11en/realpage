#!/usr/bin/env python3
"""One-time: keep `firstSeen` when a lead name loses its county shorthand.

Dallas CAD writes its own clerical notes into the name column -- "(N/C 89%)
SOLTRA FIREWHEEL", "(91% COMPLETE) FLYNN @ LIVE OAK", "AMLI TREE HOUSE (ECU 2
ACCTS)".  Now that the site strips those codes, a lead's content identity
(state + address + name) changes, and the next build would stamp every one of
those buildings as first seen today -- a false "new this week" for buildings we
have tracked since the first Texas run.

This rewrites the *previous built output* so the identity carry-over in
`build_data.add_first_seen` still matches.  It only renames a lead whose stored
name actually contains county shorthand, so a real name is never touched.  Safe
to re-run: leads already migrated find no shorthand and are left alone.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "site" / "data"))
sys.path.insert(0, str(ROOT / "propertystack" / "skills" / "lead-finder"))

from build_data import _nice_name, content_id  # noqa: E402

AREAS_DIR = ROOT / "site" / "data" / "areas"


def migrate(areas_dir: Path = AREAS_DIR) -> int:
    changed = 0
    for area_path in sorted(areas_dir.glob("*.json")):
        if area_path.name == "index.json":
            continue
        area = json.loads(area_path.read_text())
        slug = area.get("area") or area_path.stem
        touched = 0
        for lead in area.get("leads", []):
            old_name = lead.get("property") or ""
            new_name = _nice_name(old_name, lead.get("address") or "")
            if not new_name or new_name == old_name:
                continue
            lead["property"] = new_name
            lead["id"] = content_id(slug, lead.get("address") or "", new_name)
            touched += 1
        if touched:
            area_path.write_text(json.dumps(area, indent=2) + "\n")
            changed += touched
    return changed


if __name__ == "__main__":
    count = migrate()
    print(f"renamed {count} leads in the previous build so firstSeen survives")
