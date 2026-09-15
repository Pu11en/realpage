"""T9: raw plat/lot labels like "South Pier Lot 6" become "Apartments at <address>"."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "site" / "data"))

from build_data import _nice_name  # noqa: E402


def test_lot_label_becomes_apartments_at_address():
    name = _nice_name("South Pier Lot 6", "1314 E Vista Del Lago Dr")
    assert name == "Apartments at 1314 E Vista Del Lago Dr"


def test_parcel_and_tract_labels_also_cleaned():
    assert _nice_name("Rio Salado Parcel 12", "500 W Rio Salado Pkwy").startswith("Apartments at")
    assert _nice_name("Hayden Tract 3B", "600 S Hayden Rd").startswith("Apartments at")


def test_real_project_name_untouched():
    assert _nice_name("Riverwalk Commons", "100 Main St") == "Riverwalk Commons"


def test_lot_label_without_address_falls_back():
    assert _nice_name("South Pier Lot 6", "") == "Unnamed project"
