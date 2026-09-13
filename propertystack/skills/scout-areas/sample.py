"""Scout S3: RealPage share in a sample of ~25 apartment community websites per metro.

Search (Jina, counted against the run's SearchBudget) -> keep community sites, skip listing
portals and big management-company sites -> fetch each with local crawl4ai (free) -> classify
the vendor with tooling/pms_detect.py rules (same one-hop follow of resident/pay links).
Writes propertystack/data/scout/<date>/<slug>/sample.csv with the proof URL per site.
"""
import csv, collections, concurrent.futures as cf, datetime, pathlib, sys
from urllib.parse import urlparse

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]                       # repo root
sys.path.insert(0, str(ROOT / "tooling"))
sys.path.insert(0, str(ROOT))
import pms_detect  # noqa: E402

CRAWL4AI = "http://localhost:11235/crawl"
TARGET = 25            # community sites per metro
MAX_QUERIES = 8        # searches per metro at most
QUERIES = [
    "apartments {city} {st} official website",
    "apartment homes for rent {city} {st}",
    "luxury apartments {city} {st} resident portal",
    "new apartment community {city} {st} now leasing",
    "apartments near downtown {city} {st}",
    "pet friendly apartments {city} {st} floor plans",
    "townhome apartments {city} {st} schedule a tour",
    "apartment community {city} {state_name}",
]
# Listing portals, directories and big operator/brand sites: not one community's own site.
SKIP_DOMAINS = (
    "apartments.com", "zillow.com", "rent.com", "apartmentlist.com", "trulia.com", "redfin.com",
    "realtor.com", "yelp.com", "facebook.com", "instagram.com", "forrent.com", "apartmentguide.com",
    "hotpads.com", "craigslist.org", "rentcafe.com", "zumper.com", "apartmentratings.com",
    "apartmenthomeliving.com", "rentable.co", "padmapper.com", "rentals.com", "move.com",
    "homes.com", "bbb.org", "tripadvisor.com", "reddit.com", "youtube.com", "linkedin.com",
    "wikipedia.org", "niche.com", "mapquest.com", "google.com", "bing.com", "yahoo.com",
    "greystar.com", "maac.com", "camdenliving.com", "avaloncommunities.com", "equityapartments.com",
    "udr.com", "cortland.com", "lincolnapts.com", "mysticdunes.com", "uhaul.com", "rentberry.com",
    "offcampuspartners.com", "livelovely.com", "rentprogress.com", "invitationhomes.com",
    "apartmentfinder.com", "coldwellbankerhomes.com", "yugo.com", "americancampus.com",
)
# Bare vendor homepages (residentportal.com itself) are not a community; subdomains are kept.
VENDOR_ROOTS = ("residentportal.com", "securecafe.com", "securecafenet.com", "entrata.com",
                "realpage.com", "yardi.com", "appfolio.com", "loftliving.com", "prospectportal.com")
# Vendor-hosted listing domains (securecafe etc.) are fine: they ARE the proof.


def community_url(url):
    """Homepage URL if this looks like one community's own site, else None."""
    try:
        p = urlparse(url)
    except ValueError:
        return None
    host = p.netloc.lower().removeprefix("www.")
    if p.scheme not in ("http", "https") or not host:
        return None
    if any(host == d or host.endswith("." + d) for d in SKIP_DOMAINS):
        return None
    if host in VENDOR_ROOTS or host.endswith((".gov", ".edu", ".org")):
        return None
    return f"{p.scheme}://{p.netloc}/"


def find_sites(metro, budget, search, target=TARGET):
    """Run searches (each counted) until `target` unique community homepages are found."""
    city = metro["name"].split(",")[0].split("-")[0].strip()
    subs = {"city": city, "st": metro["state"], "state_name": metro["state"]}
    sites = {}
    for q in QUERIES[:MAX_QUERIES]:
        if len(sites) >= target:
            break
        budget.use()                          # raises CapReached before going over
        for r in search(q.format(**subs)):
            home = community_url(r.get("url", ""))
            if home and home not in sites:
                sites[home] = r.get("title", "")
    return [{"url": u, "title": t} for u, t in list(sites.items())[:target]]


class Crawl4aiReader:
    """pms_detect Reader interface on the local crawl4ai server: page links + raw HTML as text."""
    def __init__(self, endpoint=CRAWL4AI, post=None):
        import httpx
        self.endpoint, self.post = endpoint, post or httpx.post

    def get(self, url):
        r = self.post(self.endpoint, json={"urls": [url]}, timeout=90)
        res = (r.json().get("results") or [{}])[0]
        if not res.get("success"):
            raise RuntimeError(res.get("error_message") or "crawl failed")
        links = res.get("links") or {}
        hrefs = [x.get("href", "") for k in ("internal", "external") for x in links.get(k, [])]
        return "\n".join(hrefs) + "\n" + (res.get("html") or "")


def classify_sites(sites, reader, workers=5):
    with cf.ThreadPoolExecutor(workers) as ex:
        return list(ex.map(lambda s: pms_detect.detect(s, reader), sites))


def summarize(rows):
    """{'total': n, 'RealPage': k, ...}; a site showing two vendors counts for each."""
    c = collections.Counter()
    for r in rows:
        for v in (r.get("vendor") or "unknown").split("+"):
            c[v] += 1
    return {"total": len(rows), **c}


def write_sample(rows, slug, out_dir):
    (out_dir / slug).mkdir(parents=True, exist_ok=True)
    path = out_dir / slug / "sample.csv"
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["url", "title", "vendor", "signal", "evidence"], extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return path


def out_dir(date=None):
    date = date or datetime.date.today().isoformat()
    return ROOT / "propertystack" / "data" / "scout" / date


def sample_metro(metro, budget, search, reader, dest=None):
    """Full S3 step for one metro -> (summary dict, proof URLs, csv path)."""
    rows = classify_sites(find_sites(metro, budget, search), reader)
    path = write_sample(rows, metro["slug"], dest or out_dir())
    proof = [r["evidence"] for r in rows if r.get("vendor") in ("RealPage", "Yardi", "Entrata") and r.get("evidence")]
    return summarize(rows), proof, path


def jina_search():
    from propertystack.lib.jina import Jina
    j = Jina()
    return j.search
