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

import phonenumbers

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lead-finder"))
from merge import merge_records  # noqa: E402
from record import LeadRecord  # noqa: E402
from junk_permits import is_junk_permit  # noqa: E402

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

# Some permit feeds fill the address columns with a stand-in instead of
# leaving them empty when a permit has no sited address yet (one real TX city
# files plan-review submittals at "<submittal no> FOR REVIEW ONLY WAY"). A stand-in
# is worse than a blank: it looks like a real street to a seller, and every row
# sharing it merges into one bogus building.
# Some permit systems prefix the project name with the routing tag of the
# third-party plan reviewer handling it, separated by a triple slash
# ("X TEAM /// Spring Hill East"). The tag is who reviewed the drawings, not
# the building a seller is calling, so it is stripped off the front.
REVIEW_TAG_SEPARATOR = "///"

PLACEHOLDER_ADDRESS_RE = re.compile(
    r"\bfor review only\b|\bno address\b|\baddress (unknown|pending|tbd)\b"
    r"|\b(un|not )assigned\b|^\s*(none|null|n/?a|tbd|unknown)\s*$",
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
    stats: dict | None = None,
) -> list[LeadRecord]:
    """Fetch permit rows for `city` using `recipe` (from lead-finder-sources)
    and return one merged LeadRecord per apartment project.

    When `stats` is given it is filled with why rows were dropped, so a caller
    can tell an empty result caused by a stale feed (the city stopped
    publishing) apart from one caused by a broken fetch.  Without it, a source
    whose newest apartment permit has simply aged out of the freshness window
    looks identical to a source that failed.
    """
    today = today or datetime.date.today()
    endpoint = recipe.get("endpoint", "")
    fields = recipe.get("fields", {})
    units_pattern = recipe.get("units_text_pattern")
    rows = _fetch_rows(endpoint, http_get)

    apartment_rows = 0
    aged_out = 0
    no_date = 0
    placeholder_address = 0
    junk_dropped = 0
    newest: datetime.date | None = None
    records = []
    for row in rows:
        if not _is_apartment(row, fields, units_pattern):
            continue
        apartment_rows += 1
        issue_date = _parse_date(row.get(fields.get("issue_date", "")))
        co_date = _parse_date(_find_co_value(row, fields))
        for candidate in (issue_date, co_date):
            if candidate is not None and (newest is None or candidate > newest):
                newest = candidate
        stage = _infer_stage(issue_date, co_date, today)
        if stage is None:
            if issue_date is not None or co_date is not None:
                aged_out += 1
            else:
                no_date += 1
            continue
        if _has_placeholder_address(row, fields):
            # the feed itself says this permit has no sited address yet
            placeholder_address += 1
            continue
        record = _build_record(row, fields, city, area, endpoint, stage, issue_date, units_pattern, recipe)
        # a pool, carport, stair remodel, repair, roof or garage apartment is
        # work on an existing place, not a new apartment building
        if is_junk_permit(record.name):
            junk_dropped += 1
            continue
        records.append(record)

    merged = merge_records(records)
    if stats is not None:
        stats.update(
            {
                "rows": len(rows),
                "apartmentRows": apartment_rows,
                "agedOut": aged_out,
                "newestDate": newest.isoformat() if newest else "",
                "newestAgeDays": (today - newest).days if newest else None,
                "noDate": no_date,
                "placeholderAddress": placeholder_address,
                "junkDropped": junk_dropped,
                "built": len(records),
                "mergedAway": len(records) - len(merged),
                "kept": len(merged),
            }
        )
    return merged


def _is_apartment(row: dict, fields: dict, units_pattern: str | None) -> bool:
    # A known unit count is authoritative: a record that reports fewer than
    # 20 units is never a qualifying apartment project, even when the permit
    # type text matches (a duplex permitted as "MULTI-FAMILY DWELLING" is a
    # real example that slipped through when type matching won regardless of
    # the row's own unit count).
    units = _parse_units(row, fields, units_pattern)
    if units is not None:
        return units >= 20
    type_key = fields.get("permit_type")
    type_value = str(row.get(type_key, "")) if type_key else ""
    if APARTMENT_RE.search(type_value):
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


def _row_address(row: dict, fields: dict) -> str:
    """The row's street address, as a seller would dial it.

    Three things go wrong on real feeds and all three are handled here:
    a mapped address column that exists but holds null (``row.get(key, "")``
    returns None, and ``str(None)`` is the literal text "None" -- which then
    normalizes to "none" and merges every row in the feed into a single
    building); a layer that has no single address column at all and keeps the
    parts in separate columns (``fields.address_parts``); and a layer that
    writes a stand-in address rather than leaving it blank.
    """
    address = _joined_address(row, fields)
    if PLACEHOLDER_ADDRESS_RE.search(address):
        return ""
    return address


