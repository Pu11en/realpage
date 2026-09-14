"""lead-finder-sources (2.2) tests: fake ArcGIS/Socrata/CKAN catalogs, no network."""
import datetime
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import find_sources  # noqa: E402

TODAY = datetime.date(2026, 9, 14)


def _rows(n, *, mf_every=3, address_key="address", date_key="issue_date", unit_key="units_authorized"):
    """`n` fake permit rows, 1-in-`mf_every` multifamily, all dated recently."""
    rows = []
    for i in range(n):
        rows.append({
            "permit_type": "multifamily new construction" if i % mf_every == 0 else "single family",
            date_key: "2026-06-01",
            unit_key: "40" if i % mf_every == 0 else "1",
            address_key: f"{i} Main St",
        })
    return rows


SOCRATA_ROWS = _rows(120)

SOCRATA_CATALOG_HIT = {
    "results": [
        {
            "resource": {"id": "abcd-1234", "name": "Building Permits"},
            "metadata": {"domain": "data.rivertown-example.gov"},
        }
    ]
}

ARCGIS_CATALOG_HIT = {
    "data": [
        {"attributes": {"name": "City Building Permits Layer", "url": "https://gis.cedarville-example.gov/arcgis/rest/services/Permits/FeatureServer/0"}},
    ]
}

ARCGIS_ROWS = {
    "features": [
        {"attributes": {"PermitType": r["permit_type"], "IssueDate": r["issue_date"], "Units": r["units_authorized"], "Address": r["address"]}}
        for r in _rows(110, address_key="address", date_key="issue_date", unit_key="units_authorized")
    ]
}

CKAN_CATALOG_HIT = {
    "result": {
        "results": [
            {
                "title": "Building Permits",
                "organization": {"title": "City of Oldtown, TX"},
                "resources": [{"format": "CSV", "url": "https://data.oldtown-example.gov/permits.csv"}],
            }
        ]
    }
}


def test_socrata_catalog_hit_saved_as_recipe(tmp_path):
    def http_get(url):
        if url.startswith(find_sources.ARCGIS_ONLINE_SEARCH) or url.startswith(find_sources.ARCGIS_HUB_SEARCH):
            return {"results": []} if "sharing/rest/search" in url else {"data": []}
        if url.startswith(find_sources.SOCRATA_CATALOG):
            return SOCRATA_CATALOG_HIT
        assert "rivertown-example.gov/resource/abcd-1234.json" in url
        return SOCRATA_ROWS

    recipe = find_sources.find_sources("Rivertown", "TX", http_get, recipes_dir=tmp_path, today=TODAY)
    assert recipe["system"] == "socrata"
    assert recipe["city"] == "Rivertown"
    assert recipe["fields"]["units"] == "units_authorized"
    assert "of 120 sample rows look multifamily" in recipe["completeness"]

    saved = json.loads((tmp_path / "rivertown.json").read_text())
    assert saved == recipe


FILTER_VIEW_CATALOG_HIT = {
    "results": [
        {
            "resource": {
                "id": "view-9999", "name": "All Building Permits Filtered View",
                "type": "filter", "parent_fxf": ["base-1111"],
            },
            "metadata": {"domain": "data.rivertown-example.gov"},
        }
    ]
}


def test_filter_view_queried_via_parent_dataset_id(tmp_path):
    """A Socrata 'filter' resource is a saved view of another dataset -- querying
    /resource/<view id>.json 403s in practice, so the real dataset (parent_fxf)
    must be used instead. Found against real data.buffalony.gov catalog results."""
    def http_get(url):
        if url.startswith(find_sources.ARCGIS_ONLINE_SEARCH):
            return {"results": []}
        if url.startswith(find_sources.ARCGIS_HUB_SEARCH):
            return {"data": []}
        if url.startswith(find_sources.SOCRATA_CATALOG):
            return FILTER_VIEW_CATALOG_HIT
        assert "rivertown-example.gov/resource/base-1111.json" in url
        return SOCRATA_ROWS

    recipe = find_sources.find_sources("Rivertown", "TX", http_get, recipes_dir=tmp_path, today=TODAY)
    assert recipe["endpoint"] == "https://data.rivertown-example.gov/resource/base-1111.json"


def test_arcgis_hub_hit_used_when_ahead_of_socrata(tmp_path):
    def http_get(url):
        if url.startswith(find_sources.ARCGIS_ONLINE_SEARCH):
            return {"results": []}
        if url.startswith(find_sources.ARCGIS_HUB_SEARCH):
            return ARCGIS_CATALOG_HIT
        return ARCGIS_ROWS

    recipe = find_sources.find_sources("Cedarville", "TX", http_get, recipes_dir=tmp_path, today=TODAY)
    assert recipe["system"] == "arcgis"
    assert recipe["fields"]["units"] == "Units"
    assert (tmp_path / "cedarville.json").exists()


def test_arcgis_online_org_hub_used_before_generic_hub(tmp_path):
    """Ask ArcGIS Online for a permits item naming the place, resolve its owner
    org to that org's own hub, and search there -- never guess the hub domain."""
    online_hit = {"results": [{"orgId": "org123"}]}
    org_info = {"urlKey": "cedarville"}
    org_hub = "https://cedarville-hub.arcgis.com/api/search/v1/collections/dataset/items"

    def http_get(url):
        if url.startswith(find_sources.ARCGIS_ONLINE_SEARCH):
            return online_hit
        if url.startswith(find_sources.ARCGIS_ORG_INFO):
            assert "org123" in url
            return org_info
        if url.startswith(org_hub):
            return ARCGIS_CATALOG_HIT
        if url.startswith(find_sources.ARCGIS_HUB_SEARCH):
            raise AssertionError("should not fall back to the generic hub when the org hub hit")
        return ARCGIS_ROWS

    recipe = find_sources.find_sources("Cedarville", "TX", http_get, recipes_dir=tmp_path, today=TODAY)
    assert recipe["system"] == "arcgis"


