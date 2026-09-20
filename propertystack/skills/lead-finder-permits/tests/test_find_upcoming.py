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


def test_null_address_column_does_not_merge_every_row_into_one():
    """A mapped address column that exists but holds null used to become the
    literal string "None" on every row, so merge_records saw one building and
    collapsed a whole feed into a single lead."""
    rows = [
        {"PermitType": "Apartment", "IssueDate": "2026-08-01", "Units": "120", "Address": None, "Name": "Copper Ranch"},
        {"PermitType": "Apartment", "IssueDate": "2026-08-02", "Units": "90", "Address": None, "Name": "Rock Creek"},
        {"PermitType": "Apartment", "IssueDate": "2026-08-03", "Units": "60", "Address": None, "Name": "Basswood"},
    ]
    recipe = {**RECIPE, "fields": {**RECIPE["fields"], "name": "Name"}}
    records = find_upcoming("Rivertown", "ZZ", "zz", recipe, _http_get(rows), today=TODAY)
    assert len(records) == 3
    assert [r.address for r in records] == ["", "", ""]
    assert {r.name for r in records} == {"Copper Ranch", "Rock Creek", "Basswood"}


def test_address_parts_build_the_address_when_there_is_no_single_column():
    """Some permit layers keep no whole-address column at all -- the number,
    street and suffix live in separate columns and must be joined."""
    rows = [
        {
            "PermitType": "Apartment", "IssueDate": "2026-08-01", "Units": "228",
            "Address": None, "No": 4000, "Dir": None, "Street": "WESTBROOK", "Suffix": "DR",
        }
    ]
    recipe = {
        **RECIPE,
        "fields": {**RECIPE["fields"], "address_parts": ["No", "Dir", "Street", "Suffix"]},
    }
    records = find_upcoming("Rivertown", "ZZ", "zz", recipe, _http_get(rows), today=TODAY)
    assert len(records) == 1
    assert records[0].address == "4000 WESTBROOK DR"


def test_address_parts_ignored_when_the_real_address_column_has_a_value():
    rows = [
        {
            "PermitType": "Apartment", "IssueDate": "2026-08-01", "Units": "228",
            "Address": "100 Main St", "No": 4000, "Street": "WESTBROOK", "Suffix": "DR",
        }
    ]
    recipe = {**RECIPE, "fields": {**RECIPE["fields"], "address_parts": ["No", "Street", "Suffix"]}}
    records = find_upcoming("Rivertown", "ZZ", "zz", recipe, _http_get(rows), today=TODAY)
    assert records[0].address == "100 Main St"


def test_placeholder_address_rows_are_dropped_not_sold_as_real_streets():
    """A feed that files un-sited plan reviews at a stand-in street must not
    produce leads a seller would try to drive to."""
    rows = [
        {"PermitType": "Apartment", "IssueDate": "2026-08-01", "Units": "200",
         "Address": None, "No": 25060118, "Street": "FOR REVIEW ONLY", "Suffix": "WAY", "Name": "Hughes House"},
        {"PermitType": "Apartment", "IssueDate": "2026-08-02", "Units": "228",
         "Address": None, "No": 4000, "Street": "WESTBROOK", "Suffix": "DR", "Name": "Ridgeway Flats"},
    ]
    recipe = {
        **RECIPE,
        "fields": {**RECIPE["fields"], "name": "Name", "address_parts": ["No", "Street", "Suffix"]},
    }
    stats: dict = {}
    records = find_upcoming("Rivertown", "ZZ", "zz", recipe, _http_get(rows), today=TODAY, stats=stats)
    assert [r.name for r in records] == ["Ridgeway Flats"]
    assert stats["placeholderAddress"] == 1


def test_genuinely_blank_address_is_kept_not_treated_as_placeholder():
    """An empty address is not a stand-in: some sources legitimately have a
    named project with no street yet, and dropping those would lose real leads."""
    rows = [
        {"PermitType": "Apartment", "IssueDate": "2026-08-01", "Units": "200", "Address": "", "Name": "Hughes House"},
    ]
    recipe = {**RECIPE, "fields": {**RECIPE["fields"], "name": "Name"}}
    stats: dict = {}
    records = find_upcoming("Rivertown", "ZZ", "zz", recipe, _http_get(rows), today=TODAY, stats=stats)
    assert [r.name for r in records] == ["Hughes House"]
    assert stats["placeholderAddress"] == 0


def test_stats_name_every_drop_reason():
    """The run must be able to say where rows went, not just how few survived."""
    rows = [
        # kept
        {"PermitType": "Apartment", "IssueDate": "2026-08-01", "Units": "120", "Address": "1 A St"},
        # merged away: same address as the row above
        {"PermitType": "Apartment", "IssueDate": "2026-08-02", "Units": "120", "Address": "1 A St"},
        # aged out: permit older than the 24-month window, no CO
        {"PermitType": "Apartment", "IssueDate": "2020-01-01", "Units": "120", "Address": "2 B St"},
        # no usable date at all
        {"PermitType": "Apartment", "IssueDate": "", "Units": "120", "Address": "3 C St"},
        # placeholder address
        {"PermitType": "Apartment", "IssueDate": "2026-08-01", "Units": "120", "Address": "9 FOR REVIEW ONLY WAY"},
        # junk: a pool at an apartment complex is not a new building
        {"PermitType": "Apartment", "IssueDate": "2026-08-01", "Units": "120", "Address": "4 D St",
         "Name": "Swimming Pool"},
        # not an apartment at all: known unit count under 20
        {"PermitType": "Apartment", "IssueDate": "2026-08-01", "Units": "4", "Address": "5 E St"},
    ]
    recipe = {**RECIPE, "fields": {**RECIPE["fields"], "name": "Name"}}
    stats: dict = {}
    find_upcoming("Rivertown", "ZZ", "zz", recipe, _http_get(rows), today=TODAY, stats=stats)
    assert stats["rows"] == 7
    assert stats["apartmentRows"] == 6
    assert stats["agedOut"] == 1
    assert stats["noDate"] == 1
    assert stats["placeholderAddress"] == 1
    assert stats["junkDropped"] == 1
    assert stats["built"] == 2
    assert stats["mergedAway"] == 1
    assert stats["kept"] == 1
    assert stats["newestDate"] == "2026-08-02"


def test_plan_review_routing_tag_is_stripped_from_the_project_name():
    """Some permit systems prefix the project name with the third-party plan
    reviewer's routing tag; the seller is calling the building, not the
    reviewer."""
    rows = [
        {"PermitType": "Apartment", "IssueDate": "2026-08-01", "Units": "322",
         "Address": "3200 Hamilton Ave", "Name": "Q TEAM /// Spring Hill East"},
    ]
    recipe = {**RECIPE, "fields": {**RECIPE["fields"], "name": "Name"}}
    records = find_upcoming("Rivertown", "ZZ", "zz", recipe, _http_get(rows), today=TODAY)
    assert records[0].name == "Spring Hill East"


def test_a_name_without_a_routing_tag_is_untouched():
    rows = [
        {"PermitType": "Apartment", "IssueDate": "2026-08-01", "Units": "310",
         "Address": "1000 Jones St", "Name": "The Calhoun"},
    ]
    recipe = {**RECIPE, "fields": {**RECIPE["fields"], "name": "Name"}}
    records = find_upcoming("Rivertown", "ZZ", "zz", recipe, _http_get(rows), today=TODAY)
    assert records[0].name == "The Calhoun"