def _joined_address(row: dict, fields: dict) -> str:
    """The row's address text exactly as the feed wrote it, stand-in and all."""
    address_key = fields.get("address")
    address = str(row.get(address_key) or "").strip() if address_key else ""
    if not address:
        parts = fields.get("address_parts") or []
        pieces = [str(row.get(part) or "").strip() for part in parts]
        address = " ".join(piece for piece in pieces if piece)
    return re.sub(r"\s+", " ", address).strip()


def _has_placeholder_address(row: dict, fields: dict) -> bool:
    """True only when the feed wrote a stand-in address. A genuinely empty
    address is not a placeholder -- some sources legitimately have leads with
    no street address yet, and those are kept."""
    address = _joined_address(row, fields)
    return bool(address) and bool(PLACEHOLDER_ADDRESS_RE.search(address))


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
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
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
    recipe: dict | None = None,
) -> LeadRecord:
    address = _row_address(row, fields)
    name_key = fields.get("name")
    name = _clean_name(str(row.get(name_key) or "")) if name_key else ""
    if not name:
        # No mapped name field (or it was blank on this row): a city's
        # permit-type field often doubles as the real project name (e.g. a
        # "PERMIT_NAME" column holding "MADISON AT LOUISE APTS." with no
        # separate `fields.name` mapped); fall back to it, then to the
        # street address, rather than leaving the lead nameless.
        type_key = fields.get("permit_type")
        type_value = str(row.get(type_key) or "").strip() if type_key else ""
        name = type_value or address
    units = _parse_units(row, fields, units_pattern)
    permit_link = str(row.get("link") or row.get("url") or endpoint)
    developer, developer_source = _find_owner(row, recipe or {}, permit_link)
    office_phone, phone_source = _find_builder_phone(row, recipe or {}, permit_link)
    sources = [{"fact": "permit_date", "url": permit_link}]
    if developer_source:
        sources.append(developer_source)
    if phone_source:
        sources.append(phone_source)
    return LeadRecord(
        name=name,
        office_phone=office_phone,
        area=area,
        city=city,
        address=address,
        units=units,
        stage=stage,
        permit_date=issue_date.isoformat() if issue_date else "",
        developer=developer,
        links={"permit": permit_link},
        sources=sources,
        why="new multifamily permit" if stage != "leasing" else "certificate of occupancy issued recently",
    )


def _clean_name(name: str) -> str:
    """The project name as a seller would recognise it, with any plan-review
    routing tag stripped off the front."""
    if REVIEW_TAG_SEPARATOR in name:
        name = name.rsplit(REVIEW_TAG_SEPARATOR, 1)[-1]
    return re.sub(r"\s+", " ", name).strip()


def _find_owner(row: dict, recipe: dict, permit_link: str) -> tuple[str, dict | None]:
    """The permit row's real owner/builder field (Scottsdale/Tempe-style
    recipes), never guessed. Owner is preferred over builder (the property's
    owner, not its contractor, is who to call about software)."""
    for key in ("owner_field", "builder_field"):
        field_name = recipe.get(key)
        if not field_name:
            continue
        value = str(row.get(field_name) or "").strip()
        if value:
            return value, {"fact": "developer", "url": permit_link}
    return "", None


def _find_builder_phone(row: dict, recipe: dict, permit_link: str) -> tuple[str, dict | None]:
    """A phone number given directly on the permit row (e.g. the contractor's
    office line) -- real, never guessed, and a fallback for not-yet-built
    projects that have no website yet to crawl for a phone."""
    field_name = recipe.get("builder_phone_field")
    if not field_name:
        return "", None
    value = str(row.get(field_name) or "").strip()
    if not value:
        return "", None
    try:
        parsed = phonenumbers.parse(value, "US")
        if phonenumbers.is_valid_number(parsed):
            formatted = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL)
            return formatted, {"fact": "office_phone", "url": permit_link}
    except phonenumbers.NumberParseException:
        pass
    return "", None


# ArcGIS FeatureServer caps a single query response at 1,000 rows regardless
# of resultRecordCount, and signals it with exceededTransferLimit=true rather
# than erroring -- a source with 2,000+ matching permits silently loses
# everything past row 1,000 unless the caller pages with resultOffset.
# Capped at this many extra pages so a runaway feed can't loop forever;
# large enough for every real permit layer seen so far (one real source
# needed 3 pages for ~2,200 rows).
MAX_ARCGIS_PAGES = 20


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
        rows = [f.get("attributes", {}) for f in data.get("features", [])]
        page = 1
        offset = len(rows)
        while data.get("exceededTransferLimit") and page < MAX_ARCGIS_PAGES:
            page_url = _with_result_offset(endpoint, offset)
            try:
                data = http_get(page_url)
            except Exception:
                break
            if not isinstance(data, dict):
                break
            page_rows = [f.get("attributes", {}) for f in data.get("features", [])]
            if not page_rows:
                break
            rows.extend(page_rows)
            offset += len(page_rows)
            page += 1
        return rows
    return []


def _with_result_offset(endpoint: str, offset: int) -> str:
    separator = "&" if "?" in endpoint else "?"
    return f"{endpoint}{separator}resultOffset={offset}"
