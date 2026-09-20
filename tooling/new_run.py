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
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
STATE_RE = re.compile(r"^[a-z][a-z0-9-]*$")


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


def summary_line(summary: dict, states: Sequence[str], auto_found: Sequence[str]) -> str:
    state_list = ", ".join(state.upper() for state in states)
    line = (
        f"Last check {summary['lastCheck']}: {summary['permitsFiled']} permits, "
        f"{summary['sold']} sales, {summary['totalTracked']} tracked ({state_list})"
    )
    if auto_found:
        line += "; auto-found sources: " + ", ".join(auto_found)
    return line


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
    runner: CommandRunner | None = None,
    webhook_sender=post_discord,
) -> str | None:
    states = validate_states(states, root)
    runner = runner or CommandRunner(root)

    if dry_run:
        status = runner.output(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            label="Checking the worktree",
        )
        if status:
            raise PublishError("the worktree already has changes; dry-run from a clean checkout")
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
        built_summary, states, _auto_found_sources(root, states)
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
        runner.run(
            ["git", "commit", "-m", f"Refresh {' '.join(state.upper() for state in states)} lead data"],
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
    parser.add_argument("states", nargs="+", help="state slugs, such as nm tx az")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="list the source work without downloading, committing, pushing, or posting",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        run_pipeline(
            args.states,
            webhook_url=os.environ.get("SIGNUP_WEBHOOK_URL", ""),
            dry_run=args.dry_run,
        )
    except PublishError as exc:
        print(f"\nSTOPPED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
