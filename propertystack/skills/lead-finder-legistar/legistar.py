"""lead-finder 3.4: Legistar reader.

For a city whose agenda recipe (3.3) says "legistar", pull the last 12 months of
Planning / Zoning / Council meeting matters from the free Legistar Web API
(`https://webapi.legistar.com/v1/<client>/...`) and turn matters that mention
multifamily/apartments/rezoning/site plans into "planned" LeadRecords.

The Legistar API requires no key, but some cities' Legistar instances require a
token for the web API even though the client-facing site is public; those cities
are reported skipped, never guessed at.

No place names anywhere in this file -- city/state/client name are always
caller-supplied.
"""
from __future__ import annotations

import datetime
import re
import sys
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lead-finder"))
from merge import merge_records  # noqa: E402
from record import LeadRecord  # noqa: E402

HttpGet = Callable[[str], object]

LOOKBACK_DAYS = 365
BODY_RE = re.compile(r"planning|zoning|council", re.I)
KEYWORD_RE = re.compile(
    r"multi[- ]?family|apartment|\b\d+\s*units?\b|rezon|site plan", re.I
)
CASE_RE = re.compile(r"\b[A-Z]{1,4}-?\d{2,4}-\d{2,5}\b")
ADDRESS_RE = re.compile(r"\b\d{2,6}\s+[A-Za-z0-9.'\- ]+\b(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Dr|Drive|Ln|Lane|Way|Pkwy|Parkway|Ct|Court)\b", re.I)
UNITS_RE = re.compile(r"(\d{2,4})\s*units?\b", re.I)


def find_legistar_matters(
    city: str,
    state: str,
    area: str,
    client: str,
    http_get: HttpGet,
    today: datetime.date | None = None,
) -> list[LeadRecord] | dict:
    """Return merged planned-stage LeadRecords, or a skip note (never raises)."""
    today = today or datetime.date.today()
    since = (today - datetime.timedelta(days=LOOKBACK_DAYS)).isoformat()
    base = f"https://webapi.legistar.com/v1/{client}"
    bodies_url = f"{base}/bodies"

    try:
        bodies = http_get(bodies_url)
    except Exception:
        return {"city": city, "state": state, "skipped": True, "reason": "legistar token required or unreachable"}

    if not isinstance(bodies, list):
        return {"city": city, "state": state, "skipped": True, "reason": "legistar token required or unreachable"}

    body_ids = {
        b.get("BodyId")
        for b in bodies
        if BODY_RE.search(str(b.get("BodyName", "")))
    }
    if not body_ids:
        return {"city": city, "state": state, "skipped": True, "reason": "no planning/zoning/council body found"}

    events_url = f"{base}/events?$filter=EventDate ge datetime'{since}'"
    try:
        events = http_get(events_url)
    except Exception:
        events = []
    if not isinstance(events, list):
        events = []
    relevant_events = [e for e in events if e.get("EventBodyId") in body_ids]

    matters_seen: dict[str, dict] = {}
    for event in relevant_events:
        event_id = event.get("EventId")
        if event_id is None:
            continue
        items_url = f"{base}/events/{event_id}/eventitems"
        try:
            items = http_get(items_url)
        except Exception:
            continue
        if not isinstance(items, list):
            continue
        for item in items:
            matter_title = item.get("EventItemMatterName") or item.get("EventItemTitle") or ""
            matter_id = item.get("EventItemMatterId")
            if not matter_title or not KEYWORD_RE.search(matter_title):
                continue
            key = str(matter_id) if matter_id is not None else matter_title
            if key not in matters_seen:
                matters_seen[key] = {
                    "title": matter_title,
                    "matter_id": matter_id,
                    "event_date": event.get("EventDate", ""),
                }

    records = []
    for key, info in matters_seen.items():
        matter_id = info["matter_id"]
        matter_url = (
            f"https://{client}.legistar.com/LegislationDetail.aspx?ID={matter_id}"
            if matter_id is not None
            else base
        )
        title = info["title"]
        case_match = CASE_RE.search(title)
        address_match = ADDRESS_RE.search(title)
        units_match = UNITS_RE.search(title)
        records.append(
            LeadRecord(
                area=area,
                city=city,
                address=address_match.group(0) if address_match else "",
                units=int(units_match.group(1)) if units_match else None,
                stage="planned",
                links={"agenda": matter_url},
                sources=[{"fact": "why", "url": matter_url}],
                why=f"planning/zoning agenda item: {title}"[:200] + (
                    f" (case {case_match.group(0)})" if case_match else ""
                ),
            )
        )

    return merge_records(records)


if __name__ == "__main__":
    import argparse
    import json

    import httpx

    p = argparse.ArgumentParser()
    p.add_argument("--city", required=True)
    p.add_argument("--state", required=True)
    p.add_argument("--area", required=True)
    p.add_argument("--client", required=True, help="the city's <client>.legistar.com name")
    args = p.parse_args()

    def _get(url: str):
        r = httpx.get(url, timeout=30)
        r.raise_for_status()
        return r.json()

    result = find_legistar_matters(args.city, args.state.upper(), args.area, args.client, _get)
    if isinstance(result, dict):
        print(json.dumps(result, indent=1))
    else:
        print(json.dumps([r.to_dict() for r in result], indent=1))
