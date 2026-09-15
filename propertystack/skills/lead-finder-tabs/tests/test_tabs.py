import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tabs import find_tabs_projects  # noqa: E402

RECIPE = {
    "endpoint": "https://example.test/TABS/Search/SearchProjects",
    "detail_url_template": "https://example.test/TABS/Search/Project/{project_number}",
    "keywords": ["apartment", "multifamily"],
    "registration_date_begin": "09/01/2024",
    "data_version_id": 900001,
    "page_size": 2,
    "new_construction_type_of_work": 9001,
    "min_estimated_cost": 3000000,
    "units_text_pattern": r"(\d+)[\s-]*(?:unit|units)\b",
}

DETAIL_HTML = """
<dl class="dl-horizontal">
    <dt>Project Name:</dt>
    <dd>Sonrisa Village Apartments</dd>
    <dt>Location Address:</dt>
    <dd>5000 Bowie Road</dd>
    <dd>Rivertown, TX 78521</dd>
    <dt>Location County:</dt>
    <dd>Rivercounty</dd>
</dl>
<dl class="dl-horizontal">
    <dt>Scope of Work:</dt>
    <dd>New construction apartment complex, 300 units</dd>
</dl>
<div class="project-details-owner">
    <dl class="dl-horizontal">
      <dt>Owner Name:</dt>
      <dd>Jane Owner</dd>
      <dt>Owner Address:</dt>
      <dd>1 Main St</dd>
      <dd>Rivertown, ZZ 78521</dd>
      <dt>Owner Phone:</dt>
      <dd>(555) 555-1234</dd>
    </dl>
</div>
<div class="project-details-designer">
    <dl class="dl-horizontal">
        <dt>Design Firm Name:</dt>
        <dd>Some Design Firm</dd>
    </dl>
</div>
"""


def _row(number, name, type_of_work=9001, cost=39050000.0):
    return {
        "ProjectId": number,
        "ProjectNumber": number,
        "ProjectName": name,
        "FacilityName": name,
        "City": 211,
        "County": 2031,
        "TypeOfWork": type_of_work,
        "EstimatedCost": cost,
        "ProjectCreatedOn": "2026-09-14T14:13:52.807",
        "EstimatedStartDate": "2026-12-11T00:00:00",
        "EstimatedEndDate": "2028-07-17T00:00:00",
    }


def test_new_construction_project_is_kept_with_detail_fields_filled():
    def fetch_search(payload):
        return {"recordsTotal": 1, "data": [_row("TABS1", "Sonrisa Village Apartments")]}

    def fetch_detail(number):
        return DETAIL_HTML

    records = find_tabs_projects("tx", RECIPE, fetch_search, fetch_detail)
    assert len(records) == 1
    record = records[0]
    assert record.name == "Sonrisa Village Apartments"
    assert record.city == "Rivertown"
    assert record.units == 300
    assert record.developer == "Jane Owner"
    assert record.office_phone == "(555) 555-1234"
    assert record.links["permit"] == "https://example.test/TABS/Search/Project/TABS1"


def test_repair_type_of_work_is_dropped():
    def fetch_search(payload):
        return {"recordsTotal": 1, "data": [_row("TABS2", "Some Repair", type_of_work=9003)]}

    records = find_tabs_projects("tx", RECIPE, fetch_search, lambda n: DETAIL_HTML)
    assert records == []


def test_below_cost_floor_is_dropped():
    def fetch_search(payload):
        return {"recordsTotal": 1, "data": [_row("TABS3", "Small Project", cost=500000.0)]}

    records = find_tabs_projects("tx", RECIPE, fetch_search, lambda n: DETAIL_HTML)
    assert records == []


def test_project_matching_two_keywords_is_only_counted_once():
    calls = []

    def fetch_search(payload):
        calls.append(payload["ProjectName"])
        return {"recordsTotal": 1, "data": [_row("TABS1", "Sonrisa Village Apartments")]}

    records = find_tabs_projects("tx", RECIPE, fetch_search, lambda n: DETAIL_HTML)
    assert len(records) == 1
    assert calls == ["apartment", "multifamily"]


def test_pagination_follows_records_total():
    pages = {
        0: {"recordsTotal": 3, "data": [_row("TABS1", "A"), _row("TABS2", "B")]},
        2: {"recordsTotal": 3, "data": [_row("TABS3", "C")]},
    }

    def fetch_search(payload):
        return pages[payload["start"]]

    def fetch_detail(number):
        return DETAIL_HTML.replace("5000 Bowie Road", f"{number} Bowie Road")

    records = find_tabs_projects(
        "tx",
        {**RECIPE, "keywords": ["apartment"]},
        fetch_search,
        fetch_detail,
    )
    assert len(records) == 3


def test_no_units_in_scope_leaves_units_none():
    def fetch_search(payload):
        return {"recordsTotal": 1, "data": [_row("TABS4", "No Unit Count")]}

    def fetch_detail(number):
        return DETAIL_HTML.replace("New construction apartment complex, 300 units", "New construction apartment complex")

    records = find_tabs_projects("tx", RECIPE, fetch_search, fetch_detail)
    assert len(records) == 1
    assert records[0].units is None


def test_a_broken_detail_fetch_still_returns_a_record():
    def fetch_search(payload):
        return {"recordsTotal": 1, "data": [_row("TABS5", "Detail Fetch Fails")]}

    def fetch_detail(number):
        raise RuntimeError("network down")

    records = find_tabs_projects("tx", RECIPE, fetch_search, fetch_detail)
    assert len(records) == 1
    assert records[0].name == "Detail Fetch Fails"
    assert records[0].units is None
