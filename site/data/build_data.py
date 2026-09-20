#!/usr/bin/env python3
"""Rebuild site/data/*.json from the real PropertyStack pipeline output.

Sources (see propertystack/CONTRACTS.md):
  propertystack/data/plano-richardson/master.csv  -> properties.json, software-share.json
  propertystack/data/plano-richardson/leads.csv   -> leads.json
  propertystack/data/plano-richardson/6-upcoming.csv -> leads.json (openingNext12mo)
  propertystack/runs/*.json                       -> pipeline.json (Under the Hood)
  site/data/areas/<state>.json                     -> lead-map.json (map.html state shading)
  propertystack/data/<state-slug>/leads.json      -> site/data/areas/<state-slug>.json
    (part-1 LeadRecord format, see propertystack/skills/lead-finder/record.py;
     plano-richardson keeps using the CSV pipeline above, unchanged; the fixture
     area `_sample` is only built when LEAD_FINDER_BUILD_SAMPLE=1 is set)

Run this any time master.csv / leads.csv / runs/*.json / a state's leads.json change.
No dependencies beyond stdlib. Usage: python3 site/data/build_data.py
"""
import csv
import glob
import hashlib
import json
import os
import re
import sys
import unicodedata
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


# Part-1 lead format (any state area) -- see propertystack/skills/lead-finder/record.py.
STATE_DATA_DIR = ROOT / "propertystack" / "data"
AREAS_OUT_DIR = OUT_DIR / "areas"
NON_STATE_AREA_DIRS = {"plano-richardson", "lead-finder-targets", "dallas-parked", "raw", "scout"}
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
CURRENT_DATA_DATE = "2026-09-15"
MIN_VISIBLE_AREA_LEADS = 25
AUTO_HIDDEN_REASON = "under-25-leads"

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


def _id_slug(value: str) -> str:
    """Make one human-readable, deterministic part of a lead content ID."""
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "unknown"


def content_id(state: str, address: str, name: str) -> str:
    """Return the stable identity for a building lead.

    IDs intentionally use only durable content: the state, normalized street
    address, and project name. Ranking and source order must never affect them.
    """
    from record import normalize_address  # noqa: E402

    normalized_address = normalize_address(address or "")
    return "-".join((
        _id_slug(state),
        _id_slug(normalized_address),
        _id_slug(name),
    ))


def _lead_content_id(lead: dict, state: str | None = None) -> str:
    """Build a content ID from either a raw record-shaped or site-shaped row."""
    lead_state = state or lead.get("area") or lead.get("state") or "unknown"
    address = lead.get("address") or ""
    if not address and lead.get("propertyId"):
        address = _address_by_lead_id().get(lead["propertyId"], "")
    name = lead.get("property") or lead.get("name") or lead.get("community") or ""
    return content_id(lead_state, address, name)


def _has_content_identity(lead: dict) -> bool:
    """Avoid treating sparse test/legacy rows as the same building."""
    return bool(
        lead.get("address")
        or lead.get("propertyId")
        or lead.get("property")
        or lead.get("name")
        or lead.get("community")
    )


def ensure_unique_content_ids(leads: list[dict]) -> None:
    """Add a deterministic source-detail suffix when sparse rows collide.

    A few feeds contain unnamed, address-less rows. Their required base ID is
    necessarily the same, so use the remaining saved facts to keep every row
    addressable without falling back to its rank or input position.
    """
    groups = {}
    for lead in leads:
        groups.setdefault(lead.get("id"), []).append(lead)
    for base, rows in groups.items():
        if len(rows) < 2:
            continue
        ordered = sorted(rows, key=lambda row: json.dumps(row, sort_keys=True, default=str))
        used = set()
        for row in ordered:
            payload = json.dumps(row, sort_keys=True, default=str).encode("utf-8")
            suffix = hashlib.sha1(payload).hexdigest()[:12]
            candidate = f"{base}-{suffix}"
            ordinal = 2
            while candidate in used:
                candidate = f"{base}-{suffix}-{ordinal}"
                ordinal += 1
            used.add(candidate)
            row["id"] = candidate


