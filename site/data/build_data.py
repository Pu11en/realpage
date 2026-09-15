#!/usr/bin/env python3
"""Rebuild site/data/*.json from the real PropertyStack pipeline output.

Sources (see propertystack/CONTRACTS.md):
  propertystack/data/plano-richardson/master.csv  -> properties.json, software-share.json
  propertystack/data/plano-richardson/leads.csv   -> leads.json
  propertystack/data/plano-richardson/6-upcoming.csv -> leads.json (openingNext12mo)
  propertystack/runs/*.json                       -> pipeline.json (Under the Hood)
  propertystack/data/client-map/counts.json       -> client-map.json (map.html state shading)
  propertystack/data/<state-slug>/leads.json      -> site/data/areas/<state-slug>.json
    (part-1 LeadRecord format, see propertystack/skills/lead-finder/record.py;
     plano-richardson keeps using the CSV pipeline above, unchanged; the fixture
     area `_sample` is only built when LEAD_FINDER_BUILD_SAMPLE=1 is set)

Run this any time master.csv / leads.csv / runs/*.json / a state's leads.json change.
No dependencies beyond stdlib. Usage: python3 site/data/build_data.py
"""
import csv
import glob
import json
import os
import re
import sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = "plano-richardson"
DATA_DIR = ROOT / "propertystack" / "data" / AREA
RUNS_DIR = ROOT / "propertystack" / "runs"
OUT_DIR = Path(__file__).resolve().parent

MASTER_CSV = DATA_DIR / "master.csv"
LEADS_CSV = DATA_DIR / "leads.csv"
UPCOMING_CSV = DATA_DIR / "6-upcoming.csv"
CONTACTS_CSV = DATA_DIR / "contacts.csv"
CONTACTS_DALLAS_CSV = DATA_DIR / "contacts-dallas.csv"
LEADS_FACTS_JSONL = DATA_DIR / "leads-facts.jsonl"
SALES_CSV = DATA_DIR / "5-sales.csv"
SALES_DALLAS_CSV = DATA_DIR / "5-sales-dallas.csv"

CLIENT_MAP_COUNTS = ROOT / "propertystack" / "data" / "client-map" / "counts.json"

# Part-1 lead format (any state area) -- see propertystack/skills/lead-finder/record.py.
STATE_DATA_DIR = ROOT / "propertystack" / "data"
AREAS_OUT_DIR = OUT_DIR / "areas"
NON_STATE_AREA_DIRS = {"plano-richardson", "client-map", "dallas-parked", "raw", "scout"}
SAMPLE_AREA = "_sample"

sys.path.insert(0, str(ROOT / "propertystack" / "skills" / "lead-finder"))
sys.path.insert(0, str(ROOT / "propertystack" / "skills" / "score-leads"))

STATE_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "DC": "District of Columbia",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois",
    "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana",
    "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon",
    "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota",
    "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont", "VA": "Virginia",
    "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
}

TODAY = date.fromisoformat("2026-09-10")  # matches score-leads' fixed TODAY, see run.py

VENDOR_COLORS = {
    "RealPage": "#f472b6",
    "Yardi": "#60a5fa",
    "Entrata": "#fb923c",
    "Yotta": "#c084fc",
    "AppFolio": "#facc15",
    "ResMan": "#22d3ee",
    "MRI/RentManager": "#34d399",
    "in-house:Camden": "#94a3b8",
    "in-house:UDR": "#fca5a5",
    "unknown": "#52525b",
}


def read_csv(path: Path) -> list[dict]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def lead_score(r: dict) -> dict:
    return {
        "rank": int(r["rank"]),
        "total": int(r["score"]),
        "size": int(r["score_size"]),
        "timing": int(r["score_timing"]),
        "signal": int(r["score_signal"]),
        "open": int(r["score_open"]),
        "why": r["why"],
    }


def split_urls(s: str) -> list[str]:
    return [u.strip() for u in s.split(";") if u.strip()]


