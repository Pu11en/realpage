import io
import sys
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tdhca import find_new_affordable_projects  # noqa: E402

INVENTORY_HEADER = [
    "Rowid", "TDHCA#", "Development Name", "Project Address", "Project City",
    "Project County", "Zip Code", "Total Units", "ConType", "Year", "Board Approval",
]

STATUS_LOG_HEADER = [
    "TDHCA Number", "Development Name", "Development City", "Development County",
    "Construction Type", "Total Units", "Development Address", "Applicant Phone",
]


def _inventory_bytes(rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "PropInventory"
    ws.append(INVENTORY_HEADER)
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _status_log_bytes(rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Status Log"
    # Real file: title block + footnotes occupy rows 1-10; header is row 11.
    for _ in range(10):
        ws.append([None])
    ws.append(STATUS_LOG_HEADER)
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _recipe(**overrides):
    recipe = {
        "htc_inventory_url": "https://example.test/inventory.xlsx",
        "htc_inventory_sheet": "PropInventory",
        "since_year": 2024,
        "status_log_urls": ["https://example.test/statuslog.xlsx"],
    }
    recipe.update(overrides)
    return recipe


def test_inventory_keeps_new_construction_since_year_and_drops_others():
    inventory = _inventory_bytes([
        [1, "T1", "New Apts", "1 Main St", "City A", "County A", "78701", 200, "New Construction", 2025, 1990],
        [2, "T2", "Old Award", "2 Main St", "City A", "County A", "78701", 100, "New Construction", 2020, 1990],
        [3, "T3", "Rehab Only", "3 Main St", "City A", "County A", "78701", 100, "Rehab", 2025, 1990],
    ])
    status_log = _status_log_bytes([])

    def fetch_bytes(url):
        return inventory if "inventory" in url else status_log

    records = find_new_affordable_projects("tx", _recipe(), fetch_bytes=fetch_bytes)
    assert len(records) == 1
    assert records[0].name == "New Apts"
    assert records[0].units == 200
    assert records[0].stage == "planned"


def test_status_log_finds_real_header_row_and_keeps_only_new_construction():
    inventory = _inventory_bytes([])
    status_log = _status_log_bytes([
        [26001, "New Affordable", "City B", "City B", "NC", 150, "1 Elm St", "(512) 555-0100"],
        [26002, "Rehab Deal", "City B", "City B", "Acq/Rehab", 150, "2 Elm St", "(512) 555-0101"],
    ])

    def fetch_bytes(url):
        return inventory if "inventory" in url else status_log

    records = find_new_affordable_projects("tx", _recipe(), fetch_bytes=fetch_bytes)
    assert len(records) == 1
    record = records[0]
    assert record.name == "New Affordable"
    assert record.office_phone == "(512) 555-0100"
    assert record.units == 150


def test_missing_status_log_url_is_skipped_not_fatal():
    inventory = _inventory_bytes([
        [1, "T1", "Solo Award", "1 Main St", "City A", "County A", "78701", 80, "New Construction", 2024, 1990],
    ])

    def fetch_bytes(url):
        if "statuslog" in url:
            raise OSError("network down")
        return inventory

    records = find_new_affordable_projects("tx", _recipe(), fetch_bytes=fetch_bytes)
    assert len(records) == 1
    assert records[0].name == "Solo Award"
