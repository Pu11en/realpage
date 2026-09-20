"""Offline checks for the saved state recipes using live-shaped fixtures."""
import datetime
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from find_upcoming import find_upcoming  # noqa: E402

RECIPES_DIR = Path(__file__).resolve().parents[3] / "recipes" / "nm"
TODAY = datetime.date(2026, 9, 19)


def _load(name):
    return json.loads((RECIPES_DIR / name).read_text())


def test_albuquerque_recipe_maps_units_owner_and_text_fallback():
    recipe = _load("albuquerque.json")
    rows = {
        "features": [
            {
                "attributes": {
                    "TypeofStructure": "Apartment",
                    "WorkDescription": "NEW APARTMENT BUILDING WITH 82 DWELLING UNITS",
                    "DateIssued": 1788588000000,
                    "CalculatedAddress": "10501 CENTRAL AV NE",
                    "NumberofUnits": 82,
                    "Owner": "FAROLITO APARTMENTS LP",
                    "Applicant": "SAMPLE APPLICANT",
                }
            },
            {
                "attributes": {
                    "TypeofStructure": "Apartment",
                    "WorkDescription": "NEW APARTMENT BUILDING WITH 48 UNITS",
                    "DateIssued": 1788588000000,
                    "CalculatedAddress": "7600 CENTRAL AV SW",
                    "NumberofUnits": None,
                    "Owner": "SAMPLE OWNER LLC",
                }
            },
        ]
    }

    records = find_upcoming(
        recipe["city"], recipe["state"], "nm", recipe, lambda _url: rows, today=TODAY
    )

    assert [record.units for record in records] == [82, 48]
    assert records[0].developer == "FAROLITO APARTMENTS LP"
    assert records[0].address == "10501 CENTRAL AV NE"


def test_las_cruces_recipe_keeps_units_unknown_and_maps_owner():
    recipe = _load("las-cruces.json")
    rows = {
        "features": [
            {
                "attributes": {
                    "PropUseGrp": "APARTMENT",
                    "Permit_Number": "24CB0506272",
                    "Issued_Date": 1739516400000,
                    "Permit_Location": "3635 CENTRAL AVE",
                    "Owner_Name": "SIERRA NORTE DEVELOPMENT INC",
                    "Contractor_Business_Name": "SAMPLE CONTRACTOR",
                }
            }
        ]
    }

    records = find_upcoming(
        recipe["city"], recipe["state"], "nm", recipe, lambda _url: rows, today=TODAY
    )

    assert len(records) == 1
    assert records[0].units is None
    assert records[0].developer == "SIERRA NORTE DEVELOPMENT INC"
    assert records[0].name == "24CB0506272"


def test_unavailable_recipes_are_explicitly_disabled_with_real_supporting_urls():
    for filename in ("rio-rancho.json", "santa-fe.json", "bernalillo-county-sales.json"):
        recipe = _load(filename)
        assert recipe["enabled"] is False
        assert recipe["system"] == "unavailable"
        assert recipe["reason"]
        assert recipe["supporting_source"]["endpoint"].startswith("https://")
