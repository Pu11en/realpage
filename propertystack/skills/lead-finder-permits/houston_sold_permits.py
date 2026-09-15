"""T3: a weekly "Sold Permits" spreadsheet source (see recipes/tx/houston.json
for the real city this was built and live-tested against, kept out of this
file's own text per the lead-finder no-place-names-in-code rule).

Not a Socrata/ArcGIS/CKAN source -- the permitting site posts one xlsx per
week (issued/fee-paid permits), linked straight from its search
page's HTML, with columns Zip Code / Permit Date / Permit Type / Project No
/ Address / Comments and no structured "new construction" or "apartment"
field at all -- everything lives in the free-text Comments column. This
module discovers the posted weekly file URLs, downloads+parses each one,
and returns rows shaped like any other permit recipe's rows so they can
still be filtered/staged the same way find_upcoming does it (new
construction + apartment keyword match on Comments, units only from an
explicit "NN units" pattern in Comments, never estimated). No place names
here -- the search-page URL and keyword list are the only city-specific
inputs, and both are caller-supplied via the recipe.
"""
from __future__ import annotations

import io
import re
import urllib.parse
import urllib.request
from typing import Callable, Iterable

FetchBytes = Callable[[str], bytes]
FetchText = Callable[[str], str]

XLSX_LINK_RE = re.compile(r'href="([^"]+\.xlsx[^"]*)"', re.I)
UNITS_RE = re.compile(r"(\d+)\s*-?\s*units?\b", re.I)


def default_fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "propertystack-live-self-test"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def default_fetch_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "propertystack-live-self-test"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def discover_weekly_urls(search_page_url: str, fetch_text: FetchText = default_fetch_text) -> list[str]:
    """Every .xlsx link posted on the sold-permits search page, absolute-ized
    against the page's own URL (the page links with a mix of relative and
    absolute hrefs)."""
    html = fetch_text(search_page_url)
    urls = []
    seen = set()
    for match in XLSX_LINK_RE.finditer(html):
        href = match.group(1).replace("&amp;", "&")
        absolute = urllib.parse.urljoin(search_page_url, href)
        if absolute not in seen:
            seen.add(absolute)
            urls.append(absolute)
    return urls


def fetch_rows(recipe: dict, fetch_text: FetchText = default_fetch_text, fetch_bytes: FetchBytes = default_fetch_bytes) -> list[dict]:
    """Fetch and parse every posted weekly xlsx into plain dict rows keyed
    by the header row's own column names (Zip Code/Permit Date/Permit
    Type/Project No/Address/Comments), filtered to rows whose Comments text
    looks like new apartment construction."""
    import openpyxl  # local import: only needed for this one source

    keyword_re = re.compile(recipe.get("keyword_pattern", r"apart|multi[- ]?family"), re.I)
    new_re = re.compile(recipe.get("new_construction_pattern", r"\bnew\b"), re.I)
    urls = discover_weekly_urls(recipe["search_page_url"], fetch_text)
    rows: list[dict] = []
    for url in urls:
        try:
            data = fetch_bytes(url)
            wb = openpyxl.load_workbook(io.BytesIO(data), data_only=True)
        except Exception:
            continue
        for ws in wb.worksheets:
            header_row_idx = _find_header_row(ws)
            if header_row_idx is None:
                continue
            headers = [str(c.value or "").strip() for c in ws[header_row_idx]]
            for excel_row in ws.iter_rows(min_row=header_row_idx + 1, values_only=True):
                row = dict(zip(headers, excel_row))
                comments = str(row.get("Comments") or "")
                if not comments:
                    continue
                if not (new_re.search(comments) and keyword_re.search(comments)):
                    continue
                row["_source_url"] = url
                row["_units"] = _parse_units(comments)
                rows.append(row)
    return rows


def _find_header_row(ws) -> int | None:
    for row in ws.iter_rows(min_row=1, max_row=5):
        values = [str(c.value or "").strip() for c in row]
        if "Address" in values and "Comments" in values:
            return row[0].row
    return None


def _parse_units(comments: str) -> int | None:
    match = UNITS_RE.search(comments)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None
