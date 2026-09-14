import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lead-finder"))

from project_details import fill_project_details, geocode_address  # noqa: E402
from record import LeadRecord  # noqa: E402


class FakePage:
    def __init__(self, ok, html=""):
        self.ok = ok
        self.html = html


def make_record(**kw):
    defaults = dict(area="zz", city="Rivertown", address="123 Main St", units=None)
    defaults.update(kw)
    return LeadRecord(**defaults)


def test_geocode_address_returns_lat_lon():
    def geocode_fn(query):
        assert "123 Main St" in query
        return {"result": {"addressMatches": [{"coordinates": {"x": -96.5, "y": 32.9}}]}}

    coords = geocode_address("123 Main St", "Rivertown", "ZZ", geocode_fn)
    assert coords == (32.9, -96.5)


def test_geocode_address_no_match_returns_none():
    def geocode_fn(query):
        return {"result": {"addressMatches": []}}

    assert geocode_address("123 Main St", "Rivertown", "ZZ", geocode_fn) is None


def test_geocode_address_blank_address_returns_none():
    assert geocode_address("", "Rivertown", "ZZ", lambda q: {}) is None


def test_geocode_address_fn_raises_returns_none():
    def geocode_fn(query):
        raise OSError("down")

    assert geocode_address("123 Main St", "Rivertown", "ZZ", geocode_fn) is None


def test_fill_project_details_fills_units_developer_opening_website():
    record = make_record()
    results = [{"title": "Riverside Flats", "url": "https://riversideflats.example.com"}]
    html = (
        "<html>Riverside Flats is a new 220-unit community developed by "
        "Acme Development Group. Now leasing March 2026.</html>"
    )

    def search_fn(query, n):
        return results

    def fetch_fn(url):
        return FakePage(ok=True, html=html)

    out = fill_project_details(record, search_fn, fetch_fn)
    assert out is not None
    assert out.units == 220
    assert out.developer == "Acme Development Group"
    assert out.opening_date == "March 2026"
    assert out.website == "https://riversideflats.example.com"
    assert any(s["fact"] == "units" for s in out.sources)


def test_fill_project_details_picks_news_link_separately():
    record = make_record()
    results = [
        {"title": "Local Business Journal", "url": "https://example-businessjournal.example.com/story"},
        {"title": "Riverside Flats", "url": "https://riversideflats.example.com"},
    ]
    html = "220-unit community."

    def search_fn(query, n):
        return results

    def fetch_fn(url):
        return FakePage(ok=True, html=html)

    out = fill_project_details(record, search_fn, fetch_fn)
    assert out.links["news"] == "https://example-businessjournal.example.com/story"
    assert out.website == "https://riversideflats.example.com"


def test_fill_project_details_drops_when_units_still_unknown():
    record = make_record()

    def search_fn(query, n):
        return [{"title": "Nothing useful", "url": "https://example.com/x"}]

    def fetch_fn(url):
        return FakePage(ok=True, html="no facts here")

    assert fill_project_details(record, search_fn, fetch_fn) is None


def test_fill_project_details_keeps_existing_units_without_overwrite():
    record = make_record(units=150)

    def search_fn(query, n):
        return [{"title": "x", "url": "https://example.com/x"}]

    def fetch_fn(url):
        return FakePage(ok=True, html="300-unit community")

    out = fill_project_details(record, search_fn, fetch_fn)
    assert out.units == 150


def test_fill_project_details_no_results_drops_if_units_unknown():
    record = make_record()

    def search_fn(query, n):
        return []

    def fetch_fn(url):
        return FakePage(ok=False)

    assert fill_project_details(record, search_fn, fetch_fn) is None


def test_fill_project_details_applies_geocode_when_provided():
    record = make_record(units=100)

    def search_fn(query, n):
        return []

    def fetch_fn(url):
        return FakePage(ok=False)

    def geocode_fn(query):
        return {"result": {"addressMatches": [{"coordinates": {"x": -96.1, "y": 33.1}}]}}

    out = fill_project_details(record, search_fn, fetch_fn, geocode_fn=geocode_fn)
    assert out.lat == 33.1
    assert out.lon == -96.1


def test_fill_project_details_fetch_not_ok_skipped():
    record = make_record()
    results = [
        {"title": "blocked", "url": "https://blocked.example.com"},
        {"title": "works", "url": "https://ok.example.com"},
    ]

    def search_fn(query, n):
        return results

    def fetch_fn(url):
        if "blocked" in url:
            return FakePage(ok=False)
        return FakePage(ok=True, html="180-unit community")

    out = fill_project_details(record, search_fn, fetch_fn)
    assert out.units == 180
