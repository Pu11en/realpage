"""Build RealPage's public reach dots for site/data/reach.json from web search.

For each US metro in a small built-in table, search (Jina) for RealPage offices, case
studies and press releases naming apartment companies there. A result counts as a
"sign" for a metro only if it has a URL, mentions RealPage and names that metro's city.
Metros are geocoded from the table (no paid geocoder). Dots with source "our-data"
(seed_reach.py) and scout markers are kept untouched.

Search results are cached in tooling/reach/cache.json so a rerun costs nothing;
pass --fresh to search again. Budget: MAX_SEARCHES (about 100).
Run: JINA_API_KEY=... python3 tooling/reach/build_reach.py
"""
import json, sys, datetime as dt
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "propertystack"))
from lib.jina import Jina          # noqa: E402
from lib.runlog import RunLog      # noqa: E402

OUT = ROOT / "site/data/reach.json"
CACHE = Path(__file__).with_name("cache.json")
MAX_SEARCHES = 100
MAX_LINKS = 6

# (city, state, lat, lon, extra names that also count as this metro)
METROS = [
    ("Dallas", "TX", 32.7767, -96.7970, ["Fort Worth", "Richardson", "Frisco", "Irving"]),
    ("Houston", "TX", 29.7604, -95.3698, []),
    ("Austin", "TX", 30.2672, -97.7431, []),
    ("San Antonio", "TX", 29.4241, -98.4936, []),
    ("Atlanta", "GA", 33.7490, -84.3880, []),
    ("Phoenix", "AZ", 33.4484, -112.0740, ["Scottsdale", "Tempe"]),
    ("Denver", "CO", 39.7392, -104.9903, []),
    ("Nashville", "TN", 36.1627, -86.7816, []),
    ("Charlotte", "NC", 35.2271, -80.8431, []),
    ("Raleigh", "NC", 35.7796, -78.6382, ["Durham"]),
    ("Orlando", "FL", 28.5383, -81.3792, []),
    ("Tampa", "FL", 27.9506, -82.4572, []),
    ("Miami", "FL", 25.7617, -80.1918, ["Fort Lauderdale"]),
    ("Jacksonville", "FL", 30.3322, -81.6557, []),
    ("Las Vegas", "NV", 36.1699, -115.1398, []),
    ("Seattle", "WA", 47.6062, -122.3321, ["Bellevue"]),
    ("Portland", "OR", 45.5152, -122.6784, []),
    ("San Francisco", "CA", 37.7749, -122.4194, ["Oakland", "San Jose"]),
    ("Los Angeles", "CA", 34.0522, -118.2437, ["Irvine"]),
    ("San Diego", "CA", 32.7157, -117.1611, []),
    ("Salt Lake City", "UT", 40.7608, -111.8910, ["Lehi"]),
    ("Chicago", "IL", 41.8781, -87.6298, []),
    ("Minneapolis", "MN", 44.9778, -93.2650, []),
    ("Columbus", "OH", 39.9612, -82.9988, []),
    ("Indianapolis", "IN", 39.7684, -86.1581, []),
    ("Kansas City", "MO", 39.0997, -94.5786, []),
    ("Washington", "DC", 38.9072, -77.0369, ["D.C.", "Washington DC", "Arlington, VA", "McLean"]),
    ("Boston", "MA", 42.3601, -71.0589, []),
    ("New York", "NY", 40.7128, -74.0060, []),
    ("Philadelphia", "PA", 39.9526, -75.1652, []),
    ("Reno", "NV", 39.5296, -119.8138, []),
    ("Waco", "TX", 31.5493, -97.1467, ["Woodway"]),
]
OFFICE_PAGE = "https://www.realpage.com/company/office-locations/"
# US offices listed on OFFICE_PAGE (read 2026-09-13); HQ is in Richardson (our-data dot)
OFFICES = {"Los Angeles": "Irvine, CA", "Chicago": "Lombard, IL", "Boston": "Boston, MA",
           "Reno": "Reno, NV", "Waco": "Woodway, TX", "Seattle": "Seattle, WA"}
