"""C1: pool, carport, stair/remodel, repair, roof and garage-apartment permits are not leads."""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "propertystack/skills/lead-finder"))
from junk_permits import is_junk_permit  # noqa: E402

# the audit's junk rows (names as saved in propertystack/data/tx/leads.json)
JUNK = [
    "Riverview Apartments Carport",                                        # tx-301
    "APARTMENT AMENITY NEW IN-GROUND UNHEATED SWIMMG POOL 2021 IBC",       # tx-305
    "APARTMENT NEW OUTDOOR INGROUND UNHEATED SWIMMG POOL 2021 IBC",        # tx-325
    "The 1856 Apartments Stair Remodel",                                   # tx-327
    "APARTMENT NEW OUTDOOR IN-GROUND UNHEATED SWIMMG POOL 2021 IBC.",      # tx-328
    "NEW, UNIDENTIFIED-GARAGE APARTMENT ADDITION",                         # tx-335
    "APARTMENT NEW EXTERIOR IN-GROUND UNHEATED SWIMMING POOL 2021 IBC",    # tx-343
    "Oak Creek Apartments Roof Repair",
]
# real apartment buildings that mention a garage (audit's tx-7 and tx-365): keep
REAL = [
    "New mixed-use project, includes structured parking garage, multi-family, and retail",
    "1401 South Lamar Multifamily and Garage",
    "Enclave on Louetta",
    "Apartments at 4500 Brentwood Stair Rd",  # a street name, not stair work
]


def test_filter_words():
    assert all(is_junk_permit(n) for n in JUNK)
    assert not any(is_junk_permit(n) for n in REAL)


def test_built_site_and_chat_have_no_junk():
    leads = json.loads((ROOT / "site/data/areas/tx.json").read_text())["leads"]
    names = {l.get("community") or l["property"] for l in leads}
    assert not names & set(JUNK)
    assert set(REAL[:2]) <= names, "tx-7 / tx-365 are real apartment buildings, keep them"
    with open(ROOT / "propertystack/data/tx/chat-leads.csv") as f:
        assert not [r for r in csv.DictReader(f) if is_junk_permit(r["name"])]
