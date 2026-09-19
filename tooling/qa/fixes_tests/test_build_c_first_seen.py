"""Build C T1: every lead keeps a stable first-seen date across data builds."""
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location("build_data", ROOT / "site/data/build_data.py")
build_data = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_data)


def test_first_seen_preserves_history_and_dates_only_new_ids_today(tmp_path):
    previous_path = tmp_path / "area.json"
    previous_path.write_text(json.dumps({"leads": [
        {"id": "kept", "firstSeen": "2026-08-01"},
        {"id": "pre-field"},
    ]}))
    leads = [{"id": "kept"}, {"id": "pre-field"}, {"id": "new"}]

    build_data.add_first_seen(leads, previous_path, new_date="2026-09-19")

    assert [lead["firstSeen"] for lead in leads] == [
        "2026-08-01",
        "2026-09-15",
        "2026-09-19",
    ]


def test_all_built_area_leads_have_the_current_data_date():
    paths = [ROOT / "site/data/leads.json", *sorted((ROOT / "site/data/areas").glob("[a-z][a-z].json"))]
    assert paths
    for path in paths:
        leads = json.loads(path.read_text())["leads"]
        assert leads, path
        assert all(lead.get("firstSeen") == "2026-09-15" for lead in leads), path
