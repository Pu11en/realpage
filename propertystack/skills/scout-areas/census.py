"""Free Census numbers per metro (S2), no API key.

- New multifamily (5+ units) permitted, last 12 months: sum of the 12 latest monthly
  Building Permits Survey CBSA files (`cbsaYYMMc.txt`, imputed totals).
- Renter households: ACS 1-year table B25003 (row `310M700US<cbsa>`, column E003) from the
  table-based summary file (api.census.gov now wants a key; the flat files do not).

Raw downloads are cached under propertystack/data/raw/census/ and reused on later runs.
"""
import csv, datetime, io, pathlib, re, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[3]
CACHE = ROOT / "propertystack" / "data" / "raw" / "census"
BPS_BASE = "https://www2.census.gov/econ/bps/CBSA%20(beginning%20Jan%202024)/"
ACS_URL = ("https://www2.census.gov/programs-surveys/acs/summary_file/{y}/table-based-SF/"
           "data/1YRData/acsdt1y{y}-b25003.dat")
BPS_UNITS_5PLUS = 15  # column index: 5+ units, Units (imputed, not "rep")


def fetch(url, name, cache=CACHE, opener=urllib.request.urlopen):
    """Return file text, downloading once into the cache."""
    path = cache / name
    if not path.exists():
        cache.mkdir(parents=True, exist_ok=True)
        with opener(url, timeout=60) as r:
            path.write_bytes(r.read())
    return path.read_text(encoding="latin-1")


def parse_bps(text):
    """{cbsa: 5+ unit count} from one monthly BPS CBSA file."""
    out = {}
    for row in csv.reader(io.StringIO(text)):
        if len(row) > BPS_UNITS_5PLUS and re.fullmatch(r"\d{6}", row[0].strip()):
            out[row[2].strip()] = int(row[BPS_UNITS_5PLUS] or 0)
    return out


def parse_acs_renters(text):
    """{cbsa: renter households} from the ACS B25003 summary file."""
    rows = csv.DictReader(io.StringIO(text), delimiter="|")
    return {r["GEO_ID"][-5:]: int(r["B25003_E003"]) for r in rows
            if r["GEO_ID"].startswith("310M") and r["B25003_E003"].isdigit()}


def last_months(listing, n=12):
    """Latest n YYMM codes that have a monthly 'c' file in the directory listing."""
    return sorted(set(re.findall(r"cbsa(\d{4})c\.txt", listing)))[-n:]


def permits_12mo(fetcher=fetch):
    months = last_months(fetcher(BPS_BASE, f"bps-index-{datetime.date.today():%Y%m%d}.html"))
    if len(months) < 12:
        raise RuntimeError(f"only {len(months)} monthly permit files found")
    total = {}
    for m in months:
        for cbsa, units in parse_bps(fetcher(BPS_BASE + f"cbsa{m}c.txt", f"cbsa{m}c.txt")).items():
            total[cbsa] = total.get(cbsa, 0) + units
    return total, f"20{months[0][:2]}-{months[0][2:]}..20{months[-1][:2]}-{months[-1][2:]}"


def renters(fetcher=fetch, year=None):
    """Newest ACS 1-year B25003 file available (tries this year back to 3 years ago)."""
    years = [year] if year else range(datetime.date.today().year - 1, datetime.date.today().year - 4, -1)
    for y in years:
        try:
            return parse_acs_renters(fetcher(ACS_URL.format(y=y), f"acsdt1y{y}-b25003.dat")), y
        except Exception:
            continue
    raise RuntimeError("no ACS B25003 file found")


def census_numbers(metros, fetcher=fetch):
    """{slug: {permits_5plus_12mo, renter_households, evidence}} for the given metros."""
    permits, window = permits_12mo(fetcher)
    rent, year = renters(fetcher)
    out = {}
    for m in metros:
        c = m["cbsa"]
        out[m["slug"]] = {
            "permits_5plus_12mo": permits.get(c),
            "renter_households": rent.get(c),
            "census_window": {"permits": window, "acs_year": year},
            "evidence": [BPS_BASE, ACS_URL.format(y=year)],
        }
    return out


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(pathlib.Path(__file__).parent))
    from run import load_metros
    for slug, d in census_numbers(load_metros()).items():
        print(f"{slug:20} permits5+={d['permits_5plus_12mo']} renters={d['renter_households']}")
