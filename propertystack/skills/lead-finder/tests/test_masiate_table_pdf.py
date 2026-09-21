from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

import pytest
from pypdf import PdfReader
from weasyprint import HTML


ROOT = Path(__file__).resolve().parents[4]
spec = importlib.util.spec_from_file_location("masiate_table", ROOT / "tooling/masiate_pdf/render_table.py")
renderer = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(renderer)
RECORDS = json.loads((renderer.DATA / "masiate-reviewed-properties.json").read_text())
REVIEW = json.loads(renderer.REVIEW_PATH.read_text())
MANIFEST, DOCUMENTS, COVERAGE = renderer.load_research()


def rows():
    return renderer.build_rows(RECORDS, REVIEW, MANIFEST, DOCUMENTS)


def test_all_profiles_and_contact_counts_match_validated_ledger():
    built = rows()
    summary = renderer.coverage_summary(built, REVIEW)
    assert len({row["record"]["id"] for row in built}) == 49
    assert Counter(row["section"] for row in built) == {0: 13, 1: 13, 2: 13, 3: 10}
    assert summary["researched_rows"] == COVERAGE.researched_count == 49
    assert summary["confirmed_strong_routes"] == COVERAGE.confirmed_phone_count == 47
    assert summary["provisional_best_guess_routes"] == COVERAGE.provisional_phone_count == 2
    assert summary["researched_no_number_gaps"] == COVERAGE.researched_gap_count == 0
    assert summary["distinct_selected_contact_names"] == 47
    assert summary["distinct_selected_phone_numbers"] == 46
    assert {group: detail["rows"] for group, detail in summary["role_category_counts"].items()} == {
        "construction_contractor": 8,
        "owner_tenant_institution": 27,
        "design_engineering_professional": 12,
        "project_representative": 1,
        "public_routing_office": 1,
    }
    assert hashlib.sha256((renderer.DATA / "masiate-reviewed-properties.json").read_bytes()).hexdigest() == REVIEW["source_sha256"]


def test_duplicate_missing_or_misgrouped_profiles_fail_closed():
    with pytest.raises(ValueError, match="49"):
        renderer.build_rows(RECORDS[:-1], REVIEW, MANIFEST, DOCUMENTS)
    records = copy.deepcopy(RECORDS)
    records[0]["id"] = records[1]["id"]
    with pytest.raises(ValueError, match="Duplicate"):
        renderer.build_rows(records, REVIEW, MANIFEST, DOCUMENTS)
    review = copy.deepcopy(REVIEW)
    review["sections"][0]["ranks"].append(1)
    with pytest.raises(ValueError, match="49"):
        renderer.build_rows(RECORDS, review, MANIFEST, DOCUMENTS)
    review = copy.deepcopy(REVIEW)
    review["contact_role_groups"]["public_routing_office"]["ranks"].append(1)
    with pytest.raises(ValueError, match="more than one"):
        renderer.build_rows(RECORDS, review, MANIFEST, DOCUMENTS)


def test_selected_routes_preserve_actual_roles_and_provisional_status():
    by_rank = {row["record"]["rank"]: row for row in rows()}
    assert by_rank[1]["selected"]["phone"] == "254-697-8516"
    assert "general contractor" in by_rank[1]["selected"]["role"]
    assert by_rank[4]["selected"]["contact_name"] == "Redeemer Church Brenham"
    assert "owner/applicant" in by_rank[4]["selected"]["role"]
    assert by_rank[12]["selected"]["contact_name"] == "Eddie Hare — Accessibility Specialist"
    assert "accessibility specialist" in by_rank[12]["selected"]["role"]
    assert by_rank[14]["selected"]["contact_name"] == "McGregor Murphy Architecture"
    assert "design firm" in by_rank[14]["selected"]["role"]
    assert by_rank[38]["selected"]["contact_name"] == "J4 Engineering"
    assert "engineer" in by_rank[38]["selected"]["role"]
    assert by_rank[42]["selected"]["contact_name"] == "Lay Construction / Lay Design-Build"
    assert "project representative" in by_rank[42]["selected"]["role"]
    assert by_rank[46]["selected"]["contact_name"] == "City of Somerville City Hall"
    assert "approving-jurisdiction routing office" in by_rank[46]["selected"]["role"]
    assert by_rank[49]["selected"]["contact_name"] == "AutoZone / Michael Petty"
    assert "director of construction" in by_rank[49]["selected"]["role"]
    assert by_rank[5]["provisional"] and by_rank[33]["provisional"]
    assert not by_rank[1]["provisional"]


