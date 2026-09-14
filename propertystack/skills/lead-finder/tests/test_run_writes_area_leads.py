"""6.8: run.py's main() must persist a finished run's scored records to
propertystack/data/<slug>/leads.json (part-1 format, 1.2) so
site/data/build_data.py (5.1) can discover the area -- before this, run_chain
scored records in memory but nothing ever wrote them to disk, so a finished
run never showed up on the site.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import run as chain  # noqa: E402
from record import LeadRecord  # noqa: E402


def _sample_record() -> LeadRecord:
    return LeadRecord(
        area="zz",
        city="Sampleton",
        name="Sample Commons",
        stage="permitted",
        units=40,
    )


def test_write_area_leads_creates_data_dir_leads_json(tmp_path):
    records = [_sample_record()]
    out = chain.write_area_leads("ZZ", records, data_dir=tmp_path)

    assert out == tmp_path / "zz" / "leads.json"
    saved = json.loads(out.read_text())
    assert len(saved) == 1
    assert saved[0]["city"] == "Sampleton"
    assert saved[0]["units"] == 40

    # Round-trips through the same LeadRecord format build_data.py reads.
    reloaded = [LeadRecord.from_dict(d) for d in saved]
    assert reloaded[0].name == "Sample Commons"


def test_write_area_leads_lowercases_the_state_for_the_slug(tmp_path):
    out = chain.write_area_leads("AZ", [_sample_record()], data_dir=tmp_path)
    assert out.parent.name == "az"
