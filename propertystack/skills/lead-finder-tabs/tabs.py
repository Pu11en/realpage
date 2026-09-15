"""lead-finder T2: TDLR TABS -- the statewide backbone.

TDLR (the state's Department of Licensing and Regulation) runs the
Architectural Barriers project registry (TABS): a statewide list of every
registered construction project, searchable by keyword and filterable by
registration date. Every apartment/multifamily project of any real size has
to register here before it can be occupied, so this is the one source that
covers the whole state (not just the cities with their own permit feeds).

Two network calls per project: a paginated keyword search (returns a compact
row per project: name, city/county codes, type of work, cost, estimated
start/end) and a detail page (full address, scope, square footage, owner
name/address/phone, design firm). Both are dependency-injected
(`fetch_search`, `fetch_detail`) so the pytest suite never touches the
network; `default_fetch_search`/`default_fetch_detail` (real HTTP) are used
only by `live_self_test.py`.

No place names in this file -- keywords, date cutoff, cost floor and the
"new construction" type-of-work code all come from the recipe
(`recipes/tx/tabs.json`).
"""
from __future__ import annotations

import datetime
import json
import re
import sys
import urllib.request
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lead-finder"))
from merge import merge_records  # noqa: E402
from record import LeadRecord  # noqa: E402

FetchSearch = Callable[[dict], dict]
FetchDetail = Callable[[str], str]

# The detail page is server-rendered HTML with plain "<dt>Label:</dt><dd>value</dd>"
# pairs -- no JSON API to hit for it, so these are parsed straight out of the
# markup rather than guessed from the compact search-row fields.
_DT_DD_RE = re.compile(r"<dt>\s*([^<]+?):?\s*</dt>\s*((?:<dd>.*?</dd>\s*)+)", re.S)
_DD_RE = re.compile(r"<dd>(.*?)</dd>", re.S)
_TAG_RE = re.compile(r"<[^>]+>")


def find_tabs_projects(
    area: str,
    recipe: dict,
    fetch_search: FetchSearch,
    fetch_detail: FetchDetail,
    today: datetime.date | None = None,
) -> list[LeadRecord]:
    """Search TABS for every keyword in the recipe, keep new-construction
    projects at/above the recipe's cost floor, fetch each one's detail page,
    and return one LeadRecord per project (deduped across keywords by
    project number -- a project can match more than one keyword)."""
    today = today or datetime.date.today()
    rows_by_number: dict[str, dict] = {}
    for keyword in recipe.get("keywords", []):
        for row in _search_all_pages(keyword, recipe, fetch_search):
            number = str(row.get("ProjectNumber") or "")
            if not number:
                continue
            if not _qualifies(row, recipe):
                continue
            rows_by_number.setdefault(number, row)

    records = []
    for number, row in rows_by_number.items():
        detail_html = _safe_fetch_detail(number, recipe, fetch_detail)
        records.append(_build_record(number, row, detail_html, area, recipe))
    return merge_records(records)


def _search_all_pages(keyword: str, recipe: dict, fetch_search: FetchSearch) -> list[dict]:
    page_size = recipe.get("page_size", 100)
    start = 0
    rows: list[dict] = []
    while True:
        payload = {
            "draw": 1,
            "start": start,
            "length": page_size,
            "ProjectName": keyword,
            "RegistrationDateBegin": recipe.get("registration_date_begin", ""),
            "DataVersionId": recipe.get("data_version_id", 900001),
        }
        try:
            response = fetch_search(payload)
        except Exception:
            break
        page_rows = (response or {}).get("data") or []
        rows.extend(page_rows)
        total = (response or {}).get("recordsTotal", len(rows))
        start += page_size
        if len(page_rows) < page_size or start >= total:
            break
    return rows


def _qualifies(row: dict, recipe: dict) -> bool:
    if row.get("TypeOfWork") != recipe.get("new_construction_type_of_work"):
        return False
    cost = row.get("EstimatedCost")
    try:
        cost = float(cost)
    except (TypeError, ValueError):
        return False
    return cost >= recipe.get("min_estimated_cost", 0)


