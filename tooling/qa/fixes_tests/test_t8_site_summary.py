"""T8: one state-agnostic summary drives the Leads page hero."""
import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location("build_data_t8", ROOT / "site/data/build_data.py")
build_data = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_data)


def _write_area(path, updated, leads):
    path.write_text(json.dumps({"updated": updated, "leads": leads}))


def test_small_areas_hide_then_reappear_automatically(tmp_path, monkeypatch):
    monkeypatch.setattr(build_data, "AREAS_OUT_DIR", tmp_path)
    monkeypatch.setattr(build_data, "_included_slugs", lambda _slugs: set())
    _write_area(tmp_path / "nm.json", "2026-09-19", [{}] * 24)

    first = build_data.build_areas_manifest(["nm"])
    assert first["areas"][0]["hidden"] is True
    assert first["areas"][0]["hiddenReason"] == "under-25-leads"

    _write_area(tmp_path / "nm.json", "2026-09-20", [{}] * 25)
    second = build_data.build_areas_manifest(["nm"])
    assert "hidden" not in second["areas"][0]


def test_small_manually_hidden_area_stays_manual(tmp_path, monkeypatch):
    monkeypatch.setattr(build_data, "AREAS_OUT_DIR", tmp_path)
    monkeypatch.setattr(build_data, "_included_slugs", lambda _slugs: set())
    (tmp_path / "index.json").write_text(json.dumps({
        "areas": [{"slug": "ny", "hidden": True}],
    }))
    _write_area(tmp_path / "ny.json", "2026-09-15", [{}] * 2)

    manifest = build_data.build_areas_manifest(["ny"])

    assert manifest["areas"][0]["hidden"] is True
    assert "hiddenReason" not in manifest["areas"][0]


def test_summary_counts_current_runs_and_excludes_manually_hidden_area(tmp_path, monkeypatch):
    monkeypatch.setattr(build_data, "AREAS_OUT_DIR", tmp_path)
    _write_area(tmp_path / "tx.json", "2026-09-19", [
        {"signalType": "Upcoming", "firstSeen": "2026-09-13"},
        {"signalType": "Sold", "firstSeen": "2026-09-12"},
    ])
    _write_area(tmp_path / "nm.json", "2026-09-18", [
        {"signalType": "Planned", "firstSeen": "2026-09-18"},
    ])
    _write_area(tmp_path / "ny.json", "2026-09-15", [
        {"signalType": "Sold", "firstSeen": "2026-09-15"},
    ])
    manifest = {"areas": [
        {"slug": "tx"},
        {"slug": "nm", "hidden": True, "hiddenReason": "under-25-leads"},
        {"slug": "ny", "hidden": True},
    ], "updated": "2026-09-19"}

    assert build_data.build_summary(["tx", "nm", "ny"], manifest) == {
        "lastCheck": "2026-09-19",
        "totalTracked": 3,
        "newLast7Days": 2,
        "permitsFiled": 2,
        "sold": 1,
        "recentLast180Days": 0,
    }


def test_summary_counts_only_buildings_that_actually_moved_lately(tmp_path, monkeypatch):
    """The hero used to call every tracked building one that "just" filed or
    sold. Most last moved over a year ago, so the recent count is measured from
    each lead's own newest date rather than assumed over the whole list."""
    monkeypatch.setattr(build_data, "AREAS_OUT_DIR", tmp_path)
    _write_area(tmp_path / "tx.json", "2026-09-19", [
        {"signalType": "Sold", "saleDate": "2026-08-01"},        # 49 days -- recent
        {"signalType": "Upcoming", "permitDate": "2026-06-30"},  # 81 days -- recent
        {"signalType": "Sold", "saleDate": "2024-12-30"},        # 20 months -- not
        {"signalType": "Upcoming", "permitDate": "2025-01-05"},  # 20 months -- not
        {"signalType": "Upcoming"},                              # no date at all
        {"signalType": "Leasing", "openingDate": "2027-03-01"},  # opens next year
    ])
    manifest = {"areas": [{"slug": "tx"}], "updated": "2026-09-19"}

    summary = build_data.build_summary(["tx"], manifest)

    assert summary["totalTracked"] == 6
    assert summary["recentLast180Days"] == 2  # the 2027 opening has not happened yet


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_leads_hero_uses_summary_and_coverage_names_are_removed():
    app = (ROOT / "site/js/app.js").read_text(encoding="utf-8")
    page = (ROOT / "site/index.html").read_text(encoding="utf-8")
    functions = (
        "function formatDataDate" + app.split("function formatDataDate", 1)[1].split("function formatUpdated", 1)[0]
        + "function summaryHero" + app.split("function summaryHero", 1)[1].split("function setLastUpdated", 1)[0]
    )
    summary = {
        "lastCheck": "2026-09-19",
        "permitsFiled": 972,
        "sold": 498,
        "totalTracked": 1470,
        "recentLast180Days": 177,
    }
    out = subprocess.run(
        ["node", "-e", functions + f"console.log(summaryHero({json.dumps(summary)}));"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()

    assert out == (
        "Last check Sep 19, 2026: 1,470 buildings tracked \u2014 972 being built or planned, "
        "498 sold to a new owner. 177 with a permit or sale in the last 6 months."
    )
    # the old hero called the whole list recent; nothing may imply that again
    assert "just filed permits" not in out and "just sold" not in out
    assert '${summaryHero(siteSummary)}' in page
    assert "Texas &amp; Arizona" not in page
    assert "Covered: Texas, Arizona" not in app


def test_a_month_only_sale_never_shows_a_day_the_county_did_not_record():
    """Maricopa publishes SALEDATE_MMYYYY, so its dates are stored on the 1st.
    Cove on 44th is stored as 2026-08-01 and really sold on the 14th -- the day
    is ours, not the county's, and must not be shown."""
    import sys

    sys.path.insert(0, str(ROOT / "propertystack/skills/lead-finder"))
    sys.path.insert(0, str(ROOT / "propertystack/skills/score-leads"))
    from record import LeadRecord
    from score_leads import sale_date_label

    month_only = LeadRecord(
        area="az", city="PHOENIX", address="4030 N 44TH AVE",
        stage="sold", sale_date="2026-08-01", sale_date_precision="month",
    )
    exact = LeadRecord(
        area="tx", city="HOUSTON", address="803 DUNSON GLEN DR",
        stage="sold", sale_date="2025-12-30",
    )

    assert sale_date_label(month_only) == "Aug 2026"
    assert sale_date_label(exact) == "2025-12-30"
    assert build_data._area_signal_text(month_only) == "Sold Aug 2026"
    assert build_data._area_signal_text(exact) == "Sold 2025-12-30"


def test_sale_date_precision_survives_a_merge():
    import sys

    sys.path.insert(0, str(ROOT / "propertystack/skills/lead-finder"))
    from merge import merge_records
    from record import LeadRecord

    from_county = LeadRecord(
        area="az", city="PHOENIX", name="Cove On 44Th", address="4030 N 44TH AVE",
        stage="sold", sale_date="2026-08-01", sale_date_precision="month", units=256,
    )
    from_permits = LeadRecord(
        area="az", city="PHOENIX", name="Cove On 44Th", address="4030 N 44TH AVE",
        stage="permitted", units=256,
    )

    merged = merge_records([from_permits, from_county])

    assert len(merged) == 1
    assert merged[0].sale_date_precision == "month"
