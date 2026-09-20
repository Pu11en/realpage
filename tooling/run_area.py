#!/usr/bin/env python3
"""Run every saved lead-source recipe for one or more states.

The shell entry point is ``tooling/run-area.sh``.  Sources inside a state run
concurrently (at most six), each failed source is tried twice, and successful
or empty source results are saved by date so an interrupted run can resume.
"""
from __future__ import annotations

import argparse
import csv
import inspect
import io
import json
import os
import sys
import tempfile
import threading
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "propertystack" / "skills"
for relative in (
    "lead-finder",
    "lead-finder-awards",
    "lead-finder-permits",
    "lead-finder-sales",
    "lead-finder-tabs",
    "score-leads",
):
    sys.path.insert(0, str(SKILLS / relative))
sys.path.insert(0, str(ROOT / "site" / "data"))

import appraisal_zip  # noqa: E402
import awards  # noqa: E402
import ckan_sql  # noqa: E402
import find_sold  # noqa: E402
import find_upcoming  # noqa: E402
import houston_sold_permits  # noqa: E402
import tad_sales  # noqa: E402
import tad_zip  # noqa: E402
import tabs  # noqa: E402
import tdhca  # noqa: E402
from build_data import content_id  # noqa: E402
from merge import merge_records  # noqa: E402
from record import LeadRecord  # noqa: E402
from score_leads import score_and_rank  # noqa: E402


MAX_WORKERS = 6
FINISHED_STATUSES = {"worked", "empty"}
# A source that keeps less than this share of the apartment rows its endpoint
# actually held is reported as suspect.  Dallas, Fort Worth and Albuquerque all
# looked healthy for months because the run recorded only what we kept.
SUSPECT_KEEP_RATIO = 0.25
# Below this many apartment rows the ratio says nothing useful -- a genuinely
# small city keeping 1 of 3 is not a failure.
MIN_ROWS_TO_JUDGE = 4
# A feed still answering but with nothing newer than this is frozen, not broken.
STALE_AFTER_DAYS = 365
HTTP_HEADERS = {"User-Agent": "CraneSignalLeadRun/1.0"}


class SourceFetchError(RuntimeError):
    """A recipe adapter swallowed a network error and returned no rows."""


class TrackingFetch:
    """Record exceptions even when an existing adapter catches them."""

    def __init__(self, fn: Callable):
        self.fn = fn
        self.errors: list[Exception] = []
        self._lock = threading.Lock()

    def __call__(self, *args, **kwargs):
        try:
            return self.fn(*args, **kwargs)
        except Exception as exc:
            with self._lock:
                self.errors.append(exc)
            raise

    def raise_if_failed(self) -> None:
        if self.errors:
            error = self.errors[0]
            raise SourceFetchError(f"{type(error).__name__}: {error}")


@dataclass
class SourceResult:
    recipe: str
    status: str
    records: list[dict]
    attempts: int
    note: str = ""
    resumed: bool = False
    signal: dict = field(default_factory=dict)

    def payload(self, state: str, run_date: str) -> dict:
        return {
            "state": state,
            "recipe": self.recipe,
            "date": run_date,
            "status": self.status,
            "count": len(self.records),
            "attempts": self.attempts,
            "note": self.note,
            "signal": self.signal,
            "records": self.records,
        }

    @property
    def flags(self) -> list[str]:
        flags = self.signal.get("flags")
        return list(flags) if isinstance(flags, list) else []


def _atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as handle:
            json.dump(payload, handle, indent=2)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _read_json(path: Path, default):
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def _safe_url(url: str) -> str:
    """Percent-encode a URL a county published with characters http.client rejects.

    Dallas's bulk-file link carries a literal Windows path as a query value --
    backslashes and a space -- so `http.client` refuses it as containing control
    characters and the source failed on every run. A URL that is already valid is
    returned byte-for-byte unchanged, so no working source changes behaviour.
    """
    if " " not in url and "\\" not in url and url.isascii() and url.isprintable():
        return url
    return urllib.parse.quote(url, safe=":/?&=%")


