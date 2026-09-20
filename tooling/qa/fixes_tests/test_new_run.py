import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tooling"))

import new_run  # noqa: E402


class FakeRunner:
    def __init__(self, statuses=None, *, fail_label=None):
        self.statuses = iter(statuses or ["", "M  site/data/summary.json"])
        self.fail_label = fail_label
        self.calls = []

    def run(self, args, *, label):
        self.calls.append(("run", list(args), label))
        if label == self.fail_label:
            raise new_run.PublishError(f"{label} failed (exit 1)")

    def output(self, args, *, label):
        self.calls.append(("output", list(args), label))
        if args[:3] == ["git", "status", "--porcelain=v1"]:
            return next(self.statuses)
        if args == ["git", "branch", "--show-current"]:
            return "main"
        raise AssertionError(f"unexpected output command: {args}")


def _repo(tmp_path):
    for state in ("nm", "tx", "az"):
        recipe_dir = tmp_path / "propertystack" / "recipes" / state
        recipe_dir.mkdir(parents=True)
        (recipe_dir / "source.json").write_text("{}")
    runs = tmp_path / "propertystack" / "runs"
    runs.mkdir(parents=True)
    (runs / "source-health.json").write_text(
        json.dumps(
            {
                "sources": {
                    f"{state}/source.json": {"status": "worked"}
                    for state in ("nm", "tx", "az")
                }
            }
        )
    )
    (runs / "needs-a-source.md").write_text("# Needs a source\n")
    summary = tmp_path / "site" / "data" / "summary.json"
    summary.parent.mkdir(parents=True)
    summary.write_text(
        json.dumps(
            {
                "lastCheck": "2026-09-19",
                "permitsFiled": 936,
                "sold": 526,
                "totalTracked": 1462,
            }
        )
    )


def test_full_run_checks_before_commit_push_and_discord(tmp_path):
    _repo(tmp_path)
    runner = FakeRunner()
    posts = []

    line = new_run.run_pipeline(
        ["nm", "tx", "az"],
        root=tmp_path,
        webhook_url="https://discord.test/webhook",
        runner=runner,
        webhook_sender=lambda url, text: posts.append((url, text)),
    )

    run_commands = [call[1] for call in runner.calls if call[0] == "run"]
    assert run_commands == [
        ["bash", "tooling/run-area.sh", "nm", "tx", "az"],
        ["python3", "site/data/build_data.py"],
        [
            "python3", "-m", "pytest", "-q", "tooling/qa/fixes_tests/",
            "propertystack", "-x", "-q",
        ],
        ["python3", "tooling/qa/check_lead_data.py"],
        ["git", "add", "--", "propertystack/data", "propertystack/runs", "site/data"],
        ["git", "commit", "-m", "Refresh NM TX AZ lead data"],
        ["git", "push", "origin", "main"],
    ]
    assert line == (
        "Last check 2026-09-19: 936 permits, 526 sales, 1462 tracked (NM, TX, AZ); "
        "sources: 3 worked, 0 empty, 0 failed; "
        f"[needs a source]({new_run.NEEDS_SOURCE_URL})"
    )
    assert posts == [("https://discord.test/webhook", line)]


def test_failed_quality_gate_never_commits_pushes_or_posts(tmp_path):
    _repo(tmp_path)
    runner = FakeRunner(fail_label="Checking lead data quality")
    posts = []

    with pytest.raises(new_run.PublishError, match="Checking lead data quality failed"):
        new_run.run_pipeline(
            ["nm"],
            root=tmp_path,
            webhook_url="https://discord.test/webhook",
            runner=runner,
            webhook_sender=lambda *args: posts.append(args),
        )

    commands = [call[1] for call in runner.calls]
    assert not any(command[:2] == ["git", "commit"] for command in commands)
    assert not any(command[:2] == ["git", "push"] for command in commands)
    assert posts == []


