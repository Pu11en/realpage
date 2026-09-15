#!/usr/bin/env python3
"""site/data/software-share.json -> a chat-ready `software_share` CSV.

The site's software market-share chart (`site/data/software-share.json`, built from
`propertystack/data/plano-richardson/master.csv`) never loaded into the chat. This flattens the
`share` list to one row per vendor (vendor, properties, units, pct_of_identified_properties) and
writes it to `propertystack/data/software-share/kb/software-share.csv`, which the Dockerfile's
`kb` stage copies into `/kb/data` (table name `software_share`, from `_table_name` in the
propertystack plugin). It only covers Plano/Richardson (the site's `generatedFrom` scope), not
Dallas or any other area.
"""
from __future__ import annotations

import csv
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "site" / "data" / "software-share.json"
OUT_DIR = ROOT / "propertystack" / "data" / "software-share" / "kb"
OUT = OUT_DIR / "software-share.csv"


def build(src: pathlib.Path = SRC, out: pathlib.Path = OUT) -> None:
    data = json.loads(src.read_text())
    share = data.get("share", [])
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["vendor", "properties", "units", "pct_of_identified_properties"])
        for row in share:
            w.writerow([
                row.get("vendor", ""),
                row.get("properties", ""),
                row.get("units", ""),
                row.get("pctOfIdentifiedProperties", ""),
            ])


if __name__ == "__main__":
    build()
    print(f"wrote {OUT}")
