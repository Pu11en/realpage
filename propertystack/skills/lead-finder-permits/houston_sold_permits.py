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
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable, Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lead-finder"))
from junk_permits import is_junk_permit  # noqa: E402

FetchBytes = Callable[[str], bytes]
FetchText = Callable[[str], str]

XLSX_LINK_RE = re.compile(r'href="([^"]+\.xlsx[^"]*)"', re.I)
UNITS_RE = re.compile(r"(\d+)\s*-?\s*units?\b", re.I)

# Some weeks are linked through a document-viewer page instead of the file
# itself (".../view.aspx?src=<the real url, percent-encoded again>"). Fetching
# the viewer returns HTML, not a spreadsheet, so those weeks were silently
# skipped -- which is how the three most recent weeks went missing.
VIEWER_SRC_PARAMS = ("src", "file", "url")
# The site rate-limits a burst of ~30 downloads; a 429 that is not retried
# silently costs whole weeks of permits.
RETRY_STATUSES = (429, 500, 502, 503, 504)
RETRY_BACKOFF_SECONDS = (2, 6, 15)


def default_fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "propertystack-live-self-test"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def default_fetch_bytes(url: str) -> bytes:
    def once(target: str) -> bytes:
        req = urllib.request.Request(target, headers={"User-Agent": "propertystack-live-self-test"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read()

    return fetch_with_retry(once, url)


def direct_xlsx_url(url: str) -> str:
    """The spreadsheet itself, even when the page links to a viewer wrapper.

    A viewer link carries the real file as a query parameter that is
    percent-encoded a second time, so a space arrives as "%2520". Reading the
    parameter with the standard query parser decodes exactly that one extra
    layer and hands back a correctly encoded direct URL -- never a raw space,
    which is the mistake that kept another county broken for months.
    """
    parts = urllib.parse.urlsplit(url)
    if parts.path.lower().endswith(".xlsx"):
        return url
    query = urllib.parse.parse_qs(parts.query)
    for name in VIEWER_SRC_PARAMS:
        for value in query.get(name, []):
            if urllib.parse.urlsplit(value).path.lower().endswith(".xlsx"):
                return value
    return url


def discover_weekly_urls(search_page_url: str, fetch_text: FetchText = default_fetch_text) -> list[str]:
    """Every .xlsx link posted on the sold-permits search page, absolute-ized
    against the page's own URL (the page links with a mix of relative and
    absolute hrefs) and unwrapped when the link goes through a viewer page."""
    html = fetch_text(search_page_url)
    urls = []
    seen = set()
    for match in XLSX_LINK_RE.finditer(html):
        href = match.group(1).replace("&amp;", "&")
        absolute = direct_xlsx_url(urllib.parse.urljoin(search_page_url, href))
        if absolute not in seen:
            seen.add(absolute)
            urls.append(absolute)
    return urls


def fetch_with_retry(fetch_bytes: FetchBytes, url: str, sleep=time.sleep) -> bytes:
    """Download one weekly file, retrying the statuses that mean "ask again".

    Belongs to the fetcher, not to the download loop: a caller that records
    every exception its fetcher raises must never see one that a retry already
    recovered from, or one slow week would fail the whole source.
    """
    last: Exception | None = None
    for pause in (None, *RETRY_BACKOFF_SECONDS):
        if pause is not None:
            sleep(pause)
        try:
            return fetch_bytes(url)
        except urllib.error.HTTPError as exc:
            last = exc
            if exc.code not in RETRY_STATUSES:
                raise
    raise last  # type: ignore[misc]


def fetch_rows(
    recipe: dict,
    fetch_text: FetchText = default_fetch_text,
    fetch_bytes: FetchBytes = default_fetch_bytes,
    stats: dict | None = None,
) -> list[dict]:
    """Fetch and parse every posted weekly xlsx into plain dict rows keyed
    by the header row's own column names (Zip Code/Permit Date/Permit
    Type/Project No/Address/Comments), filtered to rows whose Comments text
    looks like new apartment construction.

    `stats`, when given, records what the feed really held -- how many weekly
    files were posted, how many were actually read, and the raw row total
    across them. Without it the run reports the number of *files* as though it
    were the endpoint's row count, so a source that quietly lost whole weeks
    still looks healthy.
    """
    import openpyxl  # local import: only needed for this one source

    keyword_re = re.compile(recipe.get("keyword_pattern", r"apart|multi[- ]?family"), re.I)
    new_re = re.compile(recipe.get("new_construction_pattern", r"\bnew\b"), re.I)
    urls = discover_weekly_urls(recipe["search_page_url"], fetch_text)
    rows: list[dict] = []
    raw_rows = 0
    keyword_rows = 0
    files_read = 0
    files_failed: list[str] = []
    for url in urls:
        try:
            data = fetch_bytes(url)
            wb = openpyxl.load_workbook(io.BytesIO(data), data_only=True)
        except Exception as exc:
            files_failed.append(f"{url}: {type(exc).__name__}")
            continue
        files_read += 1
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
                raw_rows += 1
                if keyword_re.search(comments):
                    keyword_rows += 1
                if not (new_re.search(comments) and keyword_re.search(comments)):
                    continue
                if is_junk_permit(comments):  # pool / carport / garage apartment etc.
                    continue
                row["_source_url"] = url
                row["_units"] = _parse_units(comments)
                rows.append(row)
    if stats is not None:
        stats.update(
            {
                "filesPosted": len(urls),
                "filesRead": files_read,
                "filesFailed": files_failed,
                "rawRows": raw_rows,
                "keywordRows": keyword_rows,
            }
        )
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
