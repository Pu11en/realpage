"""Skill 2 — find-website: the official website for each apartment community.

Source: Jina Search. The CAD name is cleaned (trailing phase/unit-type boilerplate
like "Ph 2", "Ii", "Tc", "Senior" stripped — see clean_name) before querying, since
an exact-phrase query built from the raw CAD name often matches no real page at all.
Tries up to 3 queries per community, widening each time: name+address+city, then
name+city, then an unquoted "official site" query, stopping at the first that finds
an acceptable result. Rejects listing/aggregator domains (apartments.com, zillow,
rent.com, ...) and local news/media domains (an article about a community is not its
own site) — see REJECT_DOMAINS. Manager-company pages (camdenliving.com/...,
udr.com/...) are OK at medium confidence; a domain/title that actually contains the
community's distinctive name is high confidence.
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
    # local news/media domains — an article *about* a community is never its own site
    # (found leaking through at "low" confidence, e.g. a foreclosure-news article
    # outranking the community's real domain — see evals/review-weak-spots.md)
    "dallasnews.com", "communityimpact.com", "candysdirt.com", "bizjournals.com",
    "star-telegram.com", "nbcdfw.com", "cbsnews.com", "fox4news.com", "wfaa.com",
    "keranews.org", "dallasnews.com", "dallasexpress.com", "dallasobserver.com",
    "dmagazine.com", "prnewswire.com", "businesswire.com",
    # CRE deal-marketplace and senior-living locator sites found leaking through at
    # "high"/"low" confidence during the 2026-09-10 re-run (see evals/review-weak-spots.md)
    "traded.co", "livingpath.com",
    # multifamily trade press (an article about a community is not its own site) and
    # another apartment-locator/aggregator, same round
    "yieldpro.com", "rentseeker.com",
    # found by the detect-software skill review 2026-09-10: these were accepted as
    # "official" sites by find-website but are a hotel-booking aggregator, a
    # corporate-housing broker, an unfamiliar third-party listing site, and a
    # management-company rollup page (linked to the real site but isn't it) —
    # see evals/review-weak-spots.md
    "travly.com", "corporatehousing.com", "wheree.com", "billingsleycollection.com",
    # hotel-booking aggregator that also leaks in on "apartments" queries, found on a
    # re-run after the travly.com fix (same whack-a-mole class, see manual-spotcheck
    # "Biggest problem left" note)
    "ostrovok.ru",
]
# rentcafe.com itself is a listing/search domain; individual *.rentcafe.com community
# subdomains (e.g. legacynorth.rentcafe.com) are the community's own leasing page — allow those.
REJECT_EXACT = {"rentcafe.com"}

STOPWORDS = {
    "the", "apartments", "apartment", "homes", "home", "residences", "residence",
    "flats", "lofts", "villas", "village", "at", "of", "on", "in", "by", "condos",
    "condominiums", "place", "community",
}

# CAD records append phase/unit-type boilerplate no real webpage ever quotes verbatim
# ("Ph 2", "Ii", "Tc", a doubled "Apartments"/"Senior") — an exact-phrase query built
# from the raw name returns zero Jina results for these. Strip trailing boilerplate
# tokens before building the query. See evals/review-weak-spots.md.
STRIP_TRAILING = {
    "apartments", "apartment", "apts", "homes", "home", "residences", "residence",
    "senior", "community", "tc", "ph", "phase",
    "i", "ii", "iii", "iv", "v",
}


def clean_name(name):
    """Strip trailing phase/unit-type boilerplate from a raw CAD community name."""
    words = (name or "").split()
    while words and (words[-1].strip(".,").lower() in STRIP_TRAILING or words[-1].strip(".,").isdigit()):
        words.pop()
    return " ".join(words) if words else (name or "")


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
    # a domain with no "." (no TLD) is malformed/truncated — seen from Jina search
    # results returning a cut-off URL (e.g. "jadalegacycentralapa" with no ".com").
    # See evals/review-weak-spots.md, found via the detect-software skill review.
    if "." not in dom:
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
    cname = clean_name(name)
    queries = [
        f'"{cname}" {address} {city} TX apartments',
        f'"{cname}" {city} TX apartments',
        f'{cname} {city} TX apartments official site',
    ]
    tier, best, query_used = "none", None, queries[0]
    for q in queries:
        results = jina.search(q)
        tier, best = pick_best(cname, results)
        query_used = q
        if tier != "none":
            break
    if tier == "none" or best is None:
        return {"apt_id": row["apt_id"], "website": "", "website_source": "search",
                "confidence": "none", "query": query_used, "notes": "no acceptable result"}
    return {"apt_id": row["apt_id"], "website": best["url"], "website_source": "search",
            "confidence": tier, "query": query_used, "notes": best.get("title", "")[:120]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--area", required=True)
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--in-file", default="1-apartments.csv",
                     help="input filename within the area dir (default: 1-apartments.csv)")
    ap.add_argument("--out-file", default="2-websites.csv",
                     help="output filename within the area dir (default: 2-websites.csv)")
    a = ap.parse_args()
    with RunLog("find-website", a.area) as log:
        in_f = area_dir(a.area) / a.in_file
        rows = list(csv.DictReader(open(in_f, encoding="utf-8-sig")))
        log.rec["inputs"] = [str(in_f.relative_to(in_f.parents[2]))]
        jina = Jina()
        with cf.ThreadPoolExecutor(a.workers) as ex:
            out = list(ex.map(lambda r: process(r, jina), rows))
        out_f = area_dir(a.area) / a.out_file
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
