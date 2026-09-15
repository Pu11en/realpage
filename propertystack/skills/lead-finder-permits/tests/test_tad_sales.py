import datetime
import io
import sys
import zipfile
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tad_sales import fetch_sale_rows, find_apartment_sales  # noqa: E402

TODAY = datetime.date(2026, 9, 14)

HEADER = [
    "PIN", "Site Name", "Address", "Number of Units", "Document Date",
    "Contract Sale Price", "Adjusted Sale Price", "Document Number",
]


def _make_zip_bytes(sheets: dict[str, list[list]], other_sheet_name="Commercial and Industrial"):
    wb = openpyxl.Workbook()
    default_ws = wb.active
    default_ws.title = other_sheet_name
    default_ws.append(HEADER)
    default_ws.append(["9", "Not An Apartment", "9 Main St", 50, datetime.datetime(2026, 1, 1), 1, 1, "D1"])
    for sheet_name, rows in sheets.items():
        ws = wb.create_sheet(sheet_name)
        ws.append(HEADER)
        for row in rows:
            ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w") as zf:
        zf.writestr("Improved Sales.xlsx", buf.getvalue())
    return zip_buf.getvalue()


def _recipe(**overrides):
    recipe = {
        "zip_urls": ["https://example.test/2026.zip"],
        "sheet_name_prefix": "apartment",
        "units_field": "Number of Units",
        "date_field": "Document Date",
        "name_field": "Site Name",
        "address_field": "Address",
        "price_field": "Adjusted Sale Price",
        "fallback_price_field": "Contract Sale Price",
        "doc_field": "Document Number",
        "min_units": 20,
        "since": "2024-09-01",
        "county": "Example County",
    }
    recipe.update(overrides)
    return recipe


def test_fetch_sale_rows_matches_sheet_name_prefix_case_insensitively():
    zip_bytes = _make_zip_bytes({"Apartment": [
        ["1", "Sold Apts", "1 Main St", 100, datetime.datetime(2025, 5, 1), 1000000, 1100000, "D100"],
    ]})
    rows = fetch_sale_rows(_recipe(), fetch_bytes=lambda url: zip_bytes)
    assert len(rows) == 1
    assert rows[0]["Site Name"] == "Sold Apts"


def test_find_apartment_sales_drops_small_and_old_and_fills_city_from_county():
    zip_bytes = _make_zip_bytes({"Apartments": [
        ["1", "Big Sale", "1 Main St", 200, datetime.datetime(2025, 6, 1), 5000000, 5500000, "D200"],
        ["2", "Small Sale", "2 Main St", 4, datetime.datetime(2025, 6, 1), 100000, 100000, "D201"],
        ["3", "Too Old", "3 Main St", 50, datetime.datetime(2020, 1, 1), 200000, 200000, "D202"],
    ]})
    records = find_apartment_sales("tx", _recipe(), fetch_bytes=lambda url: zip_bytes, today=TODAY)
    assert len(records) == 1
    record = records[0]
    assert record.name == "Big Sale"
    assert record.units == 200
    assert record.stage == "sold"
    assert record.city == "Example County"
    assert record.buyer == ""
    assert "$5,500,000" in record.why


def test_find_apartment_sales_omits_price_when_both_price_fields_are_null():
    zip_bytes = _make_zip_bytes({"Apartment": [
        ["1", "No Price Sale", "1 Main St", 30, datetime.datetime(2025, 6, 1), "NULL", "NULL", "D300"],
    ]})
    records = find_apartment_sales("tx", _recipe(), fetch_bytes=lambda url: zip_bytes, today=TODAY)
    assert len(records) == 1
    assert "price not public" in records[0].why


def test_excel_serial_document_date_converts_correctly():
    zip_bytes = _make_zip_bytes({"Apartment": [
        ["1", "Serial Date Sale", "1 Main St", 25, 45852, 900000, 950000, "D400"],
    ]})
    records = find_apartment_sales("tx", _recipe(), fetch_bytes=lambda url: zip_bytes, today=TODAY)
    assert len(records) == 1
    assert records[0].sale_date == "2025-07-14"
