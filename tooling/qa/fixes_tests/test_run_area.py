import json
import sys
import threading
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tooling"))

import run_area  # noqa: E402


def _make_state(tmp_path: Path, state: str = "zz", count: int = 8) -> Path:
    recipe_dir = tmp_path / "propertystack" / "recipes" / state
    recipe_dir.mkdir(parents=True)
    for number in range(count):
        (recipe_dir / f"source-{number}.json").write_text(
            json.dumps({"system": "fake", "city": f"City {number}"})
        )
    data_dir = tmp_path / "propertystack" / "data" / state
    data_dir.mkdir(parents=True)
    (data_dir / "leads.json").write_text(
        json.dumps(
            [
                {
                    "area": state,
                    "city": "Old City",
                    "name": "Old Apartments",
                    "address": "1 Old St",
                    "stage": "sold",
                }
            ]
        )
    )
    return recipe_dir


def _lead(recipe: Path, state: str) -> dict:
    number = recipe.stem.rsplit("-", 1)[-1]
    return {
        "area": state,
        "city": f"City {number}",
        "name": f"Building {number}",
        "address": f"{number} Main St",
        "stage": "sold" if number == "0" else "permitted",
        "sale_date": "2026-09-01" if number == "0" else "",
        "permit_date": "" if number == "0" else "2026-09-01",
        "sources": [{"fact": "record", "url": f"https://example.test/{number}"}],
    }


def test_runs_at_most_six_sources_in_parallel_and_writes_summary(tmp_path):
    _make_state(tmp_path)
    lock = threading.Lock()
    active = 0
    peak = 0

    def fake_runner(recipe, state):
        nonlocal active, peak
        with lock:
            active += 1
            peak = max(peak, active)
        time.sleep(0.02)
        with lock:
            active -= 1
        return [_lead(recipe, state)]

    summary = run_area.run_state(
        "zz", root=tmp_path, run_date="2026-09-19", source_runner=fake_runner
    )

    assert peak == 6
    assert summary == {
        "state": "zz",
        "total": 8,
        "new": 8,
        "permits": 7,
        "sales": 1,
        "worked": 8,
        "empty": 0,
        "failed": 0,
    }
    assert len(json.loads((tmp_path / "propertystack/data/zz/leads.json").read_text())) == 8
    assert json.loads(
        (tmp_path / "propertystack/data/zz/leads.before-run.json").read_text()
    )[0]["name"] == "Old Apartments"


def test_whitespace_only_name_change_is_not_counted_as_new(tmp_path):
    recipe_dir = _make_state(tmp_path, count=1)
    data_path = tmp_path / "propertystack/data/zz/leads.json"
    previous = _lead(recipe_dir / "source-0.json", "zz")
    previous["name"] = "Station 121 At Town Center Apts"
    data_path.write_text(json.dumps([previous]))

    def whitespace_changed_runner(recipe, state):
        lead = _lead(recipe, state)
        lead["name"] = "Station 121  At Town Center Apts"
        return [lead]

    summary = run_area.run_state(
        "zz",
        root=tmp_path,
        run_date="2026-09-19",
        source_runner=whitespace_changed_runner,
    )

    assert summary["total"] == 1
    assert summary["new"] == 0


def test_retries_once_reports_failure_and_resumes_finished_sources(tmp_path, capsys):
    _make_state(tmp_path, count=3)
    calls = {}

    def flaky_runner(recipe, state):
        calls[recipe.name] = calls.get(recipe.name, 0) + 1
        if recipe.name == "source-0.json" and calls[recipe.name] == 1:
            raise OSError("temporary outage")
        if recipe.name == "source-1.json":
            raise OSError("still down")
        return [_lead(recipe, state)]

    first = run_area.run_state(
        "zz", root=tmp_path, run_date="2026-09-19", source_runner=flaky_runner
    )
    assert calls == {"source-0.json": 2, "source-1.json": 2, "source-2.json": 1}
    assert first["worked"] == 2
    assert first["failed"] == 1
    assert "source failed twice" in capsys.readouterr().out

    second = run_area.run_state(
        "zz", root=tmp_path, run_date="2026-09-19", source_runner=flaky_runner
    )
    assert calls == {"source-0.json": 2, "source-1.json": 4, "source-2.json": 1}
    assert second["worked"] == 2
    assert second["failed"] == 1
    assert second["new"] == 2  # still compared with this run's original backup
    assert "already finished today" in capsys.readouterr().out

    health = json.loads(
        (tmp_path / "propertystack/runs/source-health.json").read_text()
    )["sources"]
    assert health["zz/source-0.json"]["status"] == "worked"
    assert health["zz/source-1.json"]["status"] == "failed"