QUERIES = [
    'RealPage {city} apartment management company case study',
    'RealPage {city} {state} apartments press release selects RealPage',
]
GENERAL = [
    "RealPage office locations United States",
    "RealPage customer case study multifamily",
    "property management company selects RealPage press release",
    "RealPage announces partnership apartment operator",
]
SKIP_DOMAINS = ("reddit.com", "facebook.com", "x.com", "twitter.com", "tiktok.com",
                "instagram.com", "youtube.com", "linkedin.com", "wikipedia.org", "scribd.com",
                "globaldata.com")
# RealPage's own market-report pages name cities but say nothing about customers there
SKIP_PATHS = ("realpage.com/analytics/",)


def search_all(fresh: bool):
    cache = {} if fresh or not CACHE.exists() else json.loads(CACHE.read_text())
    queries = GENERAL + [q.format(city=m[0], state=m[1]) for m in METROS for q in QUERIES]
    jina, spent = None, 0
    for q in queries:
        if q in cache:
            continue
        if spent >= MAX_SEARCHES:
            break
        jina = jina or Jina()
        cache[q] = jina.search(q)
        spent += 1
        CACHE.write_text(json.dumps(cache, indent=1) + "\n")
    return cache, spent


# city names that also mean something else ("Washington" state); only their aliases count
AMBIGUOUS = {"Washington"}


def match_metro(text: str):
    low = text.lower()
    for m in METROS:
        names = m[4] if m[0] in AMBIGUOUS else [m[0], *m[4]]
        if any(n.lower() in low for n in names):
            return m
    return None


def build(cache):
    by_metro = {}
    for results in cache.values():
        for r in results:
            url = r.get("url") or ""
            host = urlparse(url).netloc.lower()
            if (not url.startswith("http") or any(host.endswith(d) for d in SKIP_DOMAINS)
                    or any(sp in url for sp in SKIP_PATHS) or url.rstrip("/") == OFFICE_PAGE.rstrip("/")):
                continue
            text = f"{r.get('title', '')} {r.get('description', '')}"
            if "realpage" not in text.lower():
                continue
            m = match_metro(text)
            if not m:
                continue
            by_metro.setdefault(m[:4], {})[url] = r.get("title") or host
    for m in METROS:
        if m[0] in OFFICES:
            links = {OFFICE_PAGE: f"RealPage office in {OFFICES[m[0]]}"}
            links.update(by_metro.get(m[:4], {}))
            by_metro[m[:4]] = links
    dots = []
    for (city, state, lat, lon), links in by_metro.items():
        dots.append({
            "city": city, "state": state, "lat": lat, "lon": lon, "signs": len(links),
            "kind": "reach", "source": "web-search",
            "note": f"{len(links)} public pages tie RealPage to {city}",
            "links": [{"title": t[:90], "url": u} for u, t in list(links.items())[:MAX_LINKS]],
        })
    return sorted(dots, key=lambda d: -d["signs"])


def main():
    fresh = "--fresh" in sys.argv
    with RunLog("build-reach", "us") as log:
        cache, spent = search_all(fresh)
        dots = build(cache)
        existing = json.loads(OUT.read_text()) if OUT.exists() else []
        kept = [d for d in existing if d.get("source") != "web-search"]
        # our proven buildings already cover these cities; don't stack a search dot on them
        ours = {(d["city"], d["state"]) for d in kept}
        dots = [d for d in dots if (d["city"], d["state"]) not in ours]
        OUT.write_text(json.dumps(kept + dots, indent=1) + "\n")
        log.rec["api_calls"] = {"jina_search": spent}
        log.rec["counts"] = {"queries_cached": len(cache), "web_dots": len(dots), "kept_dots": len(kept)}
        log.rec["outputs"] = [str(OUT.relative_to(ROOT))]
        log.rec["notes"].append(f"built {dt.date.today()}")
        print(f"searches spent: {spent}; web dots: {len(dots)}; total dots: {len(kept) + len(dots)}")


if __name__ == "__main__":
    main()
