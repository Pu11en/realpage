#!/usr/bin/env python3
"""Build the review-west finalization outputs from preserved pilot inputs."""

from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/home/drewp/.local/state/cranesignal/masiate/pilot-20260920-2048")
INPUT = ROOT / "review-input"
OUT = ROOT / "finish" / "review-west"
MIRROR = Path("docs/plans/masiate-review-west-output")
COUNTIES = {"Robertson", "Burleson", "Washington"}


GROUPS = {
    "burleson-somerville-rfq-2025-new-city-hall-150-8th": "statewide-tdlr-tabs-TABS2026021872",
    "washington-brenham-permit-com-new-26-0014": "washington-brenham-permit-com-new-26-0014",
    "statewide-tdlr-tabs-TABS2026023085": "washington-brenham-permit-com-new-26-0014",
    "washington-brenham-permit-misc-prkg-26-0018-grace-drainage": "washington-brenham-permit-misc-prkg-26-0018-grace-drainage",
    "statewide-tdlr-tabs-TABS2026022754": "washington-brenham-permit-misc-prkg-26-0018-grace-drainage",
    "washington-brenham-permit-com-new-26-0011": "washington-brenham-permit-com-new-26-0011",
    "statewide-tdlr-tabs-TABS2026020346": "washington-brenham-permit-com-new-26-0011",
    "washington-brenham-permit-com-add-26-0006": "washington-brenham-permit-com-add-26-0006",
    "statewide-tdlr-tabs-TABS2026017664": "washington-brenham-permit-com-add-26-0006",
    "washington-brenham-permit-com-new-26-0012": "washington-brenham-permit-com-new-26-0012",
    "statewide-tdlr-tabs-TABS2026021492": "washington-brenham-permit-com-new-26-0012",
    "washington-brenham-permit-com-rem-26-0028": "washington-brenham-permit-com-rem-26-0028",
    "statewide-tdlr-tabs-TABS2026027978": "washington-brenham-permit-com-rem-26-0028",
}