def test_empty_source_is_finished_and_dry_run_never_calls_source(tmp_path):
    _make_state(tmp_path, count=1)
    calls = 0

    def empty_runner(recipe, state):
        nonlocal calls
        calls += 1
        return []

    first = run_area.run_state(
        "zz", root=tmp_path, run_date="2026-09-19", source_runner=empty_runner
    )
    second = run_area.run_state(
        "zz", root=tmp_path, run_date="2026-09-19", source_runner=empty_runner
    )
    assert first["empty"] == second["empty"] == 1
    assert calls == 1

    untouched = tmp_path / "dry"
    _make_state(untouched, count=1)
    before = (untouched / "propertystack/data/zz/leads.json").read_text()
    result = run_area.run_state(
        "zz", root=untouched, run_date="2026-09-19", dry_run=True, source_runner=empty_runner
    )
    assert result["dry_run"] is True
    assert calls == 1
    assert (untouched / "propertystack/data/zz/leads.json").read_text() == before
    assert not (untouched / "propertystack/runs").exists()


def test_disabled_source_is_skipped_without_retry_and_records_reason(tmp_path, capsys):
    recipe_dir = _make_state(tmp_path, count=1)
    recipe_path = recipe_dir / "source-0.json"
    recipe_path.write_text(
        json.dumps(
            {
                "system": "unavailable",
                "enabled": False,
                "reason": "no machine-readable event feed",
            }
        )
    )

    def should_not_run(_recipe, _state):
        raise AssertionError("a disabled source must never be fetched")

    summary = run_area.run_state(
        "zz", root=tmp_path, run_date="2026-09-19", source_runner=should_not_run
    )

    assert summary["empty"] == 1
    assert summary["failed"] == 0
    assert "disabled: no machine-readable event feed" in capsys.readouterr().out
    artifact = json.loads(
        (
            tmp_path
            / "propertystack/runs/area/2026-09-19/zz/sources/source-0.json"
        ).read_text()
    )
    assert artifact["attempts"] == 0
    assert artifact["note"] == "disabled: no machine-readable event feed"


def test_auto_found_structured_recipe_runs_through_normal_permit_adapter(
    tmp_path, monkeypatch
):
    recipe_path = tmp_path / "auto-found.json"
    recipe_path.write_text(
        json.dumps(
            {
                "city": "Exampleville",
                "state": "ZZ",
                "system": "open-data",
                "endpoint": "https://data.example.test/permits.json",
                "source": "auto-found",
                "fields": {
                    "address": "address",
                    "issue_date": "issued",
                    "units": "units",
                    "permit_type": "description",
                    "name": "description",
                },
            }
        )
    )
    monkeypatch.setattr(
        run_area,
        "_http_get_structured",
        lambda _url: [
            {
                "address": "100 Main St",
                "issued": "2026-09-01",
                "units": 40,
                "description": "New apartment building",
            }
        ],
    )

    rows = run_area.run_recipe(recipe_path, "zz")

    assert len(rows) == 1
    assert rows[0]["address"] == "100 Main St"
    assert rows[0]["sources"][0]["url"] == "https://data.example.test/permits.json"


def _stale_recipe(tmp_path: Path) -> Path:
    recipe_dir = tmp_path / "propertystack" / "recipes" / "zz"
    recipe_dir.mkdir(parents=True)
    recipe_path = recipe_dir / "stale-city.json"
    recipe_path.write_text(
        json.dumps(
            {
                "city": "Stale City",
                "state": "ZZ",
                "system": "arcgis",
                "endpoint": "https://gis.example.test/permits.json",
                "fields": {
                    "address": "address",
                    "issue_date": "issued",
                    "units": "units",
                    "permit_type": "description",
                    "name": "description",
                },
            }
        )
    )
    return recipe_path


def test_a_city_that_stopped_publishing_says_so_instead_of_looking_broken(
    tmp_path, monkeypatch
):
    # A feed frozen years ago returns plenty of apartment rows that are all
    # older than the freshness window.  Without a reason recorded, that empty
    # result reads exactly like a broken fetch -- which is how the New Mexico
    # run was misread as a runner bug.
    recipe_path = _stale_recipe(tmp_path)
    monkeypatch.setattr(
        run_area,
        "_http_get_structured",
        lambda _url: [
            {
                "address": f"{number} Old St",
                "issued": "2019-04-02",
                "units": 60,
                "description": "New apartment building",
            }
            for number in range(3)
        ],
    )

    stats: dict = {}
    rows = run_area.run_recipe(recipe_path, "zz", stats)

    assert rows == []
    assert stats["apartmentRows"] == 3
    assert stats["newestDate"] == "2019-04-02"

    note = run_area._empty_note(stats)
    assert "stale source" in note
    assert "2019-04-02" in note


def test_stale_reason_reaches_the_run_log_and_source_health(tmp_path, capsys):
    _stale_recipe(tmp_path)

    def stale_runner(_recipe, _state, stats):
        stats.update(
            {
                "rows": 400,
                "apartmentRows": 236,
                "agedOut": 236,
                "newestDate": "2024-09-19",
                "newestAgeDays": 731,
                "kept": 0,
            }
        )
        return []

    summary = run_area.run_state(
        "zz", root=tmp_path, run_date="2026-09-20", source_runner=stale_runner
    )

    assert summary["empty"] == 1
    assert "stale source" in capsys.readouterr().out
    health = json.loads(
        (tmp_path / "propertystack/runs/source-health.json").read_text()
    )
    assert "stale source" in health["sources"]["zz/stale-city.json"]["note"]
