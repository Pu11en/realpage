#!/usr/bin/env python3
"""Fail a lead-data run before broken state data can be published.

With no arguments, check every state folder under ``propertystack/data``.
One or more folders (or leads JSON files) may also be supplied explicitly:

    python3 tooling/qa/check_lead_data.py propertystack/data/tx
    python3 tooling/qa/check_lead_data.py /tmp/nm --previous /tmp/nm-before.json

The normal runner should save its pre-run data as ``leads.before-run.json`` in
the state folder.  When that file is absent, this checker uses the currently
published state snapshot as the previous-build baseline.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "site" / "data"))
sys.path.insert(0, str(ROOT / "propertystack" / "skills" / "lead-finder"))

from build_data import content_id, source_entry  # noqa: E402
from record import normalize_address  # noqa: E402


PREVIOUS_FILENAMES = (
    "leads.before-run.json",
    "leads.previous.json",
    "previous-leads.json",
)


@dataclass
class CheckResult:
    state: str
    lead_count: int = 0
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def _state_name(path: Path, rows: list[dict]) -> str:
    if rows:
        area = rows[0].get("area") or rows[0].get("state")
        if area:
            return str(area).strip().lower()
    if path.is_file():
        # Raw state data uses ``<state>/leads.json`` while built snapshots use
        # ``site/data/areas/<state>.json``.  Using the parent for both turns a
        # built Texas snapshot into the fictitious state "areas".
        return (path.parent.name if path.name == "leads.json" else path.stem).lower()
    return path.name.lower()


def _display_name(lead: dict, row_number: int) -> str:
    name = lead.get("property") or lead.get("name") or lead.get("community")
    address = lead.get("address")
    detail = name or address or "unnamed lead"
    return f'lead {row_number} ("{detail}")'


def _valid_web_url(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    parsed = urlparse(value.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _source_urls(lead: dict) -> list[str]:
    sources = lead.get("sources") or []
    if isinstance(sources, dict):
        sources = [sources]
    urls = []
    for source in sources if isinstance(sources, list) else []:
        normalized = source_entry(source)
        if normalized and _valid_web_url(normalized.get("url")):
            urls.append(normalized["url"].strip())
    normalized = source_entry(lead.get("source_url"))
    if normalized and _valid_web_url(normalized.get("url")):
        urls.append(normalized["url"].strip())
    return urls


def _read_leads(path: Path) -> tuple[list[dict], bool]:
    """Return rows and whether the file is a built/public state snapshot."""
    try:
        payload = json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise ValueError(f"cannot find {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"{path} is not valid JSON (line {exc.lineno}, column {exc.colno})"
        ) from exc
    except OSError as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc

    built_snapshot = isinstance(payload, dict)
    rows = payload.get("leads") if built_snapshot else payload
    if not isinstance(rows, list):
        raise ValueError(f"{path} must contain a JSON list of leads")
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError(f"{path} contains a lead that is not a JSON object")
    return rows, built_snapshot


def _leads_path(path: Path) -> Path:
    return path if path.is_file() else path / "leads.json"


def _published_path(state: str) -> Path:
    return ROOT / "site" / "data" / "areas" / f"{state}.json"


def _find_previous(state_path: Path, state: str, explicit: Path | None) -> Path | None:
    if explicit is not None:
        return _leads_path(explicit)
    folder = state_path.parent if state_path.is_file() else state_path
    for filename in PREVIOUS_FILENAMES:
        candidate = folder / filename
        if candidate.exists():
            return candidate
    nested = folder / ".previous" / "leads.json"
    if nested.exists():
        return nested
    published = _published_path(state)
    if published.exists() and published.resolve() != state_path.resolve():
        return published
    return None


def _find_built_snapshot(state_path: Path, state: str, is_built: bool) -> Path | None:
    if is_built:
        return state_path
    published = _published_path(state)
    if published.exists():
        return published
    return None


def _check_sources(rows: list[dict], result: CheckResult) -> None:
    for number, lead in enumerate(rows, start=1):
        if not _source_urls(lead):
            result.errors.append(
                f"{_display_name(lead, number)} has no valid http(s) source URL."
            )


def _check_duplicate_addresses(rows: list[dict], result: CheckResult) -> None:
    by_address: dict[str, list[tuple[int, dict]]] = defaultdict(list)
    for number, lead in enumerate(rows, start=1):
        address = normalize_address(str(lead.get("address") or ""))
        if address:
            by_address[address].append((number, lead))
    for address, matches in sorted(by_address.items()):
        if len(matches) < 2:
            continue
        row_numbers = ", ".join(str(number) for number, _ in matches)
        shown_address = next(
            str(lead.get("address")) for _, lead in matches if lead.get("address")
        )
        result.errors.append(
            f'address "{shown_address}" appears more than once (leads {row_numbers}).'
        )


def _check_ids(rows: list[dict], state: str, result: CheckResult) -> None:
    bases = [
        content_id(
            state,
            str(lead.get("address") or ""),
            str(lead.get("property") or lead.get("name") or lead.get("community") or ""),
        )
        for lead in rows
    ]
    base_counts = Counter(bases)
    ids: dict[str, int] = {}
    for number, (lead, base) in enumerate(zip(rows, bases), start=1):
        lead_id = lead.get("id")
        if not isinstance(lead_id, str) or not lead_id.strip():
            result.errors.append(f"{_display_name(lead, number)} has no stable id.")
            continue
        lead_id = lead_id.strip()
        if lead_id in ids:
            result.errors.append(
                f'id "{lead_id}" is used by both lead {ids[lead_id]} and lead {number}.'
            )
        else:
            ids[lead_id] = number
        valid_collision_id = base_counts[base] > 1 and lead_id.startswith(f"{base}-")
        if lead_id != base and not valid_collision_id:
            result.errors.append(
                f'{_display_name(lead, number)} has unstable id "{lead_id}"; expected "{base}".'
            )


def _check_loss(current_count: int, previous_count: int, result: CheckResult) -> None:
    if previous_count <= 0:
        return
    if current_count * 5 < previous_count * 4:  # strictly more than a 20% loss
        loss_percent = 100 * (previous_count - current_count) / previous_count
        result.errors.append(
            f"lead count fell from {previous_count} to {current_count} "
            f"({loss_percent:.1f}% lost); the maximum allowed loss is 20%."
        )


def check_state(
    path: str | Path,
    *,
    previous: str | Path | None = None,
    built: str | Path | None = None,
) -> CheckResult:
    """Check one state folder or JSON file and return all problems found."""
    supplied = Path(path)
    state_path = _leads_path(supplied)
    try:
        rows, is_built = _read_leads(state_path)
    except ValueError as exc:
        state = supplied.stem.lower() if supplied.is_file() else supplied.name.lower()
        return CheckResult(state=state, errors=[str(exc)])

    state = _state_name(state_path, rows)
    result = CheckResult(state=state, lead_count=len(rows))

    # These checks describe the current state data supplied by the caller.  A
    # published snapshot may still contain valid URLs and unique addresses
    # from the previous build, so it must never mask problems in current data.
    _check_sources(rows, result)
    _check_duplicate_addresses(rows, result)

    built_path = _leads_path(Path(built)) if built is not None else _find_built_snapshot(
        state_path, state, is_built
    )
    if built_path is not None:
        try:
            built_rows, _ = _read_leads(built_path)
        except ValueError as exc:
            result.errors.append(str(exc))
        else:
            _check_ids(built_rows, state, result)
    else:
        result.notes.append(
            "no built state snapshot was found, so stable ids could not be checked"
        )

    previous_path = _find_previous(
        state_path,
        state,
        Path(previous) if previous is not None else None,
    )
    if previous_path is None:
        result.notes.append(
            "no previous snapshot was found, so lead-count loss could not be checked"
        )
    else:
        try:
            previous_rows, _ = _read_leads(previous_path)
        except ValueError as exc:
            result.errors.append(str(exc))
        else:
            _check_loss(len(rows), len(previous_rows), result)
    return result


def _default_state_folders() -> list[Path]:
    data_root = ROOT / "propertystack" / "data"
    return sorted(
        path.parent
        for path in data_root.glob("[a-z][a-z]/leads.json")
        if path.is_file()
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check state lead data before publishing it."
    )
    parser.add_argument(
        "state_folders",
        nargs="*",
        type=Path,
        help="state folder(s), or leads JSON file(s); defaults to every state",
    )
    parser.add_argument(
        "--previous",
        type=Path,
        help="previous state folder/JSON to compare (only with one state folder)",
    )
    parser.add_argument(
        "--built",
        type=Path,
        help="built state folder/JSON whose stable ids should be checked (one state only)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    paths = args.state_folders or _default_state_folders()
    if not paths:
        parser.error("no state folders with leads.json were found")
    if len(paths) != 1 and (args.previous or args.built):
        parser.error("--previous and --built can only be used with one state folder")

    results = [
        check_state(path, previous=args.previous, built=args.built)
        for path in paths
    ]
    errors = [f"{result.state.upper()}: {error}" for result in results for error in result.errors]
    notes = [f"{result.state.upper()}: {note}." for result in results for note in result.notes]
    if errors:
        print("Lead data check failed:")
        for error in errors:
            print(f"- {error}")
        for note in notes:
            print(f"- Note: {note}")
        return 1

    total = sum(result.lead_count for result in results)
    state_word = "state" if len(results) == 1 else "states"
    print(f"Lead data check passed for {len(results)} {state_word} ({total} leads).")
    for note in notes:
        print(f"- Note: {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
