"""T4: a county appraisal-district *bulk data* zip -- the same "county
specifics in the recipe, generic code" pattern as tad_zip.py's commercial-
permits zip, but for the much bigger yearly bulk-data download every state
appraisal district posts (parcel/building CSVs, deed-transfer dates, owner
mailing info), used here for new apartment construction and recent
apartment sales.

Unlike tad_zip's single small xlsx, these zips hold several large delimited
text files (tens to hundreds of MB each), so this module never loads a
member fully into memory as a list -- it streams each CSV/TSV row by row
via `csv.DictReader` over a `zipfile.ZipFile.open()` file handle.

Two real county shapes, both covered by one recipe format:
- County A: one file (COM_DETAIL.CSV) has building facts (class, unit
  count, a name, a completion fraction) with no owner or deed date; a
  second file (ACCOUNT_INFO.CSV) has one row per account with the owner
  and deed-transfer date, joined by account number (`sold.info_table`);
- County B: one file (real_acct.txt) has everything about the parcel
  (class, address, owner mailing, a new-construction dollar value,
  building area) already in one row, but deed dates live in a separate
  file (deeds.txt) with many rows per account -- only the latest matters
  (`sold.deed_table`).
"""
from __future__ import annotations

import csv
import datetime
import io
import sys
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lead-finder"))
from merge import merge_records  # noqa: E402
from record import LeadRecord  # noqa: E402

FetchBytes = Callable[[str], bytes]


def default_fetch_bytes(url: str) -> bytes:
    # Some county sites (County A's redirect link) hand back an unescaped
    # Windows file path as a query value (backslashes and spaces), which
    # `http.client` rejects outright as control characters -- percent-encode
    # the whole URL before opening it (`safe` keeps the URL's own real
    # delimiters untouched).
    safe_url = urllib.parse.quote(url, safe=":/?&=%")
    req = urllib.request.Request(safe_url, headers={"User-Agent": "propertystack-live-self-test"})
    with urllib.request.urlopen(req, timeout=280) as resp:
        return resp.read()


def _rows(zf: zipfile.ZipFile, member: str, encoding: str):
    delimiter = "," if member.lower().endswith(".csv") else "\t"
    with zf.open(member) as raw:
        text = io.TextIOWrapper(raw, encoding=encoding, newline="")
        yield from csv.DictReader(text, delimiter=delimiter)


def _to_int(value) -> int | None:
    try:
        result = int(float(str(value).strip()))
    except (TypeError, ValueError):
        return None
    return result if result > 0 else None


def _to_float(value) -> float | None:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _to_date(value: str, date_format: str) -> datetime.date | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return datetime.datetime.strptime(value, date_format).date()
    except ValueError:
        return None


def _address(row: dict, fields: dict) -> str:
    address_field = fields.get("address_field")
    if address_field:
        return str(row.get(address_field) or "").strip()
    num = str(row.get(fields.get("street_num_field", ""), "") or "").strip()
    street = str(row.get(fields.get("street_name_field", ""), "") or "").strip()
    return " ".join(part for part in (num, street) if part)


def _class_matches(row: dict, fields: dict) -> bool:
    class_field = fields.get("class_field")
    if not class_field:
        return True
    value = str(row.get(class_field) or "").upper()
    class_filter = (fields.get("class_filter") or "").upper()
    return value == class_filter if fields.get("class_exact") else class_filter in value


def _address_info(zf: zipfile.ZipFile, bldg: dict, encoding: str, keys: set[str]) -> dict[str, dict]:
    """When the building-facts file has no street address of its own
    (County A's building-facts file -- the street is only in the separate
    ACCOUNT_INFO.CSV), `bldg["address_info_table"]` names that second
    file so new-construction rows can still get a real address instead of
    being left blank or guessed. Only rows matching `keys` (the accounts
    already picked as qualifying apartment rows) are kept in memory --
    this file has one row per every account in the county, not just
    apartments, so keeping all of it would be wasteful."""
    info_table = bldg.get("address_info_table")
    if not info_table or not keys:
        return {}
    key_field = info_table["key_field"]
    result = {}
    for row in _rows(zf, info_table["file"], encoding):
        key = str(row.get(key_field) or "").strip()
        if key in keys:
            result[key] = row
    return result


