"""One lead record format shared by every lead-finder part.

See docs/LEAD-FORMAT.md for the field-by-field description. This module has no
place names in it -- areas/cities are always data, never literals here.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

# Stages in "how advanced" order -- used by merge.py to pick the most advanced
# stage when two sources describe the same building.
STAGE_ORDER = ["planned", "permitted", "under construction", "leasing", "sold"]


def stage_rank(stage: str) -> int:
    try:
        return STAGE_ORDER.index(stage)
    except ValueError:
        return -1


@dataclass
class Source:
    fact: str  # which field this source backs, e.g. "units", "opening_date"
    url: str


@dataclass
class LeadRecord:
    area: str  # state slug, e.g. "az"
    city: str
    name: str = ""
    address: str = ""
    lat: float | None = None
    lon: float | None = None
    units: int | None = None
    stage: str = "planned"  # planned / permitted / under construction / leasing / sold
    permit_date: str = ""  # ISO date, blank if unknown
    opening_date: str = ""  # ISO date, blank if unknown
    sale_date: str = ""
    # "month" when the county only publishes month and year, so nothing shows a
    # day the source never recorded; "" means the date is exact.
    sale_date_precision: str = ""
    buyer: str = ""
    developer: str = ""
    office_phone: str = ""
    website: str = ""
    software: str = "unknown"  # "RealPage" / competitor name / "not picked" / "unknown"
    links: dict = field(default_factory=dict)  # e.g. {"map": ..., "permit": ..., "agenda": ..., "news": ..., "website": ...}
    sources: list = field(default_factory=list)  # list of {"fact": ..., "url": ...}
    why: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "LeadRecord":
        known = {f: data.get(f) for f in cls.__dataclass_fields__ if f in data}
        return cls(**known)


def save_records(records: list[LeadRecord], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump([r.to_dict() for r in records], f, indent=2)


def load_records(path: Path) -> list[LeadRecord]:
    with path.open() as f:
        data = json.load(f)
    return [LeadRecord.from_dict(d) for d in data]


# --- address normalization (self-contained, no third-party address parser) ---

_STREET_SUFFIXES = {
    "street": "st", "st": "st",
    "avenue": "ave", "ave": "ave",
    "boulevard": "blvd", "blvd": "blvd",
    "drive": "dr", "dr": "dr",
    "lane": "ln", "ln": "ln",
    "road": "rd", "rd": "rd",
    "court": "ct", "ct": "ct",
    "place": "pl", "pl": "pl",
    "circle": "cir", "cir": "cir",
    "way": "way",
    "parkway": "pkwy", "pkwy": "pkwy",
    "trail": "trl", "trl": "trl",
    "terrace": "ter", "ter": "ter",
    "highway": "hwy", "hwy": "hwy",
}

_UNIT_WORDS = {"building", "bldg", "unit", "suite", "ste", "apt", "apartment", "#"}


def normalize_address(address: str) -> str:
    """Lowercase, expand/collapse whitespace, normalize street suffixes, drop
    building/unit/suite qualifiers -- so "123 Main St" and "123 Main Street
    Bldg B" normalize to the same base string for merge matching."""
    if not address:
        return ""
    text = address.lower().strip()
    text = re.sub(r"[.,]", "", text)
    text = re.sub(r"\s+", " ", text)
    tokens = text.split(" ")

    out = []
    for tok in tokens:
        if tok in _UNIT_WORDS:
            break  # stop at the first unit/building qualifier
        out.append(_STREET_SUFFIXES.get(tok, tok))
    return " ".join(out).strip()


def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    from math import asin, cos, radians, sin, sqrt

    r = 6371000.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * r * asin(sqrt(a))
