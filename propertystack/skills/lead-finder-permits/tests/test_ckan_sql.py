import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ckan_sql import ckan_sql_http_get  # noqa: E402
from find_upcoming import find_upcoming  # noqa: E402


def test_unwraps_ckan_envelope_to_plain_list():
    seen_urls = []

    def fake_fetch(url):
        seen_urls.append(url)
        return {"result": {"records": [{"a": 1}, {"a": 2}]}}

    http_get = ckan_sql_http_get("https://example.test/action/datastore_search_sql", "SELECT 1", fake_fetch)
    rows = http_get("ignored-endpoint-arg")
    assert rows == [{"a": 1}, {"a": 2}]
    assert len(seen_urls) == 1
    assert "sql=" in seen_urls[0]


def test_non_dict_response_returns_empty_list():
    http_get = ckan_sql_http_get("https://example.test/action/datastore_search_sql", "SELECT 1", lambda url: None)
    assert http_get("ignored") == []


def test_find_upcoming_reads_ckan_rows_through_the_adapter():
    def fake_fetch(url):
        return {
            "result": {
                "records": [
                    {
                        "PROJECT NAME": "Some Apartments Building 1",
                        "ADDRESS": "1 Main St",
                        "DATE ISSUED": "2026-08-01",
                    }
                ]
            }
        }

    recipe = {
        "city": "City E",
        "state": "ZZ",
        "system": "ckan-sql",
        "endpoint": "https://example.test/action/datastore_search_sql",
        "sql": "SELECT 1",
        "fields": {
            "permit_type": "PROJECT NAME",
            "name": "PROJECT NAME",
            "issue_date": "DATE ISSUED",
            "address": "ADDRESS",
        },
    }
    http_get = ckan_sql_http_get(recipe["endpoint"], recipe["sql"], fake_fetch)
    import datetime

    records = find_upcoming("City E", "ZZ", "zz", recipe, http_get, today=datetime.date(2026, 9, 14))
    assert len(records) == 1
    assert records[0].name == "Some Apartments Building 1"
    assert records[0].units is None
