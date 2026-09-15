"""T8: the same project filed under two different city labels (e.g. "Torrington
Wilmer" appearing once as Dallas and once as Wilmer) becomes one row."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "propertystack" / "skills" / "lead-finder"))

from dedupe_leads import dedupe_leads  # noqa: E402
from record import LeadRecord  # noqa: E402


def test_same_name_different_city_label_merges():
    a = LeadRecord(
        area="tx", city="Dallas", name="Torrington Wilmer",
        address="1501 E. Beltline", units=300, stage="planned",
    )
    b = LeadRecord(
        area="tx", city="Wilmer", name="Torrington Wilmer",
        address="1501 East Beltline Road", units=300, stage="planned",
    )
    out = dedupe_leads([a, b])
    assert len(out) == 1
    assert out[0].name == "Torrington Wilmer"


def test_same_name_different_city_different_project_stays_separate():
    # Same name, different city, but nothing else in common -- still two leads.
    a = LeadRecord(
        area="tx", city="Dallas", name="Meridian Place",
        address="100 Oak St", units=180, stage="planned",
    )
    b = LeadRecord(
        area="tx", city="Austin", name="Meridian Place",
        address="900 Congress Ave", units=240, stage="leasing",
    )
    out = dedupe_leads([a, b])
    assert len(out) == 2
