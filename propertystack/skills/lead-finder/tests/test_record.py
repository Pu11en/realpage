import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from record import LeadRecord, load_records, normalize_address, save_records, stage_rank


def test_stage_rank_orders_correctly():
    assert stage_rank("planned") < stage_rank("permitted")
    assert stage_rank("permitted") < stage_rank("under construction")
    assert stage_rank("under construction") < stage_rank("leasing")
    assert stage_rank("leasing") < stage_rank("sold")


def test_stage_rank_unknown_is_negative():
    assert stage_rank("bogus") == -1


def test_normalize_address_matches_street_suffix_and_unit():
    assert normalize_address("123 Main St") == normalize_address("123 Main Street Bldg B")
    assert normalize_address("123 Main St") == "123 main st"


def test_normalize_address_blank():
    assert normalize_address("") == ""


def test_round_trip_save_load(tmp_path):
    records = [
        LeadRecord(area="_sample", city="Sampleton", name="Fake Gardens", units=100),
        LeadRecord(area="_sample", city="Sampleton", address="1 Test Way", stage="sold"),
    ]
    path = tmp_path / "leads.json"
    save_records(records, path)

    loaded = load_records(path)
    assert len(loaded) == 2
    assert loaded[0].name == "Fake Gardens"
    assert loaded[0].units == 100
    assert loaded[1].stage == "sold"


def test_saved_file_has_source_field_shape(tmp_path):
    records = [
        LeadRecord(
            area="_sample",
            city="Sampleton",
            sources=[{"fact": "units", "url": "https://example.test/1"}],
        )
    ]
    path = tmp_path / "leads.json"
    save_records(records, path)

    raw = json.loads(path.read_text())
    assert raw[0]["sources"] == [{"fact": "units", "url": "https://example.test/1"}]


def test_sample_area_fixture_loads():
    sample_path = Path(__file__).resolve().parents[3] / "data" / "_sample" / "leads.json"
    records = load_records(sample_path)
    assert len(records) == 2
    assert all(r.area == "_sample" for r in records)
