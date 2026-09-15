"""Offline: the saved cookie file is joined into a Cookie header (no network)."""
import importlib.util
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("reddit_search", ROOT / "tooling" / "reddit_search.py")
reddit_search = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reddit_search)


def test_dict_cookie_file(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(json.dumps({"a": "1", "b": "2", "skip": None}))
    assert reddit_search.cookie_from_json(path) == "a=1; b=2"


def test_browser_export_list(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(json.dumps([{"name": "a", "value": "1"}, {"name": "b", "value": ""}]))
    assert reddit_search.cookie_from_json(path) == "a=1"


def test_bad_file_gives_empty(tmp_path):
    path = tmp_path / "c.json"
    path.write_text("not json")
    assert reddit_search.cookie_from_json(path) == ""


def test_env_wins_over_files(monkeypatch):
    monkeypatch.setenv("ST_TEST_COOKIE", "x=y")
    assert reddit_search.load_cookie("ST_TEST_COOKIE") == "x=y"
