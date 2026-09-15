import io
import sys
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from houston_sold_permits import discover_weekly_urls, fetch_rows  # noqa: E402


def _make_xlsx_bytes(rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Web eReport"])
    ws.append([])
    ws.append(["Zip Code", "Permit Date", "Permit Type", "Project No", "Address", "Comments"])
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_discover_weekly_urls_finds_and_absolutizes_xlsx_links():
    html = """
    <a href="/sites/files/2026-01/week1.xlsx">week1</a>
    <a href="https://example.test/files/week2.xlsx">week2</a>
    <a href="/sites/files/not-a-spreadsheet.pdf">nope</a>
    """
    urls = discover_weekly_urls("https://example.test/sold-permits-search", fetch_text=lambda url: html)
    assert urls == [
        "https://example.test/sites/files/2026-01/week1.xlsx",
        "https://example.test/files/week2.xlsx",
    ]


def test_fetch_rows_keeps_only_new_apartment_comments():
    xlsx_bytes = _make_xlsx_bytes(
        [
            ["77002", "2026/01/07", "Building Pmt", "1", "1 Main St", "GARAGE GENERATOR REPLACEMENT"],
            ["77009", "2026/04/15", "Building Pmt", "2", "2520 Main Ave", "NEW APARTMENT COMPLEX 1-9-1-R2-B, 60 units"],
            ["77010", "2026/04/16", "Building Pmt", "3", "3 Oak St", "APARTMENT STAIR REPAIR 1-3-5-R2-B"],
        ]
    )
    recipe = {"search_page_url": "https://example.test/sold-permits-search"}
    rows = fetch_rows(
        recipe,
        fetch_text=lambda url: '<a href="/files/week1.xlsx">week1</a>',
        fetch_bytes=lambda url: xlsx_bytes,
    )
    assert len(rows) == 1
    assert rows[0]["Address"] == "2520 Main Ave"
    assert rows[0]["_units"] == 60


def test_fetch_rows_skips_a_file_that_fails_to_download():
    recipe = {"search_page_url": "https://example.test/sold-permits-search"}

    def broken_fetch_bytes(url):
        raise OSError("network down")

    rows = fetch_rows(
        recipe,
        fetch_text=lambda url: '<a href="/files/week1.xlsx">week1</a>',
        fetch_bytes=broken_fetch_bytes,
    )
    assert rows == []