def find_new_apartment_projects(
    area: str,
    recipe: dict,
    fetch_bytes: FetchBytes = default_fetch_bytes,
) -> list[LeadRecord]:
    """One LeadRecord per building row that is an apartment (recipe's
    class match), has a known unit count >= min_units, a real name or
    address, and is not yet complete -- either a completion fraction below
    1.0 (County A: a building's own PCT_COMPLETE column, where 1.0 means
    fully built) or a positive new-construction dollar value on a large
    enough building (County B: no completion column at all, so a nonzero
    `new_construction_val` on a big-enough `bld_ar` is the only
    "still under construction" signal in the file)."""
    bldg = recipe.get("bldg_table", {})
    encoding = recipe.get("encoding", "latin-1")
    min_units = bldg.get("min_units", 20)

    try:
        data = fetch_bytes(recipe["zip_url"])
    except Exception:
        return []

    matches: list[dict] = []
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            for row in _rows(zf, bldg["file"], encoding):
                if not _class_matches(row, bldg):
                    continue
                units_field = bldg.get("units_field")
                units = _to_int(row.get(units_field)) if units_field else None
                if units_field and (units is None or units < min_units):
                    continue

                new_construction = bldg.get("new_construction", {})
                mode = new_construction.get("mode", "pct_complete")
                if mode == "pct_complete":
                    pct = _to_float(row.get(new_construction.get("pct_complete_field")))
                    if pct is None or pct >= new_construction.get("max_pct_complete", 1.0):
                        continue
                elif mode == "value_and_area":
                    value = _to_float(row.get(new_construction.get("value_field"))) or 0
                    area_val = _to_float(row.get(new_construction.get("area_field"))) or 0
                    if value <= 0 or area_val < new_construction.get("min_area", 0):
                        continue
                else:
                    continue

                matches.append({"row": row, "units": units})

            keys = {str(m["row"].get(bldg.get("key_field", "")) or "").strip() for m in matches}
            address_info = _address_info(zf, bldg, encoding, keys)

            records: list[LeadRecord] = []
            for match in matches:
                row = match["row"]
                name = str(row.get(bldg.get("name_field", "")) or "").strip()
                address = _address(row, bldg)
                city = str(row.get(bldg.get("city_field", "")) or "").strip()
                if not address and address_info:
                    key = str(row.get(bldg.get("key_field", "")) or "").strip()
                    info_row = address_info.get(key)
                    if info_row is not None:
                        info_table = bldg.get("address_info_table", {})
                        address = _address(info_row, info_table)
                        city = city or str(info_row.get(info_table.get("city_field", "")) or "").strip()
                if not name and not address:
                    continue

                records.append(
                    LeadRecord(
                        name=name or address,
                        area=area,
                        city=city or recipe.get("county", ""),
                        address=address,
                        units=match["units"],
                        stage="under construction",
                        links={"permit": recipe.get("zip_url", "")},
                        sources=[{"fact": "units", "url": recipe.get("zip_url", "")}],
                        why="new apartment construction (county appraisal-district bulk file)",
                    )
                )
    except Exception:
        return []
    return merge_records(records)


