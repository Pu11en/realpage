"""Client map: where RealPage already has apartment clients (proven by resident-portal links).

Search budget, URL -> vendor (tooling/pms_detect.py rules), duplicate removal, per-state/per-city
counts (C1); targets from targets.py (C2); the search run (C3): one Jina search per target city ->
RealPage portal links in the hits -> name + address (from the hit, else the portal page via local
crawl4ai) -> lat/lon (Census batch geocoder, OpenStreetMap backup) -> buildings.csv + counts.json.
Usage: python3 propertystack/skills/client-map/run.py   (JINA_API_KEY in env or a .env)
"""
import collections, csv, datetime, json, pathlib, re, sys, time
from urllib.parse import urlparse, parse_qs

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]                       # repo root
sys.path.insert(0, str(ROOT / "tooling"))
import pms_detect  # noqa: E402

MAX_SEARCHES = 150   # hard cap for the whole run
# Hosts that prove a building is a RealPage client (residentportal.com is Entrata).
REALPAGE_PROOF = re.compile(r"(^|\.)(loftliving\.com|activebuilding\.com)$|^onesite\.realpage\.com$", re.I)


class CapReached(Exception):
    pass


class SearchBudget:
    """Counts searches; raises CapReached instead of going over the cap."""
    def __init__(self, cap=MAX_SEARCHES):
        self.cap, self.used = min(cap, MAX_SEARCHES), 0

    @property
    def left(self):
        return self.cap - self.used

    def use(self, n=1):
        if self.used + n > self.cap:
            raise CapReached(f"search cap {self.cap} reached")
        self.used += n


def query_for(city, state):
    return f'"loftliving.com" OR "activebuilding.com" OR "onesite.realpage.com" apartments {city} {state}'


def search_targets(targets, search, budget):
    """One search per target city in order; stops cleanly at the cap. Returns (hits, used)."""
    hits = []
    for t in targets:
        try:
            budget.use()
        except CapReached:
            break
        for h in search(query_for(t["city"], t["state"])) or []:
            hits.append({**h, "city": t["city"], "state": t["state"]})
    return hits, budget.used


def vendor_of(url):
    """Vendor name for a URL using pms_detect.py fingerprints ('' if none)."""
    for vendor, pat in pms_detect.VENDORS:
        if re.search(pat, url, re.I):
            return vendor
    return ""


def is_realpage_proof(url):
    host = (urlparse(url).hostname or "").lower()
    return bool(REALPAGE_PROOF.search(host)) and vendor_of(url) == "RealPage"


def _addr_key(a):
    return re.sub(r"[^a-z0-9]+", " ", (a or "").lower()).strip()


# RealPage hosts shared by many buildings: the building is the siteId in the query string.
SHARED_HOSTS = {"loftliving.com", "www.loftliving.com", "oll-leasing.loftliving.com",
                "onesite.realpage.com", "property.onesite.realpage.com", "activebuilding.com",
                "www.activebuilding.com"}


def portal_key(url):
    """One key per building portal: its own subdomain, or shared host + siteId ('' = no building)."""
    p = urlparse(url)
    host = (p.hostname or "").lower()
    if host not in SHARED_HOSTS:
        return host
    site = {k.lower(): v for k, v in parse_qs(p.query).items()}.get("siteid")
    return f"{host}?siteId={site[0]}" if site else ""


def dedupe(rows):
    """Same portal subdomain or same address = one building; first one wins."""
    seen_host, seen_addr, out = set(), set(), []
    for r in rows:
        host = portal_key(r.get("proof_url", ""))
        addr = _addr_key(r.get("address"))
        if (host and host in seen_host) or (addr and addr in seen_addr):
            continue
        seen_host.add(host)
        if addr:
            seen_addr.add(addr)
        out.append(r)
    return out


def counts(rows):
    """{state: {"total": n, "cities": {city: n}}}, states and cities most buildings first."""
    by_state = collections.defaultdict(collections.Counter)
    for r in rows:
        by_state[r["state"]][r["city"]] += 1
    order = sorted(by_state, key=lambda s: -sum(by_state[s].values()))
    return {s: {"total": sum(by_state[s].values()), "cities": dict(by_state[s].most_common())} for s in order}


# ---------- C3: hits -> buildings ----------
URL_RE = re.compile(r"https?://[^\s)\"'<>|\]]+")
ADDR_RE = re.compile(r"(\d{2,6} [A-Za-z0-9 .'#-]{3,60}?),\s*([A-Za-z .'-]{2,40}?),\s*([A-Z]{2}),?\s+(\d{5})")
GENERIC_TITLE = re.compile(r"online leasing|not found|lease term|login|sign in|^https?://", re.I)


def proof_urls(hit):
    """RealPage portal URLs that name one building: the hit itself and any URL in its snippet."""
    urls = [hit.get("url", "")] + URL_RE.findall(hit.get("description", ""))
    return [u.rstrip(".,") for u in urls if is_realpage_proof(u) and portal_key(u)]


def parse_address(text):
    """First 'street, City, ST 12345' in text -> (prefix, street, city, state, zip) or None."""
    m = ADDR_RE.search(text or "")
    if not m:
        return None
    return (text[:m.start()],) + tuple(x.strip() for x in m.groups())


