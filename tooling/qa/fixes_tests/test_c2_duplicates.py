"""C2: one row per building. Westdale Hills (an old complex) is gone; same-name
duplicates are merged; real phases are labeled "Phase 1 / Phase 2"."""
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "propertystack/skills/lead-finder"))
from dedupe_leads import GENERIC_NAMES, dedupe_leads  # noqa: E402
from record import LeadRecord  # noqa: E402

PHASE_RE = re.compile(r"\bphase\s+(\d+|i+)\b", re.I)



def published_slugs() -> list[str]:
    """The states the site actually publishes, from the area index rather than a hard-coded
    tuple. Every one of these tests named ("tx", "az", "ny") and broke on 2026-09-26 when
    CraneSignal became Texas only; read from the index they survive the next change too.
    """
    import json as _json
    index = _json.loads(
        (ROOT / "site" / "data" / "areas" / "index.json").read_text(encoding="utf-8")
    )
    return [a["slug"] for a in index["areas"] if not a.get("hidden")]

def _rows(slug):
    return json.loads((ROOT / f"site/data/areas/{slug}.json").read_text())["leads"]


def test_no_same_name_same_city_unless_phases():
    for slug in published_slugs():
        counts = Counter(
            (l["property"].lower(), (l["city"] or "").lower()) for l in _rows(slug)
            if (l.get("property") or "").strip().lower() not in GENERIC_NAMES  # renamed by address in C3
            and not PHASE_RE.search(l["property"])
        )
        assert not [k for k, n in counts.items() if n > 1], slug


def test_westdale_hills_dropped():
    assert not [l for l in _rows("tx") if "westdale hills" in l["property"].lower()]
    with open(ROOT / "propertystack/data/tx/chat-leads.csv") as f:
        assert not [r for r in csv.DictReader(f) if "westdale hills" in r["name"].lower()]


def test_audit_pairs():
    tx = _rows("tx")
    by_name = Counter(l["property"] for l in tx)
    for name in ("Belmont Apartments", "Lakeside Lofts", "Emberstone Apartments", "6802 Marbach Lofts",
                 "Tezel Road Apartments", "Oak Park", "The Reid"):
        assert by_name[name] == 1, name
    assert by_name["Lofts at Birdwell Phase 1"] == 1
    assert by_name["Lofts at Birdwell Phase 2"] == 1
    belmont = next(l for l in tx if l["property"] == "Belmont Apartments")
    assert belmont["stage"] == "under construction" and belmont["units"] == 348  # both sources kept
    assert by_name["Buena Vida Multifamily Phase 1"] == by_name["Buena Vida Multifamily Phase 2"] == 1
    assert sum("7900 easthaven" in (l.get("address") or "").lower() for l in tx) == 1


def test_rules_offline():
    r = lambda **kw: LeadRecord(area="tx", city="X", name="Same", **kw)  # noqa: E731
    merged = dedupe_leads([r(address="1 A St", stage="permitted", units=10), r(address="9 A St", units=10)])
    assert len(merged) == 1
    phases = dedupe_leads([r(address="1 A St", stage="under construction", permit_date="2025-01-01"),
                           r(address="5 B Ave", stage="under construction", permit_date="2025-02-01")])
    assert [p.name for p in phases] == ["Same Phase 1", "Same Phase 2"]
