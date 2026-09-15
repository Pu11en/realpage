"""Offline: Street Talk weekly refresh (script shape + a blocked run keeps last week's posts)."""
import importlib.util
import json
import pathlib
import re
import subprocess

HERE = pathlib.Path(__file__).resolve().parent
WEEKLY = HERE.parent / "weekly.sh"
spec = importlib.util.spec_from_file_location("build", HERE.parent / "build.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


def test_script_parses_and_stays_under_the_reddit_cap():
    subprocess.run(["bash", "-n", str(WEEKLY)], check=True)
    text = WEEKLY.read_text()
    budgets = [int(b) for b in re.findall(r"\b(?:rivals|buildings|unhappy):(\d+)", text)]
    assert len(budgets) == 3 and sum(budgets) <= 80
    assert "git push" not in text and "blocked.json" in text


def post(url, date="2026-09-01"):
    return {"url": url, "date": date, "title": "RealPage in Dallas", "excerpt": "Our Dallas complex uses RealPage.", "companies": ["RealPage"]}


def test_blocked_run_keeps_last_week_and_is_reported(tmp_path):
    old, new = tmp_path / "2026-09-08", tmp_path / "2026-09-15"
    old.mkdir(), new.mkdir()
    (old / "rivals.json").write_text(json.dumps({"posts": [post("https://www.reddit.com/r/x/1")]}))
    (new / "rivals.blocked.json").write_text(json.dumps({"posts": [], "blocked": "HTTP 429"}))
    (new / "unhappy.json").write_text(json.dumps({"posts": []}))
    d = build.build(tmp_path, today="2026-09-15")
    assert d["sourceDates"]["rivals"] == "2026-09-08" and d["counts"]["rivals"] == 1
    assert d["failedRuns"] == {"rivals": "2026-09-15"}


def test_later_good_run_clears_the_warning(tmp_path):
    (tmp_path / "2026-09-08").mkdir()
    (tmp_path / "2026-09-08" / "rivals.blocked.json").write_text("{}")
    (tmp_path / "2026-09-15").mkdir()
    (tmp_path / "2026-09-15" / "rivals.json").write_text(json.dumps({"posts": []}))
    assert build.build(tmp_path)["failedRuns"] == {}
