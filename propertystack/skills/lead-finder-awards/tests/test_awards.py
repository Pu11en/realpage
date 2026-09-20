"""lead-finder-awards (3.2) tests: fixture rows/search results, no network."""
import datetime
import json
import pathlib
import sys

import openpyxl

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import awards  # noqa: E402

TODAY = datetime.date(2026, 9, 14)


def make_row(**kw):
    defaults = dict(
        **{
            "Project Name": "Sample Apartments",
            "City": "Rivertown",
            "Units": 60,
            "Award Date": "2026-01-15",
            "Activity Type": "New Construction",
            "Developer": "Sample Developer LLC",
        }
    )
    defaults.update(kw)
    return defaults


def test_new_construction_award_becomes_planned_lead():
    rows = [make_row()]
    out = awards.parse_award_rows(rows, "ZZ", "https://example.gov/awards.pdf", today=TODAY)
    assert len(out) == 1
    r = out[0]
    assert r.stage == "planned"
    assert r.units == 60
    assert r.city == "Rivertown"
    assert r.area == "zz"
    assert r.permit_date == "2026-01-15"
    assert r.developer == "Sample Developer LLC"
    assert "tax-credit" in r.why


def test_rehab_rows_are_dropped():
    rows = [make_row(**{"Activity Type": "Acquisition-Rehab"})]
    assert awards.parse_award_rows(rows, "ZZ", "https://example.gov/awards.pdf", today=TODAY) == []


def test_under_min_units_dropped():
    rows = [make_row(Units=10)]
    assert awards.parse_award_rows(rows, "ZZ", "https://example.gov/awards.pdf", today=TODAY) == []


def test_too_old_award_dropped():
    rows = [make_row(**{"Award Date": "2020-01-01"})]
    assert awards.parse_award_rows(rows, "ZZ", "https://example.gov/awards.pdf", today=TODAY) == []


def test_missing_units_or_date_dropped_not_guessed():
    rows = [make_row(Units=""), make_row(**{"Award Date": ""})]
    assert awards.parse_award_rows(rows, "ZZ", "https://example.gov/awards.pdf", today=TODAY) == []


def test_find_award_recipe_saves_first_pdf_or_xlsx_hit(tmp_path):
    def search_fn(query):
        if "2025" in query:
            return [{"url": "https://example.gov/about"}]
        if "2026" in query:
            return [{"url": "https://example.gov/awards-2026.pdf"}]
        return []

    recipe = awards.find_award_recipe("ZZ", "Example Housing Finance Agency", search_fn, recipes_dir=tmp_path)
    assert recipe["list_url"] == "https://example.gov/awards-2026.pdf"
    assert recipe["format"] == "pdf"
    saved = json.loads((tmp_path / "awards-zz.json").read_text())
    assert saved == recipe


def test_find_award_recipe_no_hit_returns_skip_note(tmp_path):
    def search_fn(query):
        return [{"url": "https://example.gov/about"}]

    result = awards.find_award_recipe("ZZ", "Example Housing Finance Agency", search_fn, recipes_dir=tmp_path)
    assert result == {"state": "ZZ", "agency": "Example Housing Finance Agency", "skipped": True, "reason": "no award list online"}
    assert not list(tmp_path.glob("*.json"))


def test_find_awards_end_to_end_pdf(tmp_path, monkeypatch):
    def search_fn(query):
        return [{"url": "https://example.gov/awards-2026.pdf"}]

    def fetch_bytes_fn(url):
        return b"fake pdf bytes"

    monkeypatch.setattr(awards, "load_pdf_table_rows", lambda b: [make_row()])

    out = awards.find_awards("ZZ", "Example HFA", search_fn, fetch_bytes_fn, today=TODAY, recipes_dir=tmp_path)
    assert len(out) == 1
    assert out[0].units == 60


def test_find_awards_no_recipe_returns_empty(tmp_path):
    def search_fn(query):
        return []

    def fetch_bytes_fn(url):
        raise AssertionError("should not fetch when no recipe found")

    assert awards.find_awards("ZZ", "Example HFA", search_fn, fetch_bytes_fn, recipes_dir=tmp_path) == []


def test_slugify():
    assert awards.slugify("Rivertown State") == "rivertown-state"


def test_saved_multiline_workbook_keeps_only_recent_new_construction():
    from io import BytesIO

    workbook = openpyxl.Workbook()
    old = workbook.active
    old.title = "2023"
    current = workbook.create_sheet("2026")
    current.append(("title",))
    current.append(("New Homes", "Builder LLC", "Partner", 1000000, 40, 48, "New"))
    current.append(("100 Main Street", "Contact", None, None, None, None, "Construction"))
    current.append(("Rivertown, ZZ 00000",))
    current.append(("Old Homes", "Other LLC", "Partner", 500000, 30, 30, "Acquisition/"))
    current.append(("200 Main Street", None, None, None, None, None, "Rehabilitation"))
    current.append(("Rivertown, ZZ 00000",))
    payload = BytesIO()
    workbook.save(payload)
    recipe = {
        "state": "ZZ",
        "list_url": "https://example.test/awards.xlsx",
        "since_year": 2024,
        "min_units": 20,
        "columns": {"project": 0, "developer": 1, "units": 5, "type": 6},
    }

    records = awards.find_saved_multiline_awards(
        "zz", recipe, lambda _url: payload.getvalue(), today=TODAY
    )

    assert len(records) == 1
    assert records[0].name == "New Homes"
    assert records[0].address == "100 Main Street"
    assert records[0].city == "Rivertown"
    assert records[0].units == 48
    assert records[0].developer == "Builder LLC"
    assert records[0].permit_date == ""
    assert "2026" in records[0].why