INCLUDE = {
    "statewide-tdlr-tabs-TABS2026019833": "Robertson hotel new-construction registration has an identifiable address, dated TDLR record and direct fit for sitework, framing, roofing, finishes, plumbing and electrical; availability remains unknown.",
    "statewide-tdlr-tabs-TABS2026018848": "Robertson bank branch new construction has address-level TDLR evidence and a broad trade fit; availability remains unknown.",
    "statewide-tdlr-tabs-TABS2026014890": "Robertson office renovation is smaller than several projects but has a direct remodel/finish-services fit and an active 2026 TDLR window; availability remains unknown.",
    "statewide-tdlr-tabs-TABS2026014091": "Franklin ISD ag classroom addition is a separate metal-building and renovation phase with concrete, metal, finish and MEP fit; availability remains unknown.",
    "statewide-tdlr-tabs-TABS2026014016": "Franklin ISD field house addition is a distinct same-campus phase with locker room/restroom work and metal-building fit; availability remains unknown.",
    "statewide-tdlr-tabs-TABS2026008039": "Hearne ISD gymnasium record has direct new-construction, parking, restroom, concession and finish scopes; availability remains unknown.",
    "burleson-somerville-ord-26-011-avenue-p-multifamily": "Somerville multifamily SUP is planning-stage, but it is recent, address-level by tract, and strong for Masiate trades if site-plan/building permits follow.",
    "statewide-tdlr-tabs-TABS2026024787": "Somerville ISD Phase 2 has separate new ag/athletic/concession buildings and a current TDLR review; availability remains unknown.",
    "statewide-tdlr-tabs-TABS2026021872": "Somerville City Hall has current TDLR evidence for new city hall, parking and landscape work; the older RFQ is expired and only supports project history.",
    "statewide-tdlr-tabs-TABS2026028954": "Snook Watering Hole is not the largest job, but restroom, bar and seating additions are a concrete Masiate remodel fit; availability remains unknown.",
    "washington-brenham-permit-com-new-26-0010-apartment": "Brenham multifamily permit is local, recent, permitted and directly fits multiple Masiate residential/commercial trades; subcontract availability remains unknown.",
    "washington-brenham-permit-com-add-26-0008-stanpac-silos": "Stanpac silo addition is local, permitted, and likely needs concrete, metal, utility or site trades; owner/prime status remains unknown.",
    "washington-brenham-permit-com-new-26-0014": "Lex/Edward Jones tenant office buildout is supported by local permit plus TDLR record; interior buildout services fit, but contractor control is unknown.",
    "washington-brenham-permit-com-roof-26-0003": "Commercial roof replacement is a direct Masiate service fit with recent local permit evidence, even though the listed contractor may control the work.",
    "washington-brenham-permit-com-new-26-0013": "Wilkins Valley phase 3 has recent local permit evidence for public infrastructure/site development and concrete/sitework fit; parcel details need follow-up.",
    "washington-brenham-permit-com-add-26-0001-rv-parking": "RV parking addition is a modest but direct paving/sitework fit with local permit evidence; contractor and status remain unknown.",
    "washington-brenham-permit-com-new-26-0007": "Redeemer Church parking lot phase is a direct paving/drainage/lighting/fencing fit with local permit evidence; kept separate from the older campus TDLR phase.",
    "washington-brenham-permit-com-new-26-0009-apartments": "Arete apartments are local, recent and permitted with 13 units across two buildings, a strong concrete/framing/finish fit; parcel/contractor details remain incomplete.",
    "washington-brenham-permit-misc-prkg-26-0018-grace-drainage": "Grace paving/drainage has both local permit and TDLR support, with direct concrete/drainage/paving fit; named contractor is not exposed.",
    "washington-brenham-permit-com-new-26-0011": "Frost Bank has local permit, CAD and TDLR support for ground-up bank construction; SpawGlass is listed, so package availability is unknown.",
    "washington-brenham-permit-com-add-26-0006": "Moeller Electric has local permit, CAD and TDLR support for a 5,000 sf metal-building addition, a strong metal/concrete/electrical fit.",
    "washington-brenham-permit-com-rem-26-0028": "Brenham maintenance building fire remodel has local permit plus TDLR support for code/fire repair, a direct remodel/MEP/finish fit.",
    "washington-brenham-permit-com-new-26-0012": "Citizens National Bank has local permit, CAD and TDLR support for ground-up bank construction plus parking, with broad trade fit and unknown package availability.",
    "statewide-tdlr-tabs-TABS2027001180": "Brenham Rodeo C-store has a very recent TDLR registration and direct new-construction fit, but it is registration-only and starts after this pilot window.",
    "statewide-tdlr-tabs-TABS2027001065": "TSC interior renovation is a direct remodel fit, but the TDLR estimated start is 2027, so it should be labeled future/unknown rather than open work.",
}


