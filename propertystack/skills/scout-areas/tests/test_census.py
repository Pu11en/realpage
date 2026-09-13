"""Census (S2) tests: saved fixture snippets only, no network."""
import pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import census  # noqa: E402

BPS = (HERE / "fixtures" / "bps_cbsa_month.txt").read_text()
ACS = (HERE / "fixtures" / "acs_b25003.dat").read_text()
METROS = [{"slug": "tucson-az", "cbsa": "46060"}, {"slug": "boise-id", "cbsa": "14260"}]


def test_parse_bps_takes_5plus_units():
    got = census.parse_bps(BPS)
    assert got["46060"] == 194 and got["14260"] == 272
    assert "Code" not in got  # header rows skipped


def test_parse_acs_renters_metro_rows_only():
    got = census.parse_acs_renters(ACS)
    assert got == {"14260": 90465, "46060": 152892}


def test_last_months_picks_latest_12():
    listing = " ".join(f"cbsa{y}{m:02d}c.txt cbsa{y}{m:02d}y.txt" for y in (24, 25, 26) for m in range(1, 13))
    months = census.last_months(listing)
    assert months[0] == "2601" and months[-1] == "2612" and len(months) == 12


def test_census_numbers_sums_12_months(tmp_path):
    listing = " ".join(f"cbsa25{m:02d}c.txt" for m in range(1, 13))

    def fake(url, name):
        if name.startswith("bps-index"):
            return listing
        if name.startswith("cbsa"):
            return BPS
        if "2025" in name:
            raise OSError("404")  # newest ACS year not out yet -> falls back
        return ACS

    got = census.census_numbers(METROS, fetcher=fake)
    assert got["tucson-az"]["permits_5plus_12mo"] == 12 * 194
    assert got["boise-id"]["renter_households"] == 90465
    assert got["boise-id"]["census_window"]["permits"] == "2025-01..2025-12"
    assert got["boise-id"]["census_window"]["acs_year"] <= 2024


def test_fetch_caches(tmp_path):
    calls = []

    class R:
        def __init__(self, *a, **k): calls.append(a)
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def read(self): return b"hello"

    assert census.fetch("http://x", "f.txt", cache=tmp_path, opener=R) == "hello"
    assert census.fetch("http://x", "f.txt", cache=tmp_path, opener=R) == "hello"
    assert len(calls) == 1 and (tmp_path / "f.txt").exists()