def build_properties_and_share() -> tuple[list[dict], dict]:
    rows = read_csv(MASTER_CSV)
    leads_by_ref = {r["ref_id"]: r for r in read_csv(LEADS_CSV)}
    sale_files = [SALES_CSV] + ([SALES_DALLAS_CSV] if SALES_DALLAS_CSV.exists() else [])
    sales = {r["apt_id"]: r for f in sale_files for r in read_csv(f)}
    contacts = load_contacts()

    properties = []
    for r in rows:
        sale = sales.get(r["apt_id"])
        lead = leads_by_ref.get(r["apt_id"])
        properties.append({
            "id": r["apt_id"],
            "community": r["name"],
            "city": r["city"],
            "county": r.get("county") or "Collin",
            "address": r["address"],
            "units": int(r["units"]) if r["units"] else None,
            "yearBuilt": int(r["year_built"]) if r["year_built"] else None,
            "owner": r["owner"],
            "software": r["software"] or None,
            "proof": r["proof_url"] or None,
            # Page 4 (Property Detail) fields
            "website": r["website"] or None,
            "websiteConfidence": r["website_confidence"] or None,
            "checkedAt": r["checked_at"] or None,
            "unknownReason": r["unknown_reason"] or None,
            "contact": contacts.get(r["apt_id"]),
            "sale": {
                "date": sale["sale_date"],
                "newOwner": sale["new_owner"],
                "previousOwner": sale["previous_owner"],
                "source": sale["source_url"] or None,
            } if sale else None,
            "lead": lead_score(lead) if lead else None,
            "sources": split_urls(lead["sources"]) if lead else [],
        })

    upcoming = []
    for r in read_csv(UPCOMING_CSV):
        lead = leads_by_ref.get(r["project_id"])
        upcoming.append({
            "id": r["project_id"],
            "community": r["project"],
            "city": r["city"],
            "address": r["address"],
            "units": int(r["units"]) if r["units"] else None,
            "developer": r["developer"] or None,
            "stage": r["stage"],
            "stageDate": r["stage_date"] or None,
            "expectedOpen": r["expected_open"] or None,
            "sourceType": r["source_type"],
            "lead": lead_score(lead) if lead else None,
            "sources": split_urls(lead["sources"]) if lead else split_urls(r["source_url"]),
        })

    total_units = sum(p["units"] or 0 for p in properties)
    identified = [p for p in properties if p["software"] and p["software"] != "unknown"]
    not_checked = sum(1 for r in rows if r["unknown_reason"] == "no-website")
    checked = len(properties) - not_checked
    vendor_counts = Counter(p["software"] for p in identified)
    top_vendor = vendor_counts.most_common(1)[0][0] if vendor_counts else None

    properties_json = {
        "generatedFrom": "propertystack/data/plano-richardson/master.csv",
        "stats": {
            "apartments": len(properties),
            "totalUnits": total_units,
            "softwareIdentified": len(identified),
            "softwareIdentifiedPct": round(100 * len(identified) / len(properties), 1),
            "topSoftware": top_vendor,
        },
        "funnel": {
            "inArea": len(properties),
            "websiteFound": checked,
            "checked": checked,
            "identified": len(identified),
            "unknown": len(properties) - len(identified),
        },
        "vendorColors": VENDOR_COLORS,
        "properties": properties,
        "upcoming": upcoming,
    }

    share = []
    for vendor, count in vendor_counts.most_common():
        vendor_units = sum(p["units"] or 0 for p in identified if p["software"] == vendor)
        share.append({
            "vendor": vendor,
            "color": VENDOR_COLORS.get(vendor, "#52525b"),
            "properties": count,
            "units": vendor_units,
            "pctOfIdentifiedProperties": round(100 * count / len(identified), 1) if identified else 0,
        })

    share_json = {
        "generatedFrom": "propertystack/data/plano-richardson/master.csv",
        "note": "changeSinceLastRun is not tracked yet -- needs a second run to diff against.",
        "share": share,
    }

    return properties, properties_json, share_json


SOLD_DATE_RE = re.compile(r"^(Sold \S+ \d{4})")


def short_signal(signal: str, why: str) -> str:
    if signal == "sold":
        m = SOLD_DATE_RE.match(why)
        return m.group(1) if m else why.split(" · ")[0]
    return why.split(" · ")[0].split(" → ")[0].strip()


def source_tag(url: str) -> str:
    if "data.texas.gov" in url:
        return "county record"
    if "legistar" in url or "zabalist.com" in url:
        return "permit"
    if any(d in url for d in ("communityimpact.com", "dallasnews.com", "candysdirt.com")):
        return "news"
    return "website"


def load_leads_facts() -> dict:
    facts = {}
    with open(LEADS_FACTS_JSONL) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            facts[d["ref_id"]] = d
    return facts