EXCLUDE = {
    "robertson-hearne-208-fulton-fence-variance-2026-08-25": "Private/small fence-variance matter was tabled; no business buyer or approved work should be exported.",
    "statewide-tdlr-tabs-TABS2026023109": "Address is Port Arthur, not the review-west county geography; likely false county match.",
    "statewide-tdlr-tabs-TABS2026020630": "Record is for City of Burleson at 141 W Renfro, outside Burleson County review-west geography.",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_records() -> list[dict]:
    records: list[dict] = []
    for lane in ("robertson", "burleson", "washington"):
        records.extend(json.loads((INPUT / lane / "records.json").read_text()))
    statewide = json.loads((INPUT / "statewide" / "records.json").read_text())
    records.extend([record for record in statewide if record.get("county") in COUNTIES])
    return records


def evidence_list(record: dict) -> list[str]:
    checked: list[str] = []
    for source in record.get("sources", []):
        url = source.get("url")
        local_path = source.get("local_path")
        if url:
            checked.append(url)
        if local_path:
            checked.append(local_path)
    return checked


def source_paths(record: dict) -> list[str]:
    return [s["local_path"] for s in record.get("sources", []) if s.get("local_path")]


def combined_evidence(member_ids: list[str], by_id: dict[str, dict]) -> list[str]:
    seen: set[str] = set()
    checked: list[str] = []
    for member_id in member_ids:
        record = by_id.get(member_id)
        if not record:
            continue
        for item in evidence_list(record):
            if item not in seen:
                checked.append(item)
                seen.add(item)
    return checked


def combined_paths(member_ids: list[str], by_id: dict[str, dict]) -> list[str]:
    seen: set[str] = set()
    paths: list[str] = []
    for member_id in member_ids:
        record = by_id.get(member_id)
        if not record:
            continue
        for item in source_paths(record):
            if item not in seen:
                paths.append(item)
                seen.add(item)
    return paths


def group_members(record_id: str, all_ids: set[str]) -> list[str]:
    canonical = GROUPS.get(record_id, record_id)
    members = sorted([rid for rid, cid in GROUPS.items() if cid == canonical and rid in all_ids])
    if canonical in all_ids and canonical not in members:
        members.append(canonical)
    return sorted(set(members or [record_id]))


def correction_notes(record: dict, decision: str, reason: str) -> list[str]:
    notes = [
        "Treat project value as total source-reported cost/value, not Masiate contract value.",
        "Do not print local_path values in public PDF output; use them only for audit.",
        "Work availability is unknown unless the source explicitly says a bid is open.",
    ]
    if record.get("record_type") == "registration":
        notes.append("TDLR registration/review status is not an open contract or permit by itself.")
    if record.get("record_type") == "planning":
        notes.append("Planning or zoning action does not prove a building permit or active construction.")
    if record.get("record_type") == "bid" and record.get("bid_deadline"):
        notes.append("Bid deadline must be treated as expired/historical unless a later award record is found.")
    if record["id"] in GROUPS:
        notes.append(f"Use this ID as support for canonical project group {GROUPS[record['id']]}; do not double-count it as a separate detailed lead.")
    if decision == "exclude":
        notes.append(reason)
    return notes


def watch_reason(record: dict) -> str:
    if record["id"] in GROUPS:
        return f"Supporting evidence for canonical project group {GROUPS[record['id']]}; keep for audit and dedup context."
    if record.get("record_type") == "bid":
        return "Expired or historical bid/procurement item; useful context only until award/current status is verified."
    if record.get("record_type") == "planning":
        return "Planning-stage signal without a confirmed permit, current construction status or open trade package."
    if record.get("record_type") == "registration":
        return "TDLR registration-only signal; needs local permit, current status or contractor path before detailed use."
    return "Lower service-fit or lower evidence strength than the included PDF candidates."


def build_outputs() -> tuple[list[dict], dict]:
    source_records = load_records()
    by_id = {record["id"]: record for record in source_records}
    all_ids = {record["id"] for record in source_records}
    reviewed_at = now_utc()
    reviewed: list[dict] = []
    decisions: list[dict] = []

    for record in sorted(source_records, key=lambda r: (r.get("county", ""), r.get("record_date") or "", r.get("id", ""))):
        rid = record["id"]
        if rid in INCLUDE:
            decision = "include"
            reason = INCLUDE[rid]
            reviewed_bool = True
        elif rid in EXCLUDE:
            decision = "exclude"
            reason = EXCLUDE[rid]
            reviewed_bool = True
        else:
            decision = "watchlist"
            reason = watch_reason(record)
            reviewed_bool = True

        out = copy.deepcopy(record)
        out["member_ids"] = group_members(rid, all_ids)
        out["review_decision"] = decision
        out["priority_reason"] = reason
        out["reviewed_at"] = reviewed_at
        out["evidence_checked"] = combined_evidence(out["member_ids"], by_id)
        out["corrections"] = correction_notes(record, decision, reason)
        reviewed.append(out)
        decisions.append(
            {
                "id": rid,
                "county": record.get("county"),
                "project_name": record.get("project_name"),
                "reviewed": reviewed_bool,
                "review_decision": decision,
                "canonical_member_ids": out["member_ids"],
                "disposition_reason": reason,
                "source_local_paths_checked": combined_paths(out["member_ids"], by_id),
            }
        )

    include_count = sum(1 for r in reviewed if r["review_decision"] == "include")
    watch_count = sum(1 for r in reviewed if r["review_decision"] == "watchlist")
    exclude_count = sum(1 for r in reviewed if r["review_decision"] == "exclude")
    decision_doc = {
        "worker": "review-west",
        "reviewed_at": reviewed_at,
        "input_scope": {
            "counties": sorted(COUNTIES),
            "local_lanes": ["robertson", "burleson", "washington"],
            "statewide_filter": sorted(COUNTIES),
        },
        "counts": {
            "source_records_accounted_for": len(source_records),
            "reviewed_records": len(reviewed),
            "include": include_count,
            "watchlist": watch_count,
            "exclude": exclude_count,
        },
        "notes": [
            "Included records are recommended for detailed PDF consideration, not validated open contracts.",
            "Watchlist records preserve registrations, planning items, expired bids and duplicate/supporting phases without double-counting them as detailed leads.",
            "Private homeowner contact details were not added; no new outreach, purchases, live changes or paid APIs were used.",
            "Distinct phases and permits at the same address were kept separate unless a local permit and TDLR record clearly supported the same scope.",
        ],
        "decisions": decisions,
    }
    return reviewed, decision_doc


def write_summary(reviewed: list[dict], decision_doc: dict, finished_at: str) -> str:
    include = [r for r in reviewed if r["review_decision"] == "include"]
    by_county = {}
    for record in reviewed:
        by_county.setdefault(record["county"], {"include": 0, "watchlist": 0, "exclude": 0})
        by_county[record["county"]][record["review_decision"]] += 1
    lines = [
        "# Review West Finalization Summary",
        "",
        "## Status",
        "",
        f"- Worker: review-west",
        f"- Finished at UTC: {finished_at}",
        f"- Source records accounted for: {decision_doc['counts']['source_records_accounted_for']}",
        f"- Recommended PDF includes: {decision_doc['counts']['include']}",
        f"- Watchlist records preserved: {decision_doc['counts']['watchlist']}",
        f"- Excluded records: {decision_doc['counts']['exclude']}",
        "- No new crawl, paid API call, outreach, push, live change or extra agent was used.",
        "",
        "## County Counts",
        "",
    ]
    for county in sorted(by_county):
        counts = by_county[county]
        lines.append(f"- {county}: {counts['include']} include, {counts['watchlist']} watchlist, {counts['exclude']} exclude.")
    lines.extend(
        [
            "",
            "## Best Service-Fit Includes",
            "",
        ]
    )
    for record in include:
        lines.append(f"- {record['county']} - {record['project_name']} ({record['address']}): {record['priority_reason']}")
    lines.extend(
        [
            "",
            "## Important Corrections",
            "",
            "- TDLR records are registrations/reviews only, not proof of open contracts.",
            "- Planning approvals and zoning/SUP items are not building permits unless the source says so.",
            "- Expired bid deadlines were treated as historical/watchlist unless later current evidence exists.",
            "- Project values are source project values, not Masiate contract values.",
            "- Local evidence paths are retained in JSON for audit but should not print in public PDF output.",
            "- Private homeowner contact details were not exported; small private matters were excluded or left as watchlist only.",
            "",
            "## Continuation Steps",
            "",
            "- Coordinator/pdf-renderer can use reviewed_records.json directly; only review_decision=include should become detailed primary profiles.",
            "- Contacts worker should prioritize business owner/GC paths for included local-permit records where package availability is unknown.",
            "- Dedup worker should avoid merging distinct Franklin ISD phases, Redeemer parking versus older campus work, and separate Brenham permits at the same address.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    MIRROR.mkdir(parents=True, exist_ok=True)
    reviewed, decisions = build_outputs()
    finished_at = now_utc()
    status = {
        "worker": "review-west",
        "status": "complete",
        "started_at_utc": "2026-09-21T02:19:47Z",
        "checkpoint_at_utc": finished_at,
        "finished_at_utc": finished_at,
        "deadline_utc": "2026-09-21T02:38:00Z",
        "records_accounted_for": decisions["counts"]["source_records_accounted_for"],
        "reviewed_records": decisions["counts"]["reviewed_records"],
        "recommended_includes": decisions["counts"]["include"],
        "watchlist_records": decisions["counts"]["watchlist"],
        "excluded_records": decisions["counts"]["exclude"],
        "output_paths": {
            "reviewed_records": str(OUT / "reviewed_records.json"),
            "decisions": str(OUT / "decisions.json"),
            "summary": str(OUT / "summary.md"),
            "repo_mirror": str(Path.cwd() / MIRROR),
        },
        "notes": [
            "Used preserved source evidence at local_path only.",
            "No new crawl, paid API call, outreach, push, live change or extra agent.",
            "Detailed include recommendations preserve units, suites, phases and distinct permits.",
        ],
    }
    summary = write_summary(reviewed, decisions, finished_at)

    for base in (OUT, MIRROR):
        (base / "reviewed_records.json").write_text(json.dumps(reviewed, indent=2) + "\n")
        (base / "decisions.json").write_text(json.dumps(decisions, indent=2) + "\n")
        (base / "summary.md").write_text(summary)
        (base / "status.json").write_text(json.dumps(status, indent=2) + "\n")


if __name__ == "__main__":
    main()
