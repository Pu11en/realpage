"""lead-finder 2.4: find-upcoming rebuilt for any city.

city + a 2.2/2.3 recipe -> new apartment permit LeadRecords, staged from the
permit's issue date and certificate-of-occupancy date. Replaces the old
single-city find-upcoming skill (Legistar-only, hardcoded to one city). No
place names in this file -- city/state/recipe are always caller-supplied.
"""
from __future__ import annotations

import datetime
import re
import sys
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lead-finder"))
from merge import merge_records  # noqa: E402
from record import LeadRecord  # noqa: E402

HttpGet = Callable[[str], object]

APARTMENT_RE = re.compile(r"multi[- ]?family|apartment", re.I)
CO_KEY_RE = re.compile(r"cert.*occup|certificate_of_occupancy|\bco_date\b|final.*inspect", re.I)
# permit-type categories that mean work on an *existing* building (repairs, a
# trade permit, a fence) -- these show up constantly on real permit feeds with
# "apartment(s)" somewhere in the free-text description (e.g. "renovate 2
# apartments"), which is not a new apartment project and must not match.
RENOVATION_TYPE_RE = re.compile(
    r"^(repair|electrical|plumbing|mechanical|hvac|re?-?roof|sign|fence|demolition|alteration|garshed)\b",
    re.I,
)

# permits issued this long ago or more recently are still "in the pipeline"
PERMIT_WINDOW_DAYS = 24 * 30
# a CO issued within this window means the project is now leasing
CO_WINDOW_DAYS = 6 * 30


def find_upcoming(
    city: str,
    state: str,
    area: str,
    recipe: dict,
    http_get: HttpGet,
    today: datetime.date | None = None,
) -> list[LeadRecord]:
    """Fetch permit rows for `city` using `recipe` (from lead-finder-sources)
    and return one merged LeadRecord per apartment project."""
    today = today or datetime.date.today()
    endpoint = recipe.get("endpoint", "")
    fields = recipe.get("fields", {})
    units_pattern = recipe.get("units_text_pattern")
    rows = _fetch_rows(endpoint, http_get)

    records = []
    for row in rows:
        if not _is_apartment(row, fields, units_pattern):
            continue
        issue_date = _parse_date(row.get(fields.get("issue_date", "")))
        co_date = _parse_date(_find_co_value(row, fields))
        stage = _infer_stage(issue_date, co_date, today)
        if stage is None:
            continue
        records.append(_build_record(row, fields, city, area, endpoint, stage, issue_date, units_pattern))

    return merge_records(records)


def _is_apartment(row: dict, fields: dict, units_pattern: str | None) -> bool:
    type_key = fields.get("permit_type")
    type_value = str(row.get(type_key, "")) if type_key else ""
    if APARTMENT_RE.search(type_value):
        return True
    units = _parse_units(row, fields, units_pattern)
    if units is not None and units >= 20:
        return True
    if RENOVATION_TYPE_RE.match(type_value.strip()):
        return False
    return APARTMENT_RE.search(" ".join(str(v) for v in row.values())) is not None


def _parse_units(row: dict, fields: dict, units_pattern: str | None) -> int | None:
    units_key = fields.get("units")
    if units_key:
        raw = row.get(units_key)
        try:
            return int(str(raw).strip())
        except (TypeError, ValueError):
            pass
    text_key = fields.get("units_text_field")
    if text_key and units_pattern:
        text = str(row.get(text_key, ""))
        match = re.search(units_pattern, text, re.I)
        if match:
            try:
                return int(match.group(1))
            except (TypeError, ValueError, IndexError):
                return None
    return None


def _find_co_value(row: dict, fields: dict) -> str:
    co_key = fields.get("co_date")
    if co_key:
        return str(row.get(co_key) or "")
    for key, value in row.items():
        if CO_KEY_RE.search(key):
            return str(value)
    return ""


def _parse_date(value) -> datetime.date | None:
    if not value:
        return None
    if isinstance(value, (int, float)):
        # ArcGIS FeatureServer fields return dates as epoch milliseconds.
        return datetime.datetime.fromtimestamp(value / 1000, tz=datetime.timezone.utc).date()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
        try:
            return datetime.datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _infer_stage(issue_date: datetime.date | None, co_date: datetime.date | None, today: datetime.date) -> str | None:
    if co_date is not None:
        if (today - co_date).days <= CO_WINDOW_DAYS:
            return "leasing"
        return None  # CO older than 6 months -- past the "upcoming" window, drop
    if issue_date is not None:
        if (today - issue_date).days <= PERMIT_WINDOW_DAYS:
            return "permitted"
        return None  # permit too old with no CO on record -- drop
    return None  # no usable date -- drop


def _build_record(
    row: dict,
    fields: dict,
    city: str,
    area: str,
    endpoint: str,
    stage: str,
    issue_date: datetime.date | None,
    units_pattern: str | None = None,
) -> LeadRecord:
    address_key = fields.get("address")
    address = str(row.get(address_key, "")) if address_key else ""
    units = _parse_units(row, fields, units_pattern)
    permit_link = str(row.get("link") or row.get("url") or endpoint)
    return LeadRecord(
        area=area,
        city=city,
        address=address,
        units=units,
        stage=stage,
        permit_date=issue_date.isoformat() if issue_date else "",
        links={"permit": permit_link},
        sources=[{"fact": "permit_date", "url": permit_link}],
        why="new multifamily permit" if stage != "leasing" else "certificate of occupancy issued recently",
    )


def _fetch_rows(endpoint: str, http_get: HttpGet) -> list[dict]:
    if not endpoint:
        return []
    try:
        data = http_get(endpoint)
    except Exception:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "features" in data:
        return [f.get("attributes", {}) for f in data.get("features", [])]
    return []
