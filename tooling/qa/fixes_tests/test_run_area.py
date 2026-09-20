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
        "suspect": 0,
        "stale": 0,
        "incomplete": 0,
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


def test_a_county_link_holding_a_windows_path_is_encoded_not_dropped():
    # Dallas publishes its bulk-file link with a literal Windows path as the
    # query value. http.client rejects the raw backslashes and space as control
    # characters, so the county failed on every run and silently contributed
    # nothing -- an entire metro missing from the data.
    dallas = (
        "https://www.dallascad.org/ViewPDFs.aspx?type=3&id="
        "\\\\DCAD.ORG\\WEB\\WEBDATA\\WEBFORMS\\DATA PRODUCTS\\DCAD2026_CURRENT.ZIP"
    )

    encoded = run_area._safe_url(dallas)

    assert " " not in encoded and "\\" not in encoded
    assert encoded.startswith("https://www.dallascad.org/ViewPDFs.aspx?type=3&id=")
    assert "%5C%5CDCAD.ORG" in encoded
    assert "DATA%20PRODUCTS" in encoded


def test_a_url_that_already_works_is_passed_through_byte_for_byte():
    plain = "https://download.hcad.org/data/CAMA/2026/Real_acct_owner.zip"
    already_encoded = (
        "https://gis.example.org/rest/services/x/FeatureServer/0/query"
        "?where=Type%20IN%20(%27APT%27)&outFields=*&f=json"
    )

    assert run_area._safe_url(plain) == plain
    assert run_area._safe_url(already_encoded) == already_encoded


# --- the under-read and staleness alarm -------------------------------------
#
# Every case below uses numbers taken from a real run, so the alarm is tested
# against the failures that actually happened rather than invented ones.


def test_a_measured_source_records_what_its_endpoint_held():
    signal = run_area._source_signal(
        {"rows": 900, "apartmentRows": 120, "agedOut": 4, "newestDate": "2026-09-17",
         "newestAgeDays": 3},
        kept=95,
    )

    assert signal["measured"] is True
    assert signal["endpointRows"] == 900
    assert signal["apartmentRows"] == 120
    assert signal["kept"] == 95
    assert signal["flags"] == []
    assert signal["note"] == ""


def test_fort_worths_real_numbers_are_flagged_suspect():
    # Fort Worth's own recipe records a live returnCountOnly of 2,227 matching
    # rows since 2024-09-01.  The 2026-09-20 run kept one lead.
    signal = run_area._source_signal(
        {"rows": 2227, "apartmentRows": 2227, "agedOut": 0,
         "newestDate": "2026-09-15", "newestAgeDays": 5},
        kept=1,
    )

    assert signal["flags"] == ["suspect"]
    assert "2227 apartment rows" in signal["note"]
    assert "only 1 became leads" in signal["note"]


def test_a_frozen_feed_reads_as_stale_not_suspect():
    # Albuquerque: 191 apartment rows, newest permit 2024-09-19, 731 days old.
    # Nothing is being under-read -- the whole feed simply stopped.
    signal = run_area._source_signal(
        {"rows": 5000, "apartmentRows": 191, "agedOut": 191,
         "newestDate": "2024-09-19", "newestAgeDays": 731},
        kept=0,
    )

    assert signal["flags"] == ["stale"]
    assert "2024-09-19" in signal["note"] and "731 days old" in signal["note"]


def test_a_genuinely_small_source_is_not_accused():
    signal = run_area._source_signal(
        {"rows": 40, "apartmentRows": 3, "agedOut": 0,
         "newestDate": "2026-09-01", "newestAgeDays": 19},
        kept=1,
    )

    assert signal["flags"] == []


def test_a_source_that_cannot_be_counted_says_so_instead_of_guessing():
    signal = run_area._source_signal({}, kept=481)

    assert signal["measured"] is False
    assert "does not report" in signal["why"]
    assert "endpointRows" not in signal


def test_a_suspect_source_is_named_in_the_run_and_never_stops_it(tmp_path, capsys):
    _make_state(tmp_path, count=2)

    def fake_runner(recipe, state, stats):
        if recipe.stem == "source-0":
            stats.update({"rows": 2227, "apartmentRows": 2227, "agedOut": 0,
                          "newestDate": "2026-09-15", "newestAgeDays": 5})
            return [_lead(recipe, state)]
        stats.update({"rows": 90, "apartmentRows": 4, "agedOut": 0,
                      "newestDate": "2026-09-15", "newestAgeDays": 5})
        return [_lead(recipe, state)]

    summary = run_area.run_state(
        "zz", root=tmp_path, run_date="2026-09-20", source_runner=fake_runner
    )

    assert summary["suspect"] == 1
    assert summary["stale"] == 0
    assert summary["total"] == 2  # the run finished with both sources' leads
    printed = capsys.readouterr().out
    assert "*** SUSPECT *** source-0.json" in printed

    health = json.loads(
        (tmp_path / "propertystack" / "runs" / "source-health.json").read_text()
    )
    assert health["sources"]["zz/source-0.json"]["signal"]["flags"] == ["suspect"]
    assert health["sources"]["zz/source-1.json"]["signal"]["flags"] == []


def test_a_healthy_run_says_so_out_loud(tmp_path, capsys):
    _make_state(tmp_path, count=1)

    def fake_runner(recipe, state, stats):
        stats.update({"rows": 90, "apartmentRows": 4, "agedOut": 0,
                      "newestDate": "2026-09-15", "newestAgeDays": 5})
        return [_lead(recipe, state)]

    run_area.run_state(
        "zz", root=tmp_path, run_date="2026-09-20", source_runner=fake_runner
    )

    assert "every measured source returned its fair share" in capsys.readouterr().out


def test_many_permits_at_one_address_is_not_an_under_read():
    # A healthy real source: 640 apartment rows, 377 of them usable permits,
    # merged down to 126 buildings because one project files a permit per
    # building.  Judging 126 against 640 would call this broken; judging the
    # 377 that survived the quality filters does not.
    signal = run_area._source_signal(
        {"rows": 2227, "apartmentRows": 640, "agedOut": 45,
         "placeholderAddress": 218, "junkDropped": 0, "built": 377,
         "mergedAway": 251, "newestDate": "2026-08-25", "newestAgeDays": 26},
        kept=126,
    )

    assert signal["flags"] == []
    assert signal["note"] == ""
    assert signal["built"] == 377
    assert signal["mergedAway"] == 251
    assert signal["placeholderAddress"] == 218


def test_a_suspect_source_names_where_its_rows_went():
    signal = run_area._source_signal(
        {"rows": 900, "apartmentRows": 400, "agedOut": 30,
         "placeholderAddress": 350, "junkDropped": 5, "built": 15,
         "mergedAway": 3, "newestDate": "2026-09-15", "newestAgeDays": 5},
        kept=12,
    )

    assert signal["flags"] == ["suspect"]
    assert "30 too old" in signal["note"]
    assert "350 with a stand-in address" in signal["note"]
    assert "5 not a new building" in signal["note"]
    assert "3 merged into another project" in signal["note"]
