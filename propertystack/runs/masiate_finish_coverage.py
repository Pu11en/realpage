#!/usr/bin/env python3
"""Aggregate Masiate pilot source coverage from immutable review snapshots."""

from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


COUNTIES = ["Brazos", "Burleson", "Grimes", "Leon", "Madison", "Robertson", "Washington"]
LANE_ORDER = ["brazos", "burleson", "grimes", "leon", "madison", "robertson", "statewide", "washington"]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def json_default(value: Any) -> Any:
    if isinstance(value, Counter):
        return dict(value)
    if isinstance(value, set):
        return sorted(value)
    raise TypeError(f"Cannot serialize {type(value)!r}")


def normalize_files_read(files_read: Any) -> int:
    if isinstance(files_read, int):
        return files_read
    if isinstance(files_read, list):
        return len(files_read)
    if not files_read:
        return 0
    return 1


def public_receipt(entry: dict[str, Any], lane: str, idx: int) -> dict[str, Any]:
    files_read = entry.get("files_read")
    return {
        "receipt_id": f"{lane}-coverage-{idx + 1:03d}",
        "lane": lane,
        "name": entry.get("name"),
        "url": entry.get("url"),
        "county": entry.get("county"),
        "requested_from": entry.get("requested_from"),
        "requested_to": entry.get("requested_to"),
        "covered_from": entry.get("covered_from"),
        "covered_to": entry.get("covered_to"),
        "status": entry.get("status"),
        "records_found": entry.get("records_found", 0),
        "files_read_count": normalize_files_read(files_read),
        "files_read_sample": files_read[:6] if isinstance(files_read, list) else files_read,
        "reason": entry.get("reason"),
        "next_cursor": entry.get("next_cursor"),
        "retrieved_at": entry.get("retrieved_at"),
        "audit_notes": [],
    }


def add_audit_notes(receipt: dict[str, Any]) -> None:
    notes: list[str] = receipt["audit_notes"]
    status = receipt.get("status")
    name = (receipt.get("name") or "").lower()
    reason = (receipt.get("reason") or "").lower()
    next_cursor = receipt.get("next_cursor")
    covered_from = receipt.get("covered_from")
    covered_to = receipt.get("covered_to")
    requested_from = receipt.get("requested_from")
    requested_to = receipt.get("requested_to")

    if status != "complete":
        notes.append("Not exhausted; keep this as a gap in the PDF coverage section.")
    if status in {"blocked", "not_checked"}:
        notes.append("No claim of full county coverage should rely on this source.")
    if next_cursor:
        notes.append("Continuation path is documented.")
    if "aggregate" in reason:
        notes.append("Aggregate counts do not identify address-level leads.")
    if "account" in reason or "403" in reason or "401" in reason or "access denied" in reason:
        notes.append("Access restriction was recorded; no circumvention is implied.")
    if "issued-record register" in reason or "no public issued" in reason:
        notes.append("Source documents process or forms, not an issued permit register.")
    if "tdlr" in name:
        notes.append("TDLR/TABS is an accessibility registration source, not proof of open trade packages.")
    if covered_from is None or covered_to is None:
        notes.append("Covered date window is not fully established from saved evidence.")
    elif requested_from and requested_to and (covered_from != requested_from or covered_to != requested_to):
        notes.append("Covered dates differ from the requested window; do not summarize as complete window coverage without context.")


def classify_source(receipt: dict[str, Any]) -> str:
    name = (receipt.get("name") or "").lower()
    reason = (receipt.get("reason") or "").lower()
    if "tdlr" in name:
        return "statewide_registration"
    if "bid" in name or "rfb" in reason or "rfq" in reason or "purchasing" in name:
        return "bid_or_procurement"
    if "permit" in name or "accela" in name or "citizenserve" in name or "cloudpermit" in reason:
        return "permit"
    if "agenda" in name or "minutes" in name or "p&z" in name or "planning" in name or "dashboard" in name:
        return "planning_or_agenda"
    if "cad" in name:
        return "parcel_validation"
    return "other"


