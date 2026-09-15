#!/usr/bin/env python3
"""site/data/properties.json -> a chat-ready `building_extras` CSV.

The site's building pages (`site/data/properties.json`, built from
`propertystack/data/plano-richardson/master.csv` plus sale and lead lookups) show owner, website
confidence, the reason software is unknown, and sale/lead notes per building -- but the chat had
no single table with all of that per building; it would need a 3-4 way join across
`master`/`sales`/`leads`/`contacts` by `apt_id`/`ref_id`, and most buildings have no sale or lead
row at all. This flattens one row per building (keyed by `apt_id`, matching `master.apt_id`) to
`propertystack/data/building-extras/kb/building-extras.csv`, which the Dockerfile's `kb` stage
copies into `/kb/data` (table name `building_extras`).
"""
from __future__ import annotations

import csv
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "site" / "data" / "properties.json"
OUT_DIR = ROOT / "propertystack" / "data" / "building-extras" / "kb"
OUT = OUT_DIR / "building-extras.csv"

FIELDS = [
    "apt_id",
    "owner",
    "website_confidence",
    "unknown_reason",
    "sale_date",
    "sale_new_owner",
    "sale_previous_owner",
    "lead_rank",
    "lead_total_leads",
    "lead_why",
]


def build(src: pathlib.Path = SRC, out: pathlib.Path = OUT) -> None:
    data = json.loads(src.read_text())
    properties = data.get("properties", [])
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(FIELDS)
        for p in properties:
            sale = p.get("sale") or {}
            lead = p.get("lead") or {}
            w.writerow([
                p.get("id", ""),
                p.get("owner", ""),
                p.get("websiteConfidence", ""),
                p.get("unknownReason", ""),
                sale.get("date", ""),
                sale.get("newOwner", ""),
                sale.get("previousOwner", ""),
                lead.get("rank", ""),
                lead.get("total", ""),
                lead.get("why", ""),
            ])


if __name__ == "__main__":
    build()
    print(f"wrote {OUT}")
