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
SUMMARY = json.loads((renderer.DATA / "masiate-report-summary.json").read_text())


def test_all_profiles_accounted_for_once_and_counts_match():
    rows = renderer.build_rows(RECORDS, REVIEW)
    assert len({r["record"]["id"] for r in rows}) == 49
    assert Counter(r["section"] for r in rows) == {0: 3, 1: 6, 2: 3, 3: 37}
    assert sum(r["has_construction_route"] for r in rows) == 3
    assert sum(r["has_any_route"] for r in rows) == 6
    assert hashlib.sha256((renderer.DATA / "masiate-reviewed-properties.json").read_bytes()).hexdigest() == REVIEW["source_sha256"]


def test_duplicate_or_missing_profiles_fail_closed():
    with pytest.raises(ValueError, match="49"):
        renderer.build_rows(RECORDS[:-1], REVIEW)
    records = copy.deepcopy(RECORDS)
    records[0]["id"] = records[1]["id"]
    with pytest.raises(ValueError, match="Duplicate"):
        renderer.build_rows(records, REVIEW)
    review = copy.deepcopy(REVIEW)
    review["sections"][0]["ranks"].append(1)
    with pytest.raises(ValueError, match="49"):
        renderer.build_rows(RECORDS, review)


def test_actual_roles_are_not_inferred_from_company_names():
    rows = {r["record"]["rank"]: r for r in renderer.build_rows(RECORDS, REVIEW)}
    for rank in (36, 38, 39):
        assert rows[rank]["section"] == 2
        assert not rows[rank]["has_construction_route"]
    assert "sign/wall contractor only" in rows[4]["role"]
    assert "Parking contractor unknown" in rows[4]["role"]
    assert "not confirmed building contractor" in rows[42]["role"]
    assert "not confirmed builder" in rows[39]["role"]
    for rank in (3, 5, 8, 31):
        assert "outside builder unknown" in rows[rank]["role"].lower()
    for rank in (12, 14, 37):
        assert "not established" in rows[rank]["role"]
        assert not rows[rank]["has_construction_route"]
    assert "NOT matches" in rows[12]["caveat"]
    assert "NOT for construction" in rows[38]["caveat"]


def test_contact_details_remain_attached_to_the_correct_company():
    rows = {r["record"]["rank"]: r for r in renderer.build_rows(RECORDS, REVIEW)}
    assert "254-697-8516" in renderer.contacts_html(rows[1])
    assert "maceyt@collierconstruction.com" in renderer.contacts_html(rows[32])
    assert "979-836-4477" in renderer.contacts_html(rows[32])
    assert "spawglass.com" in renderer.contacts_html(rows[30])
    assert "locations.frostbank.com" not in renderer.contacts_html(rows[30])
    assert "979-739-0567" in renderer.contacts_html(rows[38])
    assert "engineer" in renderer.contacts_html(rows[38])


def test_escaping_and_non_web_links():
    assert renderer.link("javascript:alert(1)", "<script>") == "&lt;script&gt;"
    assert renderer.safe_url("file:///tmp/private") is None
    assert renderer.safe_url("https://example.test/contact")
    assert renderer.has_route({"website": "javascript:alert(1)"}) is False
    row = {"contacts": [{"name": "<x>", "role": "builder", "phone": "555-0100", "website": "file:///tmp/private"}]}
    markup = renderer.contacts_html(row)
    assert "&lt;x&gt;" in markup and "<x>" not in markup and "file:" not in markup


def test_full_pdf_text_links_layout_and_unsplit_rows(tmp_path):
    rows = renderer.build_rows(RECORDS, REVIEW)
    markup = renderer.render_html(rows, REVIEW, SUMMARY)
    assert markup.count("<tr data-id=") == 49
    document = HTML(string=markup).render()
    output = tmp_path / "table.pdf"
    document.write_pdf(output)
    pages_per_row = {}
    for page_index, page in enumerate(document.pages):
        page_box = page._page_box
        for box in page_box.descendants():
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
    assert 8 <= len(reader.pages) <= 15
    assert all(len(page.extract_text() or "") > 300 for page in reader.pages)
    assert "254-697-8516" in text and "979-836-4477" in text
    assert "maceyt@collierconstruction.com" in text.replace("\n", "")
    assert "Unknown does not mean available" in " ".join(text.split())
    assert "0" in text and "confirmed open trade packages" in text
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
    assert "https://ebcogc.com/" in urls
    assert "https://www.spawglass.com/" in urls
    assert "https://www.collierconstruction.com/contact" in urls