def add_first_seen(
    leads: list[dict],
    previous_path: Path,
    new_date: str | None = None,
    state: str | None = None,
) -> None:
    """Add the stable date each lead first appeared in a built area file.

    Existing output is the history store: a saved ``firstSeen`` survives every
    rebuild. Rows that predate this field use the current data snapshot date,
    while an id not present in the previous output is stamped on build day.
    """
    previous_by_id = {}
    previous_by_content = {}
    if previous_path.exists():
        previous = json.loads(previous_path.read_text())
        previous_leads = previous.get("leads", []) if isinstance(previous, dict) else previous
        for lead in previous_leads:
            if not isinstance(lead, dict):
                continue
            if lead.get("id"):
                previous_by_id[lead["id"]] = lead
            if _has_content_identity(lead):
                previous_by_content.setdefault(_lead_content_id(lead, state), lead)

    first_seen_for_new = new_date or date.today().isoformat()
    for lead in leads:
        previous = previous_by_id.get(lead.get("id"))
        if not previous and _has_content_identity(lead):
            previous = previous_by_content.get(_lead_content_id(lead, state))
        if previous:
            lead["firstSeen"] = previous.get("firstSeen") or CURRENT_DATA_DATE
        else:
            lead["firstSeen"] = first_seen_for_new


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
            "sources": sources_entries(split_urls(lead["sources"])) if lead else [],
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
            "sources": sources_entries(split_urls(lead["sources"]) if lead else split_urls(r["source_url"])),
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
    addresses = _address_by_lead_id()

    leads = []
    for r in rows:
        software = r["software"]
        if software in ("not chosen yet", "unknown", ""):
            software = None
        sources = sources_entries(r["sources"].split(";"))

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
            "id": content_id("tx", addresses.get(property_id, ""), r["name"]),
            "propertyId": property_id,
            "score": int(r["score"]),
            "property": r["name"],
            "city": r["city"],
            "address": addresses.get(property_id, "") or None,
            "units": int(r["units"]) if r["units"] else None,
            "signalType": "Upcoming" if r["signal"] == "upcoming" else "Sold",
            "signal": short_signal(r["signal"], r["why"]),
            "software": software,
            "why": r["why"],
            "sources": sources,
            "contact": contact,
            "isNew": is_new,
        })

    ensure_unique_content_ids(leads)
    add_first_seen(leads, OUT_DIR / "leads.json", state="tx")

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


_GENERIC_NAMES = {
    "building permit", "apartments (3+ dwelling units)", "new construction", "apartments",
    "multi-family dwelling", "commercial multi-family", "multifamily", "unnamed project",
}
# Raw subdivision/plat labels a permit feed uses instead of a project name, e.g.
# "South Pier Lot 6" (developer "City of Tempe"): a plat name plus a lot/parcel/tract number.
_LOT_LABEL_RE = re.compile(r"^.+\b(?:lot|parcel|tract)\s+\d+[a-z]?$", re.I)
_DICT_URL_RE = re.compile(r"""^\{'url': '([^']+)'\}$""")


def _plain_url(s: str) -> str:
    """Some sources were saved as "{'url': '...'}" text: keep just the URL."""
    m = _DICT_URL_RE.match(s or "")
    return m.group(1) if m else s


