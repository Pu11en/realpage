"""Assemble the reviewed first-pass selection without modifying worker evidence."""
from __future__ import annotations

import argparse
import copy
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from render_report import render_pdf


DOWNGRADES = {
    "brazos-bryan-sdrc-sp26-000056-lorca-apartments":
        "Exact street address was not resolved; retain as planning watchlist until the location is verified.",
    "grimes-iola-20260811-wwtp-contract":
        "The tender deadline has passed; an agenda naming a contract does not prove execution or open trade packages.",
    "grimes-navasota-pz-20260924-pecan-grove-phase2":
        "September 24 agenda is upcoming as of this September 20 report; verify the decision and executed agreement first.",
}
GEOGRAPHY_EXCLUSIONS = {
    "statewide-tdlr-tabs-TABS2026020630",
    "statewide-tdlr-tabs-TABS2026023109",
    "statewide-tdlr-tabs-TABS2026025873",
}
LANES = ("brazos", "burleson", "grimes", "leon", "madison", "robertson", "statewide", "washington")


def read(path):
    return json.loads(Path(path).read_text())


def unique(items):
    result, seen = [], set()
    for item in items:
        key = json.dumps(item, sort_keys=True)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def public_data(value):
    if isinstance(value, dict):
        return {k: public_data(v) for k, v in value.items()
                if k not in {"local_path", "evidence_local_paths_checked"}}
    if isinstance(value, list):
        return [public_data(v) for v in value
                if not (isinstance(v, str) and v.startswith(("/home/", "/tmp/")))]
    return value


def rank(record):
    scope = (record.get("scope") or "").lower()
    direct = any(w in scope for w in ("renovat", "remodel", "roof", "tenant", "interior",
                                      "addition", "parking", "paving", "drainage"))
    return (int(direct), int(record.get("record_type") == "permit"), record.get("record_date") or "")


def assemble(root: Path):
    originals = [r for lane in LANES for r in read(root / "review-input" / lane / "records.json")]
    by_id = {r["id"]: r for r in originals}
    assert len(by_id) == len(originals), "Duplicate source IDs"
    reviewed = [r for role in ("review-brazos", "review-west", "review-east")
                for r in read(root / "finish" / role / "reviewed_records.json")]
    contacts = read(root / "finish/contacts/contacts.json")
    selected, watchlist, audit = [], [], []
    for source in reviewed:
        if source.get("review_decision") != "include":
            continue
        record = copy.deepcopy(source)
        members = set(record.get("member_ids") or [record["id"]])
        members.add(record["id"])
        assert members <= by_id.keys(), "Unknown member ID"
        assert not members & GEOGRAPHY_EXCLUSIONS, "Out-of-area member in shortlist"
        if record["id"] in DOWNGRADES:
            record["review_decision"] = "watchlist"
            record["priority_reason"] = DOWNGRADES[record["id"]]
            watchlist.append(public_data(record))
            audit.append({"id": record["id"], "action": "watchlist", "reason": record["priority_reason"]})
            continue
        all_sources = list(record.get("sources") or [])
        for member in sorted(members):
            all_sources.extend(by_id[member].get("sources") or [])
            original = by_id[member]
            estimate = original.get("estimated_completion")
            if estimate and str(estimate)[:10] < "2026-09-20" and str(estimate)[:4].isdigit():
                record.setdefault("unknowns", []).append(
                    f"Related registration {original.get('source_record_id')} estimated completion "
                    f"{estimate}, now in the past; actual completion remains unverified.")
            value = original.get("estimated_value")
            if value and value != record.get("estimated_value"):
                record.setdefault("unknowns", []).append(
                    f"Related source {original.get('source_record_id')} reports {value}; "
                    "source values may cover different scopes and must not be added together.")
        for item in contacts:
            if members.intersection(item["record_ids"]):
                record.setdefault("business_contacts", []).append({
                    "name": item["verified_business_name"], "role": item["role"],
                    "phone": item.get("phone"), "email": item.get("email"),
                    "website": item.get("website"), "source_url": item["source_url"],
                    "role_basis": item.get("role_basis"),
                })
        # Collapse repeated organization/role entries while retaining sourced direct methods.
        merged_contacts = {}
        for contact in record.get("business_contacts") or []:
            key = (contact.get("name", "").casefold(), contact.get("role", "").casefold())
            previous = merged_contacts.setdefault(key, {})
            previous.update({k: v for k, v in contact.items() if v})
        record["business_contacts"] = list(merged_contacts.values())
        record["sources"] = unique(all_sources)
        for evidence in record["sources"]:
            assert urlsplit(evidence["url"]).scheme in {"http", "https"}, "Unsafe source URL"
            if evidence.get("local_path"):
                assert Path(evidence["local_path"]).is_file(), "Missing evidence"
        record["member_ids"] = sorted(members)
        record["unknowns"] = unique(record.get("unknowns") or [])
        record["availability"] = "Unverified: no currently open trade package established in this first pass."
        record["selection_basis"] = "Direct service fit, source evidence and recency; not project budget or sales probability."
        record["coordinator_reviewed_at"] = datetime.now(timezone.utc).isoformat()
        selected.append(public_data(record))
    selected.sort(key=rank, reverse=True)
    used = set()
    for index, record in enumerate(selected, 1):
        assert not used.intersection(record["member_ids"]), "Two selected profiles share a source record"
        used.update(record["member_ids"])
        record["rank"] = index
    coverage = public_data(read(root / "finish/coverage/coverage.json"))
    all_contacts = [c for r in selected for c in r["business_contacts"]]
    methods = {(c.get("name", "").casefold(), c.get("phone"), c.get("email"), c.get("website"))
               for c in all_contacts if c.get("phone") or c.get("email") or c.get("website")}
    stats = {
        "source_records_collected": len(originals),
        "out_of_area_source_records_excluded": len(GEOGRAPHY_EXCLUSIONS),
        "detailed_properties": len(selected),
        "county_counts": dict(sorted(Counter(r["county"] for r in selected).items())),
        "source_receipts": len(coverage),
        "contact_routes_with_phone_email_or_website": len(methods),
        "profiles_with_direct_contact_method": sum(any(c.get("phone") or c.get("email") or c.get("website")
                                                     for c in r["business_contacts"]) for r in selected),
        "open_trade_packages_confirmed": 0,
        "source_records_linked_to_detailed_profiles": len(used),
        "watchlist_downgrades": len(watchlist),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "report_date": "September 20, 2026 (Central)",
        "scope": "One bounded pilot; incomplete geographic/source coverage; not a verified open-bid list.",
        "unreviewed_brazos_records": 98,
        "clock_note": "Future worker checkpoint times were not used to measure duration; report uses coordinator clock.",
    }
    return selected, watchlist, coverage, stats, audit


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records, watchlist, coverage, stats, audit = assemble(args.root)
    args.output.mkdir(parents=True, exist_ok=True)
    for name, value in {
        "masiate-reviewed-properties.json": records,
        "masiate-watchlist.json": watchlist,
        "masiate-source-coverage.json": coverage,
        "masiate-report-summary.json": stats,
        "masiate-final-review.json": audit,
    }.items():
        (args.output / name).write_text(json.dumps(value, indent=2, ensure_ascii=True) + "\n")
    render_pdf(records, coverage, args.output / "Masiate-Top-Properties-2026-09-20.pdf",
               "Masiate Construction: Property Research", summary=stats, watchlist=watchlist)
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
