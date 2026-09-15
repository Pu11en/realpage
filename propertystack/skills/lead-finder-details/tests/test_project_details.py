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


def make_named_record(**kw):
    return make_record(name="Riverside Flats", **kw)


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
    record = make_named_record()
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
    record = make_named_record()
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


def test_fill_project_details_rejects_same_word_unrelated_site():
    """F2: 'Marquee on 5th' sharing one word with a sports-network site or an
    unrelated St. Louis building is not enough to call it the official site."""
    record = make_record(name="Marquee on 5th", city="Tucson", address="500 5th Ave")
    results = [
        {"title": "Marquee Sports Network", "url": "https://marqueesportsnetwork.com"},
        {"title": "The Marquee St. Louis", "url": "https://themarqueestl.com"},
    ]

    def search_fn(query, n):
        return results

    def fetch_fn(url):
        return FakePage(ok=True, html="220-unit community")

    out = fill_project_details(record, search_fn, fetch_fn)
    assert out is not None
    assert out.website == ""


def test_fill_project_details_searches_name_before_address():
    """F10c: the project/brand name is searched first; the street address is
    only searched if the name query found no real match."""
    record = make_record(name="La Victoria Commons", city="Tempe", address="1020 W Apache Blvd")
    queries_seen = []

    def search_fn(query, n):
        queries_seen.append(query)
        if "La Victoria Commons" in query:
            return [{"title": "La Victoria Commons", "url": "https://lavictoriacommons.example.com"}]
        return [{"title": "Wrong building", "url": "https://unrelated.example.com"}]

    def fetch_fn(url):
        return FakePage(ok=True, html="220-unit community")

    out = fill_project_details(record, search_fn, fetch_fn)
    assert out.website == "https://lavictoriacommons.example.com"
    assert queries_seen[0].startswith('"La Victoria Commons"')


def test_fill_project_details_falls_back_to_address_when_name_query_fails():
    """No acceptable match on the name query -- fall back to the address query."""
    record = make_record(name="1020 Apache", city="Tempe", address="1020 W Apache Blvd")
    queries_seen = []

    def search_fn(query, n):
        queries_seen.append(query)
        if "1020 W Apache Blvd" in query:
            return [{"title": "1020 Apache Blvd Residences", "url": "https://1020apache.example.com"}]
        return [{"title": "Unrelated site", "url": "https://unrelated.example.com"}]

    def fetch_fn(url):
        return FakePage(ok=True, html="150-unit community")

    out = fill_project_details(record, search_fn, fetch_fn)
    assert out.website == "https://1020apache.example.com"
    assert len(queries_seen) == 2


def test_fill_project_details_picks_real_building_site():
    record = make_record(name="Bella Victoria", city="Tucson", address="1 Bella Victoria Way")
    results = [{"title": "Bella Victoria Apartments", "url": "https://bellavictoria.com"}]

    def search_fn(query, n):
        return results

    def fetch_fn(url):
        return FakePage(ok=True, html="220-unit community")

    out = fill_project_details(record, search_fn, fetch_fn)
    assert out.website == "https://bellavictoria.com"
