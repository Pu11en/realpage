"""Offline: part 2 (Texas buildings) collector on saved sample files (never calls Reddit or YouTube)."""
import datetime as dt
import importlib.util
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
FIX = HERE.parent / "fixtures"
spec = importlib.util.spec_from_file_location("collect", HERE.parent / "collect.py")
collect = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collect)

NOW = dt.datetime.fromtimestamp(1788000000, dt.timezone.utc)
SEARCH = json.loads((FIX / "buildings-search.json").read_text())
THREAD = json.loads((FIX / "rivals-thread.json").read_text())
YT = (FIX / "buildings-youtube.json").read_text()
VTT = """WEBVTT
Kind: captions

00:00:01.000 --> 00:00:03.000
welcome to <c>Station 121 at Town Center</c>

00:00:03.000 --> 00:00:05.000
the pool is huge
"""


def fake_yt(args, workdir=None):
    if any(a.startswith("ytsearch") for a in args):
        return YT
    pathlib.Path(workdir, "v.en.vtt").write_text(VTT)
    return json.dumps({"upload_date": "20260301"}) + "\n"


def run(buildings=None, budget=60):
    fetched = []

    def fetch(url):
        assert url.startswith("https://www.reddit.com/")
        fetched.append(url)
        return THREAD if "/comments/" in url else SEARCH

    reddit = collect.Reddit("x=y", budget, fetch=fetch, sleep=lambda s: None)
    yt = collect.YouTube(run=fake_yt, sleep=lambda s: None)
    buildings = buildings or collect.texas_buildings(FIX / "areas")
    return reddit, collect.collect_buildings(reddit, NOW, buildings, yt), fetched


def test_picks_texas_buildings_by_size_skipping_addresses_and_dupes():
    picked = collect.texas_buildings(FIX / "areas", top=40)
    assert [b["id"] for b in picked] == ["tx-3", "tx-1", "tx-6"]
    assert picked[1]["core"] == "Station 121 At Town Center"
    assert collect.texas_buildings(FIX / "areas", top=1)[0]["id"] == "tx-3"


def test_keeps_only_posts_that_name_the_building():
    reddit, result, _ = run()
    by_building = {}
    for p in result["posts"]:
        by_building.setdefault(p["buildingId"], []).append(p)
    station = by_building["tx-1"]
    assert {p["source"] for p in station} == {"reddit", "youtube"}
    red = next(p for p in station if p["source"] == "reddit")
    assert red["comments"] == ["Same at my place in Frisco.", "Blame the algorithm."]
    video = next(p for p in station if p["source"] == "youtube")
    assert video["date"] == "2026-03-01" and "Station 121 at Town Center" in video["excerpt"]
    # 'Oak Park' is a short, common name: only the post that also says Euless counts.
    assert [p["title"] for p in by_building["tx-3"]] == ["Oak Park in Euless is loud"]
    assert collect.names_building("Oak Park in Euless, great bbq", {"core": "Oak Park", "city": "Euless"}) is False
    urls = [p["url"] for p in result["posts"]]
    assert len(urls) == len(set(urls))
    assert all(p["part"] == "buildings" and p["date"] for p in result["posts"])
    assert result["dropped"]["does not name the building"] >= 1
    assert result["dropped"]["job ad"] >= 1
    assert result["dropped"]["duplicate link"] >= 1


def test_block_stops_reddit_but_keeps_saved():
    calls = []

    def blocking(url):
        calls.append(url)
        if len(calls) > 1:
            raise collect.Blocked("HTTP 429")
        return SEARCH

    reddit = collect.Reddit("x", 60, fetch=blocking, sleep=lambda s: None)
    yt = collect.YouTube(run=fake_yt, sleep=lambda s: None)
    result = collect.collect_buildings(reddit, NOW, collect.texas_buildings(FIX / "areas"), yt)
    assert result["blocked"] == "HTTP 429" and len(calls) == 2
    assert any(p["source"] == "reddit" for p in result["posts"])


def test_budget_cap_and_report(tmp_path, monkeypatch):
    reddit, _, fetched = run(budget=2)
    assert reddit.used == len(fetched) == 2
    monkeypatch.setattr(collect, "RAW_DIR", tmp_path)
    _, result, _ = run()
    collect.save(result, "2026-09-15")
    report = (tmp_path / "2026-09-15" / "buildings-report.md").read_text()
    assert "Buildings searched: 3" in report and "5 sample posts" in report


def test_vtt_text_collapses_captions():
    assert collect.vtt_text(VTT) == "welcome to Station 121 at Town Center the pool is huge"