def test_ckan_catalog_hit_used_when_arcgis_and_socrata_have_nothing(tmp_path):
    def http_get(url):
        if url.startswith(find_sources.ARCGIS_ONLINE_SEARCH) or url.startswith(find_sources.ARCGIS_HUB_SEARCH):
            return {"results": []} if "sharing/rest/search" in url else {"data": []}
        if url.startswith(find_sources.SOCRATA_CATALOG):
            return {"results": []}
        if url.startswith(find_sources.CKAN_CATALOG):
            return CKAN_CATALOG_HIT
        return _rows(150)

    recipe = find_sources.find_sources("Oldtown", "TX", http_get, recipes_dir=tmp_path, today=TODAY)
    assert recipe["system"] == "ckan"
    assert recipe["endpoint"] == "https://data.oldtown-example.gov/permits.csv"


WRONG_JURISDICTION_CATALOG_HIT = {
    "results": [
        {
            "resource": {"id": "wxyz-9999", "name": "White Plains Building Permits"},
            "metadata": {"domain": "opendata.otherplace-example.gov"},
        }
    ]
}


def test_catalog_hit_from_unrelated_domain_is_rejected(tmp_path):
    """Real-world case: searching Socrata for "White Plains building permits"
    returned a Howard County, MD dataset whose name happened to say the city --
    reject any hit whose portal domain doesn't say it belongs to this city/state."""
    def http_get(url):
        if url.startswith(find_sources.SOCRATA_CATALOG):
            return WRONG_JURISDICTION_CATALOG_HIT
        return {"data": [], "results": []}

    assert find_sources.find_sources("White Plains", "NY", http_get, recipes_dir=tmp_path, today=TODAY) is None


def test_no_catalog_hit_returns_none_and_saves_nothing(tmp_path):
    def http_get(url):
        return {"data": [], "results": []}

    assert find_sources.find_sources("Oakford", "TX", http_get, recipes_dir=tmp_path, today=TODAY) is None
    assert not list(tmp_path.glob("*.json"))


def test_small_yearly_totals_table_is_rejected(tmp_path):
    """A dataset of a handful of rows of yearly totals is not permit-level data --
    a dataset must have at least 100 sample rows to be accepted."""
    def http_get(url):
        if url.startswith(find_sources.ARCGIS_ONLINE_SEARCH) or url.startswith(find_sources.ARCGIS_HUB_SEARCH):
            return {"results": []} if "sharing/rest/search" in url else {"data": []}
        if url.startswith(find_sources.SOCRATA_CATALOG):
            return SOCRATA_CATALOG_HIT
        if url.startswith(find_sources.CKAN_CATALOG):
            return {"result": {"results": []}}
        return _rows(22)

    assert find_sources.find_sources("Rivertown", "TX", http_get, recipes_dir=tmp_path, today=TODAY) is None
    assert not list(tmp_path.glob("*.json"))


def test_dataset_with_no_address_field_is_rejected(tmp_path):
    def http_get(url):
        if url.startswith(find_sources.ARCGIS_ONLINE_SEARCH) or url.startswith(find_sources.ARCGIS_HUB_SEARCH):
            return {"results": []} if "sharing/rest/search" in url else {"data": []}
        if url.startswith(find_sources.SOCRATA_CATALOG):
            return SOCRATA_CATALOG_HIT
        if url.startswith(find_sources.CKAN_CATALOG):
            return {"result": {"results": []}}
        return [{"permit_type": "misc", "issue_date": "2026-06-01", "notes": "no address here"} for _ in range(120)]

    assert find_sources.find_sources("Rivertown", "TX", http_get, recipes_dir=tmp_path, today=TODAY) is None


def test_dataset_with_only_old_dates_is_rejected(tmp_path):
    old_rows = _rows(120)
    for row in old_rows:
        row["issue_date"] = "2019-01-01"

    def http_get(url):
        if url.startswith(find_sources.ARCGIS_ONLINE_SEARCH) or url.startswith(find_sources.ARCGIS_HUB_SEARCH):
            return {"results": []} if "sharing/rest/search" in url else {"data": []}
        if url.startswith(find_sources.SOCRATA_CATALOG):
            return SOCRATA_CATALOG_HIT
        if url.startswith(find_sources.CKAN_CATALOG):
            return {"result": {"results": []}}
        return old_rows

    assert find_sources.find_sources("Rivertown", "TX", http_get, recipes_dir=tmp_path, today=TODAY) is None


def test_test_dataset_helper_directly():
    assert find_sources.test_dataset([], today=TODAY) is None
    assert find_sources.test_dataset([{"notes": "x"}], today=TODAY) is None
    assert find_sources.test_dataset(_rows(22), today=TODAY) is None  # too few rows
    note = find_sources.test_dataset(SOCRATA_ROWS, today=TODAY)
    assert note is not None
    assert "of 120 sample rows look multifamily" in note


def test_slugify():
    assert find_sources.slugify("Rivertown") == "rivertown"
    assert find_sources.slugify("Oakford County") == "oakford-county"
