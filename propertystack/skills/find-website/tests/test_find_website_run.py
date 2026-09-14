import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "find_website_run", Path(__file__).resolve().parents[1] / "run.py"
)
_run = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_run)
classify, pick_best = _run.classify, _run.pick_best


def test_marquee_on_5th_rejects_sports_network_and_st_louis_marquee():
    results = [
        {"url": "https://marqueesportsnetwork.com", "title": "Marquee Sports Network", "description": ""},
        {"url": "https://themarqueestl.com", "title": "The Marquee St. Louis", "description": ""},
    ]
    tier, best = pick_best("Marquee on 5th", results, "500 5th Ave")
    assert tier == "none"
    assert best is None


def test_bella_victoria_picks_its_own_site():
    results = [{"url": "https://bellavictoria.com", "title": "Bella Victoria Apartments", "description": ""}]
    tier, best = pick_best("Bella Victoria", results, "1 Bella Victoria Way")
    assert tier == "high"
    assert best["url"] == "https://bellavictoria.com"


def test_listing_site_is_never_accepted_even_with_name_match():
    results = [{"url": "https://www.apartments.com/bella-victoria", "title": "Bella Victoria Apartments", "description": ""}]
    assert classify("Bella Victoria", results[0]) is None
