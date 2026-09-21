#!/usr/bin/env python3
"""Collect official TDLR TABS project records for the Masiate pilot."""

from __future__ import annotations

import datetime as dt
import fcntl
import json
import os
import re
import tempfile
import time
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


RUN_ROOT = Path("/home/drewp/.local/state/cranesignal/masiate/pilot-20260920-2048")
LANE = RUN_ROOT / "statewide"
EVIDENCE = LANE / "evidence" / "tdlr-tabs"
MIRROR = Path.cwd() / "docs" / "masiate-pilot" / "statewide"
BASE = "https://www.tdlr.texas.gov"
SEARCH_PAGE = f"{BASE}/TABS/Search"
SEARCH_ENDPOINT = f"{BASE}/TABS/Search/SearchProjects"
PROJECT_URL = f"{BASE}/TABS/Search/Project"
LOCK_PATH = RUN_ROOT / "tdlr-tabs.lock"

COUNTIES = {
    "Brazos": "2021",
    "Robertson": "2198",
    "Burleson": "2026",
    "Grimes": "2093",
    "Leon": "2145",
    "Madison": "2154",
    "Washington": "2239",
}

RECENT_BEGIN = "06/22/2026"
RECENT_END = "09/20/2026"
BACKFILL_BEGIN = "09/20/2025"
BACKFILL_END = "06/21/2026"

STATUS = {
    3001: "Inspection Completed",
    3007: "Project Closed",
    3008: "Project Registered",
    3009: "Review Complete",
}

WORK = {
    9001: "New Construction",
    9002: "Renovation/Alteration",
    9003: "Additions to Existing Building",
    9004: "Historic Preservation",
    9005: "Public Right of Way",
}

MAX_BACKFILL_DETAILS_PER_COUNTY = 25

CANDIDATE_KEYWORDS = re.compile(
    r"\b("
    r"new|construct|construction|renovat|alteration|addition|remodel|finish out|"
    r"tenant improvement|shell|buildout|build out|site work|office|warehouse|"
    r"retail|restaurant|clinic|medical|dental|hotel|school|classroom|bathroom|"
    r"floor|paint|roof|fence|concrete|plumb|lighting|framing|siding"
    r")\b",
    re.I,
)

LOW_FIT = re.compile(r"\b(sidewalk|trail|right of way|row|traffic signal|parking lot only)\b", re.I)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as tmp:
        tmp.write(text)
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, path)