# Scraped "emails" that aren't the building's: software vendors' accessibility inboxes, lead-routing
# robots, review sites, a web agency, and image filenames the scraper mistook for emails.
JUNK_EMAIL_DOMAINS = ("entrata.com", "apartments247.com", "birdeye.com", "leadmanaging.com",
                      "aptleasing.info", "assist.rent", "eliseai.com", "knck.io", "francemediainc.com")


def usable_email(email):
    e = (email or "").strip().lower()
    if "@" not in e or e.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg")):
        return None
    local, domain = e.split("@", 1)
    if local.startswith(("accessibility", "webaccessibility", "profiles")):
        return None
    if any(domain == d or domain.endswith("." + d) for d in JUNK_EMAIL_DOMAINS):
        return None
    return email.strip()


def load_contacts() -> dict:
    contacts = {}
    contact_files = [CONTACTS_CSV] + ([CONTACTS_DALLAS_CSV] if CONTACTS_DALLAS_CSV.exists() else [])
    for f in contact_files:
        for r in read_csv(f):
            email = usable_email(r["email"])
            if r["phone"] or email:
                contacts[r["apt_id"]] = {
                    "phone": r["phone"] or None,
                    "email": email,
                }
    return contacts


def build_leads() -> dict:
    rows = read_csv(LEADS_CSV)
    facts = load_leads_facts()
    contacts = load_contacts()

    leads = []
    for r in rows:
        software = r["software"]
        if software in ("not chosen yet", "unknown", ""):
            software = None
        sources = []
        for tag in (source_tag(u.strip()) for u in r["sources"].split(";") if u.strip()):
            if tag not in sources:
                sources.append(tag)

        ref_id = r["ref_id"]
        is_sold = r["signal"] == "sold"
        fact = facts.get(ref_id, {})

        # isNew: sale/stage happened within the last 30 days of TODAY.
        date_str = fact.get("sale_date") if is_sold else fact.get("stage_date")
        is_new = False
        if date_str:
            try:
                is_new = (TODAY - date.fromisoformat(date_str)).days <= 30
            except ValueError:
                is_new = False

        # Sold leads -> apt_id; upcoming leads -> project_id (properties.json "upcoming").
        property_id = ref_id
        contact = contacts.get(ref_id) if is_sold else None

        leads.append({
            "id": f"l{r['rank']}",
            "propertyId": property_id,
            "score": int(r["score"]),
            "property": r["name"],
            "city": r["city"],
            "units": int(r["units"]) if r["units"] else None,
            "signalType": "Upcoming" if r["signal"] == "upcoming" else "Sold",
            "signal": short_signal(r["signal"], r["why"]),
            "software": software,
            "why": r["why"],
            "sources": sources,
            "contact": contact,
            "isNew": is_new,
        })

    units_in_play = sum(l["units"] or 0 for l in leads)
    new_count = sum(1 for l in leads if l["isNew"])

    horizon = TODAY + timedelta(days=365)
    opening_soon_units = 0
    for r in read_csv(UPCOMING_CSV):
        if r["stage"] not in ("leasing", "under-construction"):
            continue
        if not r["units"]:
            continue
        opens_ok = True
        if r["expected_open"]:
            try:
                opens_ok = TODAY <= date.fromisoformat(r["expected_open"]) <= horizon
            except ValueError:
                opens_ok = True
        if opens_ok:
            opening_soon_units += int(r["units"])

    return {
        "stats": {
            "leads": len(leads),
            "newThisWeek": new_count,
            "unitsInPlay": units_in_play,
            "openingNext12mo": opening_soon_units,
        },
        "leads": leads,
    }


REPO_BLOB = "https://github.com/Pu11en/realpage/blob/main/"


def summarize_counts(counts: dict) -> str:
    """Flatten a run's top-level scalar counts into a short 'k=v' string."""
    parts = [f"{k}={v}" for k, v in counts.items() if isinstance(v, (int, float, str))]
    sw = counts.get("software")
    if isinstance(sw, dict) and "identified" not in counts:
        parts.append(f"identified={sum(v for k, v in sw.items() if k != 'unknown')}")
        parts.append(f"unknown={sw.get('unknown', 0)}")
    return ", ".join(parts)


