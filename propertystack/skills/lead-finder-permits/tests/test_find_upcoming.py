import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from find_upcoming import find_upcoming  # noqa: E402

TODAY = datetime.date(2026, 9, 14)

RECIPE = {
    "city": "Rivertown",
    "state": "ZZ",
    "system": "socrata",
    "endpoint": "https://example.test/resource/permits.json",
    "fields": {
        "permit_type": "PermitType",
        "issue_date": "IssueDate",
        "units": "Units",
        "address": "Address",
    },
}


def _http_get(rows):
    return lambda url: rows


def test_recent_permit_no_co_is_permitted():
    rows = [
        {
            "PermitType": "Multifamily new construction",
            "IssueDate": "2026-08-01",
            "Units": "40",
            "Address": "1 River Rd",
        }
    ]
    records = find_upcoming("Rivertown", "ZZ", "zz", RECIPE, _http_get(rows), today=TODAY)
    assert len(records) == 1
    assert records[0].stage == "permitted"
    assert records[0].permit_date == "2026-08-01"
    assert records[0].units == 40
    assert records[0].links["permit"] == RECIPE["endpoint"]


def test_recent_co_is_leasing():
    rows = [
        {
            "PermitType": "Apartment",
            "IssueDate": "2024-01-01",
            "Units": "50",
            "Address": "2 River Rd",
            "CertificateOfOccupancyDate": "2026-06-01",
        }
    ]
    records = find_upcoming("Rivertown", "ZZ", "zz", RECIPE, _http_get(rows), today=TODAY)
    assert len(records) == 1
    assert records[0].stage == "leasing"


def test_old_co_is_dropped():
    rows = [
        {
            "PermitType": "Apartment",
            "IssueDate": "2020-01-01",
            "Units": "50",
            "Address": "3 River Rd",
            "CertificateOfOccupancyDate": "2020-06-01",
        }
    ]
    assert find_upcoming("Rivertown", "ZZ", "zz", RECIPE, _http_get(rows), today=TODAY) == []


def test_old_permit_no_co_is_dropped():
    rows = [
        {
            "PermitType": "Apartment",
            "IssueDate": "2019-01-01",
            "Units": "50",
            "Address": "4 River Rd",
        }
    ]
    assert find_upcoming("Rivertown", "ZZ", "zz", RECIPE, _http_get(rows), today=TODAY) == []


def test_non_apartment_low_units_is_dropped():
    rows = [
        {
            "PermitType": "Single family residence",
            "IssueDate": "2026-08-01",
            "Units": "1",
            "Address": "5 River Rd",
        }
    ]
    assert find_upcoming("Rivertown", "ZZ", "zz", RECIPE, _http_get(rows), today=TODAY) == []


def test_repair_permit_mentioning_apartments_in_description_is_dropped():
    """Real-world case (found running the chain on Buffalo, NY): a trade/repair
    permit type like "REPAIR" or "ELECTRICAL" whose free-text description
    happens to mention "apartments" (renovating an existing building) is not a
    new apartment project and must not be picked up by the whole-row text scan."""
    rows = [
        {
            "PermitType": "Repair",
            "IssueDate": "2026-08-01",
            "Units": "",
            "Address": "5 River Rd",
            "Description": "Renovate kitchens and bathrooms in (2) rear apartments",
        }
    ]
    assert find_upcoming("Rivertown", "ZZ", "zz", RECIPE, _http_get(rows), today=TODAY) == []


def test_large_unit_count_counts_as_apartment_even_if_type_unclear():
    rows = [
        {
            "PermitType": "New construction",
            "IssueDate": "2026-08-01",
            "Units": "30",
            "Address": "6 River Rd",
        }
    ]
    records = find_upcoming("Rivertown", "ZZ", "zz", RECIPE, _http_get(rows), today=TODAY)
    assert len(records) == 1


