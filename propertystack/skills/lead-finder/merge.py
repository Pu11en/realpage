"""Merge lead records from every source into one record per building.

Two records are the same building if either:
  - their normalized addresses match (see record.normalize_address), or
  - their geocodes are within 75 meters of each other AND they share a
    developer/name word.

The merged record keeps the most advanced stage (see record.STAGE_ORDER),
keeps every source and link from both records, and a planned project that
later gets a permit is upgraded in place rather than duplicated.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from record import LeadRecord, haversine_meters, normalize_address, stage_rank  # noqa: E402

_MERGE_RADIUS_M = 75.0


def _name_words(record: LeadRecord) -> set[str]:
    words = set()
    for text in (record.developer, record.name):
        if text:
            words |= {w for w in text.lower().split() if len(w) > 2}
    return words


def same_building(a: LeadRecord, b: LeadRecord) -> bool:
    addr_a = normalize_address(a.address)
    addr_b = normalize_address(b.address)
    if addr_a and addr_b and addr_a == addr_b:
        return True

    if a.lat is not None and a.lon is not None and b.lat is not None and b.lon is not None:
        distance = haversine_meters(a.lat, a.lon, b.lat, b.lon)
        if distance <= _MERGE_RADIUS_M and (_name_words(a) & _name_words(b)):
            return True

    return False


def _merge_pair(keep: LeadRecord, other: LeadRecord) -> LeadRecord:
    """Merge `other` into `keep`, keeping the more advanced stage and every
    source/link from both. `keep` is mutated and returned."""
    if stage_rank(other.stage) > stage_rank(keep.stage):
        # other is further along -- promote its stage/dates onto the kept record,
        # but don't throw away facts keep already has.
        keep.stage = other.stage
        for field_name in (
            "permit_date", "opening_date", "sale_date", "sale_date_precision", "buyer",
        ):
            other_value = getattr(other, field_name)
            if other_value and not getattr(keep, field_name):
                setattr(keep, field_name, other_value)

    for field_name in (
        "name", "address", "lat", "lon", "units", "developer",
        "office_phone", "website", "sale_date_precision",
    ):
        if not getattr(keep, field_name) and getattr(other, field_name):
            setattr(keep, field_name, getattr(other, field_name))

    keep.links = {**other.links, **keep.links}  # keep's links win on key clash
    keep.sources = keep.sources + [s for s in other.sources if s not in keep.sources]
    return keep


def merge_records(records: list[LeadRecord]) -> list[LeadRecord]:
    """Collapse a list of records (possibly from many sources) down to one
    record per building. First-seen record in each merge group is kept as
    the base and enriched from the rest."""
    merged: list[LeadRecord] = []
    for record in records:
        match = None
        for existing in merged:
            if same_building(existing, record):
                match = existing
                break
        if match is None:
            merged.append(record)
        else:
            _merge_pair(match, record)
    return merged
