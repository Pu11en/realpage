#!/usr/bin/env python3
"""Build and validate the offline Masiate all-row contact research ledger."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "propertystack/data/masiate/pilot-20260920"
RECORDS_PATH = DATA / "masiate-reviewed-properties.json"
PHONE_PATH = DATA / "masiate-business-phone-update.json"
RESEARCH_DIR = DATA / "contact-research"
MANIFEST_PATH = RESEARCH_DIR / "manifest.json"

BATCH_RANGES = {
    "batch-01": range(1, 14),
    "batch-02": range(14, 27),
    "batch-03": range(27, 40),
    "batch-04": range(40, 50),
}
RESEARCH_STATUSES = {"not_yet_researched", "in_progress", "researched"}
SOURCE_DISPOSITIONS = {
    "contact_found",
    "no_contact_fields",
    "inaccessible",
    "irrelevant",
    "duplicate",
    "privacy_only",
    "ambiguous_entity",
}
SOURCE_TYPES = {
    "official_company",
    "government_record",
    "institution",
    "association",
    "professional_profile",
    "directory",
    "other",
}
MATCH_STATUSES = {"confirmed", "provisional"}
SOURCE_STRENGTHS = {"strong", "provisional"}
GAP_REASON_CODES = {
    "actor_unknown",
    "no_public_business_contact",
    "inaccessible_source",
    "ambiguous_entity",
    "privacy_only",
    "no_suitable_role",
    "other_specific",
}
GENERIC_GAPS = {
    "not found",
    "none found",
    "no phone found",
    "no suitable public number found",
    "unknown",
    "n/a",
    "na",
}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_web_url(value: Any) -> bool:
    parsed = urlparse(str(value or ""))
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def clean_text(value: Any) -> str:
    return str(value or "").strip()


def valid_date(value: Any) -> bool:
    text = clean_text(value)
    if not DATE_RE.fullmatch(text):
        return False
    try:
        date.fromisoformat(text)
    except ValueError:
        return False
    return True


def batch_for_rank(rank: int) -> str:
    for batch_id, ranks in BATCH_RANGES.items():
        if rank in ranks:
            return batch_id
    raise ValueError(f"Rank {rank} is outside the fixed 1-49 inventory")


def _actors(record: dict[str, Any]) -> list[dict[str, Any]]:
    actors: dict[str, dict[str, Any]] = {}
    for raw in record.get("participants", []) + record.get("business_contacts", []):
        name = clean_text(raw.get("name"))
        role = clean_text(raw.get("role"))
        if not name or not role:
            continue
        key = name.casefold()
        actor = actors.setdefault(key, {"name": name, "roles": [], "source_urls": []})
        if role not in actor["roles"]:
            actor["roles"].append(role)
        source_url = clean_text(raw.get("source_url"))
        if is_web_url(source_url) and source_url not in actor["source_urls"]:
            actor["source_urls"].append(source_url)
    return list(actors.values())


def _source_links(record: dict[str, Any]) -> list[dict[str, Any]]:
    links: dict[str, dict[str, Any]] = {}
    for source in record.get("sources", []):
        url = clean_text(source.get("url"))
        if not is_web_url(url) or url in links:
            continue
        links[url] = {
            "url": url,
            "title": clean_text(source.get("title")),
            "recorded_date": source.get("date"),
            "evidence": clean_text(source.get("evidence")),
        }
    return list(links.values())


def _seed_contacts(
    record: dict[str, Any], phone_contacts: dict[str, dict[str, Any]], checked_on: str
) -> list[dict[str, Any]]:
    actor_roles: dict[str, str] = {}
    for actor in record.get("participants", []) + record.get("business_contacts", []):
        name = clean_text(actor.get("name"))
        role = clean_text(actor.get("role"))
        if name and role:
            actor_roles.setdefault(name, role)
    seeds = []
    for name, update in phone_contacts.items():
        if name not in actor_roles:
            continue
        status = update.get("phone_status")
        seeds.append(
            {
                "contact_name": name,
                "role": actor_roles[name],
                "phone": update.get("phone"),
                "email": update.get("email"),
                "website": update.get("website"),
                "source_url": update.get("source_url"),
                "source_type": "directory" if status == "directory_only" else (
                    "association" if status == "association_published" else "official_company"
                ),
                "match_status": "provisional" if status == "directory_only" else "confirmed",
                "source_strength": "provisional" if status == "directory_only" else "strong",
                "public_business_basis": update.get("phone_kind"),
                "match_evidence": update.get("match_basis"),
                "contact_note": update.get("contact_note"),
                "checked_on": checked_on,
            }
        )
    return seeds


def build_manifest(records_path: Path = RECORDS_PATH, phone_path: Path = PHONE_PATH) -> dict[str, Any]:
    records = load_json(records_path)
    phone_update = load_json(phone_path)
    by_rank = {int(record["rank"]): record for record in records}
    if len(records) != 49 or sorted(by_rank) != list(range(1, 50)):
        raise ValueError("Source records must contain ranks 1-49 exactly once")
    if len({record["id"] for record in records}) != 49:
        raise ValueError("Source records contain duplicate property IDs")

    properties = []
    for rank in range(1, 50):
        record = by_rank[rank]
        properties.append(
            {
                "property_id": record["id"],
                "rank": rank,
                "batch_id": batch_for_rank(rank),
                "project_name": record["project_name"],
                "location": {
                    "address": record.get("address"),
                    "city": record.get("city"),
                    "county": record.get("county"),
                },
                "actors": _actors(record),
                "source_links": _source_links(record),
                "seed_contacts": _seed_contacts(
                    record, phone_update["contacts"], clean_text(phone_update.get("checked_on"))
                ),
                "initial_research_status": "not_yet_researched",
            }
        )

    assignments = []
    for batch_id, ranks in BATCH_RANGES.items():
        assignments.append(
            {
                "batch_id": batch_id,
                "result_file": f"{batch_id}.json",
                "property_ids": [by_rank[rank]["id"] for rank in ranks],
            }
        )
    return {
        "schema_version": 1,
        "created_for": "Masiate all-row public business contact research",
        "source_records_file": records_path.name,
        "source_records_sha256": sha256(records_path),
        "property_count": 49,
        "batch_assignments": assignments,
        "properties": properties,
    }


@dataclass
class CoverageReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    result_count: int = 0
    researched_count: int = 0
    confirmed_phone_count: int = 0
    provisional_phone_count: int = 0
    researched_gap_count: int = 0

    @property
    def complete(self) -> bool:
        return self.researched_count == 49 and not self.errors


def _error(report: CoverageReport, property_id: str, message: str) -> None:
    report.errors.append(f"{property_id}: {message}")


def validate_manifest(manifest: dict[str, Any], report: CoverageReport) -> dict[str, dict[str, Any]]:
    properties = manifest.get("properties")
    if not isinstance(properties, list):
        report.errors.append("manifest: properties must be a list")
        return {}
    ids = [clean_text(item.get("property_id")) for item in properties]
    ranks = [item.get("rank") for item in properties]
    if len(properties) != 49 or len(set(ids)) != 49 or "" in ids:
        report.errors.append("manifest: must contain 49 unique non-empty property IDs")
    if sorted(ranks) != list(range(1, 50)):
        report.errors.append("manifest: ranks must be 1-49 exactly once")

    assignment_ids: list[str] = []
    assignments = manifest.get("batch_assignments", [])
    for assignment in assignments:
        batch_id = assignment.get("batch_id")
        if batch_id not in BATCH_RANGES:
            report.errors.append(f"manifest: unknown batch assignment {batch_id!r}")
        assignment_ids.extend(assignment.get("property_ids", []))
    if Counter(assignment_ids) != Counter(ids):
        report.errors.append("manifest: batch assignments must cover every property ID exactly once")

    for item in properties:
        property_id = clean_text(item.get("property_id")) or "<missing-property-id>"
        rank = item.get("rank")
        if isinstance(rank, int) and item.get("batch_id") != batch_for_rank(rank):
            _error(report, property_id, "batch_id does not match its fixed rank range")
        if item.get("initial_research_status") != "not_yet_researched":
            _error(report, property_id, "initial status must be not_yet_researched")
        actors = item.get("actors")
        if not isinstance(actors, list) or not actors:
            _error(report, property_id, "inventory must retain at least one named actor")
        else:
            for actor in actors:
                if not clean_text(actor.get("name")) or not actor.get("roles"):
                    _error(report, property_id, "every inventory actor needs a name and role")
        urls = [source.get("url") for source in item.get("source_links", [])]
        if len(urls) != len(set(urls)) or any(not is_web_url(url) for url in urls):
            _error(report, property_id, "source links must be unique HTTP(S) URLs")
    return {clean_text(item.get("property_id")): item for item in properties if item.get("property_id")}


def _validate_source_checks(
    result: dict[str, Any], inventory: dict[str, Any], report: CoverageReport
) -> dict[str, dict[str, Any]]:
    property_id = result["property_id"]
    checks = result.get("sources_checked")
    if not isinstance(checks, list) or not checks:
        _error(report, property_id, "researched result needs sources_checked")
        return {}
    checked: dict[str, dict[str, Any]] = {}
    for check in checks:
        url = clean_text(check.get("url"))
        if not is_web_url(url):
            _error(report, property_id, "each source check needs an HTTP(S) URL")
            continue
        if url in checked:
            _error(report, property_id, f"source checked more than once: {url}")
        checked[url] = check
        if check.get("disposition") not in SOURCE_DISPOSITIONS:
            _error(report, property_id, f"source {url} needs a valid disposition")
        if not clean_text(check.get("outcome")):
            _error(report, property_id, f"source {url} needs a written outcome")
        if not valid_date(check.get("checked_on")):
            _error(report, property_id, f"source {url} needs a valid checked_on date")
    expected_urls = {source["url"] for source in inventory.get("source_links", [])}
    for missing in sorted(expected_urls - set(checked)):
        _error(report, property_id, f"original source link is unchecked: {missing}")
    return checked


def _validate_actors(result: dict[str, Any], report: CoverageReport) -> None:
    property_id = result["property_id"]
    actors = result.get("actors_checked")
    if not isinstance(actors, list) or not actors:
        _error(report, property_id, "researched result needs actors_checked")
        return
    for actor in actors:
        if not clean_text(actor.get("name")):
            _error(report, property_id, "each checked actor needs a name")
        if not clean_text(actor.get("role")):
            _error(report, property_id, "each checked actor needs an actual role")
        if not clean_text(actor.get("outcome")):
            _error(report, property_id, "each checked actor needs a written outcome")


def _validate_contacts(
    result: dict[str, Any], checked_sources: dict[str, dict[str, Any]], report: CoverageReport
) -> dict[str, dict[str, Any]]:
    property_id = result["property_id"]
    contacts = result.get("contacts", [])
    if not isinstance(contacts, list):
        _error(report, property_id, "contacts must be a list")
        return {}
    by_id: dict[str, dict[str, Any]] = {}
    for contact in contacts:
        route_id = clean_text(contact.get("route_id"))
        if not route_id or route_id in by_id:
            _error(report, property_id, "contact route_id values must be unique and non-empty")
            continue
        by_id[route_id] = contact
        if not clean_text(contact.get("contact_name")):
            _error(report, property_id, f"contact {route_id} needs a name")
        if not clean_text(contact.get("role")):
            _error(report, property_id, f"contact {route_id} lost its actual role")
        if not any(clean_text(contact.get(key)) for key in ("phone", "email", "website")):
            _error(report, property_id, f"contact {route_id} has no usable route")
        source_url = clean_text(contact.get("source_url"))
        if not is_web_url(source_url) or source_url not in checked_sources:
            _error(report, property_id, f"contact {route_id} source_url lacks a checked source")
        if contact.get("source_type") not in SOURCE_TYPES:
            _error(report, property_id, f"contact {route_id} needs a valid source_type")
        if contact.get("match_status") not in MATCH_STATUSES:
            _error(report, property_id, f"contact {route_id} needs a valid match_status")
        if contact.get("source_strength") not in SOURCE_STRENGTHS:
            _error(report, property_id, f"contact {route_id} needs a valid source_strength")
        if not valid_date(contact.get("checked_on")):
            _error(report, property_id, f"contact {route_id} needs a valid checked_on date")
        if not clean_text(contact.get("public_business_basis")):
            _error(report, property_id, f"contact {route_id} needs a public-business basis")
        if not clean_text(contact.get("match_evidence")):
            _error(report, property_id, f"contact {route_id} needs entity/project match evidence")
        if clean_text(contact.get("phone")) and not is_web_url(source_url):
            _error(report, property_id, f"contact {route_id} phone is missing provenance")
        if (
            contact.get("match_status") == "provisional"
            or contact.get("source_type") == "directory"
        ) and contact.get("source_strength") == "strong":
            _error(report, property_id, f"ambiguous contact {route_id} cannot count as strong")
    return by_id


def _validate_selection(
    result: dict[str, Any], contacts: dict[str, dict[str, Any]], report: CoverageReport
) -> None:
    property_id = result["property_id"]
    selected_id = clean_text(result.get("selected_route_id"))
    alternatives = result.get("alternative_route_ids", [])
    if not isinstance(alternatives, list) or len(alternatives) > 2:
        _error(report, property_id, "alternative_route_ids must contain at most two routes")
        alternatives = []
    if len(alternatives) != len(set(alternatives)) or selected_id in alternatives:
        _error(report, property_id, "selected and alternative route IDs must be distinct")
    for route_id in alternatives:
        if route_id not in contacts:
            _error(report, property_id, f"unknown alternative route_id {route_id!r}")

    if selected_id:
        selected = contacts.get(selected_id)
        if not selected:
            _error(report, property_id, f"unknown selected_route_id {selected_id!r}")
            return
        if not clean_text(selected.get("phone")):
            _error(report, property_id, "selected route must provide a public business phone")
            return
        if result.get("researched_gap") not in (None, {}):
            _error(report, property_id, "a selected phone route and researched_gap are mutually exclusive")
        if selected.get("source_strength") == "strong":
            report.confirmed_phone_count += 1
        else:
            report.provisional_phone_count += 1
        return

    gap = result.get("researched_gap")
    if not isinstance(gap, dict):
        _error(report, property_id, "no selected phone: a researched_gap is required")
        return
    if gap.get("reason_code") not in GAP_REASON_CODES:
        _error(report, property_id, "researched_gap needs a specific reason_code")
    explanation = clean_text(gap.get("explanation"))
    if explanation.casefold() in GENERIC_GAPS or len(explanation) < 30:
        _error(report, property_id, "researched_gap explanation is unsupported or generic")
    steps = gap.get("research_steps")
    if not isinstance(steps, list) or len([step for step in steps if clean_text(step)]) < 2:
        _error(report, property_id, "researched_gap needs at least two specific research steps")
    if not valid_date(gap.get("checked_on")):
        _error(report, property_id, "researched_gap needs a valid checked_on date")
    report.researched_gap_count += 1


def validate_result(
    result: dict[str, Any], inventory: dict[str, Any], report: CoverageReport
) -> None:
    property_id = result["property_id"]
    if result.get("rank") != inventory.get("rank"):
        _error(report, property_id, "rank does not match the immutable inventory")
    status = result.get("research_status")
    if status not in RESEARCH_STATUSES:
        _error(report, property_id, "research_status is invalid")
        return
    if status != "researched":
        return
    report.researched_count += 1
    checked_sources = _validate_source_checks(result, inventory, report)
    _validate_actors(result, report)
    contacts = _validate_contacts(result, checked_sources, report)
    _validate_selection(result, contacts, report)


def validate_coverage(
    manifest: dict[str, Any], result_documents: list[dict[str, Any]], require_complete: bool = False
) -> CoverageReport:
    report = CoverageReport()
    inventory = validate_manifest(manifest, report)
    seen: set[str] = set()
    for document in result_documents:
        batch_id = document.get("batch_id")
        if batch_id not in BATCH_RANGES:
            report.errors.append(f"results: unknown batch_id {batch_id!r}")
        properties = document.get("properties")
        if not isinstance(properties, list):
            report.errors.append(f"{batch_id or 'results'}: properties must be a list")
            continue
        for result in properties:
            property_id = clean_text(result.get("property_id"))
            if not property_id:
                report.errors.append(f"{batch_id}: result is missing property_id")
                continue
            report.result_count += 1
            if property_id in seen:
                _error(report, property_id, "duplicate research result")
                continue
            seen.add(property_id)
            expected = inventory.get(property_id)
            if not expected:
                _error(report, property_id, "not present in immutable inventory")
                continue
            if batch_id != expected.get("batch_id"):
                _error(report, property_id, "result is in the wrong batch")
            validate_result(result, expected, report)

    missing = sorted(set(inventory) - seen)
    if require_complete:
        if missing:
            report.errors.append(f"coverage: {len(missing)} property IDs have no result")
        unfinished = sorted(
            property_id
            for document in result_documents
            for result in document.get("properties", [])
            if (property_id := clean_text(result.get("property_id")))
            and result.get("research_status") != "researched"
        )
        if unfinished:
            report.errors.append(f"coverage: {len(unfinished)} property IDs are not researched")
    elif missing:
        report.warnings.append(f"partial coverage: {len(missing)} property IDs have no result yet")
    return report


def load_result_documents(results_dir: Path) -> list[dict[str, Any]]:
    documents = []
    for path in sorted(results_dir.glob("batch-*.json")):
        if path.name == "manifest.json":
            continue
        documents.append(load_json(path))
    return documents


def print_report(report: CoverageReport, require_complete: bool) -> None:
    status = "COMPLETE" if report.complete else ("INVALID" if report.errors else "PARTIAL")
    print(f"Contact coverage: {status}")
    print(f"Result rows: {report.result_count}/49")
    print(f"Researched rows: {report.researched_count}/49")
    print(f"Confirmed/strong phone routes: {report.confirmed_phone_count}")
    print(f"Provisional/best-guess phone routes: {report.provisional_phone_count}")
    print(f"Researched no-number gaps: {report.researched_gap_count}")
    for warning in report.warnings:
        print(f"WARNING: {warning}")
    for error in report.errors:
        print(f"ERROR: {error}")
    if require_complete and not report.complete and not report.errors:
        print("ERROR: final coverage gate is incomplete")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--results-dir", type=Path, default=RESEARCH_DIR)
    parser.add_argument("--require-complete", action="store_true")
    parser.add_argument(
        "--write-manifest",
        action="store_true",
        help="regenerate the fixed inventory from the original records and phone supplement",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.write_manifest:
        manifest = build_manifest()
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {args.manifest} with 49 immutable property IDs")
    manifest = load_json(args.manifest)
    report = validate_coverage(manifest, load_result_documents(args.results_dir), args.require_complete)
    print_report(report, args.require_complete)
    if report.errors or (args.require_complete and not report.complete):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
