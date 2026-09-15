#!/usr/bin/env python3
"""Dallas parked survey -> chat-ready CSVs.

`propertystack/data/dallas-parked/*.csv` is a Dallas-wide building survey (not leads); it never
loaded into the chat. This copies each file, adding an `area='dallas'` column so it's obviously
scoped, into `propertystack/data/dallas-parked/kb/` where the Dockerfile's `kb` stage picks it up.
Table names come from the file name (see `_table_name` in the propertystack plugin), so files are
named `dallas-<thing>.csv` to land as `dallas_buildings`, `dallas_websites`, etc.
"""
from __future__ import annotations

import csv
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC_DIR = ROOT / "propertystack" / "data" / "dallas-parked"
OUT_DIR = SRC_DIR / "kb"

# source file -> output name (becomes table dallas_<name>)
FILES = {
    "1-buildings-dallas.csv": "dallas-buildings.csv",
    "2-websites-dallas.csv": "dallas-websites.csv",
    "3-software-dallas.csv": "dallas-software.csv",
    "5-sales-dallas.csv": "dallas-sales.csv",
    "contacts-dallas.csv": "dallas-contacts.csv",
}


def build(src_dir: pathlib.Path = SRC_DIR, out_dir: pathlib.Path = OUT_DIR) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for src_name, out_name in FILES.items():
        src = src_dir / src_name
        if not src.exists():
            continue
        with open(src, newline="") as f:
            rows = list(csv.reader(f))
        if not rows:
            continue
        header, body = rows[0], rows[1:]
        header = header + ["area"]
        body = [row + ["dallas"] for row in body]
        with open(out_dir / out_name, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(body)


if __name__ == "__main__":
    build()
    print(f"wrote {len(FILES)} tables to {OUT_DIR}")
