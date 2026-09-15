"""Offline: once the tab data is saved, check it is sound (skips until it exists)."""
import json
import pathlib

import pytest

SAVED = pathlib.Path(__file__).resolve().parents[3] / "site" / "data" / "street-talk.json"
COMPANIES = {"RealPage", "Yardi", "Entrata", "AppFolio"}


@pytest.mark.skipif(not SAVED.exists(), reason="site/data/street-talk.json not built yet")
def test_saved_posts_are_sound():
    data = json.loads(SAVED.read_text())
    posts = [p for rows in data["parts"].values() for p in rows]
    urls = [p["url"] for p in posts]
    assert len(urls) == len(set(urls)), "duplicate links"
    for p in posts:
        assert p["url"].startswith(("https://www.reddit.com/", "https://www.youtube.com/")), p["url"]
        assert p["date"] and p["part"] in {"rivals", "buildings", "unhappy"}
        if p["part"] in {"rivals", "unhappy"}:
            assert COMPANIES & set(p["companies"]), p["url"]
    assert set(data["totals"]) == COMPANIES
