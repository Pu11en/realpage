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


def test_arcgis_pagination_follows_exceeded_transfer_limit():
    """A layer with more than 1,000 matching rows must not silently drop
    everything past row 1,000 -- exceededTransferLimit=true must trigger a
    resultOffset page."""
    page1 = {
        "exceededTransferLimit": True,
        "features": [
            {"attributes": {"PermitType": "Multifamily new construction", "IssueDate": 1735689600000, "Units": "40", "Address": f"Row {i}"}}
            for i in range(3)
        ],
    }
    page2 = {
        "exceededTransferLimit": False,
        "features": [
            {"attributes": {"PermitType": "Multifamily new construction", "IssueDate": 1735689600000, "Units": "40", "Address": "Row 3"}}
        ],
    }
    calls = []

    def http_get(url):
        calls.append(url)
        return page2 if "resultOffset" in url else page1

    records = find_upcoming("Rivertown", "ZZ", "zz", RECIPE, http_get, today=TODAY)
    assert len(records) == 4
    assert any("resultOffset=3" in url for url in calls)


def test_arcgis_no_pagination_when_not_exceeded():
    page1 = {
        "exceededTransferLimit": False,
        "features": [
            {"attributes": {"PermitType": "Multifamily new construction", "IssueDate": 1735689600000, "Units": "40", "Address": "Row 0"}}
        ],
    }
    calls = []

    def http_get(url):
        calls.append(url)
        return page1

    find_upcoming("Rivertown", "ZZ", "zz", RECIPE, http_get, today=TODAY)
    assert len(calls) == 1


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


def test_recipe_keyword_pattern_can_match_local_shorthand():
    recipe = dict(RECIPE, keyword_pattern=r"\bapt\b|\br-?2\b")
    rows = [
        {
            "PermitType": "NEW APT BLD 1-5-3-R2-A",
            "IssueDate": datetime.date(2026, 8, 1),
            "Units": "",
            "Address": "7 River Rd",
        }
    ]
    records = find_upcoming("Rivertown", "ZZ", "zz", recipe, _http_get(rows), today=TODAY)
    assert len(records) == 1


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


def test_owner_field_used_as_developer():
    recipe = dict(RECIPE, owner_field="Owner", builder_field="Builder")
    rows = [
        {
            "PermitType": "Multifamily new construction",
            "IssueDate": "2026-08-01",
            "Units": "40",
            "Address": "9 River Rd",
            "Owner": "Acme Multifamily Owner LLC",
            "Builder": "Bolt Construction Co",
        }
    ]
    records = find_upcoming("Rivertown", "ZZ", "zz", recipe, _http_get(rows), today=TODAY)
    assert records[0].developer == "Acme Multifamily Owner LLC"
    assert {"fact": "developer", "url": RECIPE["endpoint"]} in records[0].sources


def test_builder_field_used_when_no_owner():
    recipe = dict(RECIPE, builder_field="Builder")
    rows = [
        {
            "PermitType": "Multifamily new construction",
            "IssueDate": "2026-08-01",
            "Units": "40",
            "Address": "10 River Rd",
            "Builder": "Bolt Construction Co",
        }
    ]
    records = find_upcoming("Rivertown", "ZZ", "zz", recipe, _http_get(rows), today=TODAY)
    assert records[0].developer == "Bolt Construction Co"


def test_no_owner_or_builder_field_leaves_developer_blank():
    rows = [
        {
            "PermitType": "Multifamily new construction",
            "IssueDate": "2026-08-01",
            "Units": "40",
            "Address": "11 River Rd",
        }
    ]
    records = find_upcoming("Rivertown", "ZZ", "zz", RECIPE, _http_get(rows), today=TODAY)
    assert records[0].developer == ""


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


def test_known_low_unit_count_is_dropped_even_if_type_text_matches():
    """S3 fixture from a real city recipe whose Socrata query already filters
    to type_of_work='Multi-Family Residential' server-side, so every row's
    own text contains that phrase and used to pass the whole-row regex
    fallback regardless of unit count -- several sub-20-unit permits
    (duplexes/triplexes) slipped through this way. A known unit count must
    win."""
    recipe = {
        "endpoint": "https://example.test/query",
        "fields": {
            "issue_date": "issued_date",
            "address": "property_address",
            "units_text_field": "description_of_work",
        },
        "units_text_pattern": r"\(?(\d+)\)?\s*-?\s*units?\b",
    }
    rows = [
        {
            "issued_date": "2026-08-01",
            "property_address": "123 Multi-Family Residential Way",
            "description_of_work": "Multi-Family Residential new triplex (3) units",
        }
    ]
    assert find_upcoming("Mesa", "AZ", "az", recipe, _http_get(rows), today=TODAY) == []


def test_blank_name_falls_back_to_permit_type_text():
    """S3 fixture from a real city recipe: its PERMIT_NAME field (used as
    `permit_type`) holds the real project name ("MADISON AT LOUISE APTS.")
    but the recipe had no `fields.name`, so every lead from it came back
    with a blank name. Falling back to the type text fixes it without
    needing a project-name field the source doesn't reliably expose."""
    recipe = {
        "endpoint": "https://example.test/query",
        "fields": {
            "permit_type": "PERMIT_NAME",
            "units": "Units",
            "issue_date": "PER_ISSUE_DATE",
            "address": "STREET_FULL_NAME",
        },
    }
    rows = [
        {
            "PERMIT_NAME": "MADISON AT LOUISE APTS.",
            "Units": "40",
            "PER_ISSUE_DATE": "2026-08-01",
            "STREET_FULL_NAME": "2825 W LOUISE DR",
        }
    ]
    records = find_upcoming("Rivertown", "ZZ", "zz", recipe, _http_get(rows), today=TODAY)
    assert len(records) == 1
    assert records[0].name == "MADISON AT LOUISE APTS."


def test_blank_name_and_type_falls_back_to_address():
    recipe = {
        "endpoint": "https://example.test/query",
        "fields": {
            "issue_date": "IssueDate",
            "address": "Address",
            "units": "Units",
        },
    }
    rows = [{"IssueDate": "2026-08-01", "Address": "5 River Rd", "Units": "40"}]
    records = find_upcoming("Rivertown", "ZZ", "zz", recipe, _http_get(rows), today=TODAY)
    assert len(records) == 1
    assert records[0].name == "5 River Rd"


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
