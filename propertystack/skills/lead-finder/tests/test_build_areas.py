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


def test_build_state_areas_writes_json_only_when_asked(tmp_path, monkeypatch):
    monkeypatch.setattr(build_data, "AREAS_OUT_DIR", tmp_path)
    slugs = build_data.build_state_areas(include_sample=True)
    assert "_sample" in slugs
    written = json.loads((tmp_path / "_sample.json").read_text())
    assert written["area"] == "_sample"

    slugs_default = build_data.build_state_areas(include_sample=False)
    assert "_sample" not in slugs_default
