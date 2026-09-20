"""T2: reject broken state lead snapshots before they are published."""

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location(
    "check_lead_data", ROOT / "tooling/qa/check_lead_data.py"
)
check_lead_data = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = check_lead_data
SPEC.loader.exec_module(check_lead_data)


def _lead(number: int) -> dict:
    return {
        "area": "zz",
        "name": f"Building {number}",
        "address": f"{number} Main Street",
        "sources": [{"fact": "permit_date", "url": f"https://example.test/{number}"}],
    }


def _write_raw(folder: Path, rows: list[dict]) -> Path:
    folder.mkdir(parents=True)
    (folder / "leads.json").write_text(json.dumps(rows))
    return folder


def _write_built(path: Path, rows: list[dict]) -> Path:
    built_rows = []
    for row in rows:
        built = dict(row)
        built["property"] = built.pop("name")
        built["id"] = check_lead_data.content_id(
            "zz", built.get("address", ""), built["property"]
        )
        built_rows.append(built)
    path.write_text(json.dumps({"leads": built_rows}))
    return path


def test_valid_state_folder_passes_all_four_checks(tmp_path):
    rows = [_lead(1), _lead(2)]
    folder = _write_raw(tmp_path / "zz", rows)
    previous = tmp_path / "previous.json"
    previous.write_text(json.dumps(rows))
    built = _write_built(tmp_path / "built.json", rows)

    result = check_lead_data.check_state(folder, previous=previous, built=built)

    assert result.lead_count == 2
    assert result.errors == []


def test_reports_every_problem_in_plain_english(tmp_path):
    current = [_lead(number) for number in range(1, 8)]
    current[0]["sources"] = []
    current[1]["address"] = "1 MAIN ST."
    folder = _write_raw(tmp_path / "zz", current)
    previous = tmp_path / "previous.json"
    previous.write_text(json.dumps([_lead(number) for number in range(1, 11)]))
    built = _write_built(tmp_path / "built.json", current)
    payload = json.loads(built.read_text())
    payload["leads"][2]["id"] = "zz-3-main-st-old-position-3"
    built.write_text(json.dumps(payload))

    result = check_lead_data.check_state(folder, previous=previous, built=built)
    message = "\n".join(result.errors)

    assert "no valid http(s) source URL" in message
    assert 'address "1 Main Street" appears more than once' in message
    assert "has unstable id" in message
    assert "30.0% lost" in message


def test_exactly_twenty_percent_loss_is_allowed(tmp_path):
    current = [_lead(number) for number in range(1, 9)]
    previous_rows = [_lead(number) for number in range(1, 11)]
    folder = _write_raw(tmp_path / "zz", current)
    previous = tmp_path / "previous.json"
    previous.write_text(json.dumps(previous_rows))
    built = _write_built(tmp_path / "built.json", current)

    result = check_lead_data.check_state(folder, previous=previous, built=built)

    assert result.errors == []


def test_built_area_file_uses_filename_as_state(tmp_path):
    rows = [_lead(1), _lead(2)]
    for row in rows:
        row.pop("area")
    areas = tmp_path / "site" / "data" / "areas"
    areas.mkdir(parents=True)
    built = _write_built(areas / "zz.json", rows)

    result = check_lead_data.check_state(built)

    assert result.state == "zz"
    assert result.errors == []


def test_current_urls_and_addresses_are_checked_when_built_snapshot_exists(tmp_path):
    current = [_lead(1), _lead(2)]
    current[0]["sources"] = [{"url": "not-a-url"}]
    current[1]["address"] = "1 MAIN ST."
    folder = _write_raw(tmp_path / "zz", current)

    # The built output is deliberately healthy.  It supplies stable IDs but
    # must not hide bad source URLs or duplicate addresses in current data.
    built_rows = [_lead(1), _lead(2)]
    built = _write_built(tmp_path / "built.json", built_rows)

    result = check_lead_data.check_state(folder, built=built)
    message = "\n".join(result.errors)

    assert "no valid http(s) source URL" in message
    assert 'address "1 Main Street" appears more than once' in message
    assert "unstable id" not in message


def test_cli_returns_nonzero_and_lists_problems(tmp_path, capsys):
    rows = [_lead(1)]
    rows[0]["sources"] = [{"url": "not-a-url"}]
    folder = _write_raw(tmp_path / "zz", rows)
    built = _write_built(tmp_path / "built.json", rows)

    exit_code = check_lead_data.main([str(folder), "--built", str(built)])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert output.startswith("Lead data check failed:\n")
    assert "ZZ: lead 1" in output