def _safe_fetch_detail(number: str, recipe: dict, fetch_detail: FetchDetail) -> str:
    try:
        return fetch_detail(number) or ""
    except Exception:
        return ""


def _parse_detail_fields(html: str) -> dict[str, list[str]]:
    """Every "<dt>Label:</dt><dd>value</dd>..." pair in the detail page,
    keyed by the label text (lowercased) -- a label can have more than one
    <dd> (e.g. a two-line address), so the value is always a list."""
    fields: dict[str, list[str]] = {}
    for label, dd_block in _DT_DD_RE.findall(html):
        values = [_strip_tags(v) for v in _DD_RE.findall(dd_block)]
        fields[label.strip().lower()] = [v for v in values if v]
    return fields


def _strip_tags(value: str) -> str:
    return _TAG_RE.sub("", value).replace("&amp;", "&").strip()


def _build_record(number: str, row: dict, detail_html: str, area: str, recipe: dict) -> LeadRecord:
    fields = _parse_detail_fields(detail_html)
    name = str(row.get("ProjectName") or row.get("FacilityName") or "").strip()
    address_lines = fields.get("location address", [])
    address = address_lines[0] if address_lines else ""
    city = ""
    if len(address_lines) > 1:
        # "Brownsville, TX 78521" -- city is the text before the first comma.
        city = address_lines[1].split(",")[0].strip()
    county = (fields.get("location county") or [""])[0]

    scope = " ".join(fields.get("scope of work", []))
    units_pattern = recipe.get("units_text_pattern")
    units = None
    if units_pattern:
        match = re.search(units_pattern, scope, re.I)
        if match:
            try:
                units = int(match.group(1))
            except (TypeError, ValueError, IndexError):
                units = None

    owner_name = (fields.get("owner name") or [""])[0]
    owner_phone = (fields.get("owner phone") or [""])[0]
    design_firm = (fields.get("design firm name") or [""])[0]

    permit_date = _parse_date(row.get("ProjectCreatedOn"))
    start_date = _parse_date(row.get("EstimatedStartDate"))
    end_date = _parse_date(row.get("EstimatedEndDate"))
    stage = "under construction" if start_date and start_date <= datetime.date.today() else "permitted"

    detail_url = recipe.get("detail_url_template", "").format(project_number=number)
    sources = [{"fact": "permit_date", "url": detail_url}]
    if owner_name:
        sources.append({"fact": "developer", "url": detail_url})
    if owner_phone:
        sources.append({"fact": "office_phone", "url": detail_url})

    why = "new multifamily project registered with TDLR TABS"
    if not county:
        county = ""

    return LeadRecord(
        area=area,
        city=city or county,
        name=name,
        address=address,
        units=units,
        stage=stage,
        permit_date=permit_date.isoformat() if permit_date else "",
        opening_date=end_date.isoformat() if end_date else "",
        developer=owner_name or design_firm,
        office_phone=_format_phone(owner_phone),
        links={"permit": detail_url},
        sources=sources,
        why=why,
    )


def _format_phone(value: str) -> str:
    if not value:
        return ""
    try:
        import phonenumbers

        parsed = phonenumbers.parse(value, "US")
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL)
    except Exception:
        pass
    return value


def _parse_date(value) -> datetime.date | None:
    if not value:
        return None
    text = str(value)
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


# --- real network fetch, used only by live_self_test.py; injected as
# `fetch_search`/`fetch_detail` above so the pytest suite never calls this. ---


def default_fetch_search(payload: dict) -> dict:
    body = "&".join(f"{k}={urllib.request.quote(str(v))}" for k, v in payload.items())
    req = urllib.request.Request(
        "https://www.tdlr.texas.gov/TABS/Search/SearchProjects",
        data=body.encode(),
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "propertystack-live-self-test",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def default_fetch_detail(project_number: str) -> str:
    url = f"https://www.tdlr.texas.gov/TABS/Search/Project/{project_number}"
    req = urllib.request.Request(url, headers={"User-Agent": "propertystack-live-self-test"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")
