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
    }


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_leads_hero_uses_summary_and_coverage_names_are_removed():
    app = (ROOT / "site/js/app.js").read_text(encoding="utf-8")
    page = (ROOT / "site/index.html").read_text(encoding="utf-8")
    functions = (
        "function formatDataDate" + app.split("function formatDataDate", 1)[1].split("function formatUpdated", 1)[0]
        + "function summaryHero" + app.split("function summaryHero", 1)[1].split("function setLastUpdated", 1)[0]
    )
    summary = {"lastCheck": "2026-09-19", "permitsFiled": 972, "sold": 498, "totalTracked": 1470}
    out = subprocess.run(
        ["node", "-e", functions + f"console.log(summaryHero({json.dumps(summary)}));"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()

    assert out == "Last check Sep 19, 2026: 972 buildings just filed permits, 498 just sold. 1,470 tracked."
    assert '${summaryHero(siteSummary)}' in page
    assert "Texas &amp; Arizona" not in page
    assert "Covered: Texas, Arizona" not in app
