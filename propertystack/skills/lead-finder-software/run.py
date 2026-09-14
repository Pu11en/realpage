"""Part 4.1 entry point -- fill in `software` on every LeadRecord that has a website.

Usage: python3 skills/lead-finder-software/run.py <in.json> <out.json>

Reads a JSON list of LeadRecord dicts (record.py), detects software for each one
that has a `website` and no software yet, writes the same list back out with
`software` set and a `links["software_proof"]` + a `sources` entry added.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEAD_FINDER = HERE.parents[0] / "lead-finder"
for p in (HERE, LEAD_FINDER):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from record import LeadRecord  # noqa: E402
from fetch import WebHelper  # noqa: E402
from detect import detect_software, load_rules  # noqa: E402


def fill_software(records: list[LeadRecord], web: WebHelper) -> list[LeadRecord]:
    rules = load_rules()
    for rec in records:
        if not rec.website or rec.software not in ("", "unknown"):
            continue
        result = detect_software(rec.website, web, rules)
        rec.software = result["software"]
        if result["proof_url"]:
            rec.links["software_proof"] = result["proof_url"]
            rec.sources.append({"fact": "software", "url": result["proof_url"]})
    return records


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("in_file")
    ap.add_argument("out_file")
    args = ap.parse_args()

    records = [LeadRecord.from_dict(d) for d in json.loads(Path(args.in_file).read_text())]
    web = WebHelper()
    records = fill_software(records, web)
    Path(args.out_file).write_text(json.dumps([r.to_dict() for r in records], indent=2))
    print(f"{len(records)} records processed")


if __name__ == "__main__":
    main()
