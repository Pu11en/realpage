import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "contact_scrape_run", Path(__file__).resolve().parents[1] / "run.py"
)
_run = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_run)
scrape = _run.scrape


class FakeJina:
    def __init__(self, page_text):
        self.page_text = page_text

    def read(self, url):
        return self.page_text


def test_scrape_skips_low_confidence():
    row = {"apt_id": "1", "website": "https://x.example.com", "website_confidence": "low"}
    out = scrape(row, FakeJina("anything"), "2026-09-14")
    assert out["notes"] == "no-website"


def test_scrape_rejects_page_not_about_this_building():
    row = {
        "apt_id": "1", "website": "https://marqueesportsnetwork.com", "website_confidence": "high",
        "name": "Marquee on 5th", "address": "500 5th Ave",
    }
    out = scrape(row, FakeJina("Marquee Sports Network schedule and scores"), "2026-09-14")
    assert out["notes"] == "page-not-about-this-building"
    assert out["phone"] == ""
    assert out["email"] == ""


def test_scrape_finds_phone_on_real_building_page():
    row = {
        "apt_id": "1", "website": "https://bellavictoria.com", "website_confidence": "high",
        "name": "Bella Victoria", "address": "1 Bella Victoria Way",
    }
    text = "Welcome to Bella Victoria Apartments. Call our office at (520) 555-0134 to schedule a tour."
    out = scrape(row, FakeJina(text), "2026-09-14")
    assert out["phone"] == "(520) 555-0134"
