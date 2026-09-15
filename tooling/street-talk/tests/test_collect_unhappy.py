"""Offline: part 3 collector on saved sample files (never calls Reddit)."""
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
SEARCH = json.loads((FIX / "unhappy-search.json").read_text())
THREAD = json.loads((FIX / "rivals-thread.json").read_text())


def fake_fetch(url):
    assert url.startswith("https://www.reddit.com/")
    return THREAD if "/comments/" in url else SEARCH


def run(budget=30):
    reddit = collect.Reddit("x=y", budget, fetch=fake_fetch, sleep=lambda s: None)
    return reddit, collect.collect_unhappy(reddit, NOW)


def test_keeps_unhappy_texas_rival_customers():
    reddit, result = run()
    titles = {p["title"] for p in result["posts"]}
    assert titles == {"Switching off Yardi, any alternative?", "Entrata support nightmare"}
    dropped = result["dropped"]
    assert dropped["no complaint words"] >= 1          # AppFolio is great
    assert dropped["no Texas mention"] >= 1            # Hate Yardi (no Texas)
    assert dropped["names none of Yardi / Entrata / AppFolio"] >= 1  # RealPage only
    assert dropped["older than 24 months"] >= 1
    assert dropped["duplicate link"] >= 1 and dropped["job ad"] >= 1
    yardi = next(p for p in result["posts"] if "Yardi" in p["title"])
    assert yardi["companies"] == ["Yardi"] and yardi["part"] == "unhappy"
    assert yardi["comments"] == ["Same at my place in Frisco.", "Blame the algorithm."]
    # every search + one comment thread per kept post
    assert reddit.used == len(collect.unhappy_searches()) + 2


def test_searches_use_complaint_and_texas_words():
    searches = collect.unhappy_searches()
    assert any("switching" in q and "alternative" in q for q, _ in searches)
    assert any("Dallas" in q for q, _ in searches)
    assert {s for _, s in searches if s} >= set(collect.PM_SUBS)
    assert all("realpage" not in q for q, _ in searches)


def test_budget_cap_and_block(tmp_path, monkeypatch):
    reddit, _ = run(budget=4)
    assert reddit.used == 4

    def blocking(url):
        raise collect.Blocked("HTTP 403")

    reddit = collect.Reddit("x", 30, fetch=blocking, sleep=lambda s: None)
    result = collect.collect_unhappy(reddit, NOW)
    assert result["blocked"] == "HTTP 403" and result["posts"] == []
    monkeypatch.setattr(collect, "RAW_DIR", tmp_path)
    collect.save(run()[1], "2026-09-15")
    assert "5 sample posts" in (tmp_path / "2026-09-15" / "unhappy-report.md").read_text()
