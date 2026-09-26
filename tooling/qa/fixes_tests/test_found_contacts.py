"""The researched contacts, and the rules about what they may overwrite.

Phase 4 of docs/plans/PLAN-texas-only-6h.md. A county sale record names the buying LLC and
nothing else, so 93% of rows arrived with no way to reach anyone -- 24 of 1,861 buildings were
actionable. These contacts are found one web search at a time and merged by
build_data.apply_found_contacts().

That merge is the riskiest code in the pipeline, because it is the only place where something
read off a web page touches rows that otherwise come entirely from public records. The rules
below are what keep those two apart.
"""
import csv
import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
FOUND = ROOT / "propertystack" / "data" / "tx" / "contacts-found.csv"
AREA = ROOT / "site" / "data" / "areas" / "tx.json"

PHONE = re.compile(r"^\(?\d{3}\)?[- ]?\d{3}-\d{4}$")


def build_data():
    spec = importlib.util.spec_from_file_location(
        "build_data_mod", ROOT / "site" / "data" / "build_data.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["build_data_mod"] = module
    spec.loader.exec_module(module)
    return module


def found_rows() -> list[dict]:
    if not FOUND.exists():
        return []
    with FOUND.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def leads() -> list[dict]:
    return json.loads(AREA.read_text(encoding="utf-8"))["leads"]


def test_the_contacts_file_exists_and_has_the_columns_the_merge_expects():
    rows = found_rows()
    assert rows, "no researched contacts yet"
    for row in rows:
        assert set(row) == {"id", "found_name", "phone", "management_company", "email",
                            "source_url", "found_on", "notes"}, sorted(row)


def test_every_contact_carries_where_it_came_from():
    """The one rule that does not bend. Every other field on this site links the public record
    behind it; a phone number read off a web page owes a reader the same."""
    for row in found_rows():
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", row["found_on"]), row
        if row["phone"] or row["management_company"]:
            assert row["source_url"].startswith("http"), row
        else:
            # A search that found nothing is recorded rather than left to be repeated, and it
            # has to say so -- an empty row with no explanation looks like a mistake.
            assert row["notes"].strip(), (
                f"{row['id']}: no phone, no management company and no note saying why"
            )


def test_no_phone_is_a_guess():
    for row in found_rows():
        if row["phone"]:
            assert PHONE.match(row["phone"].strip()), f"{row['id']}: {row['phone']!r}"


def test_every_contact_matches_a_real_building():
    """A row keyed to an id that no longer exists is a contact nobody will ever see, and
    usually means the target list was regenerated without rechecking this file."""
    ids = {lead["id"] for lead in leads()}
    orphans = [row["id"] for row in found_rows() if row["id"] not in ids]
    assert not orphans, f"{len(orphans)} contacts point at rows that are gone: {orphans[:3]}"


def test_the_contacts_reached_the_published_data():
    """Counted against the rows that actually have something to merge. A recorded miss --
    searched, nothing found, note explaining why -- fills no field and so reaches no row,
    which is correct: it exists to stop the search being repeated, not to publish a blank."""
    have_something = [r for r in found_rows() if r["phone"] or r["management_company"]]
    merged = [l for l in leads() if l.get("contactSource")]
    assert len(merged) == len(have_something), (
        f"{len(have_something)} researched contacts, {len(merged)} in the published data"
    )
    for lead in merged:
        assert lead["contactSource"].startswith("http")
        assert lead.get("contactFoundOn")


def test_a_researched_contact_never_overwrites_a_public_record():
    """The merge may only fill a blank. Apartments.com says Murdeaux Villas has 240 units
    where the county says 301 -- an aggregator disagreeing with the appraisal district is not
    a reason to believe the aggregator, so units, dates and stage are never touched."""
    module = build_data()
    row = {"id": "x", "found_name": "Real Name", "phone": "(555) 555-5555",
           "management_company": "Some Co", "email": "a@b.com",
           "source_url": "https://example.org/x", "found_on": "2026-09-26"}
    lead = {"id": "x", "property": "Already Named", "address": "1 MAIN ST",
            "officePhone": "(111) 111-1111", "units": 301, "saleDate": "2026-01-01",
            "stage": "sold", "contact": {"email": "already@there.com"}}
    # Exercised through a temporary file so the real merge code runs, not a copy of it.
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        slug_dir = Path(tmp) / "tx"
        slug_dir.mkdir()
        with (slug_dir / "contacts-found.csv").open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(row), lineterminator="\n")
            writer.writeheader(); writer.writerow(row)
        module.STATE_DATA_DIR = Path(tmp)
        module.apply_found_contacts("tx", [lead])

    assert lead["units"] == 301, "the unit count was overwritten"
    assert lead["saleDate"] == "2026-01-01"
    assert lead["stage"] == "sold"
    assert lead["officePhone"] == "(111) 111-1111", "an existing phone was overwritten"
    assert lead["contact"]["email"] == "already@there.com", "an existing email was overwritten"
    assert lead["property"] == "Already Named", "a real building name was overwritten"
    # The one thing it did fill: the field that was genuinely empty.
    assert lead["managementCompany"] == "Some Co"


