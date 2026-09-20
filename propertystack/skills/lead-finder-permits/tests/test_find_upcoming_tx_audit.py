"""Regressions from the 2026-09-20 two-city permit source audit (S5, S6).

Each test pins one thing that was silently losing real, callable leads.
"""
import datetime
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from find_upcoming import _parse_date, find_upcoming  # noqa: E402

TODAY = datetime.date(2026, 9, 20)
ROOT = Path(__file__).resolve().parents[4]
RECIPES = ROOT / "propertystack" / "recipes" / "tx"


def _http_get(rows):
    return lambda url: rows


def test_space_separated_timestamp_is_a_real_date():
    """One city's older CKAN resource renders its date column as
    '2021-09-21 00:00:00'.  Every format the parser knew used a T, so 100 of
    154 apartment rows were dropped as "no usable date" -- and a row with no
    date is not counted as aged out, so the run's alarm reported agedOut=0
    while two thirds of the feed vanished."""
    assert _parse_date("2021-09-21 00:00:00") == datetime.date(2021, 9, 21)
    assert _parse_date("2026-08-05 13:45:02.500") == datetime.date(2026, 8, 5)
    assert _parse_date("2026-08-05") == datetime.date(2026, 8, 5)
    assert _parse_date("not a date") is None


def test_space_timestamp_rows_are_counted_as_aged_out_not_lost():
    recipe = {
        "endpoint": "https://example.test/sql",
        "fields": {"permit_type": "Name", "name": "Name", "issue_date": "Issued", "address": "Addr"},
    }
    rows = [{"Name": "OLD APARTMENTS", "Issued": "2021-09-21 00:00:00", "Addr": "1 Old Rd"}]
    stats = {}
    records = find_upcoming("Rivertown", "ZZ", "zz", recipe, _http_get(rows), today=TODAY, stats=stats)
    assert records == []
    assert stats["apartmentRows"] == 1
    assert stats["agedOut"] == 1  # honestly aged out, not silently unparseable
    assert stats["newestDate"] == "2021-09-21"


def test_recipe_can_name_its_citys_own_apartment_code():
    """One city never writes "apartment" on its 2026 apartment permits --
    it prefixes them "AFF - " (its affordable housing bond programme).  With
    only the generic wording the run matched 0 of that city's 411 commercial
    new-building permits in 2026."""
    recipe = {
        "endpoint": "https://example.test/sql",
        "fields": {"permit_type": "PROJECT NAME", "name": "PROJECT NAME", "issue_date": "DATE ISSUED", "address": "ADDRESS"},
        "apartment_pattern": r"multi[- ]?family|apartment|(?:^|\s)AFF\s+-",
        "name_strip_pattern": r"^AFF\s*-\s*",
    }
    rows = [
        {"PROJECT NAME": "AFF - 1231 E COMMERCE ST - Central at Commerce",
         "DATE ISSUED": "2026-03-16", "ADDRESS": "1231 E COMMERCE ST"},
        {"PROJECT NAME": "Garage Sale", "DATE ISSUED": "2026-03-16", "ADDRESS": "9 Other Rd"},
    ]
    records = find_upcoming("Rivertown", "ZZ", "zz", recipe, _http_get(rows), today=TODAY)
    assert len(records) == 1
    assert records[0].name == "1231 E COMMERCE ST - Central at Commerce"
    assert records[0].address.startswith("1231 E COMMERCE ST")


def test_without_the_pattern_the_default_wording_still_rules():
    recipe = {
        "endpoint": "https://example.test/sql",
        "fields": {"permit_type": "PROJECT NAME", "name": "PROJECT NAME", "issue_date": "DATE ISSUED", "address": "ADDRESS"},
    }
    rows = [{"PROJECT NAME": "AFF - 1231 E COMMERCE ST", "DATE ISSUED": "2026-03-16", "ADDRESS": "1231 E COMMERCE ST"}]
    assert find_upcoming("Rivertown", "ZZ", "zz", recipe, _http_get(rows), today=TODAY) == []


def test_a_permit_row_with_no_address_is_dropped_not_named_none():
    """Two real permit rows for one project carry no address -- one Python
    None, one the literal string 'NULL'.  Both used to become leads whose
    address read "None": impossible to call and impossible to merge."""
    recipe = {
        "endpoint": "https://example.test/sql",
        "fields": {"permit_type": "Name", "name": "Name", "issue_date": "Issued", "address": "Addr"},
    }
    rows = [
        {"Name": "AAA APARTMENTS", "Issued": "2026-08-05", "Addr": None},
        {"Name": "BBB APARTMENTS", "Issued": "2026-08-05", "Addr": "NULL"},
        {"Name": "CCC APARTMENTS", "Issued": "2026-08-05", "Addr": "7 Real St"},
    ]
    stats = {}
    records = find_upcoming("Rivertown", "ZZ", "zz", recipe, _http_get(rows), today=TODAY, stats=stats)
    assert [r.address for r in records] == ["7 Real St"]
    assert stats["noAddress"] == 2


def test_first_recipe_asks_for_that_citys_own_apartment_code():
    recipe = json.loads((RECIPES / "san-antonio.json").read_text())
    assert recipe["sql"].count("ILIKE 'AFF -%'") == 2, "both CKAN resources must be searched"
    assert re.search(recipe["apartment_pattern"], "AFF - 425 San Pedro", re.I)
    assert re.search(recipe["apartment_pattern"], "The Orion Apartments", re.I)
    assert not re.search(recipe["apartment_pattern"], "Garage Sale", re.I)


def test_second_recipe_includes_the_new_commercial_permit_type():
    """TYPE='New' alone missed 116 multi-family rows filed as 'New
    Commercial', including a seven-storey student-housing project."""
    recipe = json.loads((RECIPES / "san-marcos.json").read_text())
    endpoint = recipe["endpoint"]
    assert " " not in endpoint, "a literal space in a URL is what broke a county source for months"
    assert "TYPE%3D%27New+Commercial%27" in endpoint
    assert "TYPE%3D%27New%27" in endpoint
    assert "LANDUSE%3D%27Multi-Family%27" in endpoint
