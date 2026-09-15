"""C3: unknown units show "?" (never 0); AZ's generic permit labels become
"Apartments at <address>" instead of "Multi-Family Dwelling" etc."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

# Generic AZ permit labels the audit named: these must become "Apartments at <address>".
GENERIC = {"Multi-Family Dwelling", "Commercial Multi-Family", "Multifamily"}


def _rows(slug):
    return json.loads((ROOT / f"site/data/areas/{slug}.json").read_text())["leads"]


def test_units_are_never_zero():
    # A permit feed's 0 means "not recorded" (NY's units_added), never an empty building.
    for slug in ("tx", "az", "ny"):
        zero = [l["id"] for l in _rows(slug) if l.get("units") == 0]
        assert not zero, f"{slug}: units=0 should be unknown '?' — {zero}"


def test_ny_units_are_unknown_not_zero():
    ny = _rows("ny")
    assert ny, "New York should still have its leads"
    for l in ny:
        assert l.get("units") is None or l["units"] > 0, l


def test_az_generic_labels_renamed_from_address():
    az = _rows("az")
    names = {l["property"] for l in az}
    assert not names & GENERIC, f"still generic: {names & GENERIC}"
    renamed = [l for l in az if l["property"].startswith("Apartments at ")]
    assert len(renamed) >= 40  # 29 Scottsdale + 6 Gilbert + 1 Phoenix + 9 APARTMENTS
    for l in renamed:
        assert l["property"] == f"Apartments at {(l['address'] or '').title()}", l


def test_unit_count_recovered_from_saved_text():
    # "8 UNIT MULTI-FAMILY APT." carries its count in the name; the source has units=null.
    az = _rows("az")
    row = next(l for l in az if l.get("address") == "13400 N 22ND ST")
    assert row["units"] == 8
    with open(ROOT / "propertystack/data/az/chat-leads.csv") as f:
        chat = next(r for r in csv.DictReader(f) if r["address"] == "13400 N 22ND ST")
    assert chat["units"] == "8"