class OfficialSession:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "CraneSignal Masiate pilot research (official public records)",
                "Accept": "application/json, text/html;q=0.9, */*;q=0.8",
            }
        )
        self.last_request = 0.0

    def request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOCK_PATH.open("w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            elapsed = time.monotonic() - self.last_request
            if elapsed < 2.0:
                time.sleep(2.0 - elapsed)
            response = self.session.request(method, url, timeout=30, **kwargs)
            self.last_request = time.monotonic()
        response.raise_for_status()
        return response


def load_lookup(session: OfficialSession) -> tuple[dict[str, str], dict[str, str]]:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    page_path = EVIDENCE / "search.html"
    if page_path.exists():
        html = page_path.read_text(errors="ignore")
    else:
        response = session.request("GET", SEARCH_PAGE)
        html = response.text
        page_path.write_text(html, encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    def options(select_id: str) -> dict[str, str]:
        select = soup.find(id=select_id)
        out: dict[str, str] = {}
        if not select:
            return out
        for option in select.find_all("option"):
            value = option.get("value")
            label = option.get_text(strip=True)
            if value and label:
                out[value] = label
        return out

    return options("filter-location-city"), options("filter-location-county")


def search_county(session: OfficialSession, county: str, county_id: str, begin: str, end: str, label: str) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    files: list[str] = []
    total = None
    start = 0
    draw = 1
    while total is None or start < total:
        payload = {
            "draw": str(draw),
            "start": str(start),
            "length": "100",
            "order[0][column]": "3",
            "order[0][dir]": "desc",
            "LocationCounty": county_id,
            "RegistrationDateBegin": begin,
            "RegistrationDateEnd": end,
        }
        response = session.request(
            "POST",
            SEARCH_ENDPOINT,
            headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": SEARCH_PAGE,
            },
            data=payload,
        )
        data = response.json()
        safe = f"{county.lower()}_{label}_{start:04d}.json"
        out = EVIDENCE / safe
        out.write_text(json.dumps(data, indent=2), encoding="utf-8")
        files.append(str(out))
        total = int(data.get("recordsFiltered", 0))
        rows.extend(data.get("data") or [])
        start += 100
        draw += 1
        if not data.get("data"):
            break
    return {"rows": rows, "total": total or 0, "files": files}


def field_map(section: BeautifulSoup) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for dt_tag in section.find_all("dt"):
        key = dt_tag.get_text(" ", strip=True).rstrip(":")
        vals: list[str] = []
        for sibling in dt_tag.find_next_siblings():
            if sibling.name == "dt":
                break
            if sibling.name == "dd":
                value = sibling.get_text(" ", strip=True)
                if value:
                    vals.append(value)
        if vals:
            out.setdefault(key, []).append(" ".join(vals))
    return out


def get_first(mapping: dict[str, list[str]], key: str) -> str | None:
    values = mapping.get(key) or []
    return values[0] if values else None


def fetch_project(session: OfficialSession, project_number: str) -> tuple[dict[str, Any], Path]:
    url = f"{PROJECT_URL}/{project_number}"
    response = session.request("GET", url, headers={"Referer": SEARCH_PAGE})
    path = EVIDENCE / f"{project_number}.html"
    path.write_text(response.text, encoding="utf-8")
    soup = BeautifulSoup(response.text, "html.parser")
    all_fields = field_map(soup)
    sections: dict[str, dict[str, list[str]]] = {}
    for name in ["owner", "tenant", "designer", "ras", "contact"]:
        div = soup.find("div", class_=f"project-details-{name}")
        if div:
            sections[name] = field_map(div)
    return {"url": url, "fields": all_fields, "sections": sections}, path


def to_iso_date(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    for fmt in ("%m/%d/%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
        try:
            return dt.datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            pass
    return value[:10] if re.match(r"\d{4}-\d{2}-\d{2}", value) else value


def money(value: Any) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return f"${value:,.0f} TDLR estimated cost"
    return str(value)


def score_record(row: dict[str, Any], detail: dict[str, Any]) -> tuple[str, str]:
    fields = detail["fields"]
    scope = get_first(fields, "Scope of Work") or ""
    work = WORK.get(row.get("TypeOfWork"), get_first(fields, "Type of Work") or "unknown")
    cost = row.get("EstimatedCost") or 0
    text = f"{row.get('ProjectName','')} {row.get('FacilityName','')} {scope} {work}"
    if CANDIDATE_KEYWORDS.search(text) and not LOW_FIT.search(text):
        if cost and cost >= 75000:
            return "candidate", "Scope and cost indicate current construction/remodeling work that could use Masiate trades."
        return "watchlist", "Scope fits construction/remodeling, but public cost signal is modest or missing."
    if work in {"New Construction", "Renovation/Alteration", "Additions to Existing Building"} and cost and cost >= 250000:
        return "candidate", "TDLR work type and cost show a substantial accessible building project; trade package timing is unknown."
    return "watchlist", "Official TDLR record is address-level, but the scope is not clearly aligned to Masiate trades."


def make_record(
    county: str,
    row: dict[str, Any],
    detail: dict[str, Any],
    path: Path,
    city_lookup: dict[str, str],
) -> dict[str, Any]:
    fields = detail["fields"]
    sections = detail["sections"]
    project_number = row.get("ProjectNumber")
    project_name = get_first(fields, "Project Name") or row.get("ProjectName")
    facility = get_first(fields, "Facility Name") or row.get("FacilityName")
    address = get_first(fields, "Location Address") or "unknown"
    city = city_lookup.get(str(row.get("City")), None)
    if not city and address and "," in address:
        city = address.split(",")[-1].strip().split()[0]
    work_type = get_first(fields, "Type of Work") or WORK.get(row.get("TypeOfWork"), "unknown")
    status = get_first(fields, "Current Status") or STATUS.get(row.get("ProjectStatus"), "unknown")
    disposition, fit = score_record(row, detail)
    scope = get_first(fields, "Scope of Work") or "TDLR project record did not expose a scope in the parsed detail page."
    owner = get_first(sections.get("owner", {}), "Owner Name")
    designer = get_first(sections.get("designer", {}), "Design Firm Name")
    ras = get_first(sections.get("ras", {}), "RAS Name")
    participants = []
    if owner:
        participants.append({"name": owner, "role": "owner/developer", "source_url": detail["url"]})
    if designer:
        participants.append({"name": designer, "role": "designer", "source_url": detail["url"]})
    if ras:
        participants.append({"name": ras, "role": "registered accessibility specialist", "source_url": detail["url"]})
    business_contacts = []
    if designer:
        business_contacts.append({"name": designer, "role": "design firm on TDLR record", "phone": None, "email": None, "website": None, "source_url": detail["url"]})
    return {
        "id": f"statewide-tdlr-tabs-{project_number}",
        "county": county,
        "project_name": project_name,
        "address": address,
        "city": city or "unknown",
        "record_type": "registration",
        "source_record_id": project_number,
        "record_date": to_iso_date(get_first(fields, "Registration Date") or row.get("ProjectCreatedOn")),
        "retrieved_at": utc_now(),
        "stage": "planned" if status in {"Project Registered", "Review Complete"} else "historical" if status in {"Project Closed", "Inspection Completed"} else "unknown",
        "status_basis": f"TDLR TABS status is {status}; this proves registration/review status only, not that a subcontract package remains open.",
        "scope": scope,
        "masiate_fit": fit,
        "estimated_value": money(row.get("EstimatedCost") or get_first(fields, "Estimated Cost")),
        "estimated_start": to_iso_date(get_first(fields, "Start Date") or row.get("EstimatedStartDate")),
        "estimated_completion": to_iso_date(get_first(fields, "Completion Date") or row.get("EstimatedEndDate")),
        "bid_deadline": None,
        "participants": participants,
        "business_contacts": business_contacts,
        "sources": [
            {
                "url": detail["url"],
                "title": f"TDLR TABS Project Details: {project_number}",
                "date": to_iso_date(get_first(fields, "Registration Date") or row.get("ProjectCreatedOn")),
                "page": "Project Details",
                "evidence": f"{facility}; {address}; {work_type}; {scope}",
                "local_path": str(path),
            }
        ],
        "unknowns": [
            "Whether construction has started beyond the TDLR estimated start date.",
            "Whether Masiate-relevant trade packages remain available.",
            "Whether the owner, tenant, general contractor or designer is the best contact path.",
        ],
        "next_research": "Check local permit/planning records or participant website for current project status and contractor contacts.",
        "disposition": disposition,
    }


def checkpoint(records: list[dict[str, Any]], coverage: list[dict[str, Any]], state: str = "running") -> None:
    now = utc_now()
    atomic_write(LANE / "records.json", json.dumps(records, indent=2, ensure_ascii=False) + "\n")
    atomic_write(LANE / "coverage.json", json.dumps(coverage, indent=2, ensure_ascii=False) + "\n")
    status_path = LANE / "status.json"
    status = json.loads(status_path.read_text()) if status_path.exists() else {}
    status.update({"checkpoint_at": now, "state": state, "records_saved": len(records)})
    if state in {"complete", "partial"}:
        status["finished_at"] = now
    atomic_write(status_path, json.dumps(status, indent=2, ensure_ascii=False) + "\n")


def write_summary(records: list[dict[str, Any]], coverage: list[dict[str, Any]], state: str) -> None:
    candidates = [r for r in records if r["disposition"] == "candidate"]
    by_county: dict[str, int] = {}
    for record in records:
        by_county[record["county"]] = by_county.get(record["county"], 0) + 1
    top = sorted(candidates, key=lambda r: float(re.sub(r"[^0-9.]", "", r["estimated_value"] or "0") or 0), reverse=True)[:12]
    lines = [
        "# Statewide Masiate Pilot Summary",
        "",
        f"State: {state}",
        f"Checkpoint: {utc_now()}",
        "",
        "## Counts",
        f"- TDLR/TABS records saved: {len(records)}",
        f"- Candidate dispositions: {len(candidates)}",
        f"- Watchlist dispositions: {len(records) - len(candidates)}",
        "- Counties covered: " + ", ".join(f"{k} ({v})" for k, v in sorted(by_county.items())),
        "",
        "## Strongest TDLR Candidates",
    ]
    for record in top:
        lines.append(
            f"- {record['county']}: {record['project_name']} at {record['address']} "
            f"({record['estimated_value']}; {record['estimated_start']} to {record['estimated_completion']}) - {record['scope']}"
        )
    lines += [
        "",
        "## Coverage Notes",
    ]
    for entry in coverage:
        lines.append(
            f"- {entry['name']}: {entry['status']}; requested {entry['requested_from']} to {entry['requested_to']}; "
            f"{entry['records_found']} records; reason: {entry['reason']}"
        )
    lines += [
        "",
        "## Honest Gaps",
        "- TDLR TABS is an accessibility registration source, not a live bid feed; bid availability and contractor selection remain unknown.",
        "- Private residential jobs that do not trigger TDLR accessibility registration are not represented in this statewide source.",
        "- Statewide non-TDLR sources still need deeper official endpoint testing if another pass is approved.",
    ]
    atomic_write(LANE / "summary.md", "\n".join(lines) + "\n")


def mirror_outputs() -> None:
    MIRROR.mkdir(parents=True, exist_ok=True)
    for name in ["records.json", "coverage.json", "status.json", "summary.md"]:
        src = LANE / name
        if src.exists():
            atomic_write(MIRROR / name, src.read_text(encoding="utf-8"))


def main() -> None:
    LANE.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    session = OfficialSession()
    city_lookup, county_lookup = load_lookup(session)
    records_path = LANE / "records.json"
    coverage_path = LANE / "coverage.json"
    records: list[dict[str, Any]] = json.loads(records_path.read_text()) if records_path.exists() else []
    coverage: list[dict[str, Any]] = json.loads(coverage_path.read_text()) if coverage_path.exists() else []
    seen: set[str] = {r.get("source_record_id") for r in records if r.get("source_record_id")}
    covered_names: set[str] = {c.get("name") for c in coverage}
    backfill_detail_counts: dict[str, int] = {}
    for record in records:
        if record.get("record_date") and record["record_date"] < "2026-06-22":
            backfill_detail_counts[record["county"]] = backfill_detail_counts.get(record["county"], 0) + 1

    tasks = []
    for county, county_id in COUNTIES.items():
        tasks.append((county, county_id, "recent", RECENT_BEGIN, RECENT_END))
    for county, county_id in COUNTIES.items():
        tasks.append((county, county_id, "backfill", BACKFILL_BEGIN, BACKFILL_END))

    for county, county_id, label, begin, end in tasks:
        source_name = f"TDLR TABS {county} {label}"
        if source_name in covered_names:
            files = list((EVIDENCE).glob(f"{county.lower()}_{label}_*.json"))
            rows = []
            total = 0
            for file in files:
                data = json.loads(file.read_text())
                total = max(total, int(data.get("recordsFiltered", 0)))
                rows.extend(data.get("data") or [])
            result = {"rows": rows, "total": total, "files": [str(f) for f in files]}
        else:
            result = search_county(session, county, county_id, begin, end, label)
            coverage.append(
                {
                    "name": source_name,
                    "url": SEARCH_PAGE,
                    "county": county,
                    "requested_from": begin,
                    "requested_to": end,
                    "covered_from": begin,
                    "covered_to": end,
                    "status": "complete",
                    "records_found": len(result["rows"]),
                    "files_read": result["files"],
                    "reason": f"Official TDLR SearchProjects endpoint returned {len(result['rows'])} rows for county id {county_id}.",
                    "next_cursor": None,
                    "retrieved_at": utc_now(),
                }
            )
            covered_names.add(source_name)
        for row in result["rows"]:
            project_number = row.get("ProjectNumber")
            if not project_number or project_number in seen:
                continue
            if label == "backfill" and backfill_detail_counts.get(county, 0) >= MAX_BACKFILL_DETAILS_PER_COUNTY:
                continue
            seen.add(project_number)
            detail, local_path = fetch_project(session, project_number)
            record = make_record(county_lookup.get(str(row.get("County")), county), row, detail, local_path, city_lookup)
            records.append(record)
            if label == "backfill":
                backfill_detail_counts[county] = backfill_detail_counts.get(county, 0) + 1
            if len(records) % 20 == 0:
                checkpoint(records, coverage)
                write_summary(records, coverage, "running")

    coverage.append(
        {
            "name": "TCEQ central registry / statewide construction signals",
            "url": "https://www.tceq.texas.gov/permitting/central_registry",
            "county": "statewide",
            "requested_from": RECENT_BEGIN,
            "requested_to": RECENT_END,
            "covered_from": None,
            "covered_to": None,
            "status": "not_checked",
            "records_found": 0,
            "files_read": [],
            "reason": "TDLR/TABS collection consumed the approved statewide pass; TCEQ remains a continuation target rather than an inferred source.",
            "next_cursor": "Test official TCEQ Central Registry / permit lookup for construction stormwater permit fields in the seven target counties.",
            "retrieved_at": utc_now(),
        }
    )
    checkpoint(records, coverage, state="complete")
    write_summary(records, coverage, "complete")
    mirror_outputs()


if __name__ == "__main__":
    main()
