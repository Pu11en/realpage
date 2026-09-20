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


def _positive_int(value) -> int | None:
    try:
        parsed = int(float(str(value).strip()))
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _cell(row: tuple, index: int):
    return row[index] if 0 <= index < len(row) else None


def parse_multiline_award_sheet(
    rows: list[tuple],
    *,
    area: str,
    state: str,
    year: int,
    list_url: str,
    columns: dict,
    min_units: int = 20,
) -> list[LeadRecord]:
    """Parse annual award sheets where one project spans several rows.

    A project begins on a row with a numeric total-unit value. Its address,
    city, and split type label live on the following rows until the next
    project. Column positions stay in recipe data so the parser has no agency
    or state-specific literals.
    """
    project_col = int(columns["project"])
    developer_col = int(columns["developer"])
    units_col = int(columns["units"])
    type_col = int(columns["type"])

    starts = [
        index
        for index, row in enumerate(rows)
        if _cell(row, project_col) and _positive_int(_cell(row, units_col)) is not None
    ]
    records: list[LeadRecord] = []
    location_re = re.compile(rf"^(.+?),\s*{re.escape(state)}\s+\d{{5}}(?:-\d{{4}})?\s*$", re.I)

    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(rows)
        block = rows[start:end]
        units = _positive_int(_cell(rows[start], units_col))
        if units is None or units < min_units:
            continue
        type_text = " ".join(
            str(_cell(row, type_col) or "").strip() for row in block
        )
        if not re.search(r"\bnew\s+construction\b", type_text, re.I):
            continue

        first_column = [
            str(_cell(row, project_col) or "").strip()
            for row in block
            if str(_cell(row, project_col) or "").strip()
        ]
        if not first_column:
            continue
        name = first_column[0]
        address = first_column[1] if len(first_column) > 1 else ""
        city = ""
        for value in first_column[2:]:
            match = location_re.match(value)
            if match:
                city = match.group(1).strip().title()
                break
        developer = str(_cell(rows[start], developer_col) or "").strip()
        records.append(
            LeadRecord(
                area=area,
                city=city,
                name=name,
                address=address,
                units=units,
                stage="planned",
                award_year=year,
                developer=developer,
                links={"housing_award": list_url},
                sources=[{"fact": "units", "url": list_url}, {"fact": "award_year", "url": list_url}],
                why=f"state housing tax-credit new-construction award ({year})",
            )
        )
    return records


def find_saved_multiline_awards(
    area: str,
    recipe: dict,
    fetch_bytes_fn: FetchBytesFn,
    today=None,
) -> list[LeadRecord]:
    """Read a verified saved multi-sheet award workbook without web search."""
    import io

    import openpyxl

    today = today or datetime.date.today()
    list_url = recipe["list_url"]
    workbook = openpyxl.load_workbook(
        io.BytesIO(fetch_bytes_fn(list_url)), read_only=True, data_only=True
    )
    since_year = int(recipe.get("since_year", today.year - 2))
    state = str(recipe.get("state") or "").upper()
    columns = recipe["columns"]
    records: list[LeadRecord] = []
    for worksheet in workbook.worksheets:
        title = worksheet.title.strip()
        if not title.isdigit():
            continue
        year = int(title)
        if year < since_year or year > today.year:
            continue
        rows = list(worksheet.iter_rows(values_only=True))
        records.extend(
            parse_multiline_award_sheet(
                rows,
                area=area,
                state=state,
                year=year,
                list_url=list_url,
                columns=columns,
                min_units=int(recipe.get("min_units", 20)),
            )
        )
    return records


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
            award_year=date.year,
            developer=str(row.get(developer_key) or "").strip() if developer_key else "",
            why="state housing agency tax-credit/bond award",
            sources=[
                Source(fact="units", url=list_url).__dict__,
                Source(fact="permit_date", url=list_url).__dict__,
                Source(fact="award_year", url=list_url).__dict__,
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

    sys.path.insert(0, str(ROOT / "propertystack" / "skills" / "lead-finder"))
    from fetch import WebHelper  # propertystack/skills/lead-finder/fetch.py

    def _fetch_bytes(url: str) -> bytes:
        import urllib.request

        with urllib.request.urlopen(url, timeout=60) as r:
            return r.read()

    web = WebHelper()
    records = find_awards(args.state.upper(), args.agency, web.search, _fetch_bytes)
    print(json.dumps([r.to_dict() for r in records], indent=1))
    print(f"{len(records)} state housing award leads for {args.state.upper()}")
