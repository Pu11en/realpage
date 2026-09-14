import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runfolder import (  # noqa: E402
    MAX_PROJECTS,
    MAX_SEARCHES,
    MIN_PROJECTS_TO_KEEP,
    RunCaps,
    RunFolder,
    pick_state,
)


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def test_pick_state_lowest_total_wins(tmp_path):
    targets = {
        "states": [
            {"state": "AA", "permits_5plus_12mo": 100},
            {"state": "BB", "permits_5plus_12mo": 200},
            {"state": "CC", "permits_5plus_12mo": 50},
        ]
    }
    counts = {"AA": {"total": 10}, "BB": {"total": 2}}
    targets_path = tmp_path / "targets.json"
    counts_path = tmp_path / "counts.json"
    write_json(targets_path, targets)
    write_json(counts_path, counts)

    result = pick_state(targets_path, counts_path)
    # CC has no entry in counts -> total 0, lowest -> picked first.
    assert result["state"] == "CC"
    assert result["backup_order"] == ["CC", "BB", "AA"]


def test_pick_state_missing_from_counts_is_zero(tmp_path):
    targets = {"states": [{"state": "AA", "permits_5plus_12mo": 5}]}
    counts = {}
    targets_path = tmp_path / "targets.json"
    counts_path = tmp_path / "counts.json"
    write_json(targets_path, targets)
    write_json(counts_path, counts)

    result = pick_state(targets_path, counts_path)
    assert result["state"] == "AA"


def test_pick_state_tie_more_permits_wins(tmp_path):
    targets = {
        "states": [
            {"state": "AA", "permits_5plus_12mo": 100},
            {"state": "BB", "permits_5plus_12mo": 300},
        ]
    }
    counts = {"AA": {"total": 5}, "BB": {"total": 5}}
    targets_path = tmp_path / "targets.json"
    counts_path = tmp_path / "counts.json"
    write_json(targets_path, targets)
    write_json(counts_path, counts)

    result = pick_state(targets_path, counts_path)
    assert result["state"] == "BB"


def test_run_folder_resume_skips_finished_step(tmp_path):
    rf = RunFolder(state="ZZ", run_id="run1", runs_dir=tmp_path)
    assert not rf.step_done("permits", "Sample City")
    rf.save_step("permits", "Sample City", {"ok": True})
    assert rf.step_done("permits", "Sample City")
    assert rf.load_step("permits", "Sample City") == {"ok": True}


def test_run_folder_one_file_per_step_per_city(tmp_path):
    rf = RunFolder(state="ZZ", run_id="run1", runs_dir=tmp_path)
    rf.save_step("permits", "City One", {"n": 1})
    rf.save_step("permits", "City Two", {"n": 2})
    assert rf.load_step("permits", "City One") == {"n": 1}
    assert rf.load_step("permits", "City Two") == {"n": 2}
    assert rf.step_file("permits", "City One") != rf.step_file("permits", "City Two")


def test_run_folder_state_pick_and_caps_round_trip(tmp_path):
    rf = RunFolder(state="ZZ", run_id="run1", runs_dir=tmp_path)
    pick = {"state": "ZZ", "backup_order": ["ZZ", "YY"]}
    rf.save_state_pick(pick)
    saved = json.loads((rf.path / "state-pick.json").read_text())
    assert saved == pick

    caps = RunCaps(project_count=10, jina_searches=20, brave_searches=5)
    rf.save_caps(caps)
    loaded = rf.load_caps()
    assert loaded.project_count == 10
    assert loaded.total_searches == 25


def test_caps_project_cap_hit():
    caps = RunCaps(project_count=MAX_PROJECTS)
    assert caps.project_cap_hit()
    assert caps.any_cap_hit()


def test_caps_search_cap_hit():
    caps = RunCaps(jina_searches=MAX_SEARCHES)
    assert caps.search_cap_hit()
    assert caps.any_cap_hit()


def test_caps_below_minimum_rolls_into_next_state():
    caps = RunCaps(project_count=MIN_PROJECTS_TO_KEEP - 1)
    assert caps.below_minimum()

    caps2 = RunCaps(project_count=MIN_PROJECTS_TO_KEEP)
    assert not caps2.below_minimum()


def test_caps_under_limits_not_hit():
    caps = RunCaps(project_count=5, jina_searches=5, brave_searches=0)
    assert not caps.any_cap_hit()
