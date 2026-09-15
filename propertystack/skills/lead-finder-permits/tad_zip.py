"""T3: a county appraisal-district "commercial permits" zip download,
generalized the same way the AZ Maricopa sales recipe treats a flat-file
county download (see recipes/az/maricopa-county-sales.json and
skills/lead-finder-sales/find_sold.py) -- county specifics live only in the
recipe JSON, this module just downloads+unzips+reads whatever xlsx/csv is
inside.

Unlike Maricopa's sales file, this county posts one apartment-relevant
permit sheet per year as a zip containing a single xlsx (not a delimited
text file), covering every city inside the county -- each row's own
"Issuing Agency" column names the real city, so one recipe covers every
city in the county at once (never hard-coded to a single city)."""
from __future__ import annotations

import datetime
import io
import re
import sys
import urllib.request
import zipfile
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lead-finder"))
from merge import merge_records  # noqa: E402
from record import LeadRecord  # noqa: E402

FetchBytes = Callable[[str], bytes]

PERMIT_WINDOW_DAYS = 24 * 30


def default_fetch_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "propertystack-live-self-test"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def fetch_rows(recipe: dict, fetch_bytes: FetchBytes = default_fetch_bytes) -> list[dict]:
    """Download every zip URL in recipe["zip_urls"] (one per year), unzip
    the single xlsx inside each, and return every row as a plain dict keyed
    by the sheet's own header row -- filtered to rows whose
    "Intended Property Use" (or recipe-mapped equivalent) matches
    recipe["use_filter"]."""
    import openpyxl  # local import: only needed for this one source

    use_field = recipe.get("use_field", "Intended Property Use")
    use_filter = recipe.get("use_filter", "Apartments")
    rows: list[dict] = []
    for url in recipe.get("zip_urls", []):
        try:
            data = fetch_bytes(url)
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                xlsx_names = [n for n in zf.namelist() if n.lower().endswith((".xlsx", ".xlsm"))]
                if not xlsx_names:
                    continue
                xlsx_bytes = zf.read(xlsx_names[0])
        except Exception:
            continue
        try:
            wb = openpyxl.load_workbook(io.BytesIO(xlsx_bytes), data_only=True)
        except Exception:
            continue
        for ws in wb.worksheets:
            header = [str(c.value or "").strip() for c in next(ws.iter_rows(min_row=1, max_row=1))]
            if use_field not in header:
                continue
            for excel_row in ws.iter_rows(min_row=2, values_only=True):
                row = dict(zip(header, excel_row))
                value = str(row.get(use_field) or "").strip()
                if use_filter.lower() not in value.lower():
                    continue
                row["_source_url"] = url
                rows.append(row)
    return rows


def find_new_apartment_permits(
    area: str,
    recipe: dict,
    fetch_bytes: FetchBytes = default_fetch_bytes,
    today: datetime.date | None = None,
) -> list[LeadRecord]:
    """One LeadRecord per apartment permit row, tagged with the row's own
    city (recipe["city_field"], e.g. "Issuing Agency") rather than a single
    caller-supplied city -- this source covers every city in the county at
    once, unlike find_upcoming's one-city-per-call signature."""
    today = today or datetime.date.today()
    city_field = recipe.get("city_field", "Issuing Agency")
    address_field = recipe.get("address_field", "Situs Address")
    name_field = recipe.get("name_field", "Site Name")
    units_field = recipe.get("units_field", "Total Units")
    date_field = recipe.get("date_field", "Issue Date")
    min_units = recipe.get("min_units", 20)

    records = []
    for row in fetch_rows(recipe, fetch_bytes):
        units = _to_int(row.get(units_field))
        if units is not None and units < min_units:
            continue
        issue_date = _to_date(row.get(date_field))
        if issue_date is None or (today - issue_date).days > PERMIT_WINDOW_DAYS:
            continue
        city = str(row.get(city_field) or "").strip()
        if not city:
            continue
        name = str(row.get(name_field) or "").strip() or str(row.get(address_field) or "").strip()
        source_url = row.get("_source_url", "")
        records.append(
            LeadRecord(
                name=name,
                area=area,
                city=city,
                address=str(row.get(address_field) or "").strip(),
                units=units,
                stage="permitted",
                permit_date=issue_date.isoformat(),
                links={"permit": source_url},
                sources=[{"fact": "permit_date", "url": source_url}],
                why="new apartment permit (county appraisal-district commercial permits file)",
            )
        )
    return merge_records(records)


def _to_int(value) -> int | None:
    try:
        result = int(str(value).strip())
    except (TypeError, ValueError):
        return None
    return result if result > 0 else None


def _to_date(value) -> datetime.date | None:
    if value is None:
        return None
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.datetime.strptime(str(value), fmt).date()
        except ValueError:
            continue
    return None