def build_coverage(review_input: Path) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    receipts: list[dict[str, Any]] = []
    lane_statuses: dict[str, dict[str, Any]] = {}
    records_by_lane: dict[str, list[dict[str, Any]]] = {}

    for lane in LANE_ORDER:
        lane_dir = review_input / lane
        if not lane_dir.exists():
            continue
        lane_statuses[lane] = read_json(lane_dir / "status.json")
        records_by_lane[lane] = read_json(lane_dir / "records.json")
        for idx, entry in enumerate(read_json(lane_dir / "coverage.json")):
            receipt = public_receipt(entry, lane, idx)
            receipt["source_class"] = classify_source(receipt)
            add_audit_notes(receipt)
            receipts.append(receipt)

    all_records = [record for records in records_by_lane.values() for record in records]
    status_counts = Counter(receipt.get("status") for receipt in receipts)
    source_class_counts = Counter(receipt.get("source_class") for receipt in receipts)
    local_path_missing: list[dict[str, str]] = []
    local_path_count = 0
    record_source_count = 0
    record_ids = set()
    duplicate_record_ids: list[str] = []
    sources_by_record = Counter()

    record_counts_by_county: dict[str, Counter] = defaultdict(Counter)
    local_counts_by_county: dict[str, Counter] = defaultdict(Counter)
    statewide_counts_by_county: dict[str, Counter] = defaultdict(Counter)
    source_receipts_by_county: dict[str, Counter] = defaultdict(Counter)

    for receipt in receipts:
        county = receipt.get("county") or "Unknown"
        source_receipts_by_county[county][receipt.get("status") or "unknown"] += 1

    for lane, records in records_by_lane.items():
        for record in records:
            rid = record.get("id")
            if rid in record_ids:
                duplicate_record_ids.append(rid)
            record_ids.add(rid)
            county = record.get("county") or "Unknown"
            bucket = record_counts_by_county[county]
            lane_bucket = statewide_counts_by_county[county] if lane == "statewide" else local_counts_by_county[county]
            for target in (bucket, lane_bucket):
                target["raw_records"] += 1
                target[f"record_type:{record.get('record_type') or 'unknown'}"] += 1
                target[f"stage:{record.get('stage') or 'unknown'}"] += 1
                target[f"disposition:{record.get('disposition') or 'unknown'}"] += 1
            sources = record.get("sources") or []
            sources_by_record[len(sources)] += 1
            for source in sources:
                record_source_count += 1
                local_path = source.get("local_path")
                if local_path:
                    local_path_count += 1
                    if not Path(local_path).exists():
                        local_path_missing.append({"record_id": rid, "local_path": local_path})

    counts = {
        "generated_at": utc_now(),
        "review_input_root": str(review_input),
        "scope_note": "Counts are source receipts and raw collected records, not deduped projects or final PDF leads.",
        "lanes": {
            lane: {
                "state": lane_statuses[lane].get("state"),
                "records_saved_reported": lane_statuses[lane].get("records_saved"),
                "records_json_count": len(records_by_lane.get(lane, [])),
                "coverage_receipts": sum(1 for receipt in receipts if receipt["lane"] == lane),
            }
            for lane in sorted(lane_statuses)
        },
        "totals": {
            "raw_records": len(all_records),
            "coverage_receipts": len(receipts),
            "record_source_entries": record_source_count,
            "record_source_local_paths": local_path_count,
            "missing_local_paths": len(local_path_missing),
            "duplicate_record_ids": len(duplicate_record_ids),
        },
        "coverage_status_counts": status_counts,
        "source_class_counts": source_class_counts,
        "records_by_county": {county: record_counts_by_county[county] for county in sorted(record_counts_by_county)},
        "local_records_by_county": {county: local_counts_by_county[county] for county in sorted(local_counts_by_county)},
        "statewide_records_by_county": {county: statewide_counts_by_county[county] for county in sorted(statewide_counts_by_county)},
        "source_receipts_by_county": {county: source_receipts_by_county[county] for county in sorted(source_receipts_by_county)},
        "record_source_entries_per_record": sources_by_record,
        "integrity": {
            "missing_local_paths": local_path_missing,
            "duplicate_record_ids": sorted(duplicate_record_ids),
        },
    }
    return receipts, counts, all_records


def counter_value(counter: Counter, key: str) -> int:
    return int(counter.get(key, 0))


