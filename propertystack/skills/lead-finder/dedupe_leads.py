"""Second duplicate pass over a state's saved leads, by name.

merge.py joins records by address or geocode while a lead-finder run collects
them. Some duplicates still slip through because two sources spell the same
place differently: a tax-credit list says "6832 Marbach Rd" and the permit says
"1611 Pinn Road"; a county permit feed lists one complex once per building
permit, each at another street number. Used by site/data/build_data.py on
every rebuild.

Two records with the same name in the same city are one building when any of:
  - their base addresses match ("7900 Easthaven Blvd Bld B" / "... Bld D"),
  - they are on the same street,
  - they list the same number of units (a county feed repeats the complex total),
  - one is only planned (a funding list) and the other is further along.
Otherwise they are separate buildings of one project (different streets,
separate permits) and are labeled "Phase 1", "Phase 2" in permit order.

Existing complexes that show up only because of permit work on them are not
leads at all (EXISTING_COMPLEXES).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from merge import _merge_pair  # noqa: E402
from record import LeadRecord, normalize_address  # noqa: E402

# (name, city) of old complexes listed in permit feeds, lowercase
EXISTING_COMPLEXES = {
    ("westdale hills apts", "hurst"),
    ("westdale hills apts", "euless"),
}

# labels that are not a building name: rows with these are told apart by address
GENERIC_NAMES = {
    "building permit", "apartments (3+ dwelling units)", "new construction", "apartments",
    "multi-family dwelling", "commercial multi-family", "multifamily", "unnamed project",
}


def _base(address: str) -> str:
    # "BLD B" is a building qualifier too (merge.normalize_address knows "bldg")
    text = re.sub(r"\bbld\b.*$", "", (address or "").lower().replace("\xa0", " "))
    return normalize_address(text.split(",")[0])


def _street(address: str) -> str:
    """Base address without its house number: "5726 us hwy 87 e" -> "us hwy 87 e"."""
    return re.sub(r"^\d+\s+", "", _base(address)) if re.match(r"^\d", _base(address)) else ""


def _street_key(address: str) -> str:
    # "us highway 87 e" and "us hwy 87 e" normalize alike already; drop direction words
    return " ".join(w for w in _street(address).split() if w not in {"n", "s", "e", "w"})


def same_project(a: LeadRecord, b: LeadRecord) -> bool:
    if _base(a.address) and _base(a.address) == _base(b.address):
        return True
    if _street_key(a.address) and _street_key(a.address) == _street_key(b.address):
        return True
    if a.units and a.units == b.units:
        return True
    same_city = (a.city or "").strip().lower() == (b.city or "").strip().lower()
    # Two records with different city labels need real address/unit evidence
    # above (e.g. one source says "Dallas", another says the annexed suburb
    # "Wilmer", for the same address): the stage-only heuristic below is only
    # safe once we already know they're in the same city.
    return same_city and (a.stage == "planned") != (b.stage == "planned")


def _key(r: LeadRecord) -> tuple[str, str]:
    return ((r.name or "").strip().lower(), (r.city or "").strip().lower())


def _name_key(r: LeadRecord) -> str:
    # Group by name alone: a permit feed and a funding list sometimes label the
    # same project's city differently (e.g. Dallas vs. the annexed suburb
    # Wilmer). same_project() still requires matching address/units/stage
    # before two same-named records actually merge, so unrelated projects that
    # happen to share a name in different cities are still told apart.
    return (r.name or "").strip().lower()


_PERMIT_TEXT_RE = re.compile(r"^[\d,]+\s+(?:sf\s+)?new\b|\bibc\b", re.I)  # "20,376 NEW APARTMENT BLDG ... '21 IBC"


def _merge_same_address(records: list[LeadRecord]) -> list[LeadRecord]:
    """Buildings of one complex filed as separate permits at one street address."""
    out: list[LeadRecord] = []
    by_addr: dict[tuple[str, str], LeadRecord] = {}
    for r in records:
        base = _base(r.address)
        key = ((r.city or "").lower(), base)
        if not re.match(r"^\d", base) or key not in by_addr:
            by_addr.setdefault(key, r)
            out.append(r)
            continue
        keep = by_addr[key]
        _merge_pair(keep, r)
        if _PERMIT_TEXT_RE.search(keep.name or ""):
            keep.name = f"Apartments at {keep.address.split(' BLD')[0].split(' Bld')[0].title()}"
    return out


def dedupe_leads(records: list[LeadRecord]) -> list[LeadRecord]:
    records = [r for r in records if _key(r) not in EXISTING_COMPLEXES]
    records = _merge_same_address(records)
    out: list[LeadRecord] = []
    groups: dict[str, list[LeadRecord]] = {}
    for r in records:
        name = _name_key(r)
        if not name:
            out.append(r)
            continue
        group = groups.setdefault(name, [])
        generic = name in GENERIC_NAMES
        match = next(
            (g for g in group if (_base(g.address) == _base(r.address) and _base(r.address))
             or (not generic and same_project(g, r))),
            None,
        )
        if match is None:
            group.append(r)
            out.append(r)
        else:
            _merge_pair(match, r)
            if match.units and r.units and r.units > match.units:
                match.units = r.units  # a planned total beats a blank/partial count
    # what's left with the same real name are phases of one project
    for name, group in groups.items():
        if len(group) > 1 and name not in GENERIC_NAMES:
            ordered = sorted(group, key=lambda g: (g.permit_date or "9999", str(g.links.get("permit", "")), g.address))
            for i, g in enumerate(ordered, start=1):
                name = g.name.title() if g.name.isupper() else g.name
                g.name = f"{name} Phase {i}"
    return out