def find_sold_apartments(
    area: str,
    recipe: dict,
    fetch_bytes: FetchBytes = default_fetch_bytes,
    today: datetime.date | None = None,
) -> list[LeadRecord]:
    """One LeadRecord per apartment account (recipe's class/area/unit
    filter met) whose most recent deed date is on/after `recipe["since"]`.
    Owner, phone and the deed date itself come either straight off the
    candidate's own row, from a second one-row-per-account file
    (`sold.info_table`, e.g. County A's owner file), or -- for the
    date only -- from a third file with several dated rows per account
    where only the latest counts (`sold.deed_table`, e.g. County B's
    deeds.txt)."""
    sold = recipe.get("sold", {})
    facts = sold.get("facts", recipe.get("bldg_table", {}))
    encoding = recipe.get("encoding", "latin-1")
    since = _to_date(recipe.get("since", ""), "%Y-%m-%d") or datetime.date(1900, 1, 1)

    try:
        data = fetch_bytes(recipe["zip_url"])
    except Exception:
        return []

    records: list[LeadRecord] = []
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            candidates = _sold_candidates(zf, facts, encoding)

            info_table = sold.get("info_table")
            info_by_key: dict[str, dict] = {}
            if info_table:
                for row in _rows(zf, info_table["file"], encoding):
                    key = str(row.get(info_table["key_field"]) or "").strip()
                    if key in candidates:
                        info_by_key[key] = row

            deed_dates: dict[str, datetime.date] = {}
            deed_table = sold.get("deed_table")
            if deed_table:
                date_format = deed_table.get("date_format", "%m/%d/%Y")
                for row in _rows(zf, deed_table["file"], encoding):
                    key = str(row.get(deed_table["key_field"]) or "").strip()
                    if key not in candidates:
                        continue
                    dt = _to_date(row.get(deed_table.get("date_field")), date_format)
                    if dt is None:
                        continue
                    if key not in deed_dates or dt > deed_dates[key]:
                        deed_dates[key] = dt
            else:
                date_format = sold.get("date_format", "%m/%d/%Y")
                for key in candidates:
                    info_row = info_by_key.get(key, candidates[key])
                    dt = _to_date(info_row.get(sold.get("date_field")), date_format)
                    if dt is not None:
                        deed_dates[key] = dt

            for key, sale_date in deed_dates.items():
                if sale_date < since:
                    continue
                facts_row = candidates[key]
                info_row = info_by_key.get(key, facts_row)
                address = _address(facts_row, facts)
                records.append(
                    LeadRecord(
                        name=str(facts_row.get(facts.get("name_field", "")) or "").strip() or address,
                        area=area,
                        city=str(info_row.get(sold.get("city_field", "")) or facts_row.get(facts.get("city_field", "")) or "").strip()
                        or recipe.get("county", ""),
                        address=address,
                        units=_to_int(facts_row.get(facts.get("units_field"))),
                        stage="sold",
                        sale_date=sale_date.isoformat(),
                        buyer=str(info_row.get(sold.get("owner_field", "")) or "").strip(),
                        office_phone=str(info_row.get(sold.get("phone_field", "")) or "").strip(),
                        links={"permit": recipe.get("zip_url", "")},
                        sources=[{"fact": "sale_date", "url": recipe.get("zip_url", "")}],
                        why="apartment sale (county appraisal-district bulk file, deed transfer)",
                    )
                )
    except Exception:
        return []
    return merge_records(records)


def _sold_candidates(zf: zipfile.ZipFile, facts: dict, encoding: str) -> dict[str, dict]:
    """Every account row that qualifies as an apartment building worth
    tracking for a sale -- keyed by the account/parcel id used to join
    against owner/deed info in other files."""
    key_field = facts["key_field"]
    min_units = facts.get("sold_min_units", facts.get("min_units"))
    min_area = facts.get("sold_min_area")
    area_field = facts.get("area_field")

    candidates: dict[str, dict] = {}
    for row in _rows(zf, facts["file"], encoding):
        if not _class_matches(row, facts):
            continue
        if min_units is not None:
            units = _to_int(row.get(facts.get("units_field")))
            if units is None or units < min_units:
                continue
        if min_area is not None:
            area_val = _to_float(row.get(area_field)) or 0
            if area_val < min_area:
                continue
        key = str(row.get(key_field) or "").strip()
        if not key:
            continue
        candidates[key] = row
    return candidates