# Raw data-API endpoints (ArcGIS/Socrata query URLs) that a person can't read in a
# browser. Each one becomes the public page that shows the same records, with a
# plain name (C4). Order matters: first matching fragment wins.
_SOURCE_PAGES = [
    ("arcgis.com/sharing/rest/content/items/f3484c72", "Maricopa County Assessor sales records",
     "https://www.arcgis.com/home/item.html?id=f3484c72a938497286adc4e5de7e9963"),
    ("arcgis.com/sharing/rest/content/items/936bbba5", "Maricopa County Assessor property records",
     "https://www.arcgis.com/home/item.html?id=936bbba512bf4c368618cc6e79e64668"),
    ("maps.scottsdaleaz.gov", "City of Scottsdale building permits",
     "https://eservices.scottsdaleaz.gov/bldgresources/buildingpermit"),
    ("data.mesaaz.gov", "City of Mesa building permits",
     "https://data.mesaaz.gov/Building-Development/Building-Permits/dzpk-hxfb"),
    ("maps.phoenix.gov", "City of Phoenix planning permits", "https://www.phoenixopendata.com/"),
    ("services.arcgis.com/lQySeXwbBg53XWDi", "City of Tempe building permits",
     "https://www.arcgis.com/home/item.html?id=55b38626464d48cb94e81cb8227d6fde"),
    ("maps.gilbertaz.gov", "Town of Gilbert building permits", "https://data-gilbert.opendata.arcgis.com/"),
    ("services.arcgis.com/ykpntM6e3tHvzKRJ", "Maricopa County building permits",
     "https://www.arcgis.com/home/item.html?id=86909eb1ea9149308abaadba377f388f"),
    ("gis.tucsonaz.gov", "City of Tucson building permits", "https://gis.tucsonaz.gov/"),
    ("smgis.sanmarcostx.gov", "City of San Marcos building permits",
     "https://www.sanmarcostx.gov/254/Building-Permits"),
    ("services5.arcgis.com/3ddLCBXe1bRt7mzj", "City of Fort Worth development permits",
     "https://www.arcgis.com/home/item.html?id=d2740f4d746b4bfaa03e25de0376238b"),
    ("gis2.arlingtontx.gov", "City of Arlington issued permits", "https://opendata.arlingtontx.gov/"),
    ("maps.las-cruces.org", "City of Las Cruces building permits",
     "https://lascruces.gov/directories-resources/permits-licenses-and-registrations/"),
    ("data.texas.gov/resource/5tkr-3759", "Texas county property records", "https://data.texas.gov/d/5tkr-3759"),
    ("data.buffalony.gov/resource/9p2d-f3yt", "City of Buffalo building permits",
     "https://data.buffalony.gov/Government/Building-Permits/9p2d-f3yt"),
]

# Internal labels from the Plano-Richardson CSV ("[county record]", "[houston-weekly-xlsx]"):
# a plain name a person reads, plus the public page when one exists (C4).
_SOURCE_TAGS = {
    "county record": ("County property records", "https://data.texas.gov/d/5tkr-3759"),
    "permit": ("City permit record", None),
    "news": ("News coverage", None),
    "website": ("Building website", None),
    "houston-weekly-xlsx": ("Houston weekly permit list",
                            "https://www.houstontx.gov/planning/DevelopRegs/"),
}


def _url_source_label(url: str) -> str:
    """A plain name for a source URL that is already a page a person can open."""
    if "tdlr.texas.gov" in url:
        return "State project record"
    if "austintexas.gov" in url:
        return "City permit record"
    if "tdhca.texas.gov" in url or "tad.org" in url:
        return "State permit data"
    if "data.texas.gov" in url:
        return "County record"
    if "legistar" in url or "zabalist.com" in url or "civicplus" in url:
        return "City filing"
    if any(d in url for d in ("communityimpact.com", "dallasnews.com", "candysdirt.com")):
        return "News"
    return "Website"


def _source_url(s) -> str:
    if isinstance(s, dict):
        return _plain_url(str(s.get("url") or "")).strip()
    if hasattr(s, "url"):  # record.Source
        return _plain_url(str(s.url or "")).strip()
    return _plain_url(str(s or "")).strip()


def source_entry(s) -> dict | None:
    """One source as {"label": ..., "url": ...}: raw data-API links open the
    dataset's public page, internal tags get a plain name, and links that are
    already human pages keep their URL with a plain label (C4)."""
    raw = _source_url(s)
    if not raw:
        return None
    for frag, label, url in _SOURCE_PAGES:
        if frag in raw:
            return {"label": label, "url": url}
    tag = _SOURCE_TAGS.get(raw.lower())
    if tag:
        return {"label": tag[0], "url": tag[1]}
    if raw.startswith("http"):
        return {"label": _url_source_label(raw), "url": raw}
    return {"label": raw.strip("[]"), "url": None}


def sources_entries(items) -> list[dict]:
    """Normalize a list of saved sources to {label, url}, dropping duplicates."""
    out, seen = [], set()
    for s in items or []:
        e = source_entry(s)
        if e and (e["label"], e["url"]) not in seen:
            seen.add((e["label"], e["url"]))
            out.append(e)
    return out


