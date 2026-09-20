#!/usr/bin/env python3
"""Find, prove, and save apartment-permit sources for one run of cities.

Discovery is deliberately separate from acceptance: search may suggest URLs, but the exact
URL must return structured rows and those rows must pass both apartment-project guardrails and
the repository's lead-data quality gate before a recipe is written.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import json
import re
import sys
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
for path in (
    ROOT / "propertystack" / "skills" / "lead-finder",
    ROOT / "propertystack" / "skills" / "lead-finder-permits",
    ROOT / "tooling" / "qa",
    ROOT / "site" / "data",
):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_data import content_id  # noqa: E402
from check_lead_data import check_state  # noqa: E402
from find_upcoming import find_upcoming  # noqa: E402


SEARCH_STAGES = (
    "city-open-data",
    "socrata",
    "arcgis",
    "accela",
    "county",
)
MAX_SEARCHES_PER_CITY = 20
MAX_SEARCHES_PER_RUN = 100
MIN_APARTMENT_ROWS = 5
HTTP_HEADERS = {"User-Agent": "CraneSignalSourceCheck/1.0"}
APARTMENT_RE = re.compile(r"multi[- ]?family|apartments?|\bmultifamily\b", re.I)
STREET_RE = re.compile(r"\b\d+[a-z-]*\s+\S+", re.I)

SearchFn = Callable[[str, str, str, str], list[dict]]
FetchFn = Callable[[str], object]


@dataclass
class SearchBudget:
    """One budget object is shared by every city in a run."""

    per_city_limit: int = MAX_SEARCHES_PER_CITY
    run_limit: int = MAX_SEARCHES_PER_RUN
    total: int = 0
    by_city: dict[str, int] = field(default_factory=dict)

    def spend(self, city: str, state: str) -> bool:
        key = f"{city.strip().casefold()}, {state.strip().upper()}"
        used = self.by_city.get(key, 0)
        if used >= self.per_city_limit or self.total >= self.run_limit:
            return False
        self.by_city[key] = used + 1
        self.total += 1
        return True

    def used_for(self, city: str, state: str) -> int:
        return self.by_city.get(f"{city.strip().casefold()}, {state.strip().upper()}", 0)


@dataclass
class FindResult:
    city: str
    state: str
    recipe: dict | None
    searches: int
    note: str

    @property
    def found(self) -> bool:
        return self.recipe is not None


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")


def _query(stage: str, city: str, state: str) -> str:
    terms = {
        "city-open-data": "official open data building permits API",
        "socrata": "Socrata building permits dataset API",
        "arcgis": "ArcGIS building permits FeatureServer query",
        "accela": "Accela Citizen Access building permits data API",
        "county": "county open data building permits API",
    }
    return f'"{city}" "{state}" {terms[stage]}'


def find_source(
    city: str,
    state: str,
    search_fn: SearchFn,
    fetch_fn: FetchFn,
    *,
    root: Path = ROOT,
    budget: SearchBudget | None = None,
    today: dt.date | None = None,
) -> FindResult:
    """Search in the required order and save only a tested, QA-clean recipe."""
    city = city.strip()
    state = state.strip().upper()
    today = today or dt.date.today()
    budget = budget or SearchBudget()
    seen_urls: set[str] = set()

    for stage in SEARCH_STAGES:
        if not budget.spend(city, state):
            note = "search limit reached before a source passed"
            _record_needs_source(root, city, state, today, budget.used_for(city, state), note)
            return FindResult(city, state, None, budget.used_for(city, state), note)
        try:
            results = search_fn(stage, _query(stage, city, state), city, state) or []
        except Exception:
            results = []
        for candidate in results:
            url = str(candidate.get("url") or candidate.get("endpoint") or "").strip()
            if url in seen_urls or not _web_url(url):
                continue
            seen_urls.add(url)
            if not _matches_city(candidate, city):
                continue
            recipe = _test_candidate(candidate, stage, city, state, url, fetch_fn, today)
            if recipe is None:
                continue
            path = root / "propertystack" / "recipes" / state.lower() / f"{slugify(city)}.json"
            _write_json(path, recipe)
            _remove_need(root, city, state)
            return FindResult(
                city,
                state,
                recipe,
                budget.used_for(city, state),
                f"saved {path.relative_to(root)}",
            )

    note = "no candidate returned five QA-clean apartment projects"
    _record_needs_source(root, city, state, today, budget.used_for(city, state), note)
    return FindResult(city, state, None, budget.used_for(city, state), note)


def find_sources(
    locations: list[tuple[str, str]],
    search_fn: SearchFn,
    fetch_fn: FetchFn,
    *,
    root: Path = ROOT,
    budget: SearchBudget | None = None,
    today: dt.date | None = None,
) -> list[FindResult]:
    """Process a whole run with one budget, so search 101 can never start."""
    run_budget = budget or SearchBudget()
    return [
        find_source(
            city,
            state,
            search_fn,
            fetch_fn,
            root=root,
            budget=run_budget,
            today=today,
        )
        for city, state in locations
    ]


def _test_candidate(
    candidate: dict,
    stage: str,
    city: str,
    state: str,
    url: str,
    fetch_fn: FetchFn,
    today: dt.date,
) -> dict | None:
    try:
        payload = fetch_fn(url)
    except Exception:
        return None
    rows = _coerce_rows(payload)
    fields = _guess_fields(rows)
    if not {"address", "issue_date"}.issubset(fields):
        return None
    qualifying = [row for row in rows if _qualifies(row, fields)]
    if len(qualifying) < MIN_APARTMENT_ROWS:
        return None

    system = _system(candidate, stage, payload)
    recipe = {
        "city": city,
        "state": state,
        "system": system,
        "endpoint": url,
        "fields": fields,
        "source": "auto-found",
        "date_tested": today.isoformat(),
        "validation": {
            "apartment_rows": len(qualifying),
            "minimum_required": MIN_APARTMENT_ROWS,
            "lead_data_check": "passed",
            "discovery_stage": stage,
        },
    }
    leads = find_upcoming(city, state, state.lower(), recipe, lambda _url: qualifying, today=today)
    if len(leads) < MIN_APARTMENT_ROWS or not _passes_lead_gate(leads, state):
        return None
    return recipe


def _coerce_rows(payload: object) -> list[dict]:
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8", errors="replace")
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError:
            try:
                return [dict(row) for row in csv.DictReader(io.StringIO(payload))]
            except (csv.Error, TypeError):
                return []
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if not isinstance(payload, dict):
        return []
    if isinstance(payload.get("features"), list):
        return [
            feature.get("attributes", {})
            for feature in payload["features"]
            if isinstance(feature, dict) and isinstance(feature.get("attributes"), dict)
        ]
    for key in ("results", "records", "data", "items"):
        value = payload.get(key)
        if isinstance(value, list):
            return [row for row in value if isinstance(row, dict)]
    return []


def _guess_fields(rows: list[dict]) -> dict:
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)

    def pick(patterns: tuple[str, ...], excludes: tuple[str, ...] = ()) -> str | None:
        for pattern in patterns:
            for key in keys:
                lowered = key.casefold()
                if pattern in lowered and not any(item in lowered for item in excludes):
                    return key
        return None

    fields = {}
    address = pick(("address", "street_address", "site_address", "location"))
    issue_date = pick(("issue_date", "issued", "permit_date", "date"), ("expire", "final"))
    units = pick(("units", "unit_count", "dwelling"))
    description = pick(("description", "project_name", "project", "work", "permit_type", "type", "name"))
    if address:
        fields["address"] = address
    if issue_date:
        fields["issue_date"] = issue_date
    if units:
        fields["units"] = units
    if description:
        fields["permit_type"] = description
        fields["name"] = description
    return fields


def _qualifies(row: dict, fields: dict) -> bool:
    address = str(row.get(fields.get("address", "")) or "").strip()
    if not STREET_RE.search(address):
        return False
    if _parse_date(row.get(fields.get("issue_date", ""))) is None:
        return False
    units = _integer(row.get(fields.get("units", ""))) if fields.get("units") else None
    description = str(row.get(fields.get("permit_type", "")) or "")
    return bool((units is not None and units >= 20) or APARTMENT_RE.search(description))


def _parse_date(value: object) -> dt.date | None:
    if isinstance(value, (int, float)):
        try:
            return dt.datetime.fromtimestamp(value / 1000, tz=dt.timezone.utc).date()
        except (OverflowError, OSError, ValueError):
            return None
    text = str(value or "").strip()
    if not text:
        return None
    for pattern in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            return dt.datetime.strptime(text[:19], pattern).date()
        except ValueError:
            continue
    return None


def _integer(value: object) -> int | None:
    try:
        return int(float(str(value).replace(",", "").strip()))
    except (TypeError, ValueError):
        return None


def _passes_lead_gate(leads: list, state: str) -> bool:
    rows = [lead.to_dict() if hasattr(lead, "to_dict") else lead for lead in leads]
    built = []
    for row in rows:
        item = dict(row)
        item["id"] = content_id(state, str(item.get("address") or ""), str(item.get("name") or ""))
        built.append(item)
    with tempfile.TemporaryDirectory(prefix="cranesignal-source-check-") as folder:
        root = Path(folder)
        raw_path = root / "leads.json"
        built_path = root / "built.json"
        previous_path = root / "previous.json"
        raw_path.write_text(json.dumps(rows), encoding="utf-8")
        built_path.write_text(json.dumps(built), encoding="utf-8")
        previous_path.write_text("[]\n", encoding="utf-8")
        result = check_state(raw_path, previous=previous_path, built=built_path)
    return not result.errors


def _system(candidate: dict, stage: str, payload: object) -> str:
    explicit = str(candidate.get("system") or "").strip().casefold()
    if explicit in {"socrata", "arcgis", "accela", "open-data"}:
        return explicit
    if isinstance(payload, dict) and isinstance(payload.get("features"), list):
        return "arcgis"
    if stage in {"socrata", "arcgis", "accela"}:
        return stage
    return "open-data"


def _matches_city(candidate: dict, city: str) -> bool:
    haystack = " ".join(str(candidate.get(key) or "") for key in ("title", "url", "snippet", "jurisdiction"))
    normalized = re.sub(r"[^a-z0-9]+", " ", haystack.casefold())
    words = [word for word in re.sub(r"[^a-z0-9]+", " ", city.casefold()).split() if len(word) >= 4]
    return not words or all(word in normalized for word in words)


def _web_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _need_prefix(city: str, state: str) -> str:
    return f"- {city}, {state.upper()} —"


def _record_needs_source(
    root: Path,
    city: str,
    state: str,
    today: dt.date,
    searches: int,
    reason: str,
) -> None:
    path = root / "propertystack" / "runs" / "needs-a-source.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else ["# Cities that need a source", ""]
    prefix = _need_prefix(city, state)
    lines = [line for line in lines if not line.startswith(prefix)]
    lines.append(f"{prefix} {reason} (checked {today.isoformat()}; {searches} searches)")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _remove_need(root: Path, city: str, state: str) -> None:
    path = root / "propertystack" / "runs" / "needs-a-source.md"
    if not path.exists():
        return
    prefix = _need_prefix(city, state)
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if not line.startswith(prefix)]
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _fetch_url(url: str) -> object:
    request = urllib.request.Request(url, headers=HTTP_HEADERS)
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


class LiveSearch:
    def __init__(self, root: Path):
        lead_finder = root / "propertystack" / "skills" / "lead-finder"
        if str(lead_finder) not in sys.path:
            sys.path.insert(0, str(lead_finder))
        from fetch import WebHelper

        self.web = WebHelper(cache_dir=root / "propertystack" / "runs" / "cache")

    def __call__(self, _stage: str, query: str, _city: str, _state: str) -> list[dict]:
        return self.web.search(query, n=10)


class RecordedResponses:
    """Offline search/fetch replay used by regression tests and fixture debugging."""

    def __init__(self, payload: dict):
        self.searches = payload.get("searches", {})
        self.fetches = payload.get("fetches", {})

    @classmethod
    def from_path(cls, path: Path) -> "RecordedResponses":
        return cls(json.loads(path.read_text(encoding="utf-8")))

    def search(self, stage: str, _query: str, _city: str, _state: str) -> list[dict]:
        value = self.searches.get(stage, [])
        return value if isinstance(value, list) else []

    def fetch(self, url: str) -> object:
        if url not in self.fetches:
            raise KeyError(f"no recorded response for {url}")
        return self.fetches[url]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "locations",
        nargs="+",
        metavar="CITY STATE",
        help='one or more city/state pairs, for example: "Santa Fe" NM "Austin" TX',
    )
    parser.add_argument("--recorded", type=Path, help="offline recorded search/fetch responses")
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    if len(args.locations) % 2:
        parser.error("locations must be CITY STATE pairs")
    locations = list(zip(args.locations[0::2], args.locations[1::2]))

    if args.recorded:
        replay = RecordedResponses.from_path(args.recorded)
        search_fn, fetch_fn = replay.search, replay.fetch
    else:
        search_fn, fetch_fn = LiveSearch(args.root), _fetch_url
    results = find_sources(locations, search_fn, fetch_fn, root=args.root)
    for result in results:
        if result.found:
            print(
                f"{result.city}, {result.state}: source found and tested "
                f"({result.recipe['endpoint']}; {result.searches} searches)"
            )
        else:
            print(
                f"{result.city}, {result.state}: needs a source; {result.note} "
                f"({result.searches} searches)"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
