import io
import sys
import urllib.error
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from houston_sold_permits import direct_xlsx_url, discover_weekly_urls, fetch_rows, fetch_with_retry  # noqa: E402


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


def test_discover_weekly_urls_unwraps_viewer_links_without_raw_spaces():
    html = """
    <a href="/viewer.aspx?src=https%3A%2F%2Fexample.test%2Ffiles%2FWeek%25201.xlsx">week1</a>
    """
    urls = discover_weekly_urls("https://example.test/sold-permits-search", fetch_text=lambda url: html)
    assert urls == ["https://example.test/files/Week%201.xlsx"]
    assert " " not in urls[0]


def test_direct_xlsx_url_leaves_direct_file_links_alone():
    url = "https://example.test/files/Week%201.xlsx"
    assert direct_xlsx_url(url) == url


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


def test_fetch_rows_drops_apartment_words_that_are_not_new_apartment_buildings():
    xlsx_bytes = _make_xlsx_bytes(
        [
            ["77001", "2026/01/07", "Building Pmt", "1", "1 Main St", "NEW DETACHED GAR W/APT ABOVE"],
            ["77002", "2026/01/08", "Building Pmt", "2", "2 Main St", "800 KW NEW EXT. DIESEL GEN. AND CMU WALL AT APT"],
            ["77003", "2026/01/09", "Building Pmt", "3", "3 Main St", "NEW CONDOS BUILDOUT 1-9-1-R2-B"],
            ["77004", "2026/01/10", "Building Pmt", "4", "4 Main St", "NEW APT AMENITY CNTR"],
            ["77005", "2026/01/11", "Building Pmt", "5", "5 Main St", "CREATE NEW COMMON LAUNDRY & DINING ROOMS"],
            ["77009", "2026/01/12", "Building Pmt", "6", "6 Main St", "NEW APT BLD (80 UNITS)"],
        ]
    )
    recipe = {
        "search_page_url": "https://example.test/sold-permits-search",
        "keyword_pattern": r"apart|\bapts?\b|multi[- ]?family|\br-?2\b",
    }
    rows = fetch_rows(
        recipe,
        fetch_text=lambda url: '<a href="/files/week1.xlsx">week1</a>',
        fetch_bytes=lambda url: xlsx_bytes,
    )
    assert [row["Address"] for row in rows] == ["6 Main St"]


def test_fetch_rows_reports_stats_for_read_and_failed_files():
    recipe = {"search_page_url": "https://example.test/sold-permits-search"}

    def fetch_bytes(url):
        if url.endswith("week2.xlsx"):
            raise OSError("network down")
        return _make_xlsx_bytes(
            [["77009", "2026/04/15", "Building Pmt", "2", "2520 Main Ave", "NEW APARTMENT COMPLEX, 60 units"]]
        )

    stats = {}
    rows = fetch_rows(
        recipe,
        fetch_text=lambda url: '<a href="/files/week1.xlsx">week1</a><a href="/files/week2.xlsx">week2</a>',
        fetch_bytes=fetch_bytes,
        stats=stats,
    )
    assert len(rows) == 1
    assert stats["filesPosted"] == 2
    assert stats["filesRead"] == 1
    assert stats["rawRows"] == 1
    assert stats["keywordRows"] == 1
    assert len(stats["filesFailed"]) == 1


def test_fetch_with_retry_recovers_from_retryable_http_error():
    calls = []

    def fetch_bytes(url):
        calls.append(url)
        if len(calls) == 1:
            raise urllib.error.HTTPError(url, 429, "slow down", hdrs=None, fp=None)
        return b"ok"

    assert fetch_with_retry(fetch_bytes, "https://example.test/file.xlsx", sleep=lambda seconds: None) == b"ok"
    assert calls == ["https://example.test/file.xlsx", "https://example.test/file.xlsx"]
