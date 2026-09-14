"""lead-finder 3.2: state housing agency tax-credit/bond award lists.

Every state's housing finance agency publishes LIHTC and bond award lists, but there's
no single free API for them (unlike HUD's spreadsheet in lead-finder-hud). So this part
searches for the agency's award list, saves a recipe describing where it lives, and
reads it as a table -- PDF (pdfplumber) or spreadsheet (openpyxl). Only new construction,
20+ units, awarded in the last 36 months is kept; "rehab"/"preservation" rows are
explicitly dropped since the plan wants new-project leads, not existing buildings.

No place names anywhere in this file -- state/agency are always caller-supplied data.
"""
from __future__ import annotations

import datetime
import json
import re
import sys
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "propertystack" / "skills" / "lead-finder"))

from record import LeadRecord, Source  # noqa: E402

RECIPES_DIR = ROOT / "propertystack" / "recipes"

REHAB_RE = re.compile(r"rehab|preservation|acquisition[- ]?rehab", re.I)
PDF_RE = re.compile(r"\.pdf(\?|$)", re.I)
XLSX_RE = re.compile(r"\.xlsx?(\?|$)", re.I)

SearchFn = Callable[[str], list[dict]]
FetchBytesFn = Callable[[str], bytes]


def slugify(state: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", state.lower()).strip("-")


def find_award_recipe(
    state: str,
    agency_name: str,
    search_fn: SearchFn,
    recipes_dir: Path = RECIPES_DIR,
    years: tuple[str, ...] = ("2025", "2026"),
) -> dict:
    """Search for `agency_name`'s award list; save the first PDF/spreadsheet hit as a recipe.

    Always returns a dict: either a saved recipe (has "list_url") or a skip note
    (has "skipped": True and "reason") -- never raises for "nothing found online".
    """
    queries = [f'"{agency_name}" housing tax credit awards {year}' for year in years]
    queries.append(f'"{agency_name}" "bond" "awards"')

    for query in queries:
        for result in search_fn(query):
            url = result.get("url", "")
            if PDF_RE.search(url):
                fmt = "pdf"
            elif XLSX_RE.search(url):
                fmt = "xlsx"
            else:
                continue
            recipe = {
                "state": state,
                "agency": agency_name,
                "list_url": url,
                "format": fmt,
                "date_tested": datetime.date.today().isoformat(),
            }
            recipes_dir.mkdir(parents=True, exist_ok=True)
            (recipes_dir / f"awards-{slugify(state)}.json").write_text(
                json.dumps(recipe, indent=2) + "\n", encoding="utf-8"
            )
            return recipe

    return {"state": state, "agency": agency_name, "skipped": True, "reason": "no award list online"}


def load_pdf_table_rows(pdf_bytes: bytes) -> list[dict]:
    """[{column_name: value}] from every table on every page, header = first row."""
    import io

    import pdfplumber

    out = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                if not table or len(table) < 2:
                    continue
                header = [str(c or "").strip() for c in table[0]]
                for row in table[1:]:
                    out.append({header[i]: row[i] for i in range(len(header)) if i < len(row)})
    return out


def load_xlsx_rows(xlsx_bytes: bytes) -> list[dict]:
    """[{column_name: value}] from the first sheet, header = first non-empty row."""
    import io

    import openpyxl

    wb = openpyxl.load_workbook(io.BytesIO(xlsx_bytes), read_only=True, data_only=True)
    ws = wb.worksheets[0]
    rows = ws.iter_rows(values_only=True)
    header = None
    out = []
    for r in rows:
        if header is None:
            if any(r):
                header = [str(c).strip() if c else "" for c in r]
            continue
        if not any(r):
            continue
        out.append({header[i]: r[i] for i in range(len(header)) if i < len(r)})
    return out


def _first_matching_key(row: dict, needle: str) -> str | None:
    for key in row:
        if needle in key.lower():
            return key
    return None


def _parse_date(value) -> datetime.date | None:
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    if isinstance(value, str) and value.strip():
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%B %Y", "%b %Y"):
            try:
                return datetime.datetime.strptime(value.strip(), fmt).date()
            except ValueError:
                continue
    return None


def _months_ago(date, today) -> float:
    return (today.year - date.year) * 12 + (today.month - date.month)


def parse_award_rows(
    rows: list[dict],
    state: str,
    list_url: str,
    min_units: int = 20,
    months: int = 36,
    today=None,
) -> list[LeadRecord]:
    """Award-list rows -> LeadRecords for one state.

    Drops rows with no units/date, rows outside the window, rows under min_units,
    and any row whose type/description mentions rehab or preservation -- never
    guesses a missing field.
    """
    today = today or datetime.date.today()
    area = state.lower()
    out = []
    for row in rows:
        type_key = _first_matching_key(row, "type") or _first_matching_key(row, "activity")
        type_text = str(row.get(type_key) or "") if type_key else ""
        if REHAB_RE.search(type_text):
            continue

        units_key = _first_matching_key(row, "unit")
        if units_key is None:
            continue
        try:
            units = int(str(row[units_key]).strip())
        except (TypeError, ValueError):
            continue
        if units < min_units:
            continue

        date_key = _first_matching_key(row, "date")
        date = _parse_date(row.get(date_key)) if date_key else None
        if date is None:
            continue
        if _months_ago(date, today) > months or date > today:
            continue

        name_key = _first_matching_key(row, "project") or _first_matching_key(row, "name")
        city_key = _first_matching_key(row, "city")
        developer_key = _first_matching_key(row, "developer") or _first_matching_key(row, "sponsor")

        record = LeadRecord(
            area=area,
            city=str(row.get(city_key) or "").strip().title() if city_key else "",
            name=str(row.get(name_key) or "").strip() if name_key else "",
            units=units,
            stage="planned",
            permit_date=date.isoformat(),
            developer=str(row.get(developer_key) or "").strip() if developer_key else "",
            why="state housing agency tax-credit/bond award",
            sources=[
                Source(fact="units", url=list_url).__dict__,
                Source(fact="permit_date", url=list_url).__dict__,
            ],
        )
        out.append(record)
    return out


def find_awards(
    state: str,
    agency_name: str,
    search_fn: SearchFn,
    fetch_bytes_fn: FetchBytesFn,
    min_units: int = 20,
    months: int = 36,
    today=None,
    recipes_dir: Path = RECIPES_DIR,
) -> list[LeadRecord]:
    """End to end: find/save a recipe, download the list, parse it into leads."""
    recipe = find_award_recipe(state, agency_name, search_fn, recipes_dir=recipes_dir)
    if recipe.get("skipped"):
        return []
    list_bytes = fetch_bytes_fn(recipe["list_url"])
    if recipe["format"] == "pdf":
        rows = load_pdf_table_rows(list_bytes)
    else:
        rows = load_xlsx_rows(list_bytes)
    return parse_award_rows(rows, state, recipe["list_url"], min_units=min_units, months=months, today=today)


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--state", required=True)
    p.add_argument("--agency", required=True, help="the state's housing finance agency name")
    args = p.parse_args()

    import searx_search  # tooling/searx_search.py

    sys.path.insert(0, str(ROOT / "tooling"))

    def _fetch_bytes(url: str) -> bytes:
        import urllib.request

        with urllib.request.urlopen(url, timeout=60) as r:
            return r.read()

    records = find_awards(args.state.upper(), args.agency, searx_search.search, _fetch_bytes)
    print(json.dumps([r.to_dict() for r in records], indent=1))
    print(f"{len(records)} state housing award leads for {args.state.upper()}")
