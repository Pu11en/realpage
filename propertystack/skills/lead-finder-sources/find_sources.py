"""lead-finder 2.2: permit-recipe catalog lookup.

For any city, ask the free catalog APIs -- in order, ArcGIS Online (by place name), the
city's own ArcGIS hub (found from the ArcGIS Online hit's owner org, never guessed), the
Socrata Discovery API, then data.gov's CKAN package_search -- for a building-permits
dataset. A dataset is only accepted after a real query returns permit-level rows (at
least 100 sample rows, an address field, and at least one date within the last 24
months) -- a small table of yearly totals (not permit-level rows) is rejected.
Save the result as a recipe under propertystack/recipes/<city-slug>.json. No place names
in this file -- city/state are always caller-supplied.
"""
from __future__ import annotations

import datetime
import json
import re
import urllib.parse
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RECIPES_DIR = ROOT / "propertystack" / "recipes"

SOCRATA_CATALOG = "https://api.us.socrata.com/api/catalog/v1"
ARCGIS_HUB_SEARCH = "https://hub.arcgis.com/api/search/v1/collections/dataset/items"
ARCGIS_ONLINE_SEARCH = "https://www.arcgis.com/sharing/rest/search"
ARCGIS_ORG_INFO = "https://www.arcgis.com/sharing/rest/community/organizations"
CKAN_CATALOG = "https://catalog.data.gov/api/3/action/package_search"

MULTIFAMILY_RE = re.compile(r"multi[- ]?family|apartment|\bdwelling\b", re.I)
PERMIT_KEYWORDS_RE = re.compile(r"permit", re.I)
MIN_SAMPLE_ROWS = 100
SAMPLE_LIMIT = 200

HttpGet = Callable[[str], dict]


