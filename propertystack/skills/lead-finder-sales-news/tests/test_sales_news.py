import datetime
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

from sales_news import (  # noqa: E402
    extract_buyer,
    find_sales_news,
    gdelt_url,
    hit_to_record,
    news_query,
)

TODAY = datetime.date(2026, 9, 14)


def test_news_query_has_city_and_sale_terms():
    q = news_query("Example City")
    assert '"Example City"' in q
    assert "sold" in q
    assert "acquisition" in q


def test_gdelt_url_encodes_query():
    url = gdelt_url('"Example City" apartments sold')
    assert url.startswith("https://api.gdeltproject.org/api/v2/doc/doc?")
    assert "mode=artlist" in url
    assert "format=json" in url


def test_hit_to_record_full_match():
    rec = hit_to_record(
        "Example Towers, a 220-unit apartment complex, sold",
        "Example Capital acquired by Sample Investors for $40M.",
        "https://news.example.com/a",
        "Example City",
        "zz",
        datetime.date(2026, 6, 1),
    )
    assert rec is not None
    assert rec.units == 220
    assert rec.stage == "sold"
    assert rec.sale_date == "2026-06-01"
    assert rec.city == "Example City"
    assert rec.area == "zz"
    assert rec.links["news"] == "https://news.example.com/a"
    assert rec.buyer == "Sample Investors"


def test_hit_to_record_no_sale_keyword_dropped():
    rec = hit_to_record(
        "Example Towers, a 220-unit apartment complex, breaks ground",
        "",
        "https://news.example.com/b",
        "Example City",
        "zz",
        datetime.date(2026, 6, 1),
    )
    assert rec is None


def test_hit_to_record_no_units_dropped():
    rec = hit_to_record(
        "Example Towers sold to new owner",
        "",
        "https://news.example.com/c",
        "Example City",
        "zz",
        datetime.date(2026, 6, 1),
    )
    assert rec is None


def test_hit_to_record_under_min_units_dropped():
    rec = hit_to_record(
        "Example Duplex, a 10-unit building, sold",
        "",
        "https://news.example.com/d",
        "Example City",
        "zz",
        datetime.date(2026, 6, 1),
    )
    assert rec is None


def test_hit_to_record_no_date_dropped():
    rec = hit_to_record(
        "Example Towers, a 220-unit complex, sold",
        "",
        "https://news.example.com/e",
        "Example City",
        "zz",
        None,
    )
    assert rec is None


def test_extract_buyer_acquires_pattern():
    assert extract_buyer("Sample Capital Partners acquires Example Towers") == "Sample Capital Partners"


def test_extract_buyer_none_found():
    assert extract_buyer("Example Towers sold in a private deal") == ""


def test_find_sales_news_searxng_only():
    def fake_search(query):
        assert "Example City" in query
        return [
            {
                "url": "https://news.example.com/f",
                "title": "Example Towers, a 150-unit complex, sold to Sample REIT",
                "snippet": "",
                "date": "2026-05-01",
            },
            {
                # too old -- outside the 24-month window
                "url": "https://news.example.com/old",
                "title": "Example Old Place, a 100-unit complex, sold",
                "snippet": "",
                "date": "2020-01-01",
            },
            {
                # no units -- dropped
                "url": "https://news.example.com/nounits",
                "title": "Example Place sold",
                "snippet": "",
                "date": "2026-05-01",
            },
        ]

    records = find_sales_news("Example City", "zz", fake_search, today=TODAY)
    assert len(records) == 1
    assert records[0].units == 150
    assert records[0].sale_date == "2026-05-01"


def test_find_sales_news_dedupes_across_searxng_and_gdelt():
    def fake_search(query):
        return [
            {
                "url": "https://news.example.com/dup",
                "title": "Example Towers, a 150-unit complex, sold",
                "snippet": "",
                "date": "2026-05-01",
            }
        ]

    def fake_gdelt_fetch(url):
        return json.dumps(
            {
                "articles": [
                    {
                        "url": "https://news.example.com/dup",
                        "title": "Example Towers, a 150-unit complex, sold",
                        "seendate": "20260501T000000Z",
                    },
                    {
                        "url": "https://news.example.com/gdelt-only",
                        "title": "Example Gardens, a 80-unit complex, acquired by Sample Capital",
                        "seendate": "20260601T000000Z",
                    },
                ]
            }
        ).encode("utf-8")

    records = find_sales_news("Example City", "zz", fake_search, fake_gdelt_fetch, today=TODAY)
    urls = {r.links["news"] for r in records}
    assert urls == {"https://news.example.com/dup", "https://news.example.com/gdelt-only"}
    assert len(records) == 2


def test_find_sales_news_gdelt_bad_json_ignored():
    def fake_search(query):
        return []

    def fake_gdelt_fetch(url):
        return b"not json"

    records = find_sales_news("Example City", "zz", fake_search, fake_gdelt_fetch, today=TODAY)
    assert records == []


def test_find_sales_news_no_gdelt_fetch_fn():
    def fake_search(query):
        return []

    records = find_sales_news("Example City", "zz", fake_search, today=TODAY)
    assert records == []
