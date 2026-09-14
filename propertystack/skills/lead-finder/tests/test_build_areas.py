"""Task 5.1: site/data/build_data.py builds every state area from the part-1
lead format (record.py), leaving plano-richardson's CSV pipeline untouched and
never building the `_sample` fixture area unless explicitly asked."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "site" / "data"))

import build_data  # noqa: E402


def test_sample_area_excluded_by_default():
    slugs = build_data.discover_state_areas(include_sample=False)
    assert "_sample" not in slugs
    assert "plano-richardson" not in slugs


def test_sample_area_included_when_asked():
    slugs = build_data.discover_state_areas(include_sample=True)
    assert "_sample" in slugs


def test_build_area_shapes_lead_records():
    area = build_data.build_area("_sample")
    assert area["area"] == "_sample"
    assert area["stats"]["leads"] == 2
    assert area["cities"] == ["Sampleton"]
    # score-leads (4.5) ranks and fills `why` -- sold lead only after the
    # permitted/upcoming one, per the group order in score_leads.py.
    assert [lead["stage"] for lead in area["leads"]] == ["permitted", "sold"]
    assert all(lead["why"] for lead in area["leads"])
    # 5.3: city filter + labels -- exact plan wording per stage/date state.
    by_stage = {lead["stage"]: lead for lead in area["leads"]}
    assert by_stage["sold"]["signal"].startswith("Sold ")


def test_area_signal_labels_planned_and_unknown_opening():
    from record import LeadRecord

    planned = LeadRecord(area="_sample", city="Sampleton", stage="planned")
    permitted_no_date = LeadRecord(area="_sample", city="Sampleton", stage="permitted")
    permitted_with_date = LeadRecord(
        area="_sample", city="Sampleton", stage="leasing", opening_date="2026-03-01"
    )
    sold_no_date = LeadRecord(area="_sample", city="Sampleton", stage="sold")

    assert build_data._area_signal_text(planned) == "Planned (not permitted yet)"
    assert build_data._area_signal_text(permitted_no_date) == "Opens: not public yet"
    assert build_data._area_signal_text(permitted_with_date) == "Opens: 2026-03-01"
    assert build_data._area_signal_text(sold_no_date) == "Sold"


def test_build_state_areas_writes_json_only_when_asked(tmp_path, monkeypatch):
    monkeypatch.setattr(build_data, "AREAS_OUT_DIR", tmp_path)
    slugs = build_data.build_state_areas(include_sample=True)
    assert "_sample" in slugs
    written = json.loads((tmp_path / "_sample.json").read_text())
    assert written["area"] == "_sample"

    slugs_default = build_data.build_state_areas(include_sample=False)
    assert "_sample" not in slugs_default


def test_write_chat_leads_csv_flattens_for_the_chatbot(tmp_path):
    """5.4: the chatbot's `state_leads` table comes from every area's
    chat-leads.csv -- one flat row per lead, no master/contacts join needed."""
    import csv as csv_mod

    area_json = build_data.build_area("_sample")
    out_dir = tmp_path / "_sample"
    out_dir.mkdir()
    try:
        real_dir = build_data.STATE_DATA_DIR
        build_data.STATE_DATA_DIR = tmp_path
        build_data.write_chat_leads_csv("_sample", area_json)
    finally:
        build_data.STATE_DATA_DIR = real_dir

    with (out_dir / "chat-leads.csv").open(newline="") as f:
        rows = list(csv_mod.DictReader(f))
    assert len(rows) == area_json["stats"]["leads"]
    assert {r["area"] for r in rows} == {"_sample"}
    assert set(build_data.CHAT_LEADS_COLUMNS) == set(rows[0].keys())
    assert all(r["why"] for r in rows)
