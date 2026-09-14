"""Client map targets (C2): top 15 states by new 5+ unit apartment permits (last 12 months),
and each state's ~10 cities with the most new 5+ unit permits. Free Census files, no key.

- States: Building Permits Survey state monthly files `State/stYYMMc.txt`.
- Cities: place monthly files per region `Place/<Region> Region/<rg>YYMMc.txt`.
Raw downloads are cached under propertystack/data/raw/census/ (reuses scout-areas' fetch).
"""
import csv, datetime, io, json, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "propertystack" / "skills" / "scout-areas"))
from census import fetch  # noqa: E402

BPS = "https://www2.census.gov/econ/bps/"
STATE_DIR = BPS + "State/"
REGIONS = {"Northeast": "ne", "Midwest": "mw", "South": "so", "West": "we"}
STATE_UNITS_5PLUS = 15   # stYYMMc.txt column: 5+ units, Units (imputed)
PLACE_UNITS_5PLUS = 27   # <rg>YYMMc.txt column: 5+ units, Units (imputed)
OUT = ROOT / "propertystack" / "data" / "client-map" / "targets.json"

FIPS = {"01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO", "09": "CT",
        "10": "DE", "11": "DC", "12": "FL", "13": "GA", "15": "HI", "16": "ID", "17": "IL",
        "18": "IN", "19": "IA", "20": "KS", "21": "KY", "22": "LA", "23": "ME", "24": "MD",
        "25": "MA", "26": "MI", "27": "MN", "28": "MS", "29": "MO", "30": "MT", "31": "NE",
        "32": "NV", "33": "NH", "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND",
        "39": "OH", "40": "OK", "41": "OR", "42": "PA", "44": "RI", "45": "SC", "46": "SD",
        "47": "TN", "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA", "54": "WV",
        "55": "WI", "56": "WY"}


def last_months(listing, prefix, n=12):
    """Latest n YYMM codes with a monthly 'c' file (st9912 is 1999, so sort by century)."""
    codes = set(re.findall(rf"{prefix}(\d{{4}})c\.txt", listing))
    return sorted(codes, key=lambda m: (int(m[:2]) < 80, m))[-n:]


def _rows(text):
    return (r for r in csv.reader(io.StringIO(text)) if r and re.fullmatch(r"\d{6}", r[0].strip()))


def parse_states(text):
    """{postal: 5+ units} from one state monthly file."""
    return {FIPS[r[1].strip()]: int(r[STATE_UNITS_5PLUS] or 0)
            for r in _rows(text) if r[1].strip() in FIPS and len(r) > STATE_UNITS_5PLUS}


def clean_city(name):
    """'Morrisville town' -> 'Morrisville', 'Brooklyn borough' -> 'Brooklyn' (search-friendly)."""
    name = re.sub(r"\s+", " ", name).strip()
    return re.sub(r" (town|village|borough|township|CDP)$", "", name, flags=re.I)


def parse_places(text):
    """[(postal, city, 5+ units)] from one regional place monthly file; skips county areas."""
    out = []
    for r in _rows(text):
        if len(r) <= PLACE_UNITS_5PLUS or r[1].strip() not in FIPS:
            continue
        name = clean_city(r[16])
        if not name or re.search(r"\bcounty\b|unincorporated", name, re.I):
            continue
        out.append((FIPS[r[1].strip()], name, int(r[PLACE_UNITS_5PLUS] or 0)))
    return out


def add(total, items):
    for k, v in items:
        total[k] = total.get(k, 0) + v
    return total


def build(fetcher=fetch, n_states=15, n_cities=10):
    stamp = f"{datetime.date.today():%Y%m%d}"
    months = last_months(fetcher(STATE_DIR, f"bps-state-index-{stamp}.html"), "st")
    if len(months) < 12:
        raise RuntimeError(f"only {len(months)} monthly state permit files found")
    states = {}
    for m in months:
        add(states, parse_states(fetcher(STATE_DIR + f"st{m}c.txt", f"st{m}c.txt")).items())
    top = sorted(states, key=lambda s: -states[s])[:n_states]
    cities = {}
    for region, rg in REGIONS.items():
        d = BPS + f"Place/{region}%20Region/"
        for m in months:
            add(cities, (((s, c), u) for s, c, u in
                         parse_places(fetcher(d + f"{rg}{m}c.txt", f"{rg}{m}c.txt")) if s in top))
    window = f"20{months[0][:2]}-{months[0][2:]}..20{months[-1][:2]}-{months[-1][2:]}"
    out = {"window": window, "source": BPS, "states": []}
    for s in top:
        best = sorted(((c, u) for (st, c), u in cities.items() if st == s and u > 0),
                      key=lambda x: -x[1])[:n_cities]
        out["states"].append({"state": s, "permits_5plus_12mo": states[s],
                              "cities": [{"city": c, "permits_5plus_12mo": u} for c, u in best]})
    return out


def flat(targets):
    """[{city, state}] in state order, for the C3 search loop."""
    return [{"city": c["city"], "state": s["state"]} for s in targets["states"] for c in s["cities"]]


if __name__ == "__main__":
    t = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(t, indent=1) + "\n")
    for s in t["states"]:
        print(s["state"], s["permits_5plus_12mo"], ", ".join(c["city"] for c in s["cities"]))
    print(f"{len(flat(t))} target cities, window {t['window']} -> {OUT.relative_to(ROOT)}")
