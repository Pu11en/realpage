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


def test_content_id_is_stable_when_address_format_or_order_changes():
    first = build_data.content_id("TX", "15910 Woodland Hills Drive", "Groves Apartments")
    second = build_data.content_id("tx", "15910 Woodland Hills Dr.", "GROVES APARTMENTS")

    assert first == second
    assert first == "tx-15910-woodland-hills-dr-groves-apartments"


def test_first_seen_migrates_old_positional_ids_by_content(tmp_path):
    previous_path = tmp_path / "tx.json"
    previous_path.write_text(json.dumps({"leads": [
        {"id": "tx-1", "property": "Old Apartments", "address": "12 Main Street", "firstSeen": "2026-08-01"},
        {"id": "tx-2", "property": "New Apartments", "address": "14 Main Street", "firstSeen": "2026-09-10"},
    ]}))
    leads = [
        {"id": build_data.content_id("tx", "14 Main St", "New Apartments"), "property": "New Apartments", "address": "14 Main St"},
        {"id": build_data.content_id("tx", "12 Main St", "Old Apartments"), "property": "Old Apartments", "address": "12 Main St"},
    ]

    build_data.add_first_seen(leads, previous_path, new_date="2026-09-19", state="tx")

    assert [lead["firstSeen"] for lead in leads] == ["2026-09-10", "2026-08-01"]


def test_all_built_area_leads_have_the_current_data_date():
    paths = [ROOT / "site/data/leads.json", *sorted((ROOT / "site/data/areas").glob("[a-z][a-z].json"))]
    assert paths
    for path in paths:
        leads = json.loads(path.read_text())["leads"]
        assert leads, path
        assert all(lead.get("firstSeen") == "2026-09-15" for lead in leads), path