def test_preflight_requires_webhook_before_downloading(tmp_path):
    _repo(tmp_path)
    runner = FakeRunner()

    with pytest.raises(new_run.PublishError, match="SIGNUP_WEBHOOK_URL is not set"):
        new_run.run_pipeline(["nm"], root=tmp_path, runner=runner)

    assert runner.calls == []


def test_dry_run_only_previews_sources(tmp_path):
    _repo(tmp_path)
    runner = FakeRunner(statuses=[""])

    result = new_run.run_pipeline(
        ["NM", "nm", "az"], root=tmp_path, dry_run=True, runner=runner
    )

    assert result is None
    assert [call[1] for call in runner.calls if call[0] == "run"] == [
        ["bash", "tooling/run-area.sh", "--dry-run", "nm", "az"]
    ]


def test_names_every_auto_found_source_in_the_one_line(tmp_path):
    _repo(tmp_path)
    recipe = tmp_path / "propertystack" / "recipes" / "nm" / "source.json"
    recipe.write_text(json.dumps({"source": "auto-found"}))

    assert new_run._auto_found_sources(tmp_path, ["nm", "tx"]) == ["NM/source"]
    line = new_run.summary_line(
        {
            "lastCheck": "2026-09-19",
            "permitsFiled": 1,
            "sold": 2,
            "totalTracked": 3,
        },
        ["nm", "tx"],
        ["NM/source"],
        {"worked": 1, "empty": 2, "failed": 3},
        new_run.NEEDS_SOURCE_URL,
    )
    assert line.endswith(
        "sources: 1 worked, 2 empty, 3 failed; "
        f"[needs a source]({new_run.NEEDS_SOURCE_URL}); auto-found sources: NM/source"
    )


def test_undo_restores_one_state_then_checks_commits_pushes_and_posts(tmp_path):
    _repo(tmp_path)
    state_dir = tmp_path / "propertystack" / "data" / "nm"
    state_dir.mkdir(parents=True)
    current = [{"name": "New building"}]
    previous = [{"name": "Previous building"}]
    (state_dir / "leads.json").write_text(json.dumps(current))
    (state_dir / "leads.before-run.json").write_text(json.dumps(previous))
    runner = FakeRunner()
    posts = []

    line = new_run.run_pipeline(
        ["nm"],
        root=tmp_path,
        webhook_url="https://discord.test/webhook",
        undo=True,
        runner=runner,
        webhook_sender=lambda url, text: posts.append((url, text)),
    )

    assert json.loads((state_dir / "leads.json").read_text()) == previous
    run_commands = [call[1] for call in runner.calls if call[0] == "run"]
    assert ["bash", "tooling/run-area.sh", "nm"] not in run_commands
    assert ["python3", "site/data/build_data.py"] in run_commands
    assert ["git", "commit", "-m", "Restore NM lead data backup"] in run_commands
    assert run_commands[-1] == ["git", "push", "origin", "main"]
    assert posts == [("https://discord.test/webhook", line)]


def test_undo_requires_one_valid_pre_run_copy(tmp_path):
    _repo(tmp_path)
    runner = FakeRunner(statuses=[""])

    with pytest.raises(new_run.PublishError, match="undo exactly one state"):
        new_run.run_pipeline(
            ["nm", "tx"], root=tmp_path, dry_run=True, undo=True, runner=runner
        )

    with pytest.raises(new_run.PublishError, match="no pre-run copy exists"):
        new_run.run_pipeline(
            ["nm"], root=tmp_path, dry_run=True, undo=True, runner=runner
        )


def test_source_health_counts_only_selected_configured_sources(tmp_path):
    _repo(tmp_path)
    health_path = tmp_path / "propertystack" / "runs" / "source-health.json"
    health_path.write_text(
        json.dumps(
            {
                "sources": {
                    "nm/source.json": {"status": "empty"},
                    "tx/source.json": {"status": "failed"},
                    "tx/retired.json": {"status": "worked"},
                }
            }
        )
    )

    assert new_run._source_health(tmp_path, ["nm", "tx"]) == {
        "worked": 0,
        "empty": 1,
        "failed": 1,
    }
