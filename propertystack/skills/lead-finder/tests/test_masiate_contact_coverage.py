from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
MODULE_PATH = ROOT / "tooling/masiate_pdf/contact_coverage.py"
spec = importlib.util.spec_from_file_location("masiate_contact_coverage", MODULE_PATH)
coverage = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = coverage
spec.loader.exec_module(coverage)

MANIFEST = json.loads(coverage.MANIFEST_PATH.read_text(encoding="utf-8"))


def make_result(item, *, with_phone=True):
    checks = [
        {
            "url": source["url"],
            "disposition": "no_contact_fields",
            "outcome": "Reviewed the source; it identifies the project but has no public business phone.",
            "checked_on": "2026-09-20",
        }
        for source in item["source_links"]
    ]
    actors = [
        {
            "name": item["actors"][0]["name"],
            "role": item["actors"][0]["roles"][0],
            "outcome": "Checked this actor as the first relevant public business route.",
        }
    ]
    contacts = []
    selected = None
    gap = {
        "reason_code": "no_public_business_contact",
        "explanation": "The project source and a separate official contact search exposed no suitable public business number.",
        "research_steps": [
            "Reviewed every original project source.",
            "Checked the identifiable actor's official contact presence.",
        ],
        "checked_on": "2026-09-20",
    }
    if with_phone:
        source_url = item["source_links"][0]["url"]
        checks[0]["disposition"] = "contact_found"
        checks[0]["outcome"] = "Published a public business phone for the named project actor."
        contacts = [
            {
                "route_id": "primary",
                "contact_name": item["actors"][0]["name"],
                "role": item["actors"][0]["roles"][0],
                "phone": "979-555-0100",
                "email": None,
                "website": source_url,
                "public_business_basis": "Published as the actor's business office number.",
                "match_evidence": "Exact actor name and project source agree.",
                "source_type": "government_record",
                "source_url": source_url,
                "checked_on": "2026-09-20",
                "match_status": "confirmed",
                "source_strength": "strong",
            }
        ]
        selected = "primary"
        gap = None
    return {
        "property_id": item["property_id"],
        "rank": item["rank"],
        "research_status": "researched",
        "sources_checked": checks,
        "actors_checked": actors,
        "contacts": contacts,
        "selected_route_id": selected,
        "alternative_route_ids": [],
        "researched_gap": gap,
    }


def complete_documents():
    by_batch = {batch_id: {"batch_id": batch_id, "properties": []} for batch_id in coverage.BATCH_RANGES}
    for item in MANIFEST["properties"]:
        by_batch[item["batch_id"]]["properties"].append(make_result(item))
    return list(by_batch.values())


def test_manifest_is_the_fixed_49_row_inventory_with_four_disjoint_batches():
    assert MANIFEST["property_count"] == 49
    assert [item["rank"] for item in MANIFEST["properties"]] == list(range(1, 50))
    assert len({item["property_id"] for item in MANIFEST["properties"]}) == 49
    assert [len(batch["property_ids"]) for batch in MANIFEST["batch_assignments"]] == [13, 13, 13, 10]
    assigned = [property_id for batch in MANIFEST["batch_assignments"] for property_id in batch["property_ids"]]
    assert len(assigned) == len(set(assigned)) == 49
    assert {item["initial_research_status"] for item in MANIFEST["properties"]} == {"not_yet_researched"}
    assert sum(len(item["seed_contacts"]) for item in MANIFEST["properties"]) == 9
    assert sum(
        seed["source_strength"] == "provisional"
        for item in MANIFEST["properties"]
        for seed in item["seed_contacts"]
    ) == 1
    assert MANIFEST == coverage.build_manifest()


def test_partial_mode_allows_unfinished_batches_without_claiming_complete():
    report = coverage.validate_coverage(MANIFEST, [], require_complete=False)
    assert not report.errors
    assert report.warnings == ["partial coverage: 49 property IDs have no result yet"]
    assert not report.complete


def test_final_gate_accepts_exact_complete_research_and_counts_strengths_separately():
    documents = complete_documents()
    first = documents[0]["properties"][0]
    first["contacts"][0]["match_status"] = "provisional"
    first["contacts"][0]["source_strength"] = "provisional"
    report = coverage.validate_coverage(MANIFEST, documents, require_complete=True)
    assert report.errors == []
    assert report.complete
    assert report.result_count == report.researched_count == 49
    assert report.confirmed_phone_count == 48
    assert report.provisional_phone_count == 1


def test_final_gate_rejects_missing_and_duplicate_property_ids():
    documents = complete_documents()
    duplicate = copy.deepcopy(documents[0]["properties"][0])
    documents[0]["properties"].append(duplicate)
    documents[-1]["properties"].pop()
    report = coverage.validate_coverage(MANIFEST, documents, require_complete=True)
    assert any("duplicate research result" in error for error in report.errors)
    assert any("property IDs have no result" in error for error in report.errors)


def test_validator_rejects_unchecked_links_role_loss_missing_provenance_and_false_strength():
    documents = complete_documents()
    first = documents[0]["properties"][0]
    first["sources_checked"].pop()
    first["actors_checked"][0]["role"] = ""
    first["contacts"][0]["source_url"] = "https://unreviewed.example/contact"
    first["contacts"][0]["match_status"] = "provisional"
    first["contacts"][0]["source_strength"] = "strong"
    report = coverage.validate_coverage(MANIFEST, documents, require_complete=True)
    errors = "\n".join(report.errors)
    assert "original source link is unchecked" in errors
    assert "actual role" in errors
    assert "source_url lacks a checked source" in errors
    assert "cannot count as strong" in errors


def test_validator_rejects_generic_unsupported_no_number_reason():
    item = MANIFEST["properties"][0]
    result = make_result(item, with_phone=False)
    result["researched_gap"]["explanation"] = "No phone found"
    report = coverage.validate_coverage(
        MANIFEST,
        [{"batch_id": item["batch_id"], "properties": [result]}],
        require_complete=False,
    )
    assert any("unsupported or generic" in error for error in report.errors)


def test_validator_rejects_non_phone_text_and_does_not_count_it_as_confirmed():
    documents = complete_documents()
    first = documents[0]["properties"][0]
    first["contacts"][0]["phone"] = "not a phone number"
    report = coverage.validate_coverage(MANIFEST, documents, require_complete=True)
    assert any("phone is not a usable phone number" in error for error in report.errors)
    assert report.confirmed_phone_count == 48
    assert not report.complete


def test_validator_requires_phone_evidence_disposition_before_counting_route():
    documents = complete_documents()
    first = documents[0]["properties"][0]
    first["sources_checked"][0]["disposition"] = "no_contact_fields"
    report = coverage.validate_coverage(MANIFEST, documents, require_complete=True)
    assert any("phone source disposition does not support a phone" in error for error in report.errors)
    assert report.confirmed_phone_count == 48
    assert not report.complete
