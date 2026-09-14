import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hud_loans import _program_stage, find_hud_loans, parse_hud_rows  # noqa: E402

TODAY = datetime.date(2026, 9, 14)


def make_row(**kw):
    defaults = dict(
        **{
            "FHA Number": "12345678",
            "Project Name": "Sample Apartments",
            "Project City": "RIVERTOWN",
            "Project State": "ZZ",
            "Program Subcategory": "221(d)(4) NC/SR",
            "Total Units": 200,
            "Firm Activity Date": datetime.datetime(2026, 1, 15),
        }
    )
    defaults.update(kw)
    return defaults


def test_new_construction_program_maps_to_permitted():
    rows = [make_row()]
    out = parse_hud_rows(rows, "ZZ", today=TODAY)
    assert len(out) == 1
    r = out[0]
    assert r.stage == "permitted"
    assert "221(d)(4)" in r.why
    assert r.units == 200
    assert r.city == "Rivertown"
    assert r.area == "zz"
    assert r.permit_date == "2026-01-15"
    assert r.links["hud"] == "HUD FHA #12345678"


def test_refi_sale_program_maps_to_sold():
    rows = [make_row(**{"Program Subcategory": "223(f) Refi/ Purchase Apts"})]
    out = parse_hud_rows(rows, "ZZ", today=TODAY)
    assert out[0].stage == "sold"
    assert "HUD refi or sale" in out[0].why


def test_wrong_state_dropped():
    rows = [make_row(**{"Project State": "YY"})]
    assert parse_hud_rows(rows, "ZZ", today=TODAY) == []


def test_under_min_units_dropped():
    rows = [make_row(**{"Total Units": 10})]
    assert parse_hud_rows(rows, "ZZ", today=TODAY) == []


def test_missing_units_dropped_not_guessed():
    rows = [make_row(**{"Total Units": None})]
    assert parse_hud_rows(rows, "ZZ", today=TODAY) == []


def test_older_than_window_dropped():
    old = make_row(**{"Firm Activity Date": datetime.datetime(2022, 1, 1)})
    assert parse_hud_rows([old], "ZZ", months=36, today=TODAY) == []


def test_within_window_kept():
    recent = make_row(**{"Firm Activity Date": datetime.datetime(2023, 10, 1)})
    out = parse_hud_rows([recent], "ZZ", months=36, today=TODAY)
    assert len(out) == 1


def test_missing_date_dropped():
    rows = [make_row(**{"Firm Activity Date": None})]
    assert parse_hud_rows(rows, "ZZ", today=TODAY) == []


def test_other_program_code_dropped():
    rows = [make_row(**{"Program Subcategory": "542(c) HFA Risk Sharing - NC/SR"})]
    assert parse_hud_rows(rows, "ZZ", today=TODAY) == []


def test_alternate_program_code_spelling_still_matches():
    rows = [make_row(**{"Program Subcategory": "221D4 New Construction"})]
    out = parse_hud_rows(rows, "ZZ", today=TODAY)
    assert out[0].stage == "permitted"


def test_program_stage_helper_returns_none_for_unrelated_text():
    assert _program_stage("Some other program") is None
    assert _program_stage("") is None


def test_future_date_dropped():
    rows = [make_row(**{"Firm Activity Date": datetime.datetime(2026, 12, 1)})]
    assert parse_hud_rows(rows, "ZZ", today=TODAY) == []


def test_find_hud_loans_uses_injected_fetcher_and_state_matches_case_insensitively():
    def fake_fetcher():
        return b"unused-because-load_sheet_rows-is-not-called-here"

    def fake_loader(_bytes):
        return [make_row(**{"Project State": "zz"})]

    import hud_loans

    orig = hud_loans.load_sheet_rows
    hud_loans.load_sheet_rows = fake_loader
    try:
        out = find_hud_loans("ZZ", fetcher=fake_fetcher, today=TODAY)
    finally:
        hud_loans.load_sheet_rows = orig
    assert len(out) == 1
