"""lead-finder 3.6: turn agenda hits into planned-project LeadRecords.

3.4 (Legistar) and 3.5 (CivicPlus/Granicus/PrimeGov/CivicClerk) each surface raw text
near a multifamily/rezoning keyword hit in a planning agenda. This module is the one
place that turns that raw text into a "planned" LeadRecord: an item is kept only if it
has an address or a case number (a bare keyword mention with neither is too weak to be a
real project), name/developer/units/case number are pulled out of the text, and multiple
hits for the same case (Planning & Zoning plus Council, or several packets mentioning the
same case) are merged into one project.

No place names anywhere in this file -- city/state/area are always caller-supplied.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Iterable, Protocol

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lead-finder"))
from record import LeadRecord  # noqa: E402

CASE_RE = re.compile(r"\b[A-Z]{1,4}-?\d{2,4}-\d{2,5}\b")
ADDRESS_RE = re.compile(
    r"\b\d{2,6}\s+[A-Za-z0-9.'\- ]+\b(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Dr|Drive|Ln|Lane|Way|Pkwy|Parkway|Ct|Court)\b",
    re.I,
)
UNITS_RE = re.compile(r"(\d{2,4})\s*units?\b", re.I)
DEVELOPER_RE = re.compile(
    r"(?:developer|applicant|owner)s?[:\s]+(?:is\s+|by\s+)?([A-Z][A-Za-z0-9&.,'\- ]{2,60}?)(?=[.,;\n]|$)",
    re.I,
)
NAME_RE = re.compile(
    r"(?:^|[.;:]\s*|--\s*)([A-Z][A-Za-z0-9'&\- ]{2,40}?\s+(?:Apartments|Residences|Flats|Villas|Commons|Place|Station|Lofts))\b"
)


class AgendaHitLike(Protocol):
    url: str
    text: str


def _first_match(pattern: re.Pattern, text: str) -> str:
    m = pattern.search(text)
    return m.group(1).strip() if m and m.groups() else (m.group(0) if m else "")


def hit_to_project(hit: AgendaHitLike, area: str, city: str) -> LeadRecord | None:
    """Turn one agenda hit into a planned LeadRecord, or None if it's too weak to keep."""
    text = hit.text
    case_match = CASE_RE.search(text)
    address_match = ADDRESS_RE.search(text)
    if not case_match and not address_match:
        return None

    units_match = UNITS_RE.search(text)
    developer = _first_match(DEVELOPER_RE, text)
    name = _first_match(NAME_RE, text)
    case_number = case_match.group(0) if case_match else ""

    why = f"planning agenda item{f' (case {case_number})' if case_number else ''}"

    return LeadRecord(
        area=area,
        city=city,
        name=name,
        address=address_match.group(0) if address_match else "",
        units=int(units_match.group(1)) if units_match else None,
        developer=developer,
        stage="planned",
        links={"agenda": hit.url},
        sources=[{"fact": "why", "url": hit.url}],
        why=why[:200],
    )


def _merge_key(record: LeadRecord, case_number: str) -> str:
    if case_number:
        return f"case:{case_number}"
    if record.address:
        return f"addr:{record.address.lower()}"
    return f"name:{record.name.lower()}"


def _merge_project(existing: LeadRecord, new: LeadRecord) -> LeadRecord:
    existing.name = existing.name or new.name
    existing.address = existing.address or new.address
    existing.units = existing.units or new.units
    existing.developer = existing.developer or new.developer
    if "agenda" not in existing.links and "agenda" in new.links:
        existing.links["agenda"] = new.links["agenda"]
    existing.sources.extend(s for s in new.sources if s not in existing.sources)
    return existing


def agenda_hits_to_projects(
    hits: Iterable[AgendaHitLike], area: str, city: str
) -> list[LeadRecord]:
    """Filter, extract, and merge (by case number, else address) into planned projects.

    Only P&Z + council hits about the same case (or same address, when no case number
    is present) become one project. Items with neither an address nor a case number are
    dropped -- never guessed at.
    """
    merged: dict[str, LeadRecord] = {}
    for hit in hits:
        case_match = CASE_RE.search(hit.text)
        record = hit_to_project(hit, area, city)
        if record is None:
            continue
        key = _merge_key(record, case_match.group(0) if case_match else "")
        if key in merged:
            merged[key] = _merge_project(merged[key], record)
        else:
            merged[key] = record
    return list(merged.values())