def _nice_name(name: str, address: str = "") -> str:
    """ALL-CAPS names read as shouting; a generic permit label isn't a name --
    call it "Apartments at <address>" when there is one."""
    stripped = (name or "").strip()
    if stripped.lower() in _GENERIC_NAMES or _LOT_LABEL_RE.match(stripped):
        return f"Apartments at {address.title()}" if address else "Unnamed project"
    return name.title() if name and name.isupper() else name


_UNITS_TEXT_RE = re.compile(r"(\d{1,4})\s*[- ]\s*units?\b", re.I)


def _area_units(record) -> int | None:
    """The site shows "?" for unknown units. A source's 0 means "not recorded"
    (e.g. a permit feed's units_added column), never an empty building, so treat
    0 like a blank; a few records still carry their count in saved text ("8 UNIT
    ..."), so use that when present."""
    if record.units and record.units > 0:
        return record.units
    m = _UNITS_TEXT_RE.search(f"{record.name} {record.why}")
    return int(m.group(1)) if m else None


def _is_leasing(record) -> bool:
    """A record's own "leasing" stage wins even with no opening date; otherwise
    not sold/planned and its opening date already passed."""
    if record.stage == "leasing":
        return True
    return (
        record.stage not in ("sold", "planned")
        and bool(record.opening_date)
        and record.opening_date <= date.today().isoformat()
    )


def _leasing_why(record) -> str:
    """A leasing row must not also read "opens: not public yet" (C5)."""
    parts = [p for p in _clean_why(record.why).split(" · ")
             if not re.match(r"opens?:?\s*not public yet", p, re.I)]
    return " · ".join(parts)


def _area_sort_key(record):
    """Soonest openings first, then leasing now, planned, recently sold."""
    today = date.today().isoformat()
    if record.stage == "sold":
        return (3, "", -int((record.sale_date or "0").replace("-", "") or 0))
    if record.stage == "planned":
        return (2, record.opening_date or "9999", 0)
    if _is_leasing(record):
        return (1, "", -int(record.opening_date.replace("-", "")) if record.opening_date else 0)
    return (0, record.opening_date if (record.opening_date or "") > today else "9999", 0)


