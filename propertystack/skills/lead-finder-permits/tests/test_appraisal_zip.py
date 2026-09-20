import datetime
import io
import sys
import zipfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from appraisal_zip import default_fetch_bytes, find_new_apartment_projects, find_sold_apartments  # noqa: E402

TODAY = datetime.date(2026, 9, 14)


def _csv(rows: list[list[str]]) -> str:
    return "\n".join(",".join(cell for cell in row) for row in rows) + "\n"


def _tsv(rows: list[list[str]]) -> str:
    return "\n".join("\t".join(cell for cell in row) for row in rows) + "\n"


def _zip_bytes(members: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in members.items():
            zf.writestr(name, content)
    return buf.getvalue()


# --- County A-shaped fixture: two files, joined by ACCOUNT_NUM -----------

DALLAS_BLDG_HEADER = ["ACCOUNT_NUM", "BLDG_CLASS_DESC", "NUM_UNITS", "PROPERTY_NAME", "PCT_COMPLETE"]
DALLAS_ACCT_HEADER = ["ACCOUNT_NUM", "DEED_TXFR_DATE", "OWNER_NAME1", "PHONE_NUM", "PROPERTY_CITY"]


def _dallas_recipe():
    return {
        "county": "County A",
        "zip_url": "https://example.test/dallas.zip",
        "since": "2024-09-01",
        "bldg_table": {
            "file": "COM_DETAIL.CSV",
            "key_field": "ACCOUNT_NUM",
            "class_field": "BLDG_CLASS_DESC",
            "class_filter": "APARTMENT",
            "units_field": "NUM_UNITS",
            "min_units": 20,
            "name_field": "PROPERTY_NAME",
            "new_construction": {
                "mode": "pct_complete",
                "pct_complete_field": "PCT_COMPLETE",
                "max_pct_complete": 1.0,
            },
        },
        "sold": {
            "info_table": {"file": "ACCOUNT_INFO.CSV", "key_field": "ACCOUNT_NUM"},
            "date_field": "DEED_TXFR_DATE",
            "date_format": "%m/%d/%Y",
            "owner_field": "OWNER_NAME1",
            "phone_field": "PHONE_NUM",
            "city_field": "PROPERTY_CITY",
        },
    }


def _dallas_zip():
    bldg_rows = [
        DALLAS_BLDG_HEADER,
        ["1", "APARTMENT (BRICK EXTERIOR)", "60", "UNDER CONSTRUCTION TOWERS", "0.60"],
        ["2", "APARTMENT (FRAME EXTERIOR)", "80", "ALREADY BUILT PLACE", "1.00"],
        ["3", "APARTMENT (BRICK EXTERIOR)", "10", "TOO SMALL PLACE", "0.50"],
        ["4", "STORAGE FACILITY", "500", "NOT AN APARTMENT", "0.10"],
        ["5", "APARTMENT (BRICK EXTERIOR)", "40", "", "0.20"],
    ]
    acct_rows = [
        DALLAS_ACCT_HEADER,
        ["2", "10/05/2025", "BUYCO LLC", "(555) 111-2222", "City A"],
        ["1", "01/01/2020", "OLDOWNER LLC", "", "City A"],
    ]
    return _zip_bytes({"COM_DETAIL.CSV": _csv(bldg_rows), "ACCOUNT_INFO.CSV": _csv(acct_rows)})


def test_dallas_new_construction_gets_address_from_second_file():
    recipe = _dallas_recipe()
    recipe["bldg_table"]["address_info_table"] = {
        "file": "ACCOUNT_INFO.CSV",
        "key_field": "ACCOUNT_NUM",
        "street_num_field": "STREET_NUM",
        "street_name_field": "FULL_STREET_NAME",
        "city_field": "PROPERTY_CITY",
    }

    def _dallas_zip_with_street():
        bldg_rows = [
            DALLAS_BLDG_HEADER,
            ["1", "APARTMENT (BRICK EXTERIOR)", "60", "UNDER CONSTRUCTION TOWERS", "0.60"],
        ]
        acct_rows = [
            ["ACCOUNT_NUM", "DEED_TXFR_DATE", "OWNER_NAME1", "PHONE_NUM", "PROPERTY_CITY", "STREET_NUM", "FULL_STREET_NAME"],
            ["1", "01/01/2020", "OLDOWNER LLC", "", "City A", "100", "MAIN ST"],
        ]
        return _zip_bytes({"COM_DETAIL.CSV": _csv(bldg_rows), "ACCOUNT_INFO.CSV": _csv(acct_rows)})

    records = find_new_apartment_projects("tx", recipe, fetch_bytes=lambda url: _dallas_zip_with_street())
    assert len(records) == 1
    assert records[0].address == "100 MAIN ST"
    assert records[0].city == "City A"


def test_dallas_new_construction_filters_class_units_and_completion():
    recipe = _dallas_recipe()
    records = find_new_apartment_projects("tx", recipe, fetch_bytes=lambda url: _dallas_zip())
    names = {r.name for r in records}
    assert "UNDER CONSTRUCTION TOWERS" in names  # apartment, 60 units, 60% complete
    assert "ALREADY BUILT PLACE" not in names  # 100% complete, not new construction
    assert "TOO SMALL PLACE" not in names  # only 10 units
    assert "NOT AN APARTMENT" not in names  # storage, not apartment class


def test_dallas_blank_name_and_no_address_is_dropped_not_guessed():
    recipe = _dallas_recipe()
    records = find_new_apartment_projects("tx", recipe, fetch_bytes=lambda url: _dallas_zip())
    assert all(r.units != 40 for r in records)


def test_dallas_sold_joins_second_file_and_filters_since_date():
    recipe = _dallas_recipe()
    records = find_sold_apartments("tx", recipe, fetch_bytes=lambda url: _dallas_zip(), today=TODAY)
    assert len(records) == 1
    record = records[0]
    assert record.name == "ALREADY BUILT PLACE"
    assert record.buyer == "BUYCO LLC"
    assert record.office_phone == "(555) 111-2222"
    assert record.sale_date == "2025-10-05"
    # account 1's deed date (2020) is before "since" -- correctly excluded
    assert all(r.name != "UNDER CONSTRUCTION TOWERS" for r in records)


# --- County B-shaped fixture: one facts file + a separate multi-row deed file --

HARRIS_ACCT_HEADER = ["acct", "state_class", "bld_ar", "new_construction_val", "site_addr_1", "site_addr_2", "mailto"]
HARRIS_DEED_HEADER = ["acct", "dos"]


def _harris_recipe():
    return {
        "county": "County B",
        "zip_url": "https://example.test/harris.zip",
        "since": "2024-09-01",
        "bldg_table": {
            "file": "real_acct.txt",
            "key_field": "acct",
            "class_field": "state_class",
            "class_filter": "B1",
            "class_exact": True,
            "address_field": "site_addr_1",
            "city_field": "site_addr_2",
            "sold_min_area": 15000,
            "area_field": "bld_ar",
            "new_construction": {
                "mode": "value_and_area",
                "value_field": "new_construction_val",
                "area_field": "bld_ar",
                "min_area": 15000,
            },
        },
        "sold": {
            "deed_table": {"file": "deeds.txt", "key_field": "acct", "date_field": "dos", "date_format": "%m/%d/%Y"},
            "owner_field": "mailto",
        },
    }


def _harris_zip():
    acct_rows = [
        HARRIS_ACCT_HEADER,
        ["1", "B1", "20000", "500000", "1 MAIN ST", "City B", "NEWOWNER LLC"],
        ["2", "B1", "5000", "300000", "2 SMALL ST", "City B", "SMALLOWNER LLC"],  # under area floor
        ["3", "B1", "18000", "0", "3 DONE ST", "City B", "DONEOWNER LLC"],  # no new-construction value
        ["4", "A1", "50000", "900000", "4 HOUSE ST", "City B", "HOUSEOWNER LLC"],  # not B1
    ]
    deed_rows = [
        HARRIS_DEED_HEADER,
        ["3", "01/01/2020"],
        ["3", "10/05/2025"],  # latest deed for acct 3 -- should win
        ["1", "01/01/2020"],  # before "since" -- acct 1 not sold recently
    ]
    return _zip_bytes({"real_acct.txt": _tsv(acct_rows), "deeds.txt": _tsv(deed_rows)})


def test_harris_new_construction_filters_class_value_and_area():
    recipe = _harris_recipe()
    records = find_new_apartment_projects("tx", recipe, fetch_bytes=lambda url: _harris_zip())
    addresses = {r.address for r in records}
    assert "1 MAIN ST" in addresses
    assert "2 SMALL ST" not in addresses  # area below floor
    assert "3 DONE ST" not in addresses  # no new-construction value -> already complete
    assert "4 HOUSE ST" not in addresses  # not multifamily class


def test_harris_sold_takes_latest_of_several_deed_rows():
    recipe = _harris_recipe()
    records = find_sold_apartments("tx", recipe, fetch_bytes=lambda url: _harris_zip(), today=TODAY)
    assert len(records) == 1
    record = records[0]
    assert record.address == "3 DONE ST"
    assert record.sale_date == "2025-10-05"  # the later of the two dated rows, not the first
    assert record.buyer == "DONEOWNER LLC"
    assert record.units is None  # this county's file has no unit-count column at all


def test_default_fetch_bytes_percent_encodes_a_raw_windows_path_query_value():
    """A real county redirect link (County A's) hands back a query value that
    is a literal, un-escaped Windows file path -- backslashes and spaces --
    which `http.client` rejects outright as control characters unless it's
    percent-encoded first."""
    raw_url = "https://example.test/ViewPDFs.aspx?type=3&id=\\\\HOST.ORG\\WEB\\DATA PRODUCTS\\FILE.ZIP"
    captured = {}

    class _FakeResponse:
        def read(self):
            return b"zip-bytes"

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def _fake_urlopen(req, timeout=None):
        captured["url"] = req.full_url
        return _FakeResponse()

    with patch("urllib.request.urlopen", _fake_urlopen):
        data = default_fetch_bytes(raw_url)

    assert data == b"zip-bytes"
    assert "\\" not in captured["url"]
    assert " " not in captured["url"]


# --- County B with its unit column named: str_unit is the unit count and
# --- Harris County glues it onto site_addr_1 ("9757 WINDWATER DR 150").

HARRIS_UNIT_HEADER = [
    "acct", "state_class", "bld_ar", "new_construction_val",
    "str_unit", "site_addr_1", "site_addr_2", "mailto",
]


def _harris_unit_recipe():
    recipe = _harris_recipe()
    recipe["bldg_table"]["units_field"] = "str_unit"
    recipe["bldg_table"]["address_unit_suffix_field"] = "str_unit"
    return recipe


def _harris_unit_zip():
    acct_rows = [
        HARRIS_UNIT_HEADER,
        ["1", "B1", "160000", "500000", "150", "9757 WINDWATER DR 150", "City B", "BUILDER LLC"],
        # the street name itself ends in a number -- only the unit suffix goes
        ["2", "B1", "480000", "0", "490", "1315 NASA RD 1 490", "City B", "NASAOWNER LLC"],
        # no unit designator recorded: the address is already clean, units unknown
        ["3", "B1", "90000", "0", "", "2500 TEXAS ST", "City B", "TEXASOWNER LLC"],
    ]
    deed_rows = [
        HARRIS_DEED_HEADER,
        ["2", "03/11/2025"],
        ["3", "04/22/2025"],
    ]
    return _zip_bytes({"real_acct.txt": _tsv(acct_rows), "deeds.txt": _tsv(deed_rows)})


def test_harris_sold_reads_units_and_drops_the_unit_suffix_from_the_address():
    records = find_sold_apartments(
        "tx", _harris_unit_recipe(), fetch_bytes=lambda url: _harris_unit_zip(), today=TODAY
    )
    by_address = {r.address: r for r in records}

    # "1315 NASA RD 1 490" is 1315 NASA RD 1, unit designator 490 -- the street
    # keeps its own trailing number, only the recorded suffix comes off.
    assert "1315 NASA RD 1" in by_address
    assert by_address["1315 NASA RD 1"].units == 490

    # nothing to trim and nothing to read: left exactly as the county has it
    assert "2500 TEXAS ST" in by_address
    assert by_address["2500 TEXAS ST"].units is None

    assert all(not r.address.endswith(" 490") for r in records)


def test_harris_new_construction_reads_units_and_cleans_the_address():
    records = find_new_apartment_projects(
        "tx", _harris_unit_recipe(), fetch_bytes=lambda url: _harris_unit_zip()
    )
    assert len(records) == 1
    assert records[0].address == "9757 WINDWATER DR"
    assert records[0].units == 150
    # the name falls back to the address, so it must be the cleaned one
    assert records[0].name == "9757 WINDWATER DR"


def test_a_recipe_without_the_suffix_field_leaves_the_address_untouched():
    recipe = _harris_recipe()
    recipe["bldg_table"]["units_field"] = "str_unit"
    records = find_sold_apartments(
        "tx", recipe, fetch_bytes=lambda url: _harris_unit_zip(), today=TODAY
    )
    assert "1315 NASA RD 1 490" in {r.address for r in records}