def coverage_quality(source_counter: Counter) -> str:
    complete = counter_value(source_counter, "complete")
    partial = counter_value(source_counter, "partial")
    blocked = counter_value(source_counter, "blocked")
    empty = counter_value(source_counter, "empty")
    not_checked = counter_value(source_counter, "not_checked")
    if complete and not (partial or blocked or not_checked):
        return "strong for checked sources, still not whole-county coverage"
    if complete:
        return "mixed; some exhausted sources plus important partial/blocked sources"
    if partial or blocked:
        return "partial; no whole-county coverage claim"
    if empty:
        return "limited; checked sources yielded no project register"
    return "unknown"


def write_markdown(path: Path, receipts: list[dict[str, Any]], counts: dict[str, Any]) -> None:
    lines: list[str] = []
    totals = counts["totals"]
    lines.append("# Masiate Pilot Coverage Summary")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append("- This is a reconciliation of the immutable review-input snapshots only; it is not a new crawl.")
    lines.append("- Counts below are **raw collected records**, **source receipts** and **saved evidence checks**.")
    lines.append("- These numbers are not deduped projects, final leads, open contracts or available Masiate scopes.")
    lines.append("- TDLR/TABS records are accessibility registrations and should be labeled as planning/registration signals unless another source proves current bid or work status.")
    lines.append("")
    lines.append("## Top-Level Counts")
    lines.append("")
    lines.append(f"- Raw records collected: **{totals['raw_records']}**.")
    lines.append(f"- Source coverage receipts reconciled: **{totals['coverage_receipts']}**.")
    lines.append(f"- Record source entries checked for local evidence paths: **{totals['record_source_entries']}**.")
    lines.append(f"- Missing record evidence local paths: **{totals['missing_local_paths']}**.")
    lines.append(f"- Duplicate record IDs found: **{totals['duplicate_record_ids']}**.")
    lines.append("")
    lines.append("## Coverage Status")
    lines.append("")
    for status in ["complete", "partial", "blocked", "empty", "not_checked"]:
        value = counts["coverage_status_counts"].get(status, 0)
        lines.append(f"- {status}: **{value}** source receipts.")
    lines.append("")
    lines.append("## County Coverage")
    lines.append("")
    for county in COUNTIES:
        record_counter = counts["records_by_county"].get(county, Counter())
        local_counter = counts["local_records_by_county"].get(county, Counter())
        statewide_counter = counts["statewide_records_by_county"].get(county, Counter())
        source_counter = counts["source_receipts_by_county"].get(county, Counter())
        raw_records = counter_value(record_counter, "raw_records")
        local_records = counter_value(local_counter, "raw_records")
        statewide_records = counter_value(statewide_counter, "raw_records")
        candidates = counter_value(record_counter, "disposition:candidate")
        watchlist = counter_value(record_counter, "disposition:watchlist")
        excluded = counter_value(record_counter, "disposition:excluded")
        lines.append(f"### {county}")
        lines.append("")
        lines.append(f"- Raw records: **{raw_records}** total (**{local_records}** local, **{statewide_records}** statewide TDLR/TABS).")
        lines.append(f"- Dispositions before final review: **{candidates}** candidate, **{watchlist}** watchlist, **{excluded}** excluded.")
        lines.append(
            "- Source receipts: "
            f"**{sum(source_counter.values())}** total; "
            f"{counter_value(source_counter, 'complete')} complete, "
            f"{counter_value(source_counter, 'partial')} partial, "
            f"{counter_value(source_counter, 'blocked')} blocked, "
            f"{counter_value(source_counter, 'empty')} empty, "
            f"{counter_value(source_counter, 'not_checked')} not checked."
        )
        lines.append(f"- Coverage read: **{coverage_quality(source_counter)}**.")
        gap_receipts = [
            receipt
            for receipt in receipts
            if receipt.get("county") == county and receipt.get("status") != "complete"
        ][:4]
        if gap_receipts:
            lines.append("- Main gaps:")
            for receipt in gap_receipts:
                lines.append(f"  - {receipt.get('name')}: {receipt.get('status')} - {receipt.get('reason')}")
        lines.append("")
    lines.append("## Report Language To Preserve")
    lines.append("")
    lines.append("- Do not say the pilot covered every permit or project in any county.")
    lines.append("- Do say the pilot combined selected local official sources with statewide TDLR/TABS registrations.")
    lines.append("- Keep registrations, planning cases, permits, historical awards and open bids separate.")
    lines.append("- A partial or blocked source means the PDF should expose a gap, not smooth it over.")
    lines.append("- Existing local_path evidence was present for every record source checked in this coverage pass, but private paths should not be printed in public-facing PDF output.")
    lines.append("")
    path.write_text("\n".join(lines) + "\n")


