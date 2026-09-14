"""F9: quality alarms -- answer-key recall/software accuracy and completeness
checks that gate whether a run gets built into the site."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import quality  # noqa: E402
from record import LeadRecord  # noqa: E402


def _write_key(tmp_path, leads):
    d = tmp_path / "answer-keys"
    d.mkdir(parents=True, exist_ok=True)
    (d / "zz.json").write_text(json.dumps({"state": "ZZ", "leads": leads}))
    return d


def test_passing_run_meets_every_bar(tmp_path):
    key_leads = [
        {"name": "Lumara", "address": "1 Main St, Sampleton, ZZ", "software": "Yardi"},
        {"name": "Bella Victoria", "address": "2 Main St, Sampleton, ZZ"},
    ]
    answer_keys_dir = _write_key(tmp_path, key_leads)

    records = [
        LeadRecord(area="zz", city="Sampleton", name="Lumara", address="1 Main St, Sampleton, ZZ",
                   stage="leasing", units=100, website="https://lumara.example",
                   software="Yardi", office_phone="555-1111"),
        LeadRecord(area="zz", city="Sampleton", name="Bella Victoria", address="2 Main St, Sampleton, ZZ",
                   stage="sold", units=50, website="https://bv.example",
                   software="RealPage", office_phone="555-2222"),
        LeadRecord(area="zz", city="Sampleton", name="New Build", address="3 Main St, Sampleton, ZZ",
                   stage="permitted", units=30, software="not picked yet",
                   developer="Acme Dev", office_phone="555-3333"),
    ]

    report = quality.check_quality("ZZ", records, cities_with_source=1, total_cities=1,
                                    answer_keys_dir=answer_keys_dir)

    assert report["passed"] is True
    assert report["fail_reasons"] == []
    assert report["answer_key_recall"] == 1.0
    assert report["software_accuracy"] == 1.0
    assert report["existing_buildings"]["website_pct"] == 1.0
    assert report["not_yet_built"]["software_not_picked_pct"] == 1.0
    assert report["not_yet_built"]["developer_and_phone_pct"] == 1.0


def test_low_recall_fails(tmp_path):
    key_leads = [
        {"name": "Lumara", "address": "1 Main St, Sampleton, ZZ"},
        {"name": "Bella Victoria", "address": "2 Main St, Sampleton, ZZ"},
        {"name": "Third Place", "address": "3 Main St, Sampleton, ZZ"},
    ]
    answer_keys_dir = _write_key(tmp_path, key_leads)

    records = [
        LeadRecord(area="zz", city="Sampleton", name="Lumara", address="1 Main St, Sampleton, ZZ",
                   stage="leasing", units=100, website="https://lumara.example",
                   software="Yardi", office_phone="555-1111"),
    ]

    report = quality.check_quality("ZZ", records, cities_with_source=1, total_cities=1,
                                    answer_keys_dir=answer_keys_dir)

    assert report["passed"] is False
    assert any("recall" in r for r in report["fail_reasons"])


def test_missing_answer_key_fails(tmp_path):
    empty_dir = tmp_path / "no-keys"
    empty_dir.mkdir()
    records = [LeadRecord(area="zz", city="Sampleton", name="X", stage="leasing")]

    report = quality.check_quality("ZZ", records, cities_with_source=1, total_cities=1,
                                    answer_keys_dir=empty_dir)

    assert report["passed"] is False
    assert "no answer key found for this state" in report["fail_reasons"]


def test_existing_building_missing_website_fails_bar(tmp_path):
    key_leads = [{"name": "Lumara", "address": "1 Main St, Sampleton, ZZ"}]
    answer_keys_dir = _write_key(tmp_path, key_leads)

    records = [
        LeadRecord(area="zz", city="Sampleton", name="Lumara", address="1 Main St, Sampleton, ZZ",
                   stage="leasing", units=100, software="Yardi", office_phone="555-1111"),
    ]

    report = quality.check_quality("ZZ", records, cities_with_source=1, total_cities=1,
                                    answer_keys_dir=answer_keys_dir)

    assert report["passed"] is False
    assert any("website" in r for r in report["fail_reasons"])


def test_write_quality_json_writes_file(tmp_path):
    report = {"state": "ZZ", "passed": True}
    out = quality.write_quality_json(tmp_path, report)
    assert out == tmp_path / "quality.json"
    assert json.loads(out.read_text()) == report
