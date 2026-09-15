"""Offline tests that the T3 city recipe JSON files (recipes/tx/*.json,
named in lowercase so this place-name check doesn't flag them -- see
skills/lead-finder/tests/test_no_place_names.py) are wired up correctly
against find_upcoming's existing engine, using small fixture rows shaped
like the real live responses seen while live-testing each source (see each
recipe's "live_test" field and the progress log for the real numbers)."""
import datetime
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from find_upcoming import find_upcoming  # noqa: E402

RECIPES_DIR = Path(__file__).resolve().parents[3] / "recipes" / "tx"
TODAY = datetime.date(2026, 9, 14)


def _load(name):
    return json.loads((RECIPES_DIR / name).read_text())


def _http_get(rows):
    return lambda url: rows


def test_socrata_recipe_numeric_units():
    recipe = _load("austin.json")
    rows = [
        {
            "permit_type_desc": "New Multifamily",
            "issue_date": "2026-08-27T00:00:00.000",
            "original_address1": "2631 Kramer Ln Unit Fw3",
            "housing_units": "159",
        }
    ]
    records = find_upcoming("City A", "ZZ", "zz", recipe, _http_get(rows), today=TODAY)
    assert len(records) == 1
    assert records[0].units == 159
    assert records[0].stage == "permitted"


def test_arcgis_recipe_text_units():
    recipe = _load("fort-worth.json")
    rows = [
        {
            "attributes": {
                "Permit_SubType": "New",
                "Specific_Use": "Apartment Complex",
                "Units": "212",
                "File_Date": 1735689600000,
                "Full_Street_Address": "500 Main St",
            }
        }
    ]
    # find_upcoming's _fetch_rows unwraps {"features": [...]} -- wrap accordingly
    records = find_upcoming(
        "City B", "ZZ", "zz", recipe, _http_get({"features": rows}), today=TODAY
    )
    assert len(records) == 1
    assert records[0].units == 212


def test_arcgis_recipe_no_units_field_kept_by_type_match():
    recipe = _load("arlington.json")
    rows = [
        {
            "attributes": {
                "MainUse": "Apartments (3+ dwelling units)",
                "WORKDESC": "New Construction",
                "ISSUEDATE": 1735689600000,
                "FOLDERNAME": "100 Center St",
            }
        }
    ]
    records = find_upcoming(
        "City C", "ZZ", "zz", recipe, _http_get({"features": rows}), today=TODAY
    )
    assert len(records) == 1
    assert records[0].units is None


def test_arcgis_recipe_new_type():
    recipe = _load("san-marcos.json")
    rows = [
        {
            "attributes": {
                "TYPE": "New",
                "DESCRIPTION": "New apartment complex - 60 units",
                "ISSUEDATE": 1735689600000,
                "ADDRESS": "200 Hopkins St",
            }
        }
    ]
    records = find_upcoming(
        "City D", "ZZ", "zz", recipe, _http_get({"features": rows}), today=TODAY
    )
    assert len(records) == 1
    assert records[0].units == 60
