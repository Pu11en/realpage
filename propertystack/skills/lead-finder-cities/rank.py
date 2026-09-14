"""lead-finder 2.1: rank a state's cities (free Census BPS place-level files).

Self-contained (doesn't import client-map/targets.py, which depends on a since-deleted
scout-areas/census.py): its own small cached `fetch()` and place-file parsing, for any state
(not just the client map's top 15), keeping unincorporated-county permit areas instead of
dropping them.
"""
import argparse, csv, datetime, io, json, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]

DATA = ROOT / "propertystack" / "data"
CACHE = DATA / "raw" / "census"
COUNTS_FILE = DATA / "client-map" / "counts.json"

BPS = "https://www2.census.gov/econ/bps/"
STATE_DIR = BPS + "State/"
REGIONS = {"Northeast": "ne", "Midwest": "mw", "South": "so", "West": "we"}
PLACE_UNITS_5PLUS = 27   # <rg>YYMMc.txt column: 5+ units, Units (imputed)

FIPS = {"01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO", "09": "CT",
        "10": "DE", "11": "DC", "12": "FL", "13": "GA", "15": "HI", "16": "ID", "17": "IL",
        "18": "IN", "19": "IA", "20": "KS", "21": "KY", "22": "LA", "23": "ME", "24": "MD",
        "25": "MA", "26": "MI", "27": "MN", "28": "MS", "29": "MO", "30": "MT", "31": "NE",
        "32": "NV", "33": "NH", "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND",
        "39": "OH", "40": "OK", "41": "OR", "42": "PA", "44": "RI", "45": "SC", "46": "SD",
        "47": "TN", "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA", "54": "WV",
        "55": "WI", "56": "WY"}

COUNTY_RE = re.compile(r"\bcounty\b|unincorporated", re.I)


def fetch(url, name, cache=CACHE, opener=None):
    """Return file text, downloading once into the cache."""
    import urllib.request
    opener = opener or urllib.request.urlopen
    path = cache / name
    if not path.exists():
        cache.mkdir(parents=True, exist_ok=True)
        with opener(url, timeout=60) as r:
            path.write_bytes(r.read())
    return path.read_text(encoding="latin-1")


def last_months(listing, prefix, n=12):
    """Latest n YYMM codes with a monthly 'c' file (st9912 is 1999, so sort by century)."""
    codes = set(re.findall(rf"{prefix}(\d{{4}})c\.txt", listing))
    return sorted(codes, key=lambda m: (int(m[:2]) < 80, m))[-n:]


def clean_city(name):
    """'Morrisville town' -> 'Morrisville', 'Brooklyn borough' -> 'Brooklyn' (search-friendly)."""
    name = re.sub(r"\s+", " ", name).strip()
    return re.sub(r" (town|village|borough|township|CDP)$", "", name, flags=re.I)


def parse_places_all(text, state):
    """[(city, units, is_county_area)] for one state from one regional place monthly file."""
    out = []
    for r in csv.reader(io.StringIO(text)):
        if not r or not re.fullmatch(r"\d{6}", r[0].strip()):
            continue
        if len(r) <= PLACE_UNITS_5PLUS or r[1].strip() not in FIPS:
            continue
        if FIPS[r[1].strip()] != state:
            continue
        name = clean_city(r[16])
        if not name:
            continue
        is_county = bool(COUNTY_RE.search(name))
        out.append((name, int(r[PLACE_UNITS_5PLUS] or 0), is_county))
    return out


def realpage_counts(state, counts_path=COUNTS_FILE):
    """{city: count} from the client map's counts.json, empty if the state isn't there yet."""
    if not counts_path.exists():
        return {}
    counts = json.loads(counts_path.read_text())
    return counts.get(state, {}).get("cities", {})


def rank_cities(state, fetcher=fetch, months_back=12):
    stamp = f"{datetime.date.today():%Y%m%d}"
    months = last_months(
        fetcher(STATE_DIR, f"bps-state-index-{stamp}.html"), "st", n=months_back)
    if len(months) < months_back:
        raise RuntimeError(f"only {len(months)} monthly permit files found")
    totals = {}
    for region, rg in REGIONS.items():
        d = BPS + f"Place/{region}%20Region/"
        for m in months:
            for city, units, is_county in parse_places_all(fetcher(d + f"{rg}{m}c.txt", f"{rg}{m}c.txt"), state):
                key = (city, is_county)
                totals[key] = totals.get(key, 0) + units
    rp_counts = realpage_counts(state)
    cities = [
        {"city": city, "is_county_area": is_county, "permits_5plus": units,
         "realpage_count": rp_counts.get(city, 0)}
        for (city, is_county), units in totals.items() if units > 0
    ]
    cities.sort(key=lambda c: -c["permits_5plus"])
    window = f"20{months[0][:2]}-{months[0][2:]}..20{months[-1][:2]}-{months[-1][2:]}"
    return {"state": state, "window": window, "source": BPS, "cities": cities}


def build(state, fetcher=fetch, months_back=12):
    out = rank_cities(state, fetcher, months_back)
    path = DATA / state.lower() / "cities.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=1) + "\n")
    return out, path


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--state", required=True)
    p.add_argument("--months", type=int, default=12)
    args = p.parse_args()
    out, path = build(args.state.upper(), months_back=args.months)
    for c in out["cities"][:20]:
        tag = " (county area)" if c["is_county_area"] else ""
        print(f"{c['city']}{tag}: permits={c['permits_5plus']} realpage={c['realpage_count']}")
    print(f"{len(out['cities'])} cities -> {path.relative_to(ROOT)}")
