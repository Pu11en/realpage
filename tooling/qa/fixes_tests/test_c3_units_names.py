"""C3: unknown units show "?" (never 0), and a generic permit label becomes
"Apartments at <address>" instead of "Multi-Family Dwelling".

Was written against Arizona. Retargeted 2026-09-26 when CraneSignal became Texas only --
retargeted rather than deleted, because both rules turned out to be as live in Texas as they
were in Arizona: 209 Texas rows carry the rename and 16 carry a unit count inside the name.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

# Generic permit labels the audit named: these must become "Apartments at <address>".
GENERIC = {"Multi-Family Dwelling", "Commercial Multi-Family", "Multifamily"}

# A unit count stated inside a building name, in any form.
COUNT_IN_NAME = re.compile(r"\b(\d{1,4})\s*Units?\b", re.I)
# The parenthesised form specifically: the county writes it into its own property-name field.
PARENTHESISED_COUNT = re.compile(r"\(\s*\d{1,4}\s*units?\s*\)", re.I)
# A trailing "BLD B" / "BLDG 3" on an address.
BUILDING_SUFFIX = re.compile(r"\s+Bldg?\s+\S+$", re.I)


def published_slugs() -> list[str]:
    """The states the site actually publishes, read from the area index.

    Every test in this file named ("tx", "az", "ny") and broke when the other states were
    deleted. Read from the index, they survive the next change to coverage too.
    """
    index = json.loads(
        (ROOT / "site" / "data" / "areas" / "index.json").read_text(encoding="utf-8")
    )
    return [area["slug"] for area in index["areas"] if not area.get("hidden")]


def _rows(slug):
    return json.loads((ROOT / f"site/data/areas/{slug}.json").read_text(encoding="utf-8"))["leads"]


def all_rows():
    return [lead for slug in published_slugs() for lead in _rows(slug)]


def test_units_are_never_zero():
    """A permit feed's 0 means "not recorded", never an empty building."""
    for slug in published_slugs():
        zero = [l["id"] for l in _rows(slug) if l.get("units") == 0]
        assert not zero, f"{slug}: units=0 should be unknown '?' -- {zero}"


def test_generic_labels_are_renamed_from_the_address():
    """A permit feed that gives "Multi-Family Dwelling" as the name is giving no name at all."""
    rows = all_rows()
    names = {l["property"] for l in rows}
    assert not names & GENERIC, f"still generic: {names & GENERIC}"

    renamed = [l for l in rows if l["property"].startswith("Apartments at ")]
    assert len(renamed) >= 40, f"only {len(renamed)} renamed rows"
    for lead in renamed:
        # The name is the address, title-cased -- allowing a trailing building-unit suffix to
        # be absent. 207 of 209 match exactly. Two do not, and the reason is in their own ids:
        # tx-7900-easthaven-blvd-bld-b-apartments-at-7900-easthaven-blvd was named from the
        # address before "BLD B" was appended to it, so both halves are faithful to what they
        # saw. Left alone rather than chased: it is cosmetic, and the phase-4 contact searches
        # replace these placeholder names with the real community name anyway.
        want = (lead["address"] or "").title()
        allowed = {f"Apartments at {want}", f"Apartments at {BUILDING_SUFFIX.sub('', want)}"}
        assert lead["property"] in allowed, (lead["property"], lead["address"])


def test_no_name_contradicts_the_units_column():
    """A row that says two different unit counts is a row a reader cannot trust either half of.

    Replaces a test that pinned one Arizona row. Found on 2026-09-26: Dallas County writes the
    count into its own property-name field, so "THE NATIONAL (324 UNITS)" was on the live
    Dallas page beside a Units column reading 543, both sourced, contradicting each other.
    build_data.NAME_UNIT_COUNT now takes the parenthesised count out of the name -- it is not
    a name, and the Units column already carries a number with a record behind it.

    Six rows still state a count in the name as a phase label ("Landmark At Lake Village East
    - 57 Units"). Those are kept because they agree with the column; this test is about
    disagreement, not about the count appearing.
    """
    for lead in all_rows():
        name = lead.get("property") or ""
        assert not PARENTHESISED_COUNT.search(name), (
            f"{lead['id']}: county unit count left in the name -- {name!r}"
        )
        match = COUNT_IN_NAME.search(name)
        if match:
            assert lead.get("units") == int(match.group(1)), (
                f"{lead['id']}: name says {match.group(1)} units, column says {lead.get('units')}"
            )
