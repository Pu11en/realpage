"""Part 4.1/4.2 entry point -- fill in `software` on every LeadRecord that has a website.

Usage: python3 skills/lead-finder-software/run.py <in.json> <out.json>

Reads a JSON list of LeadRecord dicts (record.py), detects software for each one
that has a `website` and no software yet, writes the list back out with
`software` set and a `links["software_proof"]` + a `sources` entry added.

Part 4.2: a confirmed RealPage building is not a lead, so it's dropped from the
output entirely. Everything else keeps the confirmed competitor name, or
`"not picked"` when the site was checked and no vendor was confirmed (a website
that was never fetched, e.g. no-website, is left `"unknown"`).
"""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEAD_FINDER = HERE.parents[0] / "lead-finder"
for p in (HERE, LEAD_FINDER):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from record import LeadRecord  # noqa: E402
from fetch import WebHelper  # noqa: E402
from detect import detect_software, load_rules  # noqa: E402


def fill_software(records: list[LeadRecord], web: WebHelper, max_workers: int = 6) -> list[LeadRecord]:
    rules = load_rules()

    def _detect(rec: LeadRecord):
        if not rec.website or rec.software not in ("", "unknown"):
            return rec, None
        return rec, detect_software(rec.website, web, rules)

    # S1: detect_software's own network calls run several records at a time;
    # applying each result (dropping RealPage buildings, setting fields) stays
    # single-threaded and in the original order so output is deterministic.
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        pairs = list(pool.map(_detect, records))

    kept: list[LeadRecord] = []
    for rec, result in pairs:
        if result is None:
            kept.append(rec)
            continue
        software = result["software"]
        if software == "RealPage":
            continue  # 4.2: a confirmed RealPage building is not a lead
        if result["proof_url"]:
            rec.links["software_proof"] = result["proof_url"]
            rec.sources.append({"fact": "software", "url": result["proof_url"]})
        if software == "unknown" and result["unknown_reason"] != "no-website":
            software = "not picked"
        rec.software = software
        kept.append(rec)
    return kept


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