def _http_get_json(url: str):
    request = urllib.request.Request(_safe_url(url), headers=HTTP_HEADERS)
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def _http_get_structured(url: str):
    """Fetch an auto-found structured endpoint without guessing its format."""
    request = urllib.request.Request(_safe_url(url), headers=HTTP_HEADERS)
    with urllib.request.urlopen(request, timeout=60) as response:
        text = response.read().decode("utf-8", errors="replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return list(csv.DictReader(io.StringIO(text)))


def _http_get_bytes(url: str) -> bytes:
    request = urllib.request.Request(_safe_url(url), headers=HTTP_HEADERS)
    with urllib.request.urlopen(request, timeout=280) as response:
        return response.read()


def _http_get_text(url: str) -> str:
    return _http_get_bytes(url).decode("utf-8", errors="replace")


def _tabs_search(endpoint: str, payload: dict) -> dict:
    request = urllib.request.Request(
        endpoint,
        data=urllib.parse.urlencode(payload).encode(),
        headers={**HTTP_HEADERS, "Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read())


def _tabs_detail(template: str, project_number: str) -> str:
    return _http_get_text(template.format(project_number=project_number))


def _records_as_dicts(records: list[LeadRecord]) -> list[dict]:
    return [record.to_dict() if isinstance(record, LeadRecord) else record for record in records]


def run_recipe(recipe_path: Path, state: str, stats: dict | None = None) -> list[dict]:
    """Dispatch one recipe to its existing, tested source adapter.

    `stats`, when given, is filled by the permit adapter with why rows were
    dropped so an empty result can name its own cause.
    """
    recipe = json.loads(recipe_path.read_text())
    if recipe.get("enabled") is False:
        return []
    system = recipe.get("system")
    area = state.lower()

    if system in {"arcgis", "socrata", "accela", "open-data"}:
        fetch = TrackingFetch(_http_get_structured)
        records = find_upcoming.find_upcoming(
            recipe.get("city") or recipe.get("county", ""),
            state.upper(),
            area,
            recipe,
            fetch,
            stats=stats,
        )
        fetch.raise_if_failed()
    elif system == "ckan-sql":
        fetch = TrackingFetch(_http_get_json)
        adapted = ckan_sql.ckan_sql_http_get(recipe["endpoint"], recipe["sql"], fetch)
        records = find_upcoming.find_upcoming(
            recipe.get("city", ""), state.upper(), area, recipe, adapted, stats=stats
        )
        fetch.raise_if_failed()
    elif system == "houston-sold-permits-xlsx":
        text_fetch = TrackingFetch(_http_get_text)
        bytes_fetch = TrackingFetch(_http_get_bytes)
        rows = houston_sold_permits.fetch_rows(recipe, text_fetch, bytes_fetch)
        text_fetch.raise_if_failed()
        bytes_fetch.raise_if_failed()
        records = find_upcoming.find_upcoming(
            recipe.get("city", ""),
            state.upper(),
            area,
            recipe,
            lambda _endpoint: rows,
            stats=stats,
        )
    elif system == "appraisal-district-bulk-file":
        fetch = TrackingFetch(_http_get_bytes)
        cache: dict[str, bytes] = {}
        cache_errors: dict[str, Exception] = {}

        def cached_fetch(url: str) -> bytes:
            if url in cache_errors:
                raise cache_errors[url]
            if url not in cache:
                try:
                    cache[url] = fetch(url)
                except Exception as exc:
                    cache_errors[url] = exc
                    raise
            return cache[url]

        records = appraisal_zip.find_new_apartment_projects(area, recipe, cached_fetch)
        records += appraisal_zip.find_sold_apartments(area, recipe, cached_fetch)
        fetch.raise_if_failed()
    elif system == "county-appraisal-zip":
        fetch = TrackingFetch(_http_get_bytes)
        records = tad_zip.find_new_apartment_permits(area, recipe, fetch)
        fetch.raise_if_failed()
    elif system == "tad-improved-sales-zip":
        fetch = TrackingFetch(_http_get_bytes)
        records = tad_sales.find_apartment_sales(area, recipe, fetch)
        fetch.raise_if_failed()
    elif system == "tdhca-affordable":
        fetch = TrackingFetch(_http_get_bytes)
        records = tdhca.find_new_affordable_projects(area, recipe, fetch)
        fetch.raise_if_failed()
    elif system == "housing-awards-multiline-xlsx":
        fetch = TrackingFetch(_http_get_bytes)
        records = awards.find_saved_multiline_awards(area, recipe, fetch)
        fetch.raise_if_failed()
    elif system == "county-assessor-flat-file":
        fetch = TrackingFetch(find_sold.default_fetch_rows)
        records = find_sold.find_sold(area, recipe, fetch)
        fetch.raise_if_failed()
    elif system == "tabs":
        search = TrackingFetch(lambda payload: _tabs_search(recipe["endpoint"], payload))
        detail = TrackingFetch(
            lambda number: _tabs_detail(recipe["detail_url_template"], number)
        )
        records = tabs.find_tabs_projects(area, recipe, search, detail)
        search.raise_if_failed()
        detail.raise_if_failed()
    else:
        raise ValueError(f"unsupported recipe system {system!r}")

    return _records_as_dicts(records)


def _accepts_stats(source_runner: Callable) -> bool:
    """Only the real runner reports why rows were dropped; test fakes take two."""
    try:
        return len(inspect.signature(source_runner).parameters) >= 3
    except (TypeError, ValueError):
        return False


def _empty_note(stats: dict) -> str:
    """Explain an empty source in the run log instead of leaving it blank."""
    if not stats:
        return ""
    rows = stats.get("rows") or 0
    apartments = stats.get("apartmentRows") or 0
    if not rows:
        return "the source returned no rows at all"
    if not apartments:
        return f"{rows} rows returned, none of them an apartment project"
    newest = stats.get("newestDate") or ""
    age = stats.get("newestAgeDays")
    if newest and age is not None:
        return (
            f"stale source: {apartments} apartment rows, "
            f"newest issued {newest} ({age} days ago), none recent enough to list"
        )
    return f"{apartments} apartment rows, none carried a usable date"


def _signal_note(signal: dict) -> str:
    """One plain sentence a person can act on, or nothing when all is well."""
    flags = signal.get("flags") or []
    if "stale" in flags:
        return (
            f"stale: the newest record this source holds is "
            f"{signal['newestDate']}, {signal['newestAgeDays']} days old"
        )
    if "suspect" in flags:
        note = (
            f"suspect: the endpoint held {signal['apartmentRows']} apartment rows "
            f"and only {signal['kept']} became leads"
        )
        reasons = [
            f"{signal[key]} {label}"
            for key, label in (
                ("agedOut", "too old"),
                ("placeholderAddress", "with a stand-in address"),
                ("junkDropped", "not a new building"),
                ("mergedAway", "merged into another project"),
            )
            if signal.get(key)
        ]
        if reasons:
            note += " (" + ", ".join(reasons) + ")"
        return note
    return ""


def _source_signal(stats: dict, kept: int) -> dict:
    """Record what the endpoint actually held next to what the run kept.

    Without both numbers a source returning 1 row out of thousands is filed as
    "worked", which is exactly how Dallas County stayed broken for months.
    Adapters that cannot report a row count say so rather than invent one.
    """
    if not stats:
        return {
            "measured": False,
            "why": "this source type does not report how many rows its endpoint holds",
        }
    apartment_rows = int(stats.get("apartmentRows") or 0)
    age = stats.get("newestAgeDays")
    # One building routinely files many permits at the same address, and
    # merge_records collapses those into a single project on purpose.  Judging
    # the post-merge count against the raw row count therefore calls a healthy
    # source broken: a real city filed 377 usable permits at 149 addresses.
    # When the adapter reports how many rows survived every quality filter
    # (`built`, pre-merge), judge on that; otherwise fall back to `kept`.
    built = stats.get("built")
    judged = int(built) if isinstance(built, int) else kept
    flags: list[str] = []
    if isinstance(age, int) and age > STALE_AFTER_DAYS:
        # A frozen feed is a finding, not an under-read: everything it holds is
        # simply too old, so the keep ratio would blame the wrong thing.
        flags.append("stale")
    elif (
        apartment_rows >= MIN_ROWS_TO_JUDGE
        and judged < apartment_rows * SUSPECT_KEEP_RATIO
    ):
        flags.append("suspect")
    signal = {
        "measured": True,
        "endpointRows": int(stats.get("rows") or 0),
        "apartmentRows": apartment_rows,
        "kept": kept,
        "agedOut": int(stats.get("agedOut") or 0),
        "newestDate": stats.get("newestDate") or "",
        "newestAgeDays": age,
        "flags": flags,
    }
    # Why rows went missing, when the adapter counted it -- so a suspect source
    # names its own cause instead of leaving someone to re-derive it.
    for key in ("noDate", "placeholderAddress", "junkDropped", "built", "mergedAway"):
        if isinstance(stats.get(key), int):
            signal[key] = int(stats[key])
    signal["note"] = _signal_note(signal)
    return signal


def _artifact_result(path: Path) -> SourceResult | None:
    payload = _read_json(path, None)
    if not isinstance(payload, dict) or payload.get("status") not in FINISHED_STATUSES:
        return None
    records = payload.get("records")
    if not isinstance(records, list):
        return None
    return SourceResult(
        recipe=str(payload.get("recipe") or path.stem),
        status=payload["status"],
        records=records,
        attempts=int(payload.get("attempts") or 1),
        note=str(payload.get("note") or ""),
        resumed=True,
        signal=payload.get("signal") if isinstance(payload.get("signal"), dict) else {},
    )


def _run_source(
    recipe_path: Path,
    state: str,
    run_date: str,
    artifact_path: Path,
    source_runner: Callable[[Path, str], list[dict]],
) -> SourceResult:
    resumed = _artifact_result(artifact_path)
    if resumed is not None:
        return resumed

    recipe = _read_json(recipe_path, {})
    if recipe.get("enabled") is False:
        reason = str(recipe.get("reason") or "disabled by recipe")
        result = SourceResult(
            recipe_path.name,
            "empty",
            [],
            0,
            f"disabled: {reason}",
        )
        _atomic_json(artifact_path, result.payload(state, run_date))
        return result

    notes: list[str] = []
    pass_stats = _accepts_stats(source_runner)
    for attempt in (1, 2):
        stats: dict = {}
        try:
            if pass_stats:
                records = source_runner(recipe_path, state, stats)
            else:
                records = source_runner(recipe_path, state)
            status = "worked" if records else "empty"
            note = "" if records else _empty_note(stats)
            result = SourceResult(
                recipe_path.name,
                status,
                records,
                attempt,
                note,
                signal=_source_signal(stats, len(records)),
            )
            _atomic_json(artifact_path, result.payload(state, run_date))
            return result
        except Exception as exc:
            notes.append(f"attempt {attempt}: {type(exc).__name__}: {exc}")

    result = SourceResult(recipe_path.name, "failed", [], 2, "; ".join(notes))
    _atomic_json(artifact_path, result.payload(state, run_date))
    return result


def _identity(row: dict, state: str) -> str:
    """Match the site's stable content identity when counting new leads."""
    return content_id(
        state,
        str(row.get("address") or ""),
        str(row.get("name") or row.get("property") or ""),
    )


def _prepare_backup(state_dir: Path, run_dir: Path) -> list[dict]:
    leads_path = state_dir / "leads.json"
    old_rows = _read_json(leads_path, [])
    if not isinstance(old_rows, list):
        old_rows = []
    run_backup = run_dir / "leads.before-run.json"
    if run_backup.exists():
        baseline = _read_json(run_backup, [])
        return baseline if isinstance(baseline, list) else []
    _atomic_json(run_backup, old_rows)
    _atomic_json(state_dir / "leads.before-run.json", old_rows)
    return old_rows


def _update_health(root: Path, state: str, run_date: str, results: list[SourceResult]) -> None:
    health_path = root / "propertystack" / "runs" / "source-health.json"
    health = _read_json(health_path, {})
    if not isinstance(health, dict):
        health = {}
    sources = health.setdefault("sources", {})
    for result in results:
        sources[f"{state}/{result.recipe}"] = {
            "status": result.status,
            "count": len(result.records),
            "attempts": result.attempts,
            "checked": run_date,
            "note": result.note,
            "signal": result.signal,
        }
    health["updatedAt"] = datetime.now(timezone.utc).isoformat()
    _atomic_json(health_path, health)


def run_state(
    state: str,
    *,
    root: Path = ROOT,
    run_date: str | None = None,
    dry_run: bool = False,
    source_runner: Callable[[Path, str], list[dict]] = run_recipe,
) -> dict:
    state = state.lower()
    run_date = run_date or date.today().isoformat()
    recipe_dir = root / "propertystack" / "recipes" / state
    recipes = sorted(recipe_dir.glob("*.json"))
    if not recipes:
        raise ValueError(f"no recipes found for {state} in {recipe_dir}")

    if dry_run:
        print(f"{state}: dry run; {len(recipes)} sources would run (no network or files changed)")
        for recipe_path in recipes:
            recipe = _read_json(recipe_path, {})
            disabled = " (disabled)" if recipe.get("enabled") is False else ""
            print(f"  - {recipe_path.name}: {recipe.get('system', 'unknown')}{disabled}")
        return {"state": state, "dry_run": True, "sources": len(recipes)}

    state_dir = root / "propertystack" / "data" / state
    state_dir.mkdir(parents=True, exist_ok=True)
    run_dir = root / "propertystack" / "runs" / "area" / run_date / state
    source_dir = run_dir / "sources"
    source_dir.mkdir(parents=True, exist_ok=True)
    old_rows = _prepare_backup(state_dir, run_dir)

    results: list[SourceResult] = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        pending = {
            pool.submit(
                _run_source,
                recipe,
                state,
                run_date,
                source_dir / f"{recipe.stem}.json",
                source_runner,
            ): recipe
            for recipe in recipes
        }
        for future in as_completed(pending):
            result = future.result()
            results.append(result)
            if result.resumed:
                print(f"{state}: skipped {result.recipe}; already finished today")
            elif result.status == "failed":
                print(f"{state}: skipped {result.recipe}; source failed twice: {result.note}")
            elif result.attempts == 0:
                print(f"{state}: skipped {result.recipe}; {result.note}")
            elif result.status == "empty" and result.note:
                print(f"{state}: {result.recipe} empty; {result.note}")
            else:
                print(f"{state}: {result.recipe} {result.status} ({len(result.records)} leads)")

    # Completion order varies under the thread pool.  Recipe order keeps the
    # merge base and final ranked output repeatable from the same inputs.
    results.sort(key=lambda result: result.recipe)

    flagged = [(result, flag) for result in results for flag in result.flags]
    for result, flag in flagged:
        print(
            f"{state}: *** {flag.upper()} *** {result.recipe}: "
            f"{result.signal.get('note', '')}"
        )
    if not flagged:
        print(f"{state}: every measured source returned its fair share")

    records = [
        LeadRecord.from_dict(row)
        for result in results
        if result.status in FINISHED_STATUSES
        for row in result.records
    ]
    merged = score_and_rank(merge_records(records))
    rows = [record.to_dict() for record in merged]
    _atomic_json(state_dir / "leads.json", rows)

    previous_ids = {_identity(row, state) for row in old_rows if isinstance(row, dict)}
    new_count = sum(_identity(row, state) not in previous_ids for row in rows)
    permits = sum(row.get("stage") != "sold" for row in rows)
    sales = sum(row.get("stage") == "sold" for row in rows)
    _update_health(root, state, run_date, results)

    summary = {
        "state": state,
        "total": len(rows),
        "new": new_count,
        "permits": permits,
        "sales": sales,
        "worked": sum(result.status == "worked" for result in results),
        "empty": sum(result.status == "empty" for result in results),
        "failed": sum(result.status == "failed" for result in results),
        "suspect": sum("suspect" in result.flags for result in results),
        "stale": sum("stale" in result.flags for result in results),
    }
    _atomic_json(run_dir / "summary.json", summary)
    print(
        f"{state}: total {summary['total']}, new {summary['new']}, "
        f"permits {summary['permits']}, sales {summary['sales']} "
        f"(sources: {summary['worked']} worked, {summary['empty']} empty, "
        f"{summary['failed']} failed, {summary['suspect']} suspect, "
        f"{summary['stale']} stale)"
    )
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("states", nargs="+", help="state abbreviations, for example: nm tx az")
    parser.add_argument("--dry-run", action="store_true", help="list work without network or writes")
    args = parser.parse_args(argv)

    failed = False
    for state in args.states:
        try:
            run_state(state, dry_run=args.dry_run)
        except Exception as exc:
            failed = True
            print(f"{state.lower()}: run failed: {type(exc).__name__}: {exc}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
