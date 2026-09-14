"""lead-finder 3.3: which meeting system does a city's planning commission use.

Every city publishes its planning/zoning commission agendas somewhere, but the software
varies (Legistar, AgendaCenter, Granicus, PrimeGov, CivicClerk, BoardDocs, eSCRIBE,
IQM2, or a plain PDF-only page). This searches for the city's planning commission
agenda page, matches the URL/page markup against known patterns, and caches the result
as a per-city recipe so 3.4/3.5 know which reader to use.

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

# (system name, patterns to match against the result URL or fetched page HTML)
SYSTEM_PATTERNS = [
    ("legistar", re.compile(r"legistar", re.I)),
    ("agendacenter", re.compile(r"agendacenter", re.I)),
    ("granicus", re.compile(r"granicus", re.I)),
    ("primegov", re.compile(r"primegov", re.I)),
    ("civicclerk", re.compile(r"civicclerk", re.I)),
    ("boarddocs", re.compile(r"boarddocs", re.I)),
    ("escribemeetings", re.compile(r"escribemeetings|escribe", re.I)),
    ("iqm2", re.compile(r"iqm2", re.I)),
]

PLANNING_RE = re.compile(r"planning|zoning", re.I)

SearchFn = Callable[[str], list[dict]]
FetchFn = Callable[[str], "str | None"]


def slugify(city: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", city.lower()).strip("-")


def identify_system(text: str) -> str | None:
    for system, pattern in SYSTEM_PATTERNS:
        if pattern.search(text):
            return system
    return None


def find_meeting_system(
    city: str,
    state: str,
    search_fn: SearchFn,
    fetch_fn: FetchFn,
    recipes_dir: Path = RECIPES_DIR,
) -> dict:
    """Search for the city's planning commission agenda page and identify its system.

    Always returns a dict: either a saved recipe (has "system") or a skip note
    (has "skipped": True and "reason") -- never raises for "nothing found online".
    """
    results = search_fn(f"{city} {state} planning commission agenda")
    for result in results:
        url = result.get("url", "")
        if not url:
            continue
        system = identify_system(url)
        html = None
        if system is None:
            html = fetch_fn(url)
            if html:
                system = identify_system(html)
        if system is None:
            continue
        recipe = {
            "city": city,
            "state": state,
            "system": system,
            "agenda_url": url,
            "date_tested": datetime.date.today().isoformat(),
        }
        _save(recipe, city, recipes_dir)
        return recipe

    return {"city": city, "state": state, "skipped": True, "reason": "no agenda system identified"}


def _save(recipe: dict, city: str, recipes_dir: Path) -> None:
    recipes_dir.mkdir(parents=True, exist_ok=True)
    path = recipes_dir / f"agendas-{slugify(city)}.json"
    path.write_text(json.dumps(recipe, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    import argparse
    import sys

    p = argparse.ArgumentParser()
    p.add_argument("--city", required=True)
    p.add_argument("--state", required=True)
    args = p.parse_args()

    sys.path.insert(0, str(ROOT / "propertystack" / "skills" / "lead-finder"))
    from fetch import WebHelper  # propertystack/skills/lead-finder/fetch.py

    def _fetch(url: str) -> "str | None":
        import urllib.request

        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception:
            return None

    web = WebHelper()
    recipe = find_meeting_system(args.city, args.state.upper(), web.search, _fetch)
    print(json.dumps(recipe, indent=1))
