import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from merge import merge_records, same_building
from record import LeadRecord


def _record(**kwargs):
    base = dict(area="_sample", city="Sampleton")
    base.update(kwargs)
    return LeadRecord(**base)


def test_same_building_by_normalized_address():
    a = _record(address="123 Main St")
    b = _record(address="123 Main Street Bldg B")
    assert same_building(a, b)


def test_different_addresses_not_same_building():
    a = _record(address="123 Main St")
    b = _record(address="456 Oak Ave")
    assert not same_building(a, b)


def test_same_building_by_geocode_and_shared_name_word():
    a = _record(lat=40.0, lon=-100.0, developer="Fixture Developer LLC")
    b = _record(lat=40.0003, lon=-100.0, developer="Fixture Developer Partners")  # ~33m north
    assert same_building(a, b)


def test_close_geocode_but_no_shared_name_is_not_merged():
    a = _record(lat=40.0, lon=-100.0, developer="Fixture Developer LLC")
    b = _record(lat=40.0003, lon=-100.0, developer="Totally Different Co")
    assert not same_building(a, b)


def test_far_geocode_not_merged_even_with_shared_name():
    a = _record(lat=40.0, lon=-100.0, developer="Fixture Developer LLC")
    b = _record(lat=41.0, lon=-100.0, developer="Fixture Developer LLC")
    assert not same_building(a, b)


def test_merge_records_keeps_most_advanced_stage_and_all_sources():
    planned = _record(
        address="123 Main St",
        stage="planned",
        developer="Fixture Developer LLC",
        sources=[{"fact": "developer", "url": "https://example.test/planned"}],
    )
    permitted = _record(
        address="123 Main Street",
        stage="permitted",
        permit_date="2026-02-01",
        units=150,
        sources=[{"fact": "permit_date", "url": "https://example.test/permit"}],
        links={"permit": "https://example.test/permit"},
    )

    merged = merge_records([planned, permitted])

    assert len(merged) == 1
    result = merged[0]
    assert result.stage == "permitted"
    assert result.permit_date == "2026-02-01"
    assert result.units == 150
    assert result.developer == "Fixture Developer LLC"
    assert {"fact": "developer", "url": "https://example.test/planned"} in result.sources
    assert {"fact": "permit_date", "url": "https://example.test/permit"} in result.sources
    assert result.links["permit"] == "https://example.test/permit"


def test_merge_records_leaves_distinct_buildings_separate():
    a = _record(address="123 Main St")
    b = _record(address="456 Oak Ave")
    merged = merge_records([a, b])
    assert len(merged) == 2


def test_planned_then_permit_upgrades_not_duplicates():
    planned = _record(address="789 Elm Ct", stage="planned")
    later_permit = _record(address="789 Elm Court", stage="permitted", permit_date="2026-03-01")

    merged = merge_records([planned, later_permit])

    assert len(merged) == 1
    assert merged[0].stage == "permitted"
    assert merged[0].permit_date == "2026-03-01"
