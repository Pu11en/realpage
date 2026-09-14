"""lead-finder 2.5: project-details.

Cleans addresses with the free Census batch geocoder (so merge.py's 75m
geocode match is reliable) and does one web lookup per project to fill in
units, developer, opening date, a news link and a website -- never guessing.
A project whose units are still unknown after the lookup is dropped. No place
names in this file -- city/state/records are always caller-supplied.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lead-finder"))
from record import LeadRecord  # noqa: E402

GeocodeFn = Callable[[str], object]
SearchFn = Callable[[str, int], list]
FetchFn = Callable[[str], object]

UNITS_RE = re.compile(r"(\d{2,4})[\s-]*(?:unit|units|apartment homes|apartments)", re.I)
DEVELOPER_RE = re.compile(r"(?:developed by|developer[:\s])\s*([A-Z][\w&.,' -]{2,60}?)(?=[.\n]|$)", re.I)
OPENING_RE = re.compile(
    r"(?:opening|now leasing|leasing (?:in|starting)|available)[^.\n]{0,20}?"
    r"((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}|\d{4})",
    re.I,
)
NEWS_HOST_RE = re.compile(r"news|journal|times|tribune|herald|business|press", re.I)


def geocode_address(address: str, city: str, state: str, geocode_fn: GeocodeFn) -> tuple[float, float] | None:
    """Look up lat/lon for a single address via the free Census batch/one-line
    geocoder (https://geocoding.geo.census.gov/geocoder/locations/onelineaddress).
    `geocode_fn` takes the query string and returns the parsed JSON response
    (injectable so tests never hit the network)."""
    if not address:
        return None
    query = f"{address}, {city}, {state}"
    try:
        data = geocode_fn(query)
    except Exception:
        return None
    matches = (data or {}).get("result", {}).get("addressMatches", [])
    if not matches:
        return None
    coords = matches[0].get("coordinates", {})
    lat, lon = coords.get("y"), coords.get("x")
    if lat is None or lon is None:
        return None
    return float(lat), float(lon)


def fill_project_details(
    record: LeadRecord,
    search_fn: SearchFn,
    fetch_fn: FetchFn,
    geocode_fn: GeocodeFn | None = None,
) -> LeadRecord | None:
    """One web lookup per project: geocode the address, then search+fetch the
    top result to fill in units/developer/opening_date/website/news link.
    Returns None (drop) if units are still unknown after the lookup."""
    if geocode_fn is not None:
        coords = geocode_address(record.address, record.city, record.area, geocode_fn)
        if coords is not None:
            record.lat, record.lon = coords

    query = f'"{record.address}" {record.city} apartments'
    results = search_fn(query, 5) or []

    website = _pick_website(results)
    if website:
        record.website = website
        record.links["website"] = website

    news = _pick_news(results)
    if news:
        record.links["news"] = news

    for result in results:
        url = result.get("url", "") if isinstance(result, dict) else ""
        if not url:
            continue
        page = fetch_fn(url)
        html = getattr(page, "html", "") if not isinstance(page, dict) else page.get("html", "")
        ok = getattr(page, "ok", False) if not isinstance(page, dict) else page.get("ok", False)
        if not ok or not html:
            continue
        _apply_facts_from_page(record, html, url)
        if record.units is not None:
            break

    if record.units is None:
        return None
    return record


def _pick_website(results: list) -> str:
    for result in results:
        if not isinstance(result, dict):
            continue
        url = result.get("url", "")
        if url and not NEWS_HOST_RE.search(url):
            return url
    return ""


def _pick_news(results: list) -> str:
    for result in results:
        if not isinstance(result, dict):
            continue
        url = result.get("url", "")
        if url and NEWS_HOST_RE.search(url):
            return url
    return ""


def _apply_facts_from_page(record: LeadRecord, html: str, url: str) -> None:
    if record.units is None:
        m = UNITS_RE.search(html)
        if m:
            record.units = int(m.group(1))
            record.sources.append({"fact": "units", "url": url})

    if not record.developer:
        m = DEVELOPER_RE.search(html)
        if m:
            record.developer = m.group(1).strip()
            record.sources.append({"fact": "developer", "url": url})

    if not record.opening_date:
        m = OPENING_RE.search(html)
        if m:
            record.opening_date = m.group(1).strip()
            record.sources.append({"fact": "opening_date", "url": url})