def test_unknown_units_kept_as_none_for_details_step():
    rows = [
        {
            "PermitType": "Multifamily",
            "IssueDate": "2026-08-01",
            "Units": "",
            "Address": "7 River Rd",
        }
    ]
    records = find_upcoming("Rivertown", "ZZ", "zz", RECIPE, _http_get(rows), today=TODAY)
    assert len(records) == 1
    assert records[0].units is None


def test_multiple_permits_same_address_merged_into_one_record():
    rows = [
        {
            "PermitType": "Multifamily new construction",
            "IssueDate": "2026-08-01",
            "Units": "40",
            "Address": "8 River Rd",
        },
        {
            "PermitType": "Multifamily electrical",
            "IssueDate": "2026-08-15",
            "Units": "40",
            "Address": "8 River Rd",
        },
    ]
    records = find_upcoming("Rivertown", "ZZ", "zz", RECIPE, _http_get(rows), today=TODAY)
    assert len(records) == 1


def test_no_endpoint_returns_empty():
    assert find_upcoming("Rivertown", "ZZ", "zz", {"fields": {}}, _http_get([]), today=TODAY) == []


def test_http_get_error_returns_empty():
    def boom(url):
        raise OSError("down")

    assert find_upcoming("Rivertown", "ZZ", "zz", RECIPE, boom, today=TODAY) == []


def test_epoch_ms_issue_date_is_parsed():
    # Some real ArcGIS FeatureServer date fields come back as epoch-millisecond
    # integers, not strings.
    epoch_ms = int(datetime.datetime(2026, 8, 1, tzinfo=datetime.timezone.utc).timestamp() * 1000)
    rows = [
        {
            "PermitType": "Apartment",
            "IssueDate": epoch_ms,
            "Units": "40",
            "Address": "10 River Rd",
        }
    ]
    records = find_upcoming("Rivertown", "ZZ", "zz", RECIPE, _http_get(rows), today=TODAY)
    assert len(records) == 1
    assert records[0].permit_date == "2026-08-01"


def test_explicit_co_date_field_overrides_generic_regex():
    # Tempe's leasing-start field is COIssuedDate, which the generic
    # cert-of-occupancy regex doesn't match -- fields["co_date"] must win.
    recipe = {**RECIPE, "fields": {**RECIPE["fields"], "co_date": "COIssuedDate"}}
    rows = [
        {
            "PermitType": "Apartment",
            "IssueDate": "2024-01-01",
            "Units": "50",
            "Address": "11 River Rd",
            "COIssuedDate": "2026-06-01",
        }
    ]
    records = find_upcoming("Rivertown", "ZZ", "zz", recipe, _http_get(rows), today=TODAY)
    assert len(records) == 1
    assert records[0].stage == "leasing"


def test_units_parsed_from_description_text_when_no_units_field():
    recipe = {
        **RECIPE,
        "fields": {
            "issue_date": "IssueDate",
            "address": "Address",
            "units_text_field": "Description",
        },
        "units_text_pattern": r"\(?(\d+)\)?\s*-?\s*units?\b",
    }
    rows = [
        {
            "IssueDate": "2026-08-01",
            "Address": "12 River Rd",
            "Description": "New development of 3-story apartment (36 unit), type VA construction",
        }
    ]
    records = find_upcoming("Rivertown", "ZZ", "zz", recipe, _http_get(rows), today=TODAY)
    assert len(records) == 1
    assert records[0].units == 36


def test_arcgis_features_shape_supported():
    recipe = {**RECIPE, "system": "arcgis"}

    def get(url):
        return {
            "features": [
                {
                    "attributes": {
                        "PermitType": "Apartment",
                        "IssueDate": "2026-08-01",
                        "Units": "60",
                        "Address": "9 River Rd",
                    }
                }
            ]
        }

    records = find_upcoming("Rivertown", "ZZ", "zz", recipe, get, today=TODAY)
    assert len(records) == 1
    assert records[0].units == 60
