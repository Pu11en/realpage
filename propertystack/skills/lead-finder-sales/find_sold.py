"""lead-finder F5: "recently sold, from the county's sales file".

area + a sales recipe (see propertystack/recipes/az/maricopa-county-sales.json)
-> LeadRecords for apartment properties (20+ units) sold in the last N months,
joining a county's sale-affidavits file to its parcel file to get unit counts.
No place names in this file -- county/state/field names/use codes are always
caller-supplied via the recipe.

Two files are involved because most county assessors record a "last recorded
sale" per parcel in one file (grantor/grantee/date/price/property-type-code,
but no unit count) and the building's unit count in a separate parcel/master
file, joined by parcel number. `fetch_rows` is injected so this module never
touches the network directly -- the real zip-download-and-join lives in
`default_fetch_rows` below, used only by `live_self_test.py`, so the pytest
suite here stays offline like every other lead-finder* skill.
"""
from __future__ import annotations

import csv
import datetime
import io
import re
import sys
import urllib.request
import zipfile
from fnmatch import fnmatch
from pathlib import Path
from typing import Callable, Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lead-finder"))
from record import LeadRecord  # noqa: E402

FetchRows = Callable[[dict], Iterable[dict]]


def find_sold(
    area: str,
    recipe: dict,
    fetch_rows: FetchRows,
    today: datetime.date | None = None,
) -> list[LeadRecord]:
    """Fetch `recipe`'s sales + parcel sources (via `fetch_rows`) and return one
    LeadRecord per apartment-type sale with a known unit count >= min_units,
    sold within `recent_months` of `today`."""
    today = today or datetime.date.today()
    sales_fields = recipe.get("sales_fields", {})
    parcel_fields = recipe.get("parcel_fields", {})
    apartment_codes = {str(c) for c in recipe.get("apartment_type_codes", [])}
    min_units = recipe.get("min_units", 20)
    recent_months = recipe.get("recent_months", 24)
    date_format = sales_fields.get("date_format", "MMYYYY")

    if not apartment_codes or not recipe.get("sales_source") or not recipe.get("parcel_source"):
        return []

    units_by_parcel = _load_units(recipe["parcel_source"], parcel_fields, fetch_rows)

    records = []
    for row in _safe_fetch(recipe["sales_source"], fetch_rows):
        type_code = str(row.get(sales_fields.get("type_code", ""), "")).strip()
        if type_code not in apartment_codes:
            continue
        sale_date = _parse_sale_date(row.get(sales_fields.get("sale_date", "")), date_format)
        if sale_date is None or not _within_months(sale_date, today, recent_months):
            continue
        parcel_id = str(row.get(sales_fields.get("parcel", ""), "")).strip()
        units = units_by_parcel.get(parcel_id)
        if units is None or units < min_units:
            continue
        records.append(
            _build_record(row, sales_fields, area, recipe, units, sale_date, date_format)
        )
    return records


def _load_units(parcel_source: dict, parcel_fields: dict, fetch_rows: FetchRows) -> dict[str, int]:
    parcel_key = parcel_fields.get("parcel", "")
    units_key = parcel_fields.get("units", "")
    units_by_parcel: dict[str, int] = {}
    if not parcel_key or not units_key:
        return units_by_parcel
    for row in _safe_fetch(parcel_source, fetch_rows):
        parcel_id = str(row.get(parcel_key, "")).strip()
        raw_units = str(row.get(units_key, "")).strip()
        if not parcel_id or not raw_units.isdigit():
            continue
        units_by_parcel[parcel_id] = int(raw_units)
    return units_by_parcel


def _safe_fetch(source: dict, fetch_rows: FetchRows) -> list[dict]:
    try:
        rows = fetch_rows(source)
    except Exception:
        return []
    return list(rows) if rows else []


def _parse_sale_date(value, date_format: str) -> datetime.date | None:
    if not value:
        return None
    text = str(value).strip()
    if date_format == "MMYYYY" and len(text) == 6 and text.isdigit():
        mm, yyyy = int(text[:2]), int(text[2:])
        if 1 <= mm <= 12:
            return datetime.date(yyyy, mm, 1)
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m%d%Y"):
        try:
            return datetime.datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _within_months(sale_date: datetime.date, today: datetime.date, months: int) -> bool:
    cutoff_days = months * 31  # generous month length -- never rejects a truly-recent sale
    return 0 <= (today - sale_date).days <= cutoff_days


def _build_record(
    row: dict,
    sales_fields: dict,
    area: str,
    recipe: dict,
    units: int,
    sale_date: datetime.date,
    date_format: str = "",
) -> LeadRecord:
    address = str(row.get(sales_fields.get("address", ""), "")).strip()
    city = str(row.get(sales_fields.get("city", ""), "")).strip()
    grantor = str(row.get(sales_fields.get("grantor", ""), "")).strip()
    grantee = str(row.get(sales_fields.get("grantee", ""), "")).strip()
    price = str(row.get(sales_fields.get("price", ""), "")).strip()
    source_url = recipe.get("sales_source", {}).get("item_page") or recipe.get("sales_source", {}).get("url", "")
    return LeadRecord(
        area=area,
        city=city or recipe.get("county", ""),
        address=address,
        units=units,
        stage="sold",
        sale_date=sale_date.isoformat(),
        # This county's column is SALEDATE_MMYYYY -- it has no day in it, so the
        # first of the month is a placeholder and must never be shown as one.
        sale_date_precision="month" if date_format == "MMYYYY" else "",
        buyer=grantee,
        developer=grantor,
        links={"sales_file": source_url},
        sources=[
            {"fact": "sale_date", "url": source_url},
            {"fact": "units", "url": recipe.get("parcel_source", {}).get("item_page", source_url)},
        ],
        why=f"recently sold apartment property ({units} units, ${price or 'price unknown'})" if price else f"recently sold apartment property ({units} units)",
    )


# --- real network fetch, used only by live_self_test.py; injected as
# `fetch_rows` above so the pytest suite never calls this. ---


def default_fetch_rows(source: dict) -> list[dict]:
    """Download a county's zip'd pipe-delimited file(s) from `source["url"]`
    and return every row (across every file matching `source["file_glob"]`
    inside the zip) as a dict keyed by its header row."""
    req = urllib.request.Request(source["url"], headers={"User-Agent": "propertystack-live-self-test"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        blob = resp.read()
    file_glob = source.get("file_glob", "*.txt")
    rows: list[dict] = []
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        for name in zf.namelist():
            if not fnmatch(name, file_glob):
                continue
            with zf.open(name) as fh:
                text = io.TextIOWrapper(fh, encoding="latin-1", newline="")
                reader = csv.DictReader(text, delimiter="|")
                rows.extend(reader)
    return rows