def build_pipeline(properties: list[dict]) -> dict:
    run_files = sorted(glob.glob(str(RUNS_DIR / "*.json")))
    runs_by_skill: dict[str, list[dict]] = {}
    runs = []
    for path in run_files:
        with open(path) as f:
            run = json.load(f)
        if "skill" not in run:  # e.g. brave-usage.json, not a skill run
            continue
        runs_by_skill.setdefault(run["skill"], []).append(run)
        runs.append({
            "runId": Path(path).stem,
            "started": run.get("started"),
            "skill": run["skill"],
            "area": run.get("area"),
            "status": run.get("status"),
            "counts": summarize_counts(run.get("counts", {})),
            "errors": len(run.get("errors", [])),
            "durationSec": run.get("duration_s"),
        })
    runs.reverse()  # newest first

    def latest_counts(skill: str) -> dict:
        return runs_by_skill[skill][-1]["counts"] if runs_by_skill.get(skill) else {}

    bt = latest_counts("build-table")
    sales = latest_counts("find-sales")
    leads = latest_counts("score-leads")
    steps = [
        {"name": "find-apartments", "label": "buildings", "count": bt.get("in_area")},
        {"name": "find-website", "label": "with websites", "count": bt.get("website_found")},
        {"name": "detect-software", "label": "software identified", "count": bt.get("identified")},
        {"name": "find-sales", "label": "recent sales", "count": sales.get("sold")},
        {"name": "find-upcoming", "label": "upcoming projects", "count": leads.get("upcoming_leads")},
        {"name": "score-leads", "label": "ranked leads", "count": leads.get("total_leads")},
    ]

    queue = [
        {
            "id": p["id"],
            "community": p["community"],
            "city": p["city"],
            "units": p["units"],
            "reason": p["unknownReason"] or "unknown",
            "website": p["website"],
        }
        for p in properties
        if not p["software"] or p["software"] == "unknown"
    ]
    queue.sort(key=lambda r: (r["reason"] != "no-website", -(r["units"] or 0)))

    return {
        "steps": steps,
        "runs": runs,
        "accuracy": {
            "reviewDoc": REPO_BLOB + "propertystack/evals/review-weak-spots.md",
            "spotcheckDoc": REPO_BLOB + "propertystack/evals/manual-spotcheck-2026-09-10.md",
        },
        "costPerArea": {"note": "PLACEHOLDER -- run logs record API call counts, not dollars."},
        "reviewQueue": {
            "byReason": dict(Counter(r["reason"] for r in queue).most_common()),
            "rows": queue,
        },
    }


def build_client_map() -> dict:
    """Per-state RealPage building counts + top 3 cities, keyed by full state name
    (the map's topojson names states, not abbreviations)."""
    counts = json.loads(CLIENT_MAP_COUNTS.read_text())
    states = {}
    for abbr, d in counts.items():
        cities: dict[str, dict] = {}
        for city, n in d["cities"].items():  # merge spelling variants (Mckinney / McKinney)
            c = cities.setdefault(city.lower(), {"city": city, "count": 0})
            c["count"] += n
            if city != city.title() and c["city"] == c["city"].title():
                c["city"] = city
        top = sorted(cities.values(), key=lambda c: -c["count"])[:3]
        states[STATE_NAMES.get(abbr, abbr)] = {"abbr": abbr, "total": d["total"], "topCities": top}
    return {"source": "propertystack/data/client-map/counts.json", "states": states}


def discover_state_areas(include_sample: bool = False) -> list[str]:
    """State-area slugs with a part-1 `leads.json` (record.py format), excluding
    plano-richardson (still built from CSV, above) and non-area data dirs. The
    `_sample` fixture area is only included when explicitly asked for."""
    slugs = []
    for path in sorted(STATE_DATA_DIR.glob("*/leads.json")):
        slug = path.parent.name
        if slug in NON_STATE_AREA_DIRS:
            continue
        if slug == SAMPLE_AREA and not include_sample:
            continue
        slugs.append(slug)
    return slugs


def _area_signal_text(record) -> str:
    """The plan's exact labels: 'Planned (not permitted yet)', 'Opens: not
    public yet', 'Sold <date>' -- for whatever stage/date data a state-area
    record actually has (never guessed)."""
    if record.stage == "sold":
        return f"Sold {record.sale_date}" if record.sale_date else "Sold"
    if record.stage == "planned":
        return "Planned (not permitted yet)"
    return f"Opens: {record.opening_date}" if record.opening_date else "Opens: not public yet"


_URL_BITS_RE = re.compile(r"\s*\[?https?://\S+\]?")


