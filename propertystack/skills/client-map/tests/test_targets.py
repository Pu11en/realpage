"""Client map targets (C2) tests: small inline Census fixtures, no network."""
import pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import targets  # noqa: E402

HEAD = "Survey,FIPS\nDate,State\n \n"


def st_row(fips, name, units):
    return f"202601,{fips},3,7,{name},1,1,1,0,0,0,0,0,0,2,{units},9,0,0,0,0,0,0,0,0,0,0,0,0\n"


def pl_row(fips, name, units):
    return (f"202601,{fips},000100,001,0001,00100 ,00000 ,1000 ,1,19100, , ,75001 ,3,7,5,"
            f"{name},1,1,1,0,0,0,0,0,0,2,{units},9\n")


def fixture_fetcher():
    months = [f"25{m:02d}" for m in range(8, 13)] + [f"26{m:02d}" for m in range(1, 8)]
    listing = " ".join(f"st{m}c.txt" for m in months + ["9912", "2507"])
    files = {"bps-state-index": listing}
    for m in months:
        files[f"st{m}c.txt"] = HEAD + st_row("48", "Texas", 100) + st_row("12", "Florida", 50) + st_row("06", "California", 10)
        files[f"so{m}c.txt"] = HEAD + pl_row("48", "Austin", 30) + pl_row("48", "Dallas", 40) + \
            pl_row("48", "Harris County", 99) + pl_row("12", "Miami", 5)
        files[f"we{m}c.txt"] = HEAD + pl_row("06", "Fresno", 3)
        files[f"ne{m}c.txt"] = files[f"mw{m}c.txt"] = HEAD

    def fetch(url, name):
        return files["bps-state-index" if name.startswith("bps-state-index") else name]
    return fetch


def test_last_months_ignores_1999_and_keeps_latest_12():
    listing = "st9912c.txt st9911c.txt " + " ".join(f"st25{m:02d}c.txt" for m in range(1, 13)) + " st2601c.txt st2601y.txt"
    got = targets.last_months(listing, "st")
    assert len(got) == 12 and got[0] == "2502" and got[-1] == "2601"


def test_build_ranks_states_and_cities_skips_counties():
    t = targets.build(fixture_fetcher(), n_states=2, n_cities=10)
    assert [s["state"] for s in t["states"]] == ["TX", "FL"]
    tx = t["states"][0]
    assert tx["permits_5plus_12mo"] == 1200
    assert [c["city"] for c in tx["cities"]] == ["Dallas", "Austin"]   # county area skipped
    assert tx["cities"][0]["permits_5plus_12mo"] == 480
    assert t["window"] == "2025-08..2026-07"
    assert targets.flat(t)[:3] == [{"city": "Dallas", "state": "TX"}, {"city": "Austin", "state": "TX"},
                                   {"city": "Miami", "state": "FL"}]


def test_clean_city_drops_place_type_suffix():
    assert targets.clean_city("DeForest  village") == "DeForest"
    assert targets.clean_city("Brooklyn borough") == "Brooklyn"
    assert targets.clean_city("Salt Lake City") == "Salt Lake City"