def _area_lead_dict(record, idx: int, total: int = 34) -> dict:
    is_sold = record.stage == "sold"
    leasing = _is_leasing(record)
    name = _nice_name(record.name or record.address or "Unnamed project", record.address)
    return {
        "id": content_id(record.area, record.address, name),
        "property": name,
        "community": record.name or None,
        "city": record.city,
        "address": record.address or None,
        "units": _area_units(record),
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
        "sources": sources_entries(record.sources),
        "signalType": "Sold" if is_sold else (
            "Planned" if record.stage == "planned" else ("Leasing" if leasing else "Upcoming")
        ),
        "signal": (f"Opened {record.opening_date}" if record.opening_date else "Leasing now") if leasing
                  else _area_signal_text(record),
        "why": _leasing_why(record) if leasing else _clean_why(record.why),
        # Records already come out of score_and_rank in rank order (4.5); this
        # is a display-only stand-in for a numeric score until the site needs one.
        "score": max(1, round(100 * (1 - (idx - 1) / total))),
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
    from junk_permits import is_junk_permit  # noqa: E402
    records = [LeadRecord.from_dict(d) for d in raw]
    # permits already saved before the lead finder learned to skip them
    records = [r for r in records if not is_junk_permit(r.name, r.address, r.why)]
    # one row per building: same-name duplicates merged, phases labeled (C2)
    from dedupe_leads import dedupe_leads  # noqa: E402
    records = dedupe_leads(records)
    ranked = sorted(score_and_rank(records), key=_area_sort_key)

    leads = [_area_lead_dict(r, i, len(ranked)) for i, r in enumerate(ranked, start=1)]
    metros = _load_metros(slug)
    if metros:
        city_to_metro = {c.lower(): m for m, cs in metros["metros"].items() for c in cs}
        for lead in leads:
            lead["metro"] = city_to_metro.get((lead["city"] or "").lower(), metros["rest_label"])
        order = list(metros["metros"]) + [metros["rest_label"]]
        counts = Counter(lead["metro"] for lead in leads)
        metro_list = [{"name": m, "leads": counts[m]} for m in order if counts[m]]
    else:
        metro_list = []
    cities = sorted({r.city for r in ranked if r.city})
    units_in_play = sum(r.units or 0 for r in ranked if r.units)

    return {
        "area": slug,
        # The lead snapshot date, not the day the site happens to be rebuilt.
        "updated": latest_area_run_date(slug) or CURRENT_DATA_DATE,
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
        "metros": metro_list,
        "leads": leads,
    }


def _load_metros(slug: str) -> dict | None:
    """Optional data/<slug>/metros.json: city -> metro group for the metro buttons."""
    path = STATE_DATA_DIR / slug / "metros.json"
    if not path.exists():
        return None
    with path.open() as f:
        return json.load(f)


CHAT_LEADS_COLUMNS = [
    "area", "name", "city", "address", "units", "stage", "signal", "why",
    "permit_date", "opening_date", "sale_date", "buyer", "developer",
    "office_phone", "website", "software", "permit_link", "news_link",
    "website_link", "agenda_link", "map_link", "source_link", "region", "status",
]


def _included_stage(lead: dict) -> str:
    """Included older areas (Plano-Richardson) have no stage, only Sold/Upcoming."""
    if not lead.get("subArea"):
        return ""
    return "sold" if lead.get("signalType") == "Sold" else "planned"


def write_chat_leads_csv(slug: str, area_json: dict) -> None:
    """Flatten one state area's JSON (5.1's `build_area`) into a chat-ready CSV
    at propertystack/data/<slug>/chat-leads.csv -- the chatbot's plugin (5.4)
    copies every area's chat-leads.csv into one `state_leads` table, since a
    state area has no master/contacts CSVs to join against (its lead rows are
    already flat)."""
    out_path = STATE_DATA_DIR / slug / "chat-leads.csv"
    with out_path.open("w", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")  # LF, same as git stores it
        writer.writerow(CHAT_LEADS_COLUMNS)
        for lead in area_json["leads"]:
            links = lead.get("links") or {}
            source_link = next(
                (source.get("url") for source in (lead.get("sources") or [])
                 if isinstance(source, dict) and source.get("url")),
                "",
            ) or next((url for url in links.values() if url), "")
            writer.writerow([
                slug, lead.get("property") or "", lead.get("city") or "",
                lead.get("address") or "", lead.get("units") or "",
                lead.get("stage") or _included_stage(lead), lead.get("signal") or "", lead.get("why") or "",
                lead.get("permitDate") or "", lead.get("openingDate") or "",
                lead.get("saleDate") or "", lead.get("buyer") or "",
                lead.get("developer") or "", lead.get("officePhone") or "",
                lead.get("website") or "", lead.get("software") or "",
                links.get("permit") or "", links.get("news") or "",
                links.get("website") or "", links.get("agenda") or "",
                links.get("map") or "",
                source_link,
                lead.get("metro") or "", lead.get("signalType") or "",
            ])


def build_state_areas(include_sample: bool = False) -> list[str]:
    """Build every discovered state area's JSON under site/data/areas/, plus
    its chat-leads.csv (for the chatbot). Returns the slugs actually built."""
    slugs = discover_state_areas(include_sample=include_sample)
    if not slugs:
        return []
    AREAS_OUT_DIR.mkdir(parents=True, exist_ok=True)
    for slug in slugs:
        area_json = _merge_included_areas(slug, build_area(slug))
        ensure_unique_content_ids(area_json["leads"])
        add_first_seen(area_json["leads"], AREAS_OUT_DIR / f"{slug}.json", state=slug)
        # after the merge, so the chat counts included areas (Plano-Richardson
        # in Texas / Dallas-Fort Worth) exactly like the site does
        write_chat_leads_csv(slug, area_json)
        (AREAS_OUT_DIR / f"{slug}.json").write_text(json.dumps(area_json, indent=2))
    return slugs


def _address_by_lead_id() -> dict:
    """ref_id / project_id -> street address from the saved Plano-Richardson
    property data, so included rows (and the chat) can give addresses (C5)."""
    path = OUT_DIR / "properties.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    out = {}
    for p in (data.get("properties") or []) + (data.get("upcoming") or []):
        if p.get("id") and p.get("address"):
            out[p["id"]] = p["address"]
    return out


def _merge_included_areas(slug: str, area_json: dict) -> dict:
    """Show older areas (e.g. a city pair inside this state) inside the state's
    table, under their metro, instead of as a separate button."""
    metros = _load_metros(slug)
    addrs = _address_by_lead_id() if (metros or {}).get("include_areas") else {}
    existing_by_name_city = {
        (_id_slug(lead.get("property") or ""), _id_slug(lead.get("city") or "")): lead
        for lead in area_json["leads"]
        if lead.get("property") and lead.get("city")
    }
    for inc in (metros or {}).get("include_areas", []):
        path = OUT_DIR / inc["dataPath"]
        if not path.exists():
            continue
        extra = json.loads(path.read_text())
        rows = extra.get("leads", []) if isinstance(extra, dict) else extra
        for i, lead in enumerate(rows, start=1):
            lead = dict(lead)
            lead["metro"] = inc["metro"]
            lead["subArea"] = inc["label"]
            if not lead.get("address"):
                lead["address"] = addrs.get(lead.get("propertyId")) or None
            lead["id"] = content_id(slug, lead.get("address") or "", lead.get("property") or "")
            lead.setdefault("sources", [])
            duplicate = existing_by_name_city.get((
                _id_slug(lead.get("property") or ""),
                _id_slug(lead.get("city") or ""),
            ))
            if duplicate:
                duplicate["metro"] = inc["metro"]
                duplicate["subArea"] = inc["label"]
                for field in ("units", "website", "software", "contact"):
                    if not duplicate.get(field) and lead.get(field):
                        duplicate[field] = lead[field]
                duplicate["sources"] = sources_entries(
                    [*(duplicate.get("sources") or []), *lead["sources"]]
                )
                continue
            area_json["leads"].append(lead)
    if (metros or {}).get("include_areas"):
        area_json["leads"].sort(key=lambda lead: -lead.get("score", 0))
        counts = Counter(lead.get("metro") for lead in area_json["leads"])
        area_json["metros"] = [{"name": m["name"], "leads": counts[m["name"]]} for m in area_json["metros"]]
        area_json["cities"] = sorted({lead["city"] for lead in area_json["leads"] if lead.get("city")})
        st = area_json["stats"]
        st["leads"] = len(area_json["leads"])
        st["cities"] = len(area_json["cities"])
        st["unitsInPlay"] = sum(lead.get("units") or 0 for lead in area_json["leads"])
        st["newThisWeek"] = sum(1 for lead in area_json["leads"] if lead.get("isNew"))
    return area_json


def _included_slugs(area_slugs: list[str]) -> set[str]:
    """Areas shown inside a state's table rather than as their own button."""
    return {inc["slug"] for s in area_slugs for inc in ((_load_metros(s) or {}).get("include_areas", []))}


def latest_area_run_date(slug: str) -> str | None:
    """Return the newest completed run date for one state area."""
    dates = []
    for path in (RUNS_DIR / "area").glob(f"*/{slug}/summary.json"):
        value = path.parent.parent.name
        try:
            date.fromisoformat(value)
        except ValueError:
            continue
        dates.append(value)
    return max(dates, default=None)


def build_areas_manifest(area_slugs: list[str]) -> dict:
    """Write site/data/areas/index.json: one entry per area button on the Early
    Leads page (5.2). Plano-Richardson keeps its own legacy leads.json; every
    discovered state area (5.1) points at its file under data/areas/."""
    manifest_path = AREAS_OUT_DIR / "index.json"
    previous_areas = {}
    if manifest_path.exists():
        try:
            previous_manifest = json.loads(manifest_path.read_text())
            previous_areas = {
                area["slug"]: area
                for area in previous_manifest.get("areas", [])
                if isinstance(area, dict) and area.get("slug")
            }
        except (json.JSONDecodeError, OSError):
            pass
    included = _included_slugs(area_slugs)
    areas = [] if AREA in included else [{"slug": AREA, "label": "Plano–Richardson", "dataPath": "data/leads.json", "leads": None}]
    area_dates = []
    for slug in area_slugs:
        area = json.loads((AREAS_OUT_DIR / f"{slug}.json").read_text())
        area_dates.append(area["updated"])
        manifest_area = {
            "slug": slug,
            "label": _STATE_NAMES.get(slug, slug.replace("-", " ").title()),
            "dataPath": f"data/areas/{slug}.json",
            "leads": len(area["leads"]),
        }
        previous = previous_areas.get(slug, {})
        was_auto_hidden = previous.get("hiddenReason") == AUTO_HIDDEN_REASON
        manually_hidden = previous.get("hidden") is True and not was_auto_hidden
        if manually_hidden:
            manifest_area["hidden"] = True
            if previous.get("hiddenReason"):
                manifest_area["hiddenReason"] = previous["hiddenReason"]
        elif len(area["leads"]) < MIN_VISIBLE_AREA_LEADS:
            manifest_area["hidden"] = True
            manifest_area["hiddenReason"] = AUTO_HIDDEN_REASON
        areas.append(manifest_area)
    # Biggest first: the state with the most leads opens by default.
    areas.sort(key=lambda a: -(a["leads"] or 0))
    # Old links (?area=plano-richardson) open the state that now holds that area.
    aliases = {inc: s for s in area_slugs for inc in [i["slug"] for i in (_load_metros(s) or {}).get("include_areas", [])]}
    # Derive freshness from the area snapshots. Rebuilding/deploying the site
    # must not make unchanged lead data appear newer than it is.
    manifest = {"areas": areas, "aliases": aliases, "updated": max(area_dates, default=CURRENT_DATA_DATE)}
    AREAS_OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def build_summary(area_slugs: list[str], manifest: dict) -> dict:
    """Build the public, state-agnostic counts used by both site heroes.

    Areas automatically hidden only because they are still small remain part of
    the tracked total. Manually hidden fixture/retired areas do not.
    """
    by_slug = {area["slug"]: area for area in manifest.get("areas", [])}
    leads = []
    check_dates = []
    for slug in area_slugs:
        area_meta = by_slug.get(slug, {})
        manually_hidden = (
            area_meta.get("hidden") is True
            and area_meta.get("hiddenReason") != AUTO_HIDDEN_REASON
        )
        if manually_hidden:
            continue
        path = AREAS_OUT_DIR / f"{slug}.json"
        if not path.exists():
            continue
        area = json.loads(path.read_text())
        leads.extend(area.get("leads", []))
        if area.get("updated"):
            check_dates.append(area["updated"])

    last_check = max(check_dates, default=manifest.get("updated") or CURRENT_DATA_DATE)
    try:
        new_cutoff = (date.fromisoformat(last_check) - timedelta(days=6)).isoformat()
    except ValueError:
        new_cutoff = last_check

    sold = sum(lead.get("signalType") == "Sold" for lead in leads)
    return {
        "lastCheck": last_check,
        "totalTracked": len(leads),
        "newLast7Days": sum(
            new_cutoff <= lead.get("firstSeen", "") <= last_check
            for lead in leads
        ),
        # Keep the runner's established definition: every current non-sale
        # building signal is in the permits side of the summary.
        "permitsFiled": len(leads) - sold,
        "sold": sold,
    }


_STATE_NAMES = {
    "al": "Alabama", "ak": "Alaska", "az": "Arizona", "ar": "Arkansas", "ca": "California", "co": "Colorado",
    "ct": "Connecticut", "de": "Delaware", "fl": "Florida", "ga": "Georgia", "hi": "Hawaii", "id": "Idaho",
    "il": "Illinois", "in": "Indiana", "ia": "Iowa", "ks": "Kansas", "ky": "Kentucky", "la": "Louisiana",
    "me": "Maine", "md": "Maryland", "ma": "Massachusetts", "mi": "Michigan", "mn": "Minnesota",
    "ms": "Mississippi", "mo": "Missouri", "mt": "Montana", "ne": "Nebraska", "nv": "Nevada",
    "nh": "New Hampshire", "nj": "New Jersey", "nm": "New Mexico", "ny": "New York", "nc": "North Carolina",
    "nd": "North Dakota", "oh": "Ohio", "ok": "Oklahoma", "or": "Oregon", "pa": "Pennsylvania",
    "ri": "Rhode Island", "sc": "South Carolina", "sd": "South Dakota", "tn": "Tennessee", "tx": "Texas",
    "ut": "Utah", "vt": "Vermont", "va": "Virginia", "wa": "Washington", "wv": "West Virginia",
    "wi": "Wisconsin", "wy": "Wyoming", "dc": "District of Columbia",
}


def build_map_markers(area_slugs: list[str]) -> dict:
    """site/data/map-markers.json: one orange marker per state we have leads in.
    Statewide areas are named by state code; the legacy Plano-Richardson area rolls
    up into Texas when there is no statewide Texas area."""
    markers = {}
    for slug in area_slugs:
        name = _STATE_NAMES.get(slug)
        if not name:
            continue
        area = json.loads((AREAS_OUT_DIR / f"{slug}.json").read_text())
        counts = Counter(lead["city"] for lead in area["leads"] if lead.get("city"))
        markers[name] = {
            "state": name,
            "code": slug.upper(),
            "leads": len(area["leads"]),
            "label": f"{slug.upper()} · {len(area['leads'])} leads",
            "topCities": [c for c, _ in counts.most_common(3)],
            "link": f"index.html?area={slug}",
        }
    if "Texas" not in markers:
        legacy = json.loads((OUT_DIR / "leads.json").read_text())
        rows = legacy.get("leads", legacy) if isinstance(legacy, dict) else legacy
        markers["Texas"] = {
            "state": "Texas", "code": "TX", "leads": len(rows), "label": f"TX · {len(rows)} leads",
            "topCities": [c for c, _ in Counter(r.get("city") for r in rows if r.get("city")).most_common(3)],
            "link": f"index.html?area={AREA}",
        }
    return {"markers": list(markers.values())}


def build_lead_map(area_slugs: list[str]) -> dict:
    """site/data/lead-map.json: per-state lead counts + top 3 cities, keyed by full
    state name (the map's topojson names states, not abbreviations)."""
    states = {}
    for slug in area_slugs:
        name = _STATE_NAMES.get(slug)
        if not name:
            continue
        leads = json.loads((AREAS_OUT_DIR / f"{slug}.json").read_text())["leads"]
        states[name] = {"abbr": slug.upper(), "rows": leads}
    if "Texas" not in states:
        legacy = json.loads((OUT_DIR / "leads.json").read_text())
        states["Texas"] = {"abbr": "TX", "rows": legacy.get("leads", legacy) if isinstance(legacy, dict) else legacy}
    for name, d in states.items():
        rows = d.pop("rows")
        top = Counter(r["city"] for r in rows if r.get("city")).most_common(3)
        d.update(total=len(rows), topCities=[{"city": c, "count": n} for c, n in top])
    return {"source": "site/data/areas", "states": states}


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

    include_sample = os.environ.get("LEAD_FINDER_BUILD_SAMPLE") == "1"
    area_slugs = build_state_areas(include_sample=include_sample)
    if area_slugs:
        print(f"wrote {len(area_slugs)} state area(s) under site/data/areas/: {', '.join(area_slugs)}")

    manifest = build_areas_manifest(area_slugs)
    print(f"wrote areas/index.json ({len(manifest['areas'])} area button(s))")

    summary = build_summary(area_slugs, manifest)
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(f"wrote summary.json ({summary['totalTracked']} tracked buildings)")

    markers = build_map_markers(area_slugs)
    (OUT_DIR / "map-markers.json").write_text(json.dumps(markers, indent=2))
    print(f"wrote map-markers.json ({len(markers['markers'])} state marker(s))")

    lead_map = build_lead_map(area_slugs)
    (OUT_DIR / "lead-map.json").write_text(json.dumps(lead_map, indent=2))
    print(f"wrote lead-map.json ({len(lead_map['states'])} states)")


if __name__ == "__main__":
    main()