def _clean_why(why: str) -> str:
    """Drop raw source URLs from the why text (sources show as links)."""
    return re.sub(r"\s{2,}", " ", _URL_BITS_RE.sub("", why or "")).strip(" ·")


_GENERIC_NAMES = {"building permit", "apartments (3+ dwelling units)", "new construction", "apartments"}
_DICT_URL_RE = re.compile(r"""^\{'url': '([^']+)'\}$""")


def _plain_url(s: str) -> str:
    """Some sources were saved as "{'url': '...'}" text: keep just the URL."""
    m = _DICT_URL_RE.match(s or "")
    return m.group(1) if m else s


def _nice_name(name: str, address: str = "") -> str:
    """ALL-CAPS names read as shouting; a generic permit label isn't a name."""
    if name and name.strip().lower() in _GENERIC_NAMES:
        name = address or name
    return name.title() if name and name.isupper() else name


def _is_leasing(record) -> bool:
    """Not sold, not planned, and its opening date already passed."""
    return (
        record.stage not in ("sold", "planned")
        and bool(record.opening_date)
        and record.opening_date <= date.today().isoformat()
    )


def _area_sort_key(record):
    """Soonest openings first, then leasing now, planned, recently sold."""
    today = date.today().isoformat()
    if record.stage == "sold":
        return (3, "", -int((record.sale_date or "0").replace("-", "") or 0))
    if record.stage == "planned":
        return (2, record.opening_date or "9999", 0)
    if _is_leasing(record):
        return (1, "", -int(record.opening_date.replace("-", "")))
    return (0, record.opening_date if (record.opening_date or "") > today else "9999", 0)


def _area_lead_dict(record, idx: int) -> dict:
    is_sold = record.stage == "sold"
    leasing = _is_leasing(record)
    name = _nice_name(record.name or record.address or "Unnamed project", record.address)
    return {
        "id": f"{record.area}-{idx}",
        "property": name,
        "community": record.name or None,
        "city": record.city,
        "address": record.address or None,
        "units": record.units,
        "stage": record.stage,
        "permitDate": record.permit_date or None,
        "openingDate": record.opening_date or None,
        "saleDate": record.sale_date or None,
        "buyer": record.buyer or None,
        "developer": record.developer or None,
        "officePhone": record.office_phone or None,
        "website": record.website or None,
        "software": record.software if record.software not in ("", "unknown") else None,
        "links": {k: _plain_url(str(v)) for k, v in record.links.items() if v},
        "sources": list(dict.fromkeys(_plain_url(s["url"] if isinstance(s, dict) else s.url) for s in record.sources)),
        "signalType": "Sold" if is_sold else (
            "Planned" if record.stage == "planned" else ("Leasing" if leasing else "Upcoming")
        ),
        "signal": f"Opened {record.opening_date}" if leasing else _area_signal_text(record),
        "why": _clean_why(record.why),
        # Records already come out of score_and_rank in rank order (4.5); this
        # is a display-only stand-in for a numeric score until the site needs one.
        "score": max(0, 100 - (idx - 1) * 3),
        "isNew": False,
    }


def build_area(slug: str) -> dict:
    """Build one state area's site JSON from its part-1 `leads.json` (LeadRecord
    list): score/rank the records (4.5) and shape them for the site."""
    from record import LeadRecord  # noqa: E402  (path added at import time, above)
    from score_leads import score_and_rank  # noqa: E402

    path = STATE_DATA_DIR / slug / "leads.json"
    with path.open() as f:
        raw = json.load(f)
    records = [LeadRecord.from_dict(d) for d in raw]
    ranked = sorted(score_and_rank(records), key=_area_sort_key)

    leads = [_area_lead_dict(r, i) for i, r in enumerate(ranked, start=1)]
    cities = sorted({r.city for r in ranked if r.city})
    units_in_play = sum(r.units or 0 for r in ranked if r.units)

    return {
        "area": slug,
        "generatedFrom": f"propertystack/data/{slug}/leads.json",
        "stats": {
            "leads": len(leads),
            "cities": len(cities),
            "unitsInPlay": units_in_play,
            "newThisWeek": 0,
            "openingNext12mo": sum(
                1 for r in ranked
                if r.stage != "sold" and r.opening_date
                and date.today().isoformat() < r.opening_date <= date.today().replace(year=date.today().year + 1).isoformat()
            ),
        },
        "cities": cities,
        "leads": leads,
    }


