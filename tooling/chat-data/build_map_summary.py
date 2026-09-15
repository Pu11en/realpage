#!/usr/bin/env python3
"""site/data/client-map.json -> a chat-ready `map_summary` CSV.

The site's leads-by-state map (`site/data/client-map.json`, built from
`propertystack/data/client-map/counts.json`) never loaded into the chat, so "where are most
leads?" couldn't match what the map shows. This flattens it to one row per state/top-city pair
(state, abbr, state_total, city, city_count) and writes it to
`propertystack/data/map-summary/kb/map-summary.csv`, which the Dockerfile's `kb` stage copies
into `/kb/data` (table name `map_summary`, from `_table_name` in the propertystack plugin).
"""
from __future__ import annotations

import csv
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "site" / "data" / "client-map.json"
OUT_DIR = ROOT / "propertystack" / "data" / "map-summary" / "kb"
OUT = OUT_DIR / "map-summary.csv"


def build(src: pathlib.Path = SRC, out: pathlib.Path = OUT) -> None:
    data = json.loads(src.read_text())
    states = data.get("states", {})
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["state", "abbr", "state_total", "city", "city_count"])
        for state, info in states.items():
            top_cities = info.get("topCities") or []
            if not top_cities:
                w.writerow([state, info.get("abbr", ""), info.get("total", ""), "", ""])
                continue
            for city in top_cities:
                w.writerow([state, info.get("abbr", ""), info.get("total", ""), city.get("city", ""), city.get("count", "")])


if __name__ == "__main__":
    build()
    print(f"wrote {OUT}")
