"""lead-finder-cities (2.1) tests: small inline Census fixtures, no network."""
import json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import rank  # noqa: E402


def pl_row(fips, name, units):
    return (f"202601,{fips},000100,001,0001,00100 ,00000 ,1000 ,1,19100, , ,75001 ,3,7,5,"
            f"{name},1,1,1,0,0,0,0,0,0,2,{units},9\n")


HEAD = "Survey,FIPS\nDate,State\n \n"


def fixture_fetcher():
    months = [f"25{m:02d}" for m in range(8, 13)] + [f"26{m:02d}" for m in range(1, 8)]
    listing = " ".join(f"st{m}c.txt" for m in months)
    files = {"bps-state-index": listing}
    for m in months:
        files[f"so{m}c.txt"] = HEAD + pl_row("48", "Rivertown", 30) + pl_row("48", "Cedarville", 40) + \
            pl_row("48", "Oakford County (unincorporated area)", 12) + pl_row("12", "Bayshore", 5)
        files[f"we{m}c.txt"] = files[f"ne{m}c.txt"] = files[f"mw{m}c.txt"] = HEAD

    def fetch(url, name):
        return files["bps-state-index" if name.startswith("bps-state-index") else name]
    return fetch


def test_rank_cities_keeps_county_areas_and_sorts():
    out = rank.rank_cities("TX", fixture_fetcher())
    assert out["state"] == "TX"
    assert out["window"] == "2025-08..2026-07"
    cities = out["cities"]
    assert [c["city"] for c in cities] == ["Cedarville", "Rivertown", "Oakford County (unincorporated area)"]
    assert cities[0]["permits_5plus"] == 480          # 40 * 12 months
    assert cities[2]["is_county_area"] is True
    assert all(not c["is_county_area"] for c in cities[:2])
    assert "Bayshore" not in [c["city"] for c in cities]  # other state filtered out


def test_realpage_counts_reads_client_map(tmp_path):
    counts = tmp_path / "counts.json"
    counts.write_text(json.dumps({"TX": {"total": 3, "cities": {"Cedarville": 3}}}))
    assert rank.realpage_counts("TX", counts) == {"Cedarville": 3}
    assert rank.realpage_counts("ZZ", counts) == {}


def test_realpage_counts_missing_file_returns_empty(tmp_path):
    assert rank.realpage_counts("TX", tmp_path / "missing.json") == {}


def test_build_writes_state_slug_file(tmp_path, monkeypatch):
    monkeypatch.setattr(rank, "DATA", tmp_path)
    out, path = rank.build("TX", fixture_fetcher())
    assert path == tmp_path / "tx" / "cities.json"
    assert json.loads(path.read_text())["state"] == "TX"
    assert out["cities"][0]["city"] == "Cedarville"