CHAT_LEADS_COLUMNS = [
    "area", "name", "city", "address", "units", "stage", "signal", "why",
    "permit_date", "opening_date", "sale_date", "buyer", "developer",
    "office_phone", "website", "software", "permit_link", "news_link",
    "website_link", "agenda_link", "map_link",
]


def write_chat_leads_csv(slug: str, area_json: dict) -> None:
    """Flatten one state area's JSON (5.1's `build_area`) into a chat-ready CSV
    at propertystack/data/<slug>/chat-leads.csv -- the chatbot's plugin (5.4)
    copies every area's chat-leads.csv into one `state_leads` table, since a
    state area has no master/contacts CSVs to join against (its lead rows are
    already flat)."""
    out_path = STATE_DATA_DIR / slug / "chat-leads.csv"
    with out_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(CHAT_LEADS_COLUMNS)
        for lead in area_json["leads"]:
            links = lead.get("links") or {}
            writer.writerow([
                slug, lead.get("property") or "", lead.get("city") or "",
                lead.get("address") or "", lead.get("units") or "",
                lead.get("stage") or "", lead.get("signal") or "", lead.get("why") or "",
                lead.get("permitDate") or "", lead.get("openingDate") or "",
                lead.get("saleDate") or "", lead.get("buyer") or "",
                lead.get("developer") or "", lead.get("officePhone") or "",
                lead.get("website") or "", lead.get("software") or "",
                links.get("permit") or "", links.get("news") or "",
                links.get("website") or "", links.get("agenda") or "",
                links.get("map") or "",
            ])


def build_state_areas(include_sample: bool = False) -> list[str]:
    """Build every discovered state area's JSON under site/data/areas/, plus
    its chat-leads.csv (for the chatbot). Returns the slugs actually built."""
    slugs = discover_state_areas(include_sample=include_sample)
    if not slugs:
        return []
    AREAS_OUT_DIR.mkdir(parents=True, exist_ok=True)
    for slug in slugs:
        area_json = build_area(slug)
        (AREAS_OUT_DIR / f"{slug}.json").write_text(json.dumps(area_json, indent=2))
        write_chat_leads_csv(slug, area_json)
    return slugs


def build_areas_manifest(area_slugs: list[str]) -> dict:
    """Write site/data/areas/index.json: one entry per area button on the Early
    Leads page (5.2). Plano-Richardson keeps its own legacy leads.json; every
    discovered state area (5.1) points at its file under data/areas/."""
    areas = [{"slug": AREA, "label": "Plano–Richardson", "dataPath": "data/leads.json"}]
    for slug in area_slugs:
        areas.append({
            "slug": slug,
            "label": slug.replace("-", " ").title(),
            "dataPath": f"data/areas/{slug}.json",
        })
    manifest = {"areas": areas}
    AREAS_OUT_DIR.mkdir(parents=True, exist_ok=True)
    (AREAS_OUT_DIR / "index.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def main() -> None:
    properties, properties_json, share_json = build_properties_and_share()
    (OUT_DIR / "properties.json").write_text(json.dumps(properties_json, indent=2))
    (OUT_DIR / "software-share.json").write_text(json.dumps(share_json, indent=2))

    leads_json = build_leads()
    (OUT_DIR / "leads.json").write_text(json.dumps(leads_json, indent=2))

    pipeline_json = build_pipeline(properties)
    (OUT_DIR / "pipeline.json").write_text(json.dumps(pipeline_json, indent=2))

    print(f"wrote properties.json ({len(properties)} rows)")
    print(f"wrote software-share.json ({len(share_json['share'])} vendors)")
    print(f"wrote leads.json ({len(leads_json['leads'])} leads)")
    print(f"wrote pipeline.json")

    client_map = build_client_map()
    (OUT_DIR / "client-map.json").write_text(json.dumps(client_map, indent=2))
    print(f"wrote client-map.json ({len(client_map['states'])} states)")

    include_sample = os.environ.get("LEAD_FINDER_BUILD_SAMPLE") == "1"
    area_slugs = build_state_areas(include_sample=include_sample)
    if area_slugs:
        print(f"wrote {len(area_slugs)} state area(s) under site/data/areas/: {', '.join(area_slugs)}")

    manifest = build_areas_manifest(area_slugs)
    print(f"wrote areas/index.json ({len(manifest['areas'])} area button(s))")


if __name__ == "__main__":
    main()
