"""lead-finder 2.3: find-sources fallback for cities with no Socrata/ArcGIS catalog hit.

Used only after find_sources.find_sources() (2.2) returns None. Searches for the city's
permit portal, identifies which system it runs (by URL/markup pattern), tests it on 5
permits, and saves a recipe the same way as 2.2. If nothing usable turns up online, the
city is reported skipped with a reason -- never guessed at.

No place names anywhere in this file -- city/state are always caller-supplied.
"""
from __future__ import annotations

import datetime
import json
import re
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RECIPES_DIR = ROOT / "propertystack" / "recipes"

MIN_SAMPLE_PERMITS = 5

# (system name, patterns to match against the result URL or fetched page HTML)
SYSTEM_PATTERNS = [
    ("accela", re.compile(r"aca-prod\.accela\.com|citizenaccess", re.I)),
    ("tyler-energov", re.compile(r"energov|citizenselfservice", re.I)),
    ("opengov", re.compile(r"opengov\.com|permitting\.opengov", re.I)),
    ("centralsquare", re.compile(r"centralsquare", re.I)),
    ("mygovernmentonline", re.compile(r"mygovernmentonline", re.I)),
]

REPORT_FILE_RE = re.compile(r"\.(pdf|xlsx?|csv)(\?|$)", re.I)
PERMIT_ROW_RE = re.compile(r"permit[^a-z]{0,20}(no\.?|number|#)?\s*[:#]?\s*\d{2,}", re.I)
MULTIFAMILY_RE = re.compile(r"multi[- ]?family|apartment|\bdwelling\b", re.I)

SearchFn = Callable[[str], list[dict]]
FetchFn = Callable[[str], "str | None"]


def slugify(city: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", city.lower()).strip("-")


def find_sources_fallback(
    city: str,
    state: str,
    search_fn: SearchFn,
    fetch_fn: FetchFn,
    recipes_dir: Path = RECIPES_DIR,
) -> dict:
    """Search for the city's permit portal, identify + test it, and save a recipe.

    Always returns a dict: either a saved recipe (has "system") or a skip note
    (has "skipped": True and "reason") -- never raises for "nothing found online".
    """
    results = search_fn(f"{city} {state} building permit portal citizen access permits online")
    for result in results:
        url = result.get("url", "")
        if not url:
            continue
        system = identify_system(url)
        html = fetch_fn(url)
        if system is None and html:
            system = identify_system(html)
        if system is None:
            continue
        if not html:
            continue
        sample_count = count_sample_permits(html)
        if sample_count < MIN_SAMPLE_PERMITS:
            continue
        mf_hits = count_multifamily_hits(html)
        recipe = _recipe(city, state, system, url, sample_count, mf_hits)
        _save(recipe, city, recipes_dir)
        return recipe

    report = _find_report_file(results, fetch_fn)
    if report is not None:
        url, sample_count, mf_hits = report
        recipe = _recipe(city, state, "report-file", url, sample_count, mf_hits)
        _save(recipe, city, recipes_dir)
        return recipe

    return {"city": city, "state": state, "skipped": True, "reason": "no permits online"}


def identify_system(text: str) -> str | None:
    for system, pattern in SYSTEM_PATTERNS:
        if pattern.search(text):
            return system
    return None


def count_sample_permits(html: str) -> int:
    return len(PERMIT_ROW_RE.findall(html))


def count_multifamily_hits(html: str) -> int:
    return len(MULTIFAMILY_RE.findall(html))


def _find_report_file(results: list[dict], fetch_fn: FetchFn) -> tuple | None:
    for result in results:
        url = result.get("url", "")
        if not url or not REPORT_FILE_RE.search(url):
            continue
        html = fetch_fn(url)
        if not html:
            continue
        sample_count = count_sample_permits(html)
        if sample_count < MIN_SAMPLE_PERMITS:
            continue
        return url, sample_count, count_multifamily_hits(html)
    return None


def _recipe(city: str, state: str, system: str, url: str, sample_count: int, mf_hits: int) -> dict:
    return {
        "city": city,
        "state": state,
        "system": system,
        "endpoint": url,
        "date_tested": datetime.date.today().isoformat(),
        "completeness": f"tested {sample_count} sample permits; {mf_hits} look multifamily",
    }


def _save(recipe: dict, city: str, recipes_dir: Path) -> None:
    recipes_dir.mkdir(parents=True, exist_ok=True)
    path = recipes_dir / f"{slugify(city)}.json"
    path.write_text(json.dumps(recipe, indent=2) + "\n", encoding="utf-8")