def test_selected_and_alternative_details_remain_attached_to_correct_rows():
    by_rank = {row["record"]["rank"]: row for row in rows()}
    assert "254-697-8516" in renderer.selected_route_html(by_rank[1])
    assert "BEST-GUESS / VERIFY IDENTITY" in renderer.selected_route_html(by_rank[33])
    assert "979-739-0567" in renderer.selected_route_html(by_rank[38])
    assert "901-495-7232" in renderer.selected_route_html(by_rank[49])
    assert "City of Brenham" in renderer.alternatives_html(by_rank[33])
    assert "developer" in renderer.alternatives_html(by_rank[49])
    assert "No additional route selected" in renderer.alternatives_html(by_rank[3])


def test_escaping_and_non_web_links():
    assert renderer.link("javascript:alert(1)", "<script>") == "&lt;script&gt;"
    assert renderer.safe_url("file:///tmp/private") is None
    assert renderer.safe_url("https://example.test/contact")
    contact = {
        "contact_name": "<x>",
        "role": "builder",
        "phone": "555-555-0100",
        "website": "file:///tmp/private",
        "source_url": "javascript:alert(1)",
        "source_type": "other",
        "source_strength": "strong",
        "checked_on": "2026-09-20",
    }
    markup = renderer.contact_html(contact, selected=True)
    assert "&lt;x&gt;" in markup and "<x>" not in markup and "file:" not in markup
    assert "javascript:" not in markup


def test_full_pdf_text_links_layout_and_unsplit_rows(tmp_path):
    built = rows()
    summary = renderer.coverage_summary(built, REVIEW)
    markup = renderer.render_html(built, REVIEW, summary)
    assert markup.count("<tr data-id=") == 49
    document = HTML(string=markup).render()
    output = tmp_path / "all-contacts.pdf"
    document.write_pdf(output)
    pages_per_row = {}
    for page_index, page in enumerate(document.pages):
        for box in page._page_box.descendants():
            if box.element_tag == "tr" and box.element is not None and box.element.get("data-id"):
                pages_per_row.setdefault(box.element.get("data-id"), set()).add(page_index)
            if type(box).__name__ == "TextBox":
                assert box.position_x >= 0
                assert box.position_x + box.width <= page.width + 1
                assert box.position_y >= 0
                assert box.position_y + box.height <= page.height + 1
            if type(box).__name__ == "TableCellBox":
                for child in box.descendants():
                    if type(child).__name__ == "TextBox":
                        assert child.position_x + child.width <= box.position_x + box.border_width() + 1
                        assert child.position_y + child.height <= box.position_y + box.border_height() + 1
    assert len(pages_per_row) == 49
    assert all(len(pages) == 1 for pages in pages_per_row.values())

    reader = PdfReader(output)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    normalized_text = " ".join(text.split())
    assert 10 <= len(reader.pages) <= 35
    assert all(len(page.extract_text() or "") > 250 for page in reader.pages)
    assert "47" in text and "confirmed / strong routes" in text
    assert "2" in text and "best-guess routes to verify" in text
    assert "0" in text and "rows without a suitable number" in normalized_text
    assert "254-697-8516" in text and "901-495-7232" in text
    assert "Brennan Taylor Developments" in text and "Valco Builders" in text
    assert "BEST-GUESS / VERIFY IDENTITY" in text
    assert "Best public business route" in text
    assert "Sep. 20, 2026" in text and "Sep 20, 2026" in text
    assert all(row["selected"]["phone"] in text for row in built)
    assert "/home/" not in text and "/tmp/" not in text

    urls = set()
    for page in reader.pages:
        for annotation in page.get("/Annots", []):
            action = annotation.get_object().get("/A", {})
            if action.get("/URI"):
                urls.add(str(action["/URI"]))
    assert all(renderer.safe_url(url) for url in urls)
    for record in RECORDS:
        for source in record["sources"]:
            if renderer.safe_url(source.get("url")):
                assert source["url"] in urls
    for row in built:
        for contact in [row["selected"], *row["alternatives"]]:
            if contact:
                assert contact["source_url"] in urls


def test_render_writes_pdf_and_merged_coverage_summary(tmp_path):
    pdf = tmp_path / "contacts.pdf"
    summary_path = tmp_path / "summary.json"
    result = renderer.render(pdf, summary_path)
    merged = json.loads(summary_path.read_text())
    assert pdf.exists() and len(PdfReader(pdf).pages) == result["pages"]
    assert merged["property_rows"] == len(merged["properties"]) == 49
    assert len({item["property_id"] for item in merged["properties"]}) == 49
    assert merged["confirmed_strong_routes"] == 47
    assert merged["provisional_best_guess_routes"] == 2
    assert merged["researched_no_number_gaps"] == 0
