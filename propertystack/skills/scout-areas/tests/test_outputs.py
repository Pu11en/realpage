"""S5 outputs: areas.json, cards with why-text, scout map markers, saved-data rebuild. No network."""
import csv, json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import run  # noqa: E402

FIX = json.loads((HERE / "fixtures" / "metro_inputs.json").read_text())


def _result():
    metros = [m for m in run.load_metros() if m["slug"] in ("tucson-az", "boise-id")]
    return run.run_metros(metros, run.SearchBudget(100), lambda m, b: FIX[m["slug"]])


def test_areas_json_numbers_and_links_only(tmp_path):
    path = run.write_areas(_result(), tmp_path)
    doc = json.loads(path.read_text())
    assert path.name == "areas.json" and doc["searches"] == 0 and doc["stopped_by_cap"] is False
    a = doc["areas"][0]
    assert a["slug"] == "tucson-az" and a["total"] == round((a["growth"] + a["churn"] + a["pain"]) / 3)
    assert {"lat", "lon", "inputs", "evidence"} <= set(a) and "why" not in a
    assert all(isinstance(u, str) and u.startswith("http") for u in a["evidence"])


def test_cards_use_why_file(tmp_path):
    res = _result()
    (tmp_path / "why.json").write_text(json.dumps({"tucson-az": "Line one.\nLine two.\nLine three."}))
    md = run.write_cards(res["areas"], tmp_path).read_text()
    assert "Line one." in md and "Line three." in md
    assert "(written in S5" not in md.split("## Boise")[0]


def test_scout_markers_replace_old_and_keep_reach(tmp_path):
    reach = tmp_path / "reach.json"
    reach.write_text(json.dumps([
        {"city": "Plano", "state": "TX", "lat": 33, "lon": -96.7, "signs": 3, "kind": "reach", "links": []},
        {"city": "Old", "state": "FL", "lat": 27, "lon": -82, "signs": 0, "kind": "scout", "links": []}]))
    run.update_reach(reach, _result()["areas"], top=5)
    d = json.loads(reach.read_text())
    assert [x["city"] for x in d if x["kind"] == "reach"] == ["Plano"]
    scouts = [x for x in d if x["kind"] == "scout"]
    assert [x["city"] for x in scouts] == ["Tucson", "Boise"]
    t = scouts[0]
    assert t["source"] == "scout" and "total" in t["note"].lower() and t["links"][0]["url"].startswith("http")


def test_update_reach_creates_file(tmp_path):
    reach = tmp_path / "reach.json"
    run.update_reach(reach, _result()["areas"], top=1)
    assert [x["city"] for x in json.loads(reach.read_text())] == ["Tucson"]


def test_gather_saved_uses_no_searches(tmp_path, monkeypatch):
    d = tmp_path / "tucson-az"
    d.mkdir()
    with open(d / "sample.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["url", "title", "vendor", "signal", "evidence"])
        w.writerow(["https://a.com/", "A", "Yardi", "portal", "https://a.securecafe.com/"])
        w.writerow(["https://b.com/", "B", "unknown", "", ""])
    (d / "evidence.json").write_text(json.dumps({"slug": "tucson-az", "churn": [
        {"url": "https://news.com/sale", "title": "sale", "date": "2026-01-01"}], "complaints": []}))
    monkeypatch.setitem(run._CENSUS, "tucson-az", {"permits_5plus_12mo": 1000, "renter_households": 150000,
                                                   "evidence": ["https://census.gov/bps"]})
    budget = run.SearchBudget(10)
    got = run.gather_saved({"slug": "tucson-az"}, budget, tmp_path)
    assert budget.used == 0
    assert got["sample"] == {"total": 2, "Yardi": 1, "unknown": 1}
    assert got["churn_items"] == 1 and got["complaints"] == 0
    assert "https://news.com/sale" in got["evidence"] and "https://a.securecafe.com/" in got["evidence"]
