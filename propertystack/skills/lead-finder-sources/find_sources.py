"""lead-finder 2.2: permit-recipe catalog lookup (Socrata Discovery API + ArcGIS Hub search).

For any city, ask the two free catalog APIs for a building-permits dataset, test the dataset
really has recent rows that look like multifamily permits, and save the result as a recipe
under propertystack/recipes/<city-slug>.json. No place names in this file -- city/state are
always caller-supplied.
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

SOCRATA_CATALOG = "https://api.us.socrata.com/api/catalog/v1"
ARCGIS_HUB_SEARCH = "https://hub.arcgis.com/api/search/v1/collections/dataset/items"

MULTIFAMILY_RE = re.compile(r"multi[- ]?family|apartment|\bdwelling\b", re.I)
PERMIT_KEYWORDS_RE = re.compile(r"permit", re.I)

HttpGet = Callable[[str], dict]


def slugify(city: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", city.lower()).strip("-")


def find_sources(city: str, state: str, http_get: HttpGet, recipes_dir: Path = RECIPES_DIR) -> dict | None:
    """Try Socrata Discovery, then ArcGIS Hub search; test and save the first hit that works."""
    recipe = _try_socrata(city, state, http_get) or _try_arcgis(city, state, http_get)
    if recipe is None:
        return None
    recipes_dir.mkdir(parents=True, exist_ok=True)
    path = recipes_dir / f"{slugify(city)}.json"
    path.write_text(json.dumps(recipe, indent=2) + "\n", encoding="utf-8")
    return recipe


def _try_socrata(city: str, state: str, http_get: HttpGet) -> dict | None:
    query = f"{SOCRATA_CATALOG}?q={_q(city)}+building+permits"
    try:
        catalog = http_get(query)
    except Exception:
        return None
    for result in catalog.get("results", []):
        resource = result.get("resource", {})
        if not PERMIT_KEYWORDS_RE.search(resource.get("name", "")):
            continue
        endpoint = _socrata_endpoint(result)
        if not endpoint:
            continue
        rows = _sample_rows(endpoint, http_get)
        completeness = test_dataset(rows)
        if completeness is None:
            continue
        fields = _guess_fields(rows[0]) if rows else {}
        return _recipe(city, state, "socrata", endpoint, fields, completeness)
    return None


def _try_arcgis(city: str, state: str, http_get: HttpGet) -> dict | None:
    query = f"{ARCGIS_HUB_SEARCH}?q={_q(city)}%20building%20permits"
    try:
        catalog = http_get(query)
    except Exception:
        return None
    for item in catalog.get("data", []):
        attrs = item.get("attributes", {})
        if not PERMIT_KEYWORDS_RE.search(attrs.get("name", "")):
            continue
        endpoint = attrs.get("url")
        if not endpoint:
            continue
        rows = _sample_rows(endpoint, http_get)
        completeness = test_dataset(rows)
        if completeness is None:
            continue
        fields = _guess_fields(rows[0]) if rows else {}
        return _recipe(city, state, "arcgis", endpoint, fields, completeness)
    return None


def test_dataset(rows: list[dict]) -> str | None:
    """Return a completeness note if `rows` looks like recent multifamily permit data, else None."""
    if not rows:
        return None
    has_units = any(_first_matching_key(row, "unit") for row in rows)
    has_date = any(_first_matching_key(row, "date") for row in rows)
    if not (has_units or has_date):
        return None
    mf_hits = sum(1 for row in rows if MULTIFAMILY_RE.search(" ".join(str(v) for v in row.values())))
    fields_found = ", ".join(sorted({k for row in rows for k in row if _looks_useful_field(k)}))
    return f"has {fields_found or 'no recognizable fields'}; {mf_hits} of {len(rows)} sample rows look multifamily"


def _looks_useful_field(key: str) -> bool:
    return bool(re.search(r"unit|date|address|type|permit", key, re.I))


def _first_matching_key(row: dict, needle: str) -> str | None:
    for key in row:
        if needle in key.lower():
            return key
    return None


def _guess_fields(row: dict) -> dict:
    fields = {}
    for label, needle in (("permit_type", "type"), ("issue_date", "date"), ("units", "unit"), ("address", "address")):
        key = _first_matching_key(row, needle)
        if key:
            fields[label] = key
    return fields


def _sample_rows(endpoint: str, http_get: HttpGet) -> list[dict]:
    try:
        data = http_get(f"{endpoint}?$limit=20" if "?" not in endpoint else endpoint)
    except Exception:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "features" in data:
        return [f.get("attributes", {}) for f in data.get("features", [])]
    return []


def _socrata_endpoint(result: dict) -> str | None:
    link = result.get("link")
    if link:
        return link
    resource = result.get("resource", {})
    resource_id = resource.get("id")
    domain = (result.get("metadata") or {}).get("domain")
    if resource_id and domain:
        return f"https://{domain}/resource/{resource_id}.json"
    return None


def _recipe(city: str, state: str, system: str, endpoint: str, fields: dict, completeness: str) -> dict:
    return {
        "city": city,
        "state": state,
        "system": system,
        "endpoint": endpoint,
        "fields": fields,
        "date_tested": datetime.date.today().isoformat(),
        "completeness": completeness,
    }


def _q(text: str) -> str:
    import urllib.parse

    return urllib.parse.quote(text)