def pick_name(title, prefix):
    lead = re.split(r"[.|\n]\s+|\|", prefix.strip().rstrip("|. "))[-1].strip() if prefix.strip() else ""
    if 2 < len(lead) <= 60 and not GENERIC_TITLE.search(lead):
        return lead
    t = re.split(r"\s+[-|\u2013]\s+|\s*\|\s*", title or "")[0].strip()
    return "" if GENERIC_TITLE.search(t) else t


def building_from_hit(hit, fetch=None):
    """Hit -> {name, street, city, state, zip, proof_url} or None (no RealPage proof / no address)."""
    urls = proof_urls(hit)
    if not urls:
        return None
    proof = urls[0]
    own = proof == hit.get("url")               # snippet describes the portal page itself
    addr = parse_address(hit.get("description", "")) if own else None
    title = hit.get("title", "") if own else ""
    if not addr and fetch:
        try:
            title, text = fetch(proof)
        except Exception:
            return None
        addr = parse_address(text)
        if addr:
            addr = ("",) + addr[1:]
    if not addr:
        return None
    prefix, street, city, state, zip_ = addr
    city = city.title() if city.isupper() or city.islower() else city   # TACOMA -> Tacoma
    name = pick_name(title, prefix) or street
    return {"name": name, "street": street, "city": city, "state": state, "zip": zip_,
            "address": f"{street}, {city}, {state} {zip_}", "proof_url": proof}


def crawl4ai_fetch(url, endpoint="http://localhost:11235/crawl"):
    """Portal page (JS app) -> (title, markdown) via the local crawl4ai server, 3 s render wait."""
    import httpx
    r = httpx.post(endpoint, timeout=90, json={"urls": [url], "crawler_config": {
        "type": "CrawlerRunConfig", "params": {"delay_before_return_html": 3}}})
    res = (r.json().get("results") or [{}])[0]
    if not res.get("success"):
        raise RuntimeError(res.get("error_message") or "crawl failed")
    md = res.get("markdown") or ""
    md = md.get("raw_markdown", "") if isinstance(md, dict) else md
    return (res.get("metadata") or {}).get("title", ""), md


def cached_search(search, cache_path):
    """Wrap search with a JSON cache (a rerun never pays twice for the same query)."""
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}

    def run_search(q):
        if q not in cache:
            cache[q] = search(q)
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps(cache, indent=1))
        return cache[q]
    return run_search


def osm_geocode(address):
    import httpx
    time.sleep(1.1)                            # Nominatim: 1 request per second
    r = httpx.get("https://nominatim.openstreetmap.org/search", timeout=30,
                  params={"q": address, "format": "json", "limit": 1, "countrycodes": "us"},
                  headers={"User-Agent": "propertystack-client-map/1.0 (local research)"})
    d = r.json()
    return (float(d[0]["lat"]), float(d[0]["lon"])) if d else None


def geocode_all(rows, cache_path):
    """Adds lat/lon to rows: Census batch geocoder first, OpenStreetMap for the misses. Cached."""
    sys.path.insert(0, str(ROOT / "tooling" / "reach"))
    from build_buildings import geocode as census_batch
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    todo = {r["address"]: (r["street"], r["city"], r["state"], r["zip"]) for r in rows if r["address"] not in cache}
    if todo:
        keyed = {str(i): v for i, v in enumerate(todo.values())}
        found = census_batch(keyed)
        for i, addr in enumerate(todo):
            ll = found.get(str(i))
            if not ll:
                try:
                    ll = osm_geocode(addr)
                except Exception:
                    ll = None
            cache[addr] = list(ll) if ll else None
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(cache, indent=1))
    for r in rows:
        ll = cache.get(r["address"]) or (None, None)
        r["lat"], r["lon"] = ll
    return rows


def flat_targets(targets_json):
    return [{"city": c["city"], "state": s["state"]} for s in targets_json["states"] for c in s["cities"]]


def main():
    from propertystack.lib.jina import Jina
    data = ROOT / "propertystack" / "data"
    out, raw = data / "client-map", data / "raw" / "client-map"
    targets = flat_targets(json.loads((out / "targets.json").read_text()))
    jina = Jina()
    hits, used = search_targets(targets, cached_search(jina.search, raw / "searches.json"), SearchBudget())
    print(f"{used} searches ({jina.calls['search']} paid this run), {len(hits)} hits", flush=True)

    found, fetched = [], {}
    def fetch(url):
        if url not in fetched:
            fetched[url] = crawl4ai_fetch(url)
        return fetched[url]
    for h in hits:
        b = building_from_hit(h, fetch)
        if b:
            found.append(b)
    rows = geocode_all(dedupe(found), raw / "geocode.json")
    fields = ["name", "city", "state", "lat", "lon", "proof_url"]
    with open(out / "buildings.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    c = counts(rows)
    (out / "counts.json").write_text(json.dumps(c, indent=1))
    log = ROOT / "propertystack" / "runs" / f"{datetime.datetime.now():%Y%m%dT%H%M%S}-client-map.json"
    log.write_text(json.dumps({"skill": "client-map", "searches_used": used, "searches_cap": MAX_SEARCHES,
                               "searches_paid_this_run": jina.calls["search"], "hits": len(hits),
                               "portal_pages_crawled": len(fetched), "buildings_before_dedupe": len(found),
                               "buildings": len(rows), "not_geocoded": sum(r["lat"] is None for r in rows),
                               "states": {s: v["total"] for s, v in c.items()}}, indent=1))
    print(f"{len(rows)} buildings in {len(c)} states; log {log.name}")


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    main()
