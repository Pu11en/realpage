"""Offline: part 1 collector on saved sample files (never calls Reddit)."""
import datetime as dt
import importlib.util
import json
import pathlib

import pytest

HERE = pathlib.Path(__file__).resolve().parent
FIX = HERE.parent / "fixtures"
spec = importlib.util.spec_from_file_location("collect", HERE.parent / "collect.py")
collect = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collect)

NOW = dt.datetime.fromtimestamp(1788000000, dt.timezone.utc)
SEARCH = json.loads((FIX / "rivals-search.json").read_text())
THREAD = json.loads((FIX / "rivals-thread.json").read_text())


def fake_fetch(url):
    assert url.startswith("https://www.reddit.com/")
    return THREAD if "/comments/" in url else SEARCH


def run(budget=30):
    reddit = collect.Reddit("x=y", budget, fetch=fake_fetch, sleep=lambda s: None)
    return reddit, collect.collect_rivals(reddit, NOW)


def test_keeps_texas_company_posts_and_dedupes():
    reddit, result = run()
    urls = [p["url"] for p in result["posts"]]
    assert len(urls) == len(set(urls)) == 2
    assert {p["title"] for p in result["posts"]} == {
        "RealPage raised our rent in Dallas", "Yardi vs Entrata for a Houston portfolio"}
    assert result["dropped"]["older than 12 months"] >= 1
    assert result["dropped"]["no Texas mention"] >= 1
    assert result["dropped"]["names none of the four companies"] >= 1
    assert result["dropped"]["duplicate link"] >= 1
    first = next(p for p in result["posts"] if p["title"].startswith("RealPage"))
    assert first["companies"] == ["RealPage"]
    assert first["comments"] == ["Same at my place in Frisco.", "Blame the algorithm."]
    assert first["date"] and first["part"] == "rivals"
    # 11 searches + 1 comment thread (only one kept post has comments).
    assert reddit.used == len(collect.rivals_searches()) + 1


def test_budget_is_a_hard_cap():
    reddit, _ = run(budget=3)
    assert reddit.used == 3
    assert collect.Reddit("x", 500).budget == collect.MAX_REQUESTS


def test_block_stops_and_keeps_saved():
    calls = []

    def blocking(url):
        calls.append(url)
        if len(calls) > 1:
            raise collect.Blocked("HTTP 429")
        return SEARCH

    reddit = collect.Reddit("x", 30, fetch=blocking, sleep=lambda s: None)
    result = collect.collect_rivals(reddit, NOW)
    assert result["blocked"] == "HTTP 429"
    assert len(calls) == 2 and len(result["posts"]) == 2


def test_rate_limit_waits_between_requests():
    waits = []
    reddit = collect.Reddit("x", 5, fetch=lambda u: {}, sleep=waits.append)
    reddit.get("https://www.reddit.com/a")
    reddit.get("https://www.reddit.com/b")
    assert waits and waits[0] == pytest.approx(3.0, abs=0.2)


def test_report_and_save(tmp_path, monkeypatch):
    monkeypatch.setattr(collect, "RAW_DIR", tmp_path)
    _, result = run()
    path = collect.save(result, "2026-09-15")
    assert json.loads(path.read_text())["posts"]
    report = (tmp_path / "2026-09-15" / "rivals-report.md").read_text()
    assert "Reddit requests used" in report and "5 sample posts" in report
