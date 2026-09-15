import datetime
import io
import sys
import zipfile
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tad_zip import fetch_rows, find_new_apartment_permits  # noqa: E402

TODAY = datetime.date(2026, 9, 14)

HEADER = [
    "Account", "Site Name", "Situs Address", "Total Units",
    "Issuing Agency", "Intended Property Use", "Issue Date",
]


def _make_zip_bytes(rows, xlsx_name="Comm Permits.xlsx"):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Permits"
    ws.append(HEADER)
    for row in rows:
        ws.append(row)
    xlsx_buf = io.BytesIO()
    wb.save(xlsx_buf)

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w") as zf:
        zf.writestr(xlsx_name, xlsx_buf.getvalue())
    return zip_buf.getvalue()


def _recipe(**overrides):
    recipe = {
        "zip_urls": ["https://example.test/2026.zip"],
        "use_field": "Intended Property Use",
        "use_filter": "Apartments",
        "city_field": "Issuing Agency",
        "address_field": "Situs Address",
        "name_field": "Site Name",
        "units_field": "Total Units",
        "date_field": "Issue Date",
        "min_units": 20,
    }
    recipe.update(overrides)
    return recipe


def test_fetch_rows_filters_by_use_field():
    zip_bytes = _make_zip_bytes(
        [
            ["1", "Some Apartments", "1 Main St", 40, "City A", "Apartments", datetime.datetime(2026, 8, 1)],
            ["2", "An Office", "2 Main St", 0, "City A", "Office", datetime.datetime(2026, 8, 1)],
        ]
    )
    rows = fetch_rows(_recipe(), fetch_bytes=lambda url: zip_bytes)
    assert len(rows) == 1
    assert rows[0]["Site Name"] == "Some Apartments"


def test_find_new_apartment_permits_tags_city_per_row_and_drops_small_units():
    zip_bytes = _make_zip_bytes(
        [
            ["1", "Big Apts", "1 Main St", 120, "City A", "Apartments", datetime.datetime(2026, 8, 1)],
            ["2", "Small Duplex", "2 Main St", 4, "City B", "Apartments", datetime.datetime(2026, 8, 1)],
            ["3", "In Development Apts", "3 Main St", 0, "City C", "Apartments", datetime.datetime(2026, 8, 1)],
        ]
    )
    records = find_new_apartment_permits("zz", _recipe(), fetch_bytes=lambda url: zip_bytes, today=TODAY)
    cities = {r.city for r in records}
    assert cities == {"City A", "City C"}
    big = next(r for r in records if r.city == "City A")
    assert big.units == 120
    in_dev = next(r for r in records if r.city == "City C")
    assert in_dev.units is None  # 0 on this feed means "not yet known", never literally zero


def test_find_new_apartment_permits_drops_old_permits():
    zip_bytes = _make_zip_bytes(
        [["1", "Old Apts", "1 Main St", 100, "City A", "Apartments", datetime.datetime(2020, 1, 1)]]
    )
    records = find_new_apartment_permits("zz", _recipe(), fetch_bytes=lambda url: zip_bytes, today=TODAY)
    assert records == []


def test_fetch_rows_skips_a_zip_that_fails_to_download():
    def broken_fetch_bytes(url):
        raise OSError("network down")

    rows = fetch_rows(_recipe(), fetch_bytes=broken_fetch_bytes)
    assert rows == []
