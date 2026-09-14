import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from find_sold import find_sold  # noqa: E402

TODAY = datetime.date(2026, 9, 14)

RECIPE = {
    "county": "Rivertown County",
    "state": "ZZ",
    "sales_source": {"url": "https://example.test/sales.zip", "file_glob": "*.txt"},
    "parcel_source": {"url": "https://example.test/parcel.zip", "file_glob": "*.txt"},
    "sales_fields": {
        "parcel": "PARCELNUMBER",
        "sale_date": "SALEDATE_MMYYYY",
        "date_format": "MMYYYY",
        "price": "SALEPRICE",
        "type_code": "PROPERTYTYPECODE",
        "address": "SITUSADDRESS",
        "city": "SITUSCITY",
        "grantor": "GRANTOROWNERNAME",
        "grantee": "GRANTEEOWNERNAME",
    },
    "parcel_fields": {"parcel": "FolioKey", "units": "NumUnits"},
    "apartment_type_codes": ["E"],
    "min_units": 20,
    "recent_months": 24,
}

SALES_ROW = {
    "PARCELNUMBER": "100200300",
    "SALEDATE_MMYYYY": "062026",
    "SALEPRICE": "20000000",
    "PROPERTYTYPECODE": "E",
    "SITUSADDRESS": "1 River Rd",
    "SITUSCITY": "Rivertown",
    "GRANTOROWNERNAME": "OLD OWNER LLC",
    "GRANTEEOWNERNAME": "NEW OWNER LLC",
}

PARCEL_ROW = {"FolioKey": "100200300", "NumUnits": "150"}


def _fetch_rows(sales_rows=None, parcel_rows=None):
    sales_rows = sales_rows if sales_rows is not None else [SALES_ROW]
    parcel_rows = parcel_rows if parcel_rows is not None else [PARCEL_ROW]

    def fetch(source: dict):
        if "sales" in source["url"]:
            return sales_rows
        return parcel_rows

    return fetch


def test_apartment_sale_with_enough_units_is_kept():
    records = find_sold("zz", RECIPE, _fetch_rows(), today=TODAY)
    assert len(records) == 1
    r = records[0]
    assert r.address == "1 River Rd"
    assert r.city == "Rivertown"
    assert r.units == 150
    assert r.stage == "sold"
    assert r.sale_date == "2026-06-01"
    assert r.buyer == "NEW OWNER LLC"
    assert r.developer == "OLD OWNER LLC"


def test_non_apartment_type_code_is_dropped():
    row = {**SALES_ROW, "PROPERTYTYPECODE": "B"}  # single family
    assert find_sold("zz", RECIPE, _fetch_rows(sales_rows=[row]), today=TODAY) == []


def test_apartment_with_too_few_units_is_dropped():
    row = {**PARCEL_ROW, "NumUnits": "8"}
    assert find_sold("zz", RECIPE, _fetch_rows(parcel_rows=[row]), today=TODAY) == []


def test_apartment_with_no_unit_record_at_all_is_dropped_not_guessed():
    assert find_sold("zz", RECIPE, _fetch_rows(parcel_rows=[]), today=TODAY) == []


def test_sale_older_than_recent_months_is_dropped():
    row = {**SALES_ROW, "SALEDATE_MMYYYY": "062020"}
    assert find_sold("zz", RECIPE, _fetch_rows(sales_rows=[row]), today=TODAY) == []


def test_sale_in_the_future_relative_to_today_is_dropped():
    row = {**SALES_ROW, "SALEDATE_MMYYYY": "012030"}
    assert find_sold("zz", RECIPE, _fetch_rows(sales_rows=[row]), today=TODAY) == []


def test_unparseable_date_is_dropped():
    row = {**SALES_ROW, "SALEDATE_MMYYYY": ""}
    assert find_sold("zz", RECIPE, _fetch_rows(sales_rows=[row]), today=TODAY) == []


def test_missing_sales_source_returns_empty():
    recipe = {**RECIPE, "sales_source": None}
    assert find_sold("zz", recipe, _fetch_rows(), today=TODAY) == []


def test_fetch_error_returns_empty_not_raises():
    def boom(source):
        raise OSError("network down")

    assert find_sold("zz", RECIPE, boom, today=TODAY) == []


def test_multiple_sales_only_qualifying_ones_kept():
    rows = [
        SALES_ROW,
        {**SALES_ROW, "PARCELNUMBER": "999", "PROPERTYTYPECODE": "B"},
    ]
    records = find_sold("zz", RECIPE, _fetch_rows(sales_rows=rows), today=TODAY)
    assert len(records) == 1
    assert records[0].address == "1 River Rd"
