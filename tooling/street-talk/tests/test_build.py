"""Offline: Street Talk build (labels + saved tab data) on saved sample raw files."""
import csv
import importlib.util
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
RAW = HERE.parent / "fixtures" / "raw"
spec = importlib.util.spec_from_file_location("build", HERE.parent / "build.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


def data():
    return build.build(RAW, today="2026-09-15")


def test_newest_file_per_part_and_older_kept():
    d = data()
    assert d["sourceDates"] == {"rivals": "2026-09-08", "buildings": "2026-09-08", "unhappy": "2026-09-01"}
    assert d["updated"] == "2026-09-08"
    assert d["counts"] == {"rivals": 2, "buildings": 2, "unhappy": 2}


def test_dupes_and_undated_dropped_newest_first():
    rivals = data()["parts"]["rivals"]
    assert [p["date"] for p in rivals] == ["2026-09-01", "2026-08-01"]
    assert len({p["url"] for p in rivals}) == 2


def test_labels():
    d = data()
    angry, happy = d["parts"]["rivals"]
    assert angry["sentiment"] == "angry" and angry["companies"] == ["RealPage"] and angry["city"] == "Dallas"
    assert happy["sentiment"] == "happy" and happy["companies"] == ["Yardi", "AppFolio"]
    assert happy["city"] == "Houston"
    park = d["parts"]["buildings"][0]
    assert park["buildingId"] == "tx-1" and park["city"] == "Houston" and park["sentiment"] == "angry"
    assert d["parts"]["buildings"][1]["source"] == "youtube"


def test_warm_lead_manager_not_renter():
    manager, renter = data()["parts"]["unhappy"]
    assert manager["warmLead"] is True and manager["city"] == "Austin"
    assert renter["warmLead"] is False
    assert data()["warmLeads"] == 1


def test_sentiment_words():
    assert build.sentiment("I hate it, awful") == "angry"
    assert build.sentiment("love it, great") == "happy"
    assert build.sentiment("love it but hate the fees") == "mixed"
    assert build.sentiment("switched last week") == "neutral"


def test_totals():
    t = data()["totals"]
    assert t["RealPage"] == {"posts": 1, "angryPct": 100, "happyPct": 0, "mixedPct": 0, "neutralPct": 0}
    assert t["AppFolio"]["posts"] == 2 and t["Entrata"]["posts"] == 1


def test_write_json_and_csv(tmp_path):
    build.write(data(), tmp_path / "st.json", tmp_path / "st.csv")
    rows = list(csv.DictReader((tmp_path / "st.csv").open()))
    assert len(rows) == 6 and all(r["url"].startswith("https://www.") for r in rows)
    assert {r["warm_lead"] for r in rows} == {"yes", ""}
