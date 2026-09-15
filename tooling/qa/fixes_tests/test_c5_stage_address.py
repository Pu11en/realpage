"""C5: a leasing row never reads "Upcoming / opens not public yet", and the
Plano-Richardson rows carry the street address already saved with them."""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "site/data"))
sys.path.insert(0, str(ROOT / "propertystack/skills/lead-finder"))
import build_data  # noqa: E402
from record import LeadRecord  # noqa: E402


def _rows(slug):
    return json.loads((ROOT / f"site/data/areas/{slug}.json").read_text())["leads"]


def test_leasing_rows_read_as_leasing():
    for slug in ("tx", "az", "ny"):
        for l in _rows(slug):
            if (l.get("stage") or "").lower() == "leasing":
                assert l["signalType"] == "Leasing", (slug, l["id"], l["signalType"])
                assert "not public yet" not in (l.get("signal") or "").lower(), (slug, l["id"])
                assert "not public yet" not in (l.get("why") or "").lower(), (slug, l["id"])


def test_no_row_contradicts_a_leasing_stage():
    for slug in ("tx", "az", "ny"):
        for l in _rows(slug):
            if "opens: not public yet" in (l.get("signal") or "").lower():
                assert (l.get("stage") or "").lower() != "leasing", (slug, l["id"])


def test_leasing_with_no_opening_date_says_leasing_now():
    rec = LeadRecord(area="az", city="Tempe", name="X", stage="leasing", opening_date="",
                     why="Leasing · opens: not public yet · 104 units")
    d = build_data._area_lead_dict(rec, 1)
    assert d["signalType"] == "Leasing" and d["signal"] == "Leasing now"
    assert "not public yet" not in d["why"].lower(), d["why"]


def test_plano_rows_carry_their_saved_address():
    props = json.loads((ROOT / "site/data/properties.json").read_text())
    saved = {p["id"]: p["address"] for p in (props["properties"] + props["upcoming"]) if p.get("address")}
    rows = [l for l in _rows("tx") if l.get("subArea")]
    assert len(rows) == 42, len(rows)
    assert sum(1 for l in rows if l.get("address")) >= 40
    for l in rows:
        want = saved.get(l.get("propertyId"))
        if want:
            assert l.get("address") == want, (l["id"], l.get("address"), want)
    # The chat's Texas table carries them too (that is what the assistant reads).
    with open(ROOT / "propertystack/data/tx/chat-leads.csv") as f:
        chat = list(csv.DictReader(f))
    assert sum(1 for r in chat if r["city"] in ("Plano", "Richardson") and r["address"]) >= 40