@pytest.mark.parametrize("placeholder", [
    "",                       # no name at all
    "Apartments at 1 Main St",  # the generated stand-in
    "1 MAIN ST",              # the address doing duty as a name
    "9999 Kempwood Dr",       # same, title-cased
])
def test_a_placeholder_name_is_replaced_by_the_real_one(placeholder):
    """A page that prints the address in the name column and again in the address column
    looks broken. "9999 Kempwood Dr" is called "3 Corners East" by everyone who lives there."""
    module = build_data()
    import tempfile
    row = {"id": "x", "found_name": "3 Corners East", "phone": "(555) 555-5555",
           "management_company": "", "email": "",
           "source_url": "https://example.org/x", "found_on": "2026-09-26"}
    lead = {"id": "x", "property": placeholder, "address": "1 MAIN ST"}
    with tempfile.TemporaryDirectory() as tmp:
        slug_dir = Path(tmp) / "tx"
        slug_dir.mkdir()
        with (slug_dir / "contacts-found.csv").open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(row), lineterminator="\n")
            writer.writeheader(); writer.writerow(row)
        module.STATE_DATA_DIR = Path(tmp)
        module.apply_found_contacts("tx", [lead])
    assert lead["property"] == "3 Corners East", placeholder


def test_who_to_call_reaches_the_pages_and_the_spreadsheets():
    dallas = (ROOT / "site" / "leads" / "tx" / "dallas.html").read_text(encoding="utf-8")
    assert "<th>Who to call</th>" in dallas
    header = (ROOT / "site" / "leads" / "tx.csv").read_text(encoding="utf-8").splitlines()[0]
    for column in ("Office phone", "Management company", "Contact source"):
        assert column in header, header


def test_the_merge_runs_after_the_ids_are_final():
    """apply_found_contacts matches on `id`, and two earlier steps rewrite `id`.

    Found 2026-09-26 by the count above coming out one short. The merge ran first, so it
    matched ids that were about to change, and a contact keyed to the *final* id missed its
    row without any error -- it hit the second "Northwood Heights", which
    disambiguate_duplicate_display_names renames to "Northwood Heights - 15702 El Estado Dr"
    and re-keys. One row in 178, silently.

    Asserted on the order of the calls rather than on the symptom, because the symptom only
    appears when two rows happen to share a name.
    """
    source = (ROOT / "site" / "data" / "build_data.py").read_text(encoding="utf-8")
    body = source.split("def build_state_areas", 1)[1].split("\ndef ", 1)[0]
    positions = {
        name: body.find(name)
        for name in ("disambiguate_duplicate_display_names(",
                     "ensure_unique_content_ids(",
                     "apply_found_contacts(")
    }
    for name, at in positions.items():
        assert at != -1, f"{name} is no longer called in build_state_areas"
    assert positions["apply_found_contacts("] > positions["disambiguate_duplicate_display_names("], \
        "contacts are merged before the display names are disambiguated, which rewrites ids"
    assert positions["apply_found_contacts("] > positions["ensure_unique_content_ids("], \
        "contacts are merged before the ids are made unique, which rewrites ids"