def slugify(city: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", city.lower()).strip("-")


def find_sources(
    city: str,
    state: str,
    http_get: HttpGet,
    recipes_dir: Path = RECIPES_DIR,
    today: datetime.date | None = None,
) -> dict | None:
    """Try ArcGIS Online (by place), the city's ArcGIS hub, Socrata, then CKAN;
    test and save the first hit whose sample rows look like real permit data."""
    today = today or datetime.date.today()
    recipe = (
        _try_arcgis(city, state, http_get, today)
        or _try_socrata(city, state, http_get, today)
        or _try_ckan(city, state, http_get, today)
    )
    if recipe is None:
        return None
    recipes_dir.mkdir(parents=True, exist_ok=True)
    path = recipes_dir / f"{slugify(city)}.json"
    path.write_text(json.dumps(recipe, indent=2) + "\n", encoding="utf-8")
    return recipe


def _find_city_hub(city: str, state: str, http_get: HttpGet) -> str | None:
    """Ask ArcGIS Online for a permits item naming this place, then resolve its
    owner org to that org's own ArcGIS Hub search endpoint -- never guess a
    city's hub domain from its name."""
    query = f'{ARCGIS_ONLINE_SEARCH}?q=title:permits "{city}"&f=json'
    try:
        result = http_get(query)
    except Exception:
        return None
    for item in result.get("results", []):
        org_id = item.get("orgId")
        if not org_id:
            continue
        try:
            org = http_get(f"{ARCGIS_ORG_INFO}/{org_id}?f=json")
        except Exception:
            continue
        url_key = org.get("urlKey")
        if not url_key:
            continue
        return f"https://{url_key}-hub.arcgis.com/api/search/v1/collections/dataset/items"
    return None


def _domain_matches_place(domain: str, city: str, state: str) -> bool:
    """A Socrata/ArcGIS catalog text search can return another jurisdiction's
    dataset that merely mentions the city name (e.g. searching "White Plains
    building permits" hit a Howard County, MD portal). Require the portal's
    own domain to say it belongs to this city or state before trusting it."""
    domain = domain.lower()
    city_slug = re.sub(r"[^a-z0-9]", "", city.lower())
    if city_slug and city_slug in re.sub(r"[^a-z0-9]", "", domain):
        return True
    state_slug = state.lower()
    return bool(re.search(rf"[.-]{state_slug}[.-]|[.-]{state_slug}\.gov", domain))


def _try_socrata(city: str, state: str, http_get: HttpGet, today: datetime.date) -> dict | None:
    query = f"{SOCRATA_CATALOG}?q={_q(city)}+building+permits"
    try:
        catalog = http_get(query)
    except Exception:
        return None
    for result in catalog.get("results", []):
        resource = result.get("resource", {})
        if not PERMIT_KEYWORDS_RE.search(resource.get("name", "")):
            continue
        domain = (result.get("metadata") or {}).get("domain", "")
        if not _domain_matches_place(domain, city, state):
            continue
        endpoint = _socrata_endpoint(result)
        if not endpoint:
            continue
        rows = _sample_rows(endpoint, http_get)
        completeness = test_dataset(rows, today)
        if completeness is None:
            continue
        fields = _guess_fields(rows) if rows else {}
        return _recipe(city, state, "socrata", endpoint, fields, completeness)
    return None


def _try_arcgis(city: str, state: str, http_get: HttpGet, today: datetime.date) -> dict | None:
    hub_url = _find_city_hub(city, state, http_get)
    for search_url in filter(None, [hub_url, ARCGIS_HUB_SEARCH]):
        recipe = _try_arcgis_hub(city, state, search_url, http_get, today)
        if recipe is not None:
            return recipe
    return None


def _try_arcgis_hub(
    city: str, state: str, hub_search_url: str, http_get: HttpGet, today: datetime.date
) -> dict | None:
    query = f"{hub_search_url}?q={_q(city)}%20building%20permits"
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
        domain = urllib.parse.urlparse(endpoint).netloc
        if not _domain_matches_place(domain, city, state):
            continue
        rows = _sample_rows(endpoint, http_get)
        completeness = test_dataset(rows, today)
        if completeness is None:
            continue
        fields = _guess_fields(rows) if rows else {}
        return _recipe(city, state, "arcgis", endpoint, fields, completeness)
    return None


def _try_ckan(city: str, state: str, http_get: HttpGet, today: datetime.date) -> dict | None:
    query = f"{CKAN_CATALOG}?q={_q(city)}+building+permits"
    try:
        catalog = http_get(query)
    except Exception:
        return None
    for result in (catalog.get("result") or {}).get("results", []):
        if not PERMIT_KEYWORDS_RE.search(result.get("title", "")):
            continue
        organization = (result.get("organization") or {}).get("title", "")
        if not _domain_matches_place(organization, city, state):
            continue
        endpoint = _ckan_endpoint(result)
        if not endpoint:
            continue
        rows = _sample_rows(endpoint, http_get)
        completeness = test_dataset(rows, today)
        if completeness is None:
            continue
        fields = _guess_fields(rows) if rows else {}
        return _recipe(city, state, "ckan", endpoint, fields, completeness)
    return None


def _ckan_endpoint(result: dict) -> str | None:
    for res in result.get("resources", []):
        if (res.get("format") or "").lower() in ("csv", "json"):
            return res.get("url")
    return None


def test_dataset(rows: list[dict], today: datetime.date | None = None) -> str | None:
    """Return a completeness note if `rows` looks like real, recent multifamily permit
    data, else None. Requires a real permit-level sample (not a small yearly-totals
    table), an address field, and at least one row dated within the last 24 months."""
    if not rows or len(rows) < MIN_SAMPLE_ROWS:
        return None
    today = today or datetime.date.today()
    has_address = any(
        _first_matching_key(row, "address") or _first_matching_key(row, "stname") or _first_matching_key(row, "street")
        for row in rows
    )
    if not has_address:
        return None
    date_key = next((_first_matching_key(row, "date") for row in rows if _first_matching_key(row, "date")), None)
    if not date_key or not _has_recent_date(rows, date_key, today):
        return None
    mf_hits = sum(1 for row in rows if MULTIFAMILY_RE.search(" ".join(str(v) for v in row.values())))
    fields_found = ", ".join(sorted({k for row in rows for k in row if _looks_useful_field(k)}))
    return f"has {fields_found or 'no recognizable fields'}; {mf_hits} of {len(rows)} sample rows look multifamily"


def _has_recent_date(rows: list[dict], date_key: str, today: datetime.date, months: int = 24) -> bool:
    cutoff = today - datetime.timedelta(days=months * 31)
    for row in rows:
        value = row.get(date_key)
        if not value:
            continue
        parsed = _parse_date(str(value))
        if parsed is not None and parsed >= cutoff:
            return True
    return False


def _parse_date(text: str) -> datetime.date | None:
    text = text[:10]
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _looks_useful_field(key: str) -> bool:
    return bool(re.search(r"unit|date|address|type|permit", key, re.I))


def _first_matching_key(row: dict, needle: str, exclude: str = "") -> str | None:
    for key in row:
        low = key.lower()
        if needle in low and not (exclude and exclude in low):
            return key
    return None


def _guess_fields(rows: list[dict]) -> dict:
    """Field-name synonyms across permit systems (Socrata/ArcGIS column names vary
    city to city): prefer a plain "issued" date over an expiration/final-inspection
    date, and accept "street"/"stname" as well as "address" for the address column
    -- both seen in real city permit datasets. Merge keys across every sampled row,
    not just the first -- Socrata omits null fields from a row's JSON entirely, so
    one row alone can be missing columns other rows have."""
    row: dict = {}
    for r in rows:
        row.update(r)
    fields = {}
    issue_key = (
        _first_matching_key(row, "issue")
        or _first_matching_key(row, "date", exclude="exp")
        or _first_matching_key(row, "date")
    )
    if issue_key:
        fields["issue_date"] = issue_key
    for label, needles in (
        ("permit_type", ("type",)),
        ("units", ("unit",)),
        ("address", ("address", "stname", "street")),
    ):
        for needle in needles:
            key = _first_matching_key(row, needle)
            if key:
                fields[label] = key
                break
    return fields


def _sample_rows(endpoint: str, http_get: HttpGet) -> list[dict]:
    try:
        data = http_get(f"{endpoint}?$limit={SAMPLE_LIMIT}" if "?" not in endpoint else endpoint)
    except Exception:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "features" in data:
        return [f.get("attributes", {}) for f in data.get("features", [])]
    return []


def _socrata_endpoint(result: dict) -> str | None:
    # `link` is the human-browsable catalog page, not the API -- always build
    # the real /resource/<id>.json endpoint from domain + resource id instead.
    resource = result.get("resource", {})
    resource_id = resource.get("id")
    domain = (result.get("metadata") or {}).get("domain")
    if resource.get("type") == "filter":
        # A "filter" resource is a saved view of another dataset; Socrata's
        # /resource/<id>.json endpoint 403s for the view id itself, so query
        # the parent dataset instead (parent_fxf: the base dataset's id).
        parent_fxf = resource.get("parent_fxf") or []
        if parent_fxf:
            resource_id = parent_fxf[0]
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
