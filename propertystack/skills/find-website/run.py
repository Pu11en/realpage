"""Skill 2 — find-website: the official website for each apartment community.

Source: Jina Search. Query is the community name + address + city, falling back to
name + city if the first query finds nothing acceptable. Rejects listing/aggregator
domains (apartments.com, zillow, rent.com, ...) — those are not the community's own
site. Manager-company pages (camdenliving.com/..., udr.com/...) are OK at medium
confidence; a domain/title that actually contains the community's distinctive name
is high confidence.
Usage: python3 skills/find-website/run.py --area plano-richardson
"""
import argparse, collections, csv, datetime as dt, re, sys, pathlib
import concurrent.futures as cf
from urllib.parse import urlparse
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from lib.paths import area_dir
from lib.runlog import RunLog
from lib.jina import Jina

COLS = ["apt_id", "website", "website_source", "confidence", "query", "notes"]

REJECT_DOMAINS = [
    "apartments.com", "zillow.com", "rent.com", "apartmentlist.com", "trulia.com",
    "redfin.com", "realtor.com", "hotpads.com", "forrent.com", "apartmentguide.com",
    "apartmentfinder.com", "craigslist.org", "yelp.com", "facebook.com", "instagram.com",
    "linkedin.com", "loopnet.com", "costar.com", "padmapper.com", "zumper.com",
    "rentable.co", "apartmentratings.com", "bbb.org", "mapquest.com", "yellowpages.com",
    "niche.com", "google.com",
    # aggregators / apartment-locator services found leaking through as false "official" sites
    "homes.com", "har.com", "apartmenthomeliving.com", "umovefree.com",
    "tiktok.com", "reddit.com", "pinterest.com", "youtube.com", "twitter.com",
    "x.com", "nextdoor.com", "wikipedia.org",
    "aptamigo.com", "safebutler.com", "waze.com", "oasissenioradvisors.com",
    "rentersvoice.com", "forrentuniversity.com", "sulekha.com", "maps.apple.com",
    "apple.com", "bing.com", "maps.google.com",
    "cortera.com", "chamberofcommerce.com", "manta.com", "buzzfile.com", "dnb.com",
    "opencorporates.com", "usnews.com", "caring.com", "seniorliving.org", "aplaceformom.com",
    # generic apartment-locator keyword: catches averagejoeslocating.com and similar
    "locating", "locator",
]
# rentcafe.com itself is a listing/search domain; individual *.rentcafe.com community
# subdomains (e.g. legacynorth.rentcafe.com) are the community's own leasing page — allow those.
REJECT_EXACT = {"rentcafe.com"}

STOPWORDS = {
    "the", "apartments", "apartment", "homes", "home", "residences", "residence",
    "flats", "lofts", "villas", "village", "at", "of", "on", "in", "by", "condos",
    "condominiums", "place", "community",
}


def distinctive_words(name):
    words = re.findall(r"[a-z0-9]+", (name or "").lower())
    out = [w for w in words if w not in STOPWORDS and len(w) >= 3]
    return out or words


def name_hits(words, text):
    if not words or not text:
        return 0
    text = text.lower()
    return sum(1 for w in words if w in text)


def domain_of(url):
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def is_rejected(url):
    dom = domain_of(url)
    if not dom:
        return True
    if dom in REJECT_EXACT:
        return True
    return any(rd in dom for rd in REJECT_DOMAINS)


def classify(name, result):
    """Return confidence tier ('high'|'medium'|'low') for one accepted search result, or None to reject."""
    url, title, desc = result.get("url", ""), result.get("title", ""), result.get("description", "")
    if not url.startswith("http") or is_rejected(url):
        return None
    words = distinctive_words(name)
    need = max(1, len(words) - 1)  # allow one miss on longer names
    dom_hit = name_hits(words, domain_of(url)) >= 1
    title_hit = name_hits(words, title) >= need
    url_hit = name_hits(words, url) >= 1
    if dom_hit or title_hit:
        return "high"
    if url_hit:
        return "medium"
    return "low"


def pick_best(name, results):
    tiers = {"high": None, "medium": None, "low": None}
    for r in results:
        tier = classify(name, r)
        if tier and tiers[tier] is None:
            tiers[tier] = r
    for tier in ("high", "medium", "low"):
        if tiers[tier]:
            return tier, tiers[tier]
    return "none", None


def process(row, jina):
    name, address, city = row["name"], row["address"], row["city"]
    q1 = f'"{name}" {address} {city} TX apartments'
    results = jina.search(q1)
    tier, best = pick_best(name, results)
    query_used = q1
    if tier == "none":
        q2 = f'"{name}" {city} TX apartments'
        results2 = jina.search(q2)
        tier, best = pick_best(name, results2)
        query_used = q2
    if tier == "none" or best is None:
        return {"apt_id": row["apt_id"], "website": "", "website_source": "search",
                "confidence": "none", "query": query_used, "notes": "no acceptable result"}
    return {"apt_id": row["apt_id"], "website": best["url"], "website_source": "search",
            "confidence": tier, "query": query_used, "notes": best.get("title", "")[:120]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--area", required=True)
    ap.add_argument("--workers", type=int, default=5)
    a = ap.parse_args()
    with RunLog("find-website", a.area) as log:
        in_f = area_dir(a.area) / "1-apartments.csv"
        rows = list(csv.DictReader(open(in_f, encoding="utf-8-sig")))
        log.rec["inputs"] = [str(in_f.relative_to(in_f.parents[2]))]
        jina = Jina()
        with cf.ThreadPoolExecutor(a.workers) as ex:
            out = list(ex.map(lambda r: process(r, jina), rows))
        out_f = area_dir(a.area) / "2-websites.csv"
        with open(out_f, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=COLS)
            w.writeheader()
            w.writerows(out)
        log.rec["outputs"] = [str(out_f.relative_to(out_f.parents[2]))]
        counts = collections.Counter(r["confidence"] for r in out)
        log.rec["counts"] = {"total": len(out), **{k: counts.get(k, 0) for k in ("high", "medium", "low", "none")}}
        log.rec["api_calls"] = dict(jina.calls)
        print(log.rec["counts"], log.rec["api_calls"])


if __name__ == "__main__":
    main()