def write_summary(path: Path, counts: dict[str, Any]) -> None:
    totals = counts["totals"]
    lines = [
        "# Coverage Worker Summary",
        "",
        "## Result",
        "",
        f"- Reconciled **{totals['coverage_receipts']}** source receipts and **{totals['raw_records']}** raw collected records from the immutable review-input snapshot.",
        f"- Verified that **{totals['record_source_local_paths']}** record source local paths exist; missing paths: **{totals['missing_local_paths']}**.",
        "- Wrote coverage.json, counts.json, coverage.md, summary.md and status.json in the coverage finish directory.",
        "",
        "## Main Coverage Read",
        "",
        "- Strongest exhausted source family is statewide TDLR/TABS recent-window registrations, plus selected complete local sources such as Grimes/Navasota ArcGIS and CivicClerk checks.",
        "- The local county picture is intentionally mixed: many permit systems, CAD lookups, city agendas and purchasing pages were only partial, blocked, aggregate-only or process-only.",
        "- PDF language should distinguish source receipts, raw records, distinct projects and final leads.",
        "",
        "## Key Warnings",
        "",
        "- TDLR/TABS registrations do not prove active bids or remaining subcontract availability.",
        "- Bryan/College Station, Caldwell, Navasota Citizenserve, Buffalo Revize, Calvert blobs and several issued-permit registers remain unresolved or blocked.",
        "- Madison output is partial and consists of planning records, not issued construction permits.",
        "- Public bid records with expired deadlines should be treated as award-follow-up/watchlist, not open contracts.",
    ]
    path.write_text("\n".join(lines) + "\n")


def mirror_outputs(out_dir: Path, mirror_dir: Path) -> None:
    mirror_dir.mkdir(parents=True, exist_ok=True)
    for name in ["coverage.json", "counts.json", "coverage.md", "summary.md", "status.json"]:
        shutil.copy2(out_dir / name, mirror_dir / name)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review-input", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--mirror-dir", type=Path)
    parser.add_argument("--started-at")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    existing_status_path = args.output_dir / "status.json"
    existing_status = read_json(existing_status_path) if existing_status_path.exists() else {}
    started_at = args.started_at or existing_status.get("started_at") or utc_now()

    receipts, counts, _records = build_coverage(args.review_input)
    counts["generated_at"] = utc_now()

    (args.output_dir / "coverage.json").write_text(json.dumps(receipts, indent=2, default=json_default) + "\n")
    (args.output_dir / "counts.json").write_text(json.dumps(counts, indent=2, default=json_default) + "\n")
    write_markdown(args.output_dir / "coverage.md", receipts, counts)
    write_summary(args.output_dir / "summary.md", counts)

    finished_at = utc_now()
    status = {
        "worker": "coverage",
        "state": "complete",
        "started_at": started_at,
        "checkpoint_at": finished_at,
        "finished_at": finished_at,
        "records_saved": counts["totals"]["raw_records"],
        "source_receipts_saved": counts["totals"]["coverage_receipts"],
        "output_paths": {
            "coverage_json": str(args.output_dir / "coverage.json"),
            "counts_json": str(args.output_dir / "counts.json"),
            "coverage_md": str(args.output_dir / "coverage.md"),
            "summary_md": str(args.output_dir / "summary.md"),
            "status_json": str(args.output_dir / "status.json"),
        },
        "notes": [
            "Reconciled immutable review-input source receipts and raw-record counts.",
            "No new collection, paid API use, outreach, pushes or live changes.",
            "All record source local_path references checked by this worker existed.",
        ],
    }
    (args.output_dir / "status.json").write_text(json.dumps(status, indent=2) + "\n")

    if args.mirror_dir:
        mirror_outputs(args.output_dir, args.mirror_dir)

    print(json.dumps(status, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
