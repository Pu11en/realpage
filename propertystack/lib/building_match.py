""""Is this really about this building?" check, shared by every skill that
picks a website or reads a page for one building/project.

A result only counts as being about a building if its distinctive name words
(all of them, not just one -- a single shared word like "Marquee" is not
enough, see the Tucson/St. Louis/sports-network mixups below) or its street
address actually appear in the URL, title or page text. Listing/aggregator
sites are never the official website, even if they mention the building by
name.
"""
from __future__ import annotations

import re
from urllib.parse import urlparse

STOPWORDS = {
    "the", "apartments", "apartment", "homes", "home", "residences", "residence",
    "flats", "lofts", "villas", "village", "at", "of", "on", "in", "by", "condos",
    "condominiums", "place", "community",
}

# Listing/aggregator sites are never a building's own website, no matter how
# well the name matches (found leaking through as "official" sites).
LISTING_DOMAINS = [
    "apartments.com", "zillow.com", "rent.com", "apartmentlist.com", "trulia.com",
    "redfin.com", "realtor.com", "hotpads.com", "forrent.com", "apartmentguide.com",
    "apartmentfinder.com", "craigslist.org", "yelp.com", "facebook.com", "instagram.com",
    "linkedin.com", "loopnet.com", "costar.com", "padmapper.com", "zumper.com",
    "rentable.co", "apartmentratings.com", "bbb.org", "mapquest.com", "yellowpages.com",
    "niche.com", "google.com", "homes.com", "har.com", "apartmenthomeliving.com",
    "umovefree.com", "tiktok.com", "reddit.com", "pinterest.com", "youtube.com",
    "twitter.com", "x.com", "nextdoor.com", "wikipedia.org", "aptamigo.com",
    "safebutler.com", "waze.com", "oasissenioradvisors.com", "rentersvoice.com",
    "forrentuniversity.com", "sulekha.com", "maps.apple.com", "apple.com", "bing.com",
    "maps.google.com", "cortera.com", "chamberofcommerce.com", "manta.com",
    "buzzfile.com", "dnb.com", "opencorporates.com", "usnews.com", "caring.com",
    "seniorliving.org", "aplaceformom.com", "locating", "locator",
    "movoto.com", "cityfeet.com", "gridics.com", "erasmusplay.com", "amberstudent.com",
]
# rentcafe.com the search/listing hub is a reject; a *.rentcafe.com community
# subdomain (e.g. legacynorth.rentcafe.com) is the community's own leasing
# page -- and separately, evidence the community runs Yardi.
LISTING_EXACT = {"rentcafe.com"}


def distinctive_words(name: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", (name or "").lower())
    out = [w for w in words if w not in STOPWORDS and len(w) >= 3]
    return out or words


def domain_of(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def is_listing_domain(url: str) -> bool:
    dom = domain_of(url)
    if not dom:
        return True
    if "." not in dom:
        return True
    if dom in LISTING_EXACT:
        return True
    return any(ld in dom for ld in LISTING_DOMAINS)


def street_hit(address: str, text: str) -> bool:
    """A street address counts as a hit if its house number and its street
    name (first word after the number, e.g. "5th" in "500 5th Ave") both
    appear in the text."""
    if not address or not text:
        return False
    text = text.lower()
    m = re.match(r"\s*(\d+)\s+([a-z0-9]+)", address.lower())
    if not m:
        return False
    number, street_word = m.group(1), m.group(2)
    return number in text and street_word in text


def matches_building(name: str, address: str, *texts: str) -> bool:
    """True if the combined url/title/page text is really about this
    building: either every distinctive word of its name appears somewhere in
    the combined text, or its street address does. A single matching word
    ("Marquee" also being a sports network's name) is never enough on its
    own."""
    combined = " ".join(t.lower() for t in texts if t)
    if not combined:
        return False
    words = distinctive_words(name)
    name_hit = bool(words) and all(w in combined for w in words)
    return name_hit or street_hit(address, combined)


def is_about_building(name: str, address: str, url: str, *texts: str) -> bool:
    """The full check used before accepting a page as a building's own site
    or as a source of facts about it: reject listing domains outright, then
    require matches_building on url + any extra text (title, page body)."""
    if url and is_listing_domain(url):
        return False
    return matches_building(name, address, url, *texts)
