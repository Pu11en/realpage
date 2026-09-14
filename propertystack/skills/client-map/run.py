"""Client map: where RealPage already has apartment clients (proven by resident-portal links).

C1 skeleton: search budget, URL -> vendor (tooling/pms_detect.py rules), duplicate removal and
per-state/per-city counts. The search run itself (C3) and targets (C2) come later.
"""
import collections, pathlib, re, sys
from urllib.parse import urlparse

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


def dedupe(rows):
    """Same portal subdomain or same address = one building; first one wins."""
    seen_host, seen_addr, out = set(), set(), []
    for r in rows:
        host = (urlparse(r.get("proof_url", "")).hostname or "").lower()
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


if __name__ == "__main__":
    sys.exit("client-map: search run not built yet (task C3)")
