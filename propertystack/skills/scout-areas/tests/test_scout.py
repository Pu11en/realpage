"""Scout skeleton tests: saved fixtures only, no network."""
import csv, json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import run  # noqa: E402

FIX = json.loads((HERE / "fixtures" / "metro_inputs.json").read_text())


def test_metros_csv_shape_and_no_dfw():
    rows = run.load_metros()
    assert 20 <= len(rows) <= 30
    slugs = {r["slug"] for r in rows}
    assert len(slugs) == len(rows)
    for r in rows:
        assert r["cbsa"].isdigit() and len(r["cbsa"]) == 5
        assert -125 < float(r["lon"]) < -65 and 24 < float(r["lat"]) < 50
        assert r["cbsa"] != "19100"  # Dallas-Fort Worth-Arlington
        assert not any(w in r["name"].lower() for w in ("dallas", "fort worth", "arlington", "plano"))
    assert {"tucson-az", "boise-id"} <= slugs


def test_scoring_math():
    t = run.score_metro(FIX["tucson-az"])
    # growth: 40*min(15/20,1)=30 + 20*min(160k/300k,1)=10.67 + 40*(1-0.2)=32 -> 72.67 -> 73
    assert t["growth"] == 73
    assert t["churn"] == 60           # 12/20
    assert t["pain"] == 57            # 60*(11/20)=33 + 40*(6/10)=24
    assert t["total"] == round((73 + 60 + 57) / 3)
    b = run.score_metro(FIX["boise-id"])
    assert b["growth"] == 55          # 40 (capped) + 6.67 + 8 -> 54.67
    assert b["churn"] == 10 and b["pain"] == 6
    for s in (t, b):
        assert all(0 <= s[k] <= 100 for k in ("growth", "churn", "pain", "total"))


def test_scoring_handles_missing_data():
    s = run.score_metro({})
    assert s == {"growth": 0, "churn": 0, "pain": 0, "total": 0}


def test_cap_stops_run_cleanly():
    calls = []

    def gather(metro, budget):
        for _ in range(3):
            budget.use()
            calls.append(metro["slug"])
        return FIX.get(metro["slug"], {})

    metros = [m for m in run.load_metros() if m["slug"] in ("tucson-az", "boise-id")]
    budget = run.SearchBudget(4)
    result = run.run_metros(metros, budget, gather)
    assert budget.used == 4
    assert result["stopped_by_cap"] is True
    assert [a["slug"] for a in result["areas"]] == [metros[0]["slug"]]
    assert result["unfinished"] == [metros[1]["slug"]]


def test_run_without_cap_hit():
    metros = [m for m in run.load_metros() if m["slug"] in ("tucson-az", "boise-id")]
    result = run.run_metros(metros, run.SearchBudget(100), lambda m, b: FIX[m["slug"]])
    assert result["stopped_by_cap"] is False and result["unfinished"] == []
    assert [a["slug"] for a in result["areas"]] == ["tucson-az", "boise-id"]  # ranked by total


def test_cards_render():
    metros = [m for m in run.load_metros() if m["slug"] in ("tucson-az", "boise-id")]
    result = run.run_metros(metros, run.SearchBudget(100), lambda m, b: FIX[m["slug"]])
    md = run.render_cards(result["areas"], top=5)
    assert md.startswith("# ")
    assert md.index("Tucson") < md.index("Boise")
    assert "Growth + weakness: 73" in md and "Churn: 60" in md and "Competitor pain: 57" in md
    assert "https://example.com/tucson-sale-1" in md
    assert "no evidence links yet" in md.lower()  # boise has none
