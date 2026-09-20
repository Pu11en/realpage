#!/usr/bin/env python3
"""Run, validate, publish, and announce a CraneSignal lead refresh.

The shell entry point is ``tooling/new-run.sh``.  Publishing is deliberately
last: a clean ``main`` checkout, a Discord webhook, and every data/test gate
must be present before this command will push anything.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
STATE_RE = re.compile(r"^[a-z][a-z0-9-]*$")
# The routine weekly refresh is Texas only.  Every other state keeps the lead
# data it already has on the site and is re-run only when named explicitly,
# e.g. ``tooling/new-run.sh az``.
ROUTINE_STATES = ("tx",)
NEEDS_SOURCE_URL = (
    "https://github.com/Pu11en/realpage/blob/main/"
    "propertystack/runs/needs-a-source.md"
)


class PublishError(RuntimeError):
    """A plain-language reason the run stopped before it could finish."""


class CommandRunner:
    def __init__(self, root: Path):
        self.root = root

    def run(self, args: Sequence[str], *, label: str) -> None:
        print(f"\n==> {label}", flush=True)
        result = subprocess.run(list(args), cwd=self.root, text=True)
        if result.returncode:
            raise PublishError(f"{label} failed (exit {result.returncode})")

    def output(self, args: Sequence[str], *, label: str) -> str:
        result = subprocess.run(
            list(args), cwd=self.root, text=True, capture_output=True
        )
        if result.returncode:
            detail = result.stderr.strip() or result.stdout.strip()
            suffix = f": {detail}" if detail else ""
            raise PublishError(
                f"{label} failed (exit {result.returncode}){suffix}"
            )
        return result.stdout.strip()


def validate_states(states: Sequence[str], root: Path) -> list[str]:
    normalized: list[str] = []
    for supplied in states:
        state = supplied.strip().lower()
        if not STATE_RE.fullmatch(state):
            raise PublishError(f'"{supplied}" is not a valid state slug')
        if state in normalized:
            continue
        if not (root / "propertystack" / "recipes" / state).is_dir():
            raise PublishError(f'no recipes found for state "{state}"')
        normalized.append(state)
    if not normalized:
        raise PublishError("give at least one state, for example: nm tx az")
    return normalized


def _require_clean_main(runner: CommandRunner) -> None:
    status = runner.output(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        label="Checking the worktree",
    )
    if status:
        raise PublishError(
            "the worktree already has changes; commit or set them aside before this run"
        )
    branch = runner.output(
        ["git", "branch", "--show-current"], label="Checking the current branch"
    )
    if branch != "main":
        raise PublishError(
            f'the current branch is "{branch or "detached"}"; publishing is only allowed from main'
        )


def _summary(root: Path) -> dict:
    path = root / "site" / "data" / "summary.json"
    try:
        summary = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise PublishError(f"could not read the built site summary: {exc}") from exc
    required = ("lastCheck", "permitsFiled", "sold", "totalTracked")
    missing = [key for key in required if key not in summary]
    if missing:
        raise PublishError(
            "the built site summary is missing: " + ", ".join(missing)
        )
    for key in required[1:]:
        if not isinstance(summary[key], int) or summary[key] < 0:
            raise PublishError(f'the built site summary has an invalid "{key}" count')
    return summary


def _auto_found_sources(root: Path, states: Sequence[str]) -> list[str]:
    found = []
    for state in states:
        for path in sorted((root / "propertystack" / "recipes" / state).glob("*.json")):
            try:
                recipe = json.loads(path.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            if recipe.get("source") == "auto-found":
                found.append(f"{state.upper()}/{path.stem}")
    return found


def _source_health(root: Path, states: Sequence[str]) -> dict[str, int]:
    """Count the latest health entry for every configured source in the run."""
    health_path = root / "propertystack" / "runs" / "source-health.json"
    try:
        payload = json.loads(health_path.read_text())
    except (OSError, json.JSONDecodeError):
        payload = {}
    entries = payload.get("sources", {}) if isinstance(payload, dict) else {}
    counts = {"worked": 0, "empty": 0, "failed": 0}
    for state in states:
        recipe_dir = root / "propertystack" / "recipes" / state
        for recipe_path in recipe_dir.glob("*.json"):
            entry = entries.get(f"{state}/{recipe_path.name}", {})
            status = entry.get("status") if isinstance(entry, dict) else None
            if status in counts:
                counts[status] += 1
    return counts


def _flagged_sources(root: Path, states: Sequence[str]) -> list[str]:
    """Name every source the run measured as under-reading or frozen.

    The health file recorded these already; nobody read it while Dallas County
    was broken, so the weekly notice says them out loud instead.
    """
    health_path = root / "propertystack" / "runs" / "source-health.json"
    try:
        payload = json.loads(health_path.read_text())
    except (OSError, json.JSONDecodeError):
        return []
    entries = payload.get("sources", {}) if isinstance(payload, dict) else {}
    flagged = []
    for state in states:
        recipe_dir = root / "propertystack" / "recipes" / state
        for recipe_path in sorted(recipe_dir.glob("*.json")):
            entry = entries.get(f"{state}/{recipe_path.name}")
            if not isinstance(entry, dict):
                continue
            signal = entry.get("signal")
            flags = signal.get("flags") if isinstance(signal, dict) else None
            if isinstance(flags, list) and flags:
                flagged.append(
                    f"{state.upper()}/{recipe_path.stem} ({', '.join(flags)})"
                )
    return flagged


def _needs_source_url(root: Path) -> str:
    path = root / "propertystack" / "runs" / "needs-a-source.md"
    return NEEDS_SOURCE_URL if path.is_file() else ""


def summary_line(
    summary: dict,
    states: Sequence[str],
    auto_found: Sequence[str],
    health: dict[str, int],
    needs_source_url: str,
    flagged: Sequence[str] = (),
) -> str:
    state_list = ", ".join(state.upper() for state in states)
    line = (
        f"Last check {summary['lastCheck']}: {summary['permitsFiled']} permits, "
        f"{summary['sold']} sales, {summary['totalTracked']} tracked ({state_list})"
    )
    line += (
        f"; sources: {health.get('worked', 0)} worked, "
        f"{health.get('empty', 0)} empty, {health.get('failed', 0)} failed"
    )
    if flagged:
        line += "; CHECK THESE SOURCES: " + ", ".join(flagged)
    else:
        line += "; all measured sources healthy"
    if needs_source_url:
        line += f"; [needs a source]({needs_source_url})"
    if auto_found:
        line += "; auto-found sources: " + ", ".join(auto_found)
    return line


def _backup_path(root: Path, state: str) -> Path:
    return root / "propertystack" / "data" / state / "leads.before-run.json"


def _validate_backup(root: Path, state: str) -> Path:
    backup = _backup_path(root, state)
    try:
        rows = json.loads(backup.read_text())
    except FileNotFoundError as exc:
        raise PublishError(
            f'no pre-run copy exists for "{state}"; nothing was restored'
        ) from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise PublishError(
            f'the pre-run copy for "{state}" could not be read: {exc}'
        ) from exc
    if not isinstance(rows, list):
        raise PublishError(f'the pre-run copy for "{state}" is not a lead list')
    return backup


def _restore_backup(root: Path, state: str) -> None:
    backup = _validate_backup(root, state)
    leads_path = root / "propertystack" / "data" / state / "leads.json"
    temporary = leads_path.with_suffix(".json.undo-tmp")
    shutil.copyfile(backup, temporary)
    temporary.replace(leads_path)
    print(f'\nRestored the pre-run copy for {state.upper()} ({backup.name}).')


def post_discord(webhook_url: str, line: str) -> None:
    request = urllib.request.Request(
        webhook_url,
        data=json.dumps({"content": line}).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "CraneSignal"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            if response.status not in {200, 204}:
                raise PublishError(
                    f"Discord returned HTTP {response.status} after the site was published"
                )
    except PublishError:
        raise
    except Exception as exc:
        raise PublishError(
            f"the site was published, but the Discord summary could not be posted: {exc}"
        ) from exc


def _check_only_generated_changes(status: str) -> None:
    """Refuse to commit anything a normal data run did not generate."""
    allowed = ("propertystack/data/", "propertystack/runs/", "site/data/")
    unexpected = []
    for line in status.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].split(" -> ")[-1]
        if not path.startswith(allowed):
            unexpected.append(path)
    if unexpected:
        raise PublishError(
            "the run changed unexpected files, so nothing was committed: "
            + ", ".join(unexpected)
        )


def run_pipeline(
    states: Sequence[str],
    *,
    root: Path = ROOT,
    webhook_url: str = "",
    dry_run: bool = False,
    undo: bool = False,
    runner: CommandRunner | None = None,
    webhook_sender=post_discord,
) -> str | None:
    states = validate_states(states, root)
    if undo and len(states) != 1:
        raise PublishError("undo exactly one state at a time")
    runner = runner or CommandRunner(root)

    if dry_run:
        status = runner.output(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            label="Checking the worktree",
        )
        if status:
            raise PublishError("the worktree already has changes; dry-run from a clean checkout")
        if undo:
            _validate_backup(root, states[0])
            print(f"\nDry run: {states[0].upper()} has a pre-run copy ready to restore.")
        else:
            runner.run(
                ["bash", "tooling/run-area.sh", "--dry-run", *states],
                label="Previewing source runs",
            )
        print("\nDry run complete; no data was changed or published.")
        return None

    if not webhook_url:
        raise PublishError(
            "SIGNUP_WEBHOOK_URL is not set; no run started because its final notice could not be sent"
        )
    _require_clean_main(runner)

    if undo:
        _restore_backup(root, states[0])
    else:
        runner.run(
            ["bash", "tooling/run-area.sh", *states], label="Refreshing lead sources"
        )
    runner.run(
        ["python3", "site/data/build_data.py"], label="Building site and chat data"
    )
    runner.run(
        [
            "python3",
            "-m",
            "pytest",
            "-q",
            "tooling/qa/fixes_tests/",
            "propertystack",
            "-x",
            "-q",
        ],
        label="Running project tests",
    )
    runner.run(
        ["python3", "tooling/qa/check_lead_data.py"],
        label="Checking lead data quality",
    )

    built_summary = _summary(root)
    line = summary_line(
        built_summary,
        states,
        _auto_found_sources(root, states),
        _source_health(root, states),
        _needs_source_url(root),
        _flagged_sources(root, states),
    )

    runner.run(
        ["git", "add", "--", "propertystack/data", "propertystack/runs", "site/data"],
        label="Staging generated data",
    )
    status = runner.output(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        label="Reviewing generated changes",
    )
    _check_only_generated_changes(status)
    if status:
        if undo:
            commit_message = f"Restore {states[0].upper()} lead data backup"
        else:
            commit_message = f"Refresh {' '.join(state.upper() for state in states)} lead data"
        runner.run(
            ["git", "commit", "-m", commit_message],
            label="Committing refreshed data",
        )
    else:
        print("\nNo generated data changed; using the existing commit.")

    runner.run(["git", "push", "origin", "main"], label="Publishing from main")
    webhook_sender(webhook_url, line)
    print(f"\n{line}")
    return line


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Refresh lead sources, check them, publish main, and announce the result."
    )
    parser.add_argument(
        "states",
        nargs="*",
        help=(
            "state slugs, such as nm tx az; with none given the routine refresh "
            "runs " + " ".join(ROUTINE_STATES)
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="list the source work without downloading, committing, pushing, or posting",
    )
    parser.add_argument(
        "--undo",
        action="store_true",
        help="restore one state's pre-run copy, check it, publish it, and announce it",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    states = args.states
    if not states and not args.undo:
        states = list(ROUTINE_STATES)
        print(f"No state named; running the routine refresh: {' '.join(states)}")
    try:
        run_pipeline(
            states,
            webhook_url=os.environ.get("SIGNUP_WEBHOOK_URL", ""),
            dry_run=args.dry_run,
            undo=args.undo,
        )
    except PublishError as exc:
        print(f"\nSTOPPED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
