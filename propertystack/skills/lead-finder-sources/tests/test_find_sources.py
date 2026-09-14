"""lead-finder-sources (2.2) tests: fake Socrata/ArcGIS catalogs, no network."""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import find_sources  # noqa: E402


SOCRATA_CATALOG_HIT = {
    "results": [
        {
            "resource": {"id": "abcd-1234", "name": "Building Permits"},
            "metadata": {"domain": "data.rivertown-example.gov"},
        }
    ]
}

SOCRATA_ROWS = [
    {"permit_type": "multifamily new construction", "issue_date": "2026-01-05", "units_authorized": "40", "address": "1 Main St"},
    {"permit_type": "single family", "issue_date": "2026-01-06", "units_authorized": "1", "address": "2 Main St"},
]

ARCGIS_CATALOG_HIT = {
    "data": [
        {"attributes": {"name": "City Building Permits Layer", "url": "https://gis.cedarville-example.gov/arcgis/rest/services/Permits/FeatureServer/0"}},
    ]
}

ARCGIS_ROWS = {
    "features": [
        {"attributes": {"PermitType": "apartment", "IssueDate": "2026-02-01", "Units": "60", "Address": "9 Oak Ave"}},
    ]
}


def test_socrata_catalog_hit_saved_as_recipe(tmp_path):
    def http_get(url):
        if url.startswith(find_sources.SOCRATA_CATALOG):
            return SOCRATA_CATALOG_HIT
        assert "rivertown-example.gov/resource/abcd-1234.json" in url
        return SOCRATA_ROWS

    recipe = find_sources.find_sources("Rivertown", "TX", http_get, recipes_dir=tmp_path)
    assert recipe["system"] == "socrata"
    assert recipe["city"] == "Rivertown"
    assert recipe["fields"]["units"] == "units_authorized"
    assert "1 of 2 sample rows look multifamily" in recipe["completeness"]

    saved = json.loads((tmp_path / "rivertown.json").read_text())
    assert saved == recipe


def test_arcgis_hub_hit_used_when_socrata_has_nothing(tmp_path):
    def http_get(url):
        if url.startswith(find_sources.SOCRATA_CATALOG):
            return {"results": []}
        if url.startswith(find_sources.ARCGIS_HUB_SEARCH):
            return ARCGIS_CATALOG_HIT
        return ARCGIS_ROWS

    recipe = find_sources.find_sources("Cedarville", "TX", http_get, recipes_dir=tmp_path)
    assert recipe["system"] == "arcgis"
    assert recipe["fields"]["units"] == "Units"
    assert (tmp_path / "cedarville.json").exists()


def test_no_catalog_hit_returns_none_and_saves_nothing(tmp_path):
    def http_get(url):
        if url.startswith(find_sources.SOCRATA_CATALOG):
            return {"results": []}
        return {"data": []}

    assert find_sources.find_sources("Oakford", "TX", http_get, recipes_dir=tmp_path) is None
    assert not list(tmp_path.glob("*.json"))


def test_dataset_with_no_units_or_date_fields_is_rejected(tmp_path):
    def http_get(url):
        if url.startswith(find_sources.SOCRATA_CATALOG):
            return SOCRATA_CATALOG_HIT
        if url.startswith(find_sources.ARCGIS_HUB_SEARCH):
            return {"data": []}
        return [{"permit_type": "misc", "notes": "nothing useful"}]

    assert find_sources.find_sources("Rivertown", "TX", http_get, recipes_dir=tmp_path) is None


def test_test_dataset_helper_directly():
    assert find_sources.test_dataset([]) is None
    assert find_sources.test_dataset([{"notes": "x"}]) is None
    note = find_sources.test_dataset(SOCRATA_ROWS)
    assert note is not None
    assert "1 of 2" in note


def test_slugify():
    assert find_sources.slugify("Rivertown") == "rivertown"
    assert find_sources.slugify("Oakford County") == "oakford-county"
