"""lead-finder 3.5: other meeting systems + PDF agenda packets.

3.3 (`lead-finder-agendas`) identifies which system a city's planning commission agenda
lives on; 3.4 (`lead-finder-legistar`) handles Legistar's free web API. This covers the
rest (AgendaCenter/CivicPlus, Granicus, PrimeGov, CivicClerk) plus plain PDF/HTML agenda
packets, which don't have a structured API -- the agenda listing page and PDF/HTML
packets themselves have to be fetched and read directly.

No civic-scraper dependency: it isn't installed in this environment, and its scraping
logic is CivicPlus/Granicus/PrimeGov/CivicClerk-listing-page-shaped in the same way this
module's `find_agenda_links()` is, so a small self-contained reader avoids adding a new
dependency for one part. Packets over 25 MB are skipped (never fetched into memory in
full); only the pages within a small window of a keyword hit are extracted with PyMuPDF,
and OCR (an injectable `ocr_fn`, since no OCR engine is bundled with this repo) only runs
on pages PyMuPDF finds no text on at all.

This part only reads matter text near keyword hits and hands it to 3.6, which turns a hit
into a planned-project record (address/case number required, name/developer/units parsed
out). No place names anywhere in this file -- city/state are always caller-supplied.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

MAX_PACKET_BYTES = 25 * 1024 * 1024  # 25 MB
WINDOW_PAGES = 5  # pages kept before/after a keyword hit (~10 pages total)

KEYWORD_RE = re.compile(
    r"multi[- ]?family|apartment|\b\d+\s*units?\b|rezon|site plan", re.I
)

# systems 3.5 is responsible for (3.4 already covers legistar)
SUPPORTED_SYSTEMS = {"agendacenter", "granicus", "primegov", "civicclerk"}

LINK_RE = re.compile(
    r'href=["\']([^"\']+\.(?:pdf|html?))["\']([^>]*)>([^<]*)', re.I
)
AGENDA_WORD_RE = re.compile(r"agenda|packet", re.I)

FetchFn = Callable[[str], "bytes | None"]


@dataclass
class AgendaHit:
    url: str
    page: int
    text: str


def find_agenda_links(html: str, base_url: str) -> list[str]:
    """Pull agenda/packet document links out of a listing page's HTML."""
    links: list[str] = []
    for match in LINK_RE.finditer(html):
        href, _attrs, link_text = match.groups()
        if not (AGENDA_WORD_RE.search(href) or AGENDA_WORD_RE.search(link_text)):
            continue
        links.append(_absolute_url(href, base_url))
    return links


def _absolute_url(href: str, base_url: str) -> str:
    if href.startswith("http://") or href.startswith("https://"):
        return href
    base = base_url.rstrip("/")
    if not href.startswith("/"):
        return f"{base}/{href}"
    scheme_end = base.find("://")
    if scheme_end == -1:
        return base + href
    root_end = base.find("/", scheme_end + 3)
    root = base if root_end == -1 else base[:root_end]
    return root + href


def is_pdf(content: bytes) -> bool:
    return content[:4] == b"%PDF"


def extract_pdf_pages(pdf_bytes: bytes, ocr_fn: "Callable[[bytes], str] | None" = None) -> list[str]:
    """One text string per page. Pages with no extractable text go through ocr_fn if given."""
    import fitz  # PyMuPDF

    pages: list[str] = []
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            text = page.get_text().strip()
            if not text and ocr_fn is not None:
                pix = page.get_pixmap()
                text = ocr_fn(pix.tobytes("png")).strip()
            pages.append(text)
    return pages


def keyword_hit_windows(pages_text: list[str], window: int = WINDOW_PAGES) -> list[tuple[int, str]]:
    """Return (page_index, text) for every page within `window` pages of a keyword hit."""
    hit_pages = [i for i, text in enumerate(pages_text) if text and KEYWORD_RE.search(text)]
    if not hit_pages:
        return []
    keep: set[int] = set()
    for hit in hit_pages:
        for i in range(max(0, hit - window), min(len(pages_text), hit + window + 1)):
            keep.add(i)
    return [(i, pages_text[i]) for i in sorted(keep)]


def find_civic_agenda_items(
    city: str,
    state: str,
    recipe: dict,
    fetch_fn: FetchFn,
    ocr_fn: "Callable[[bytes], str] | None" = None,
) -> list[AgendaHit] | dict:
    """For a 3.3 recipe naming a system this module covers, read its agenda packets.

    Returns a list of AgendaHit (page text near a keyword hit, with the packet URL and
    page number so 3.6 can trace it back), or a skip note dict -- never raises.
    """
    system = recipe.get("system")
    if system not in SUPPORTED_SYSTEMS:
        return {"city": city, "state": state, "skipped": True, "reason": f"system '{system}' not handled here"}

    agenda_url = recipe.get("agenda_url")
    if not agenda_url:
        return {"city": city, "state": state, "skipped": True, "reason": "no agenda url in recipe"}

    listing = fetch_fn(agenda_url)
    if not listing:
        return {"city": city, "state": state, "skipped": True, "reason": "agenda listing page unreachable"}

    listing_html = listing.decode("utf-8", errors="replace") if isinstance(listing, bytes) else listing
    links = find_agenda_links(listing_html, agenda_url)
    if not links:
        return {"city": city, "state": state, "skipped": True, "reason": "no agenda documents found"}

    hits: list[AgendaHit] = []
    for link in links:
        content = fetch_fn(link)
        if not content:
            continue
        if len(content) > MAX_PACKET_BYTES:
            continue  # packets over 25 MB skipped, per the plan
        if not is_pdf(content):
            continue  # a bare .html agenda page has no page structure to window around
        pages = extract_pdf_pages(content, ocr_fn=ocr_fn)
        for page_idx, text in keyword_hit_windows(pages):
            hits.append(AgendaHit(url=link, page=page_idx, text=text))

    return hits


if __name__ == "__main__":
    import argparse
    import json
    import sys
    from pathlib import Path

    ROOT = Path(__file__).resolve().parents[2]

    p = argparse.ArgumentParser()
    p.add_argument("--city", required=True)
    p.add_argument("--state", required=True)
    args = p.parse_args()

    recipe_path = ROOT / "propertystack" / "recipes" / f"agendas-{args.city.lower().replace(' ', '-')}.json"
    recipe = json.loads(recipe_path.read_text())

    def _fetch(url: str) -> "bytes | None":
        import urllib.request

        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return r.read()
        except Exception:
            return None

    result = find_civic_agenda_items(args.city, args.state.upper(), recipe, _fetch)
    if isinstance(result, dict):
        print(json.dumps(result, indent=1))
    else:
        for hit in result:
            print(hit.url, hit.page, hit.text[:80])
