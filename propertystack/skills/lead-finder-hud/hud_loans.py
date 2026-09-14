"""lead-finder 3.1: HUD's free FHA multifamily firm-commitments/endorsements list.

Source: https://www.hud.gov/hud-partners/multifamily-data ("FHA Multifamily Firm
Commitments and Endorsements Database", updated quarterly). It's one workbook with a
"Firm Commitments" sheet whose real header row (row 9, 0-indexed 8 -- rows above it are
a title block) is, as of FY26 Q3:

  FHA Number, Project Name, Project City, Project State, Program Type, Program Category,
  Activity Description, Activity Group, Facility Type, Program Subcategory, Firm Activity,
  Lender Name for Firm Activity, Mortgage Amount, Total Units, Firm Activity Date,
  Fiscal Year at Firm Activity, MAP or TAP, LIHTC, Tax Exempt Bonds, Home, CDBG,
  Refi 202, IRP Decoupling, Hope VI, Current Status

Program Subcategory carries the program code we key off of, e.g. "221(d)(4) NC/SR" or
"223(f) Refi/ Purchase Apts" -- matched loosely below since HUD's own docs show it written
several ways ("221(d)(4)", "221D4", "221 (d)(4)").
"""
from __future__ import annotations

import datetime
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "propertystack" / "skills" / "lead-finder"))

from record import LeadRecord, Source  # noqa: E402

CACHE = ROOT / "propertystack" / "data" / "raw" / "hud"
HUD_URL = (
    "https://www.hud.gov/sites/default/files/Housing/documents/"
    "FHA-MF-Firm-Commitments-and-Endorsements-Database-FY01-FY26-Q3.xlsx"
)
SHEET = "Firm Commitments"
HEADER_ROW = 8  # 0-indexed; rows 0-7 are a title block, not data

NEW_CONSTRUCTION_RE = re.compile(r"221\s*\(?d\)?\s*\(?4\)?", re.I)
REFI_SALE_RE = re.compile(r"223\s*\(?f\)?", re.I)


def fetch_workbook_bytes(url=HUD_URL, name=None, cache=CACHE, opener=None):
    """Return the workbook's raw bytes, downloading once into the cache."""
    import urllib.request

    opener = opener or urllib.request.urlopen
    path = cache / (name or pathlib.Path(url).name)
    if not path.exists():
        cache.mkdir(parents=True, exist_ok=True)
        with opener(url, timeout=120) as r:
            path.write_bytes(r.read())
    return path.read_bytes()


def load_sheet_rows(workbook_bytes, sheet=SHEET, header_row=HEADER_ROW):
    """[{column_name: value}] for one sheet, skipping the title block above the header."""
    import io

    import openpyxl

    wb = openpyxl.load_workbook(io.BytesIO(workbook_bytes), read_only=True, data_only=True)
    ws = wb[sheet]
    rows = ws.iter_rows(values_only=True)
    for _ in range(header_row):
        next(rows)
    header = [str(c).strip() if c else "" for c in next(rows)]
    out = []
    for r in rows:
        if not any(r):
            continue
        out.append({header[i]: r[i] for i in range(len(header)) if i < len(r)})
    return out


def _program_stage(program_subcategory: str) -> tuple[str, str] | None:
    """(stage, why) for a Program Subcategory string, or None if it's neither program."""
    text = program_subcategory or ""
    if NEW_CONSTRUCTION_RE.search(text):
        return "permitted", "HUD FHA 221(d)(4) firm commitment for new construction"
    if REFI_SALE_RE.search(text):
        return "sold", "HUD refi or sale (FHA 223(f))"
    return None


def _months_ago(date, today) -> float:
    return (today.year - date.year) * 12 + (today.month - date.month)


def parse_hud_rows(
    rows: list[dict], state: str, min_units: int = 20, months: int = 36, today=None
) -> list[LeadRecord]:
    """Rows already shaped like load_sheet_rows()'s output -> LeadRecords for one state.

    Filters: matching state, Total Units >= min_units, Firm Activity Date within the last
    `months` months, and only the two program codes the plan asks for (221(d)(4) new
    construction, 223(f) refi/sale). Never guesses a missing units or date -- those rows
    are dropped rather than kept with a made-up value.
    """
    today = today or datetime.date.today()
    area = state.lower()
    out = []
    for row in rows:
        row_state = str(row.get("Project State") or "").strip().upper()
        if row_state != state.upper():
            continue

        units = row.get("Total Units")
        if units is None or units == "":
            continue
        try:
            units = int(units)
        except (TypeError, ValueError):
            continue
        if units < min_units:
            continue

        date = row.get("Firm Activity Date")
        if isinstance(date, datetime.datetime):
            date = date.date()
        if not isinstance(date, datetime.date):
            continue
        if _months_ago(date, today) > months or date > today:
            continue

        stage_why = _program_stage(row.get("Program Subcategory"))
        if stage_why is None:
            continue
        stage, why = stage_why

        city = str(row.get("Project City") or "").strip().title()
        name = str(row.get("Project Name") or "").strip()
        fha_number = str(row.get("FHA Number") or "").strip()

        record = LeadRecord(
            area=area,
            city=city,
            name=name,
            units=units,
            stage=stage,
            permit_date=date.isoformat(),
            why=why,
            sources=[
                Source(fact="units", url=HUD_URL).__dict__,
                Source(fact="permit_date", url=HUD_URL).__dict__,
            ],
        )
        if fha_number:
            record.links["hud"] = f"HUD FHA #{fha_number}"
        out.append(record)
    return out


def find_hud_loans(state: str, min_units: int = 20, months: int = 36, today=None, fetcher=None):
    """End-to-end: download/cache the workbook, load its sheet, filter to one state."""
    fetcher = fetcher or fetch_workbook_bytes
    rows = load_sheet_rows(fetcher())
    return parse_hud_rows(rows, state, min_units=min_units, months=months, today=today)


if __name__ == "__main__":
    import argparse
    import json

    p = argparse.ArgumentParser()
    p.add_argument("--state", required=True)
    p.add_argument("--print-columns", action="store_true", help="print the real header row and exit")
    args = p.parse_args()

    if args.print_columns:
        rows = load_sheet_rows(fetch_workbook_bytes())
        print(list(rows[0].keys()) if rows else "no rows")
    else:
        records = find_hud_loans(args.state.upper())
        print(json.dumps([r.to_dict() for r in records], indent=1))
        print(f"{len(records)} HUD loan leads for {args.state.upper()}")
