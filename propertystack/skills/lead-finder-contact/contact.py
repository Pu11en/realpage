"""Part 4.4 -- who to call, any area.

`find_website`: for a developer/owner name, one search for their site.
`find_office_phone`: pulls phone numbers out of page HTML with `phonenumbers`,
preferring an office/leasing line over a fax or cell line (never returning a
number found next to "fax").
`find_named_contact`: a person's name only when a permit, agenda or news page
actually names one (never guessed from a developer's generic "About Us" page).
`find_owner_by_parcel` / `find_developer_by_news` / `find_developer_for_new_permit`
(F10b): a brand-new permit's contractor fields are empty at issue time, so the
developer/owner for a not-yet-built project comes from (1) the county's free
parcel file (owner name by address), then (2) a news/press-release search for
the project's own name, corroborating a generic-sounding parcel owner name
("XYZ Owner LLC") against news before trusting it alone -- never guessed.
`fill_contacts`: the batch entry point over `LeadRecord`s.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import phonenumbers

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))
from building_match import is_about_building  # noqa: E402

PHONE_CONTEXT_WINDOW = 15
FAX_KEYWORDS = ("fax",)
CELL_KEYWORDS = ("cell", "mobile")

# Only matched against permit/agenda/news pages (never a generic developer
# website) -- see fill_contacts.
PERSON_PATTERNS = [
    re.compile(
        r"(?i:contact|property manager|leasing manager|project manager|"
        r"developer contact)[:\s]+([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)",
    ),
]


def _page_html(result) -> str:
    if result is None:
        return ""
    if hasattr(result, "ok"):
        return result.html if result.ok else ""
    if isinstance(result, dict):
        return result.get("html", "") if result.get("ok", True) else ""
    return str(result)


def _result_url(item) -> str:
    if isinstance(item, dict):
        return item.get("url", "")
    return getattr(item, "url", "")


def _result_title(item) -> str:
    if isinstance(item, dict):
        return item.get("title", "")
    return getattr(item, "title", "")


def find_website(developer: str, search_fn) -> str:
    """One search for a developer/owner's own website. A result only counts
    if it's really about this developer (F2 check: not a listing/directory
    site, and the developer's name actually appears in its url/title) --
    never guesses a URL from the first hit alone."""
    if not developer:
        return ""
    results = search_fn(f"{developer} apartments website") or []
    for item in results:
        url = _result_url(item)
        if url and is_about_building(developer, "", url, _result_title(item)):
            return url
    return ""


def find_office_phone(html: str) -> str:
    """The best phone number on the page: an office/unlabeled number is
    always preferred over a fax or cell/mobile line; a cell number is
    returned only if nothing else is found. Duplicate numbers (the same
    number printed more than once) count once."""
    if not html:
        return ""
    seen = set()
    fallback = ""
    for match in phonenumbers.PhoneNumberMatcher(html, "US"):
        context = html[max(0, match.start - PHONE_CONTEXT_WINDOW) : match.start].lower()
        if any(k in context for k in FAX_KEYWORDS):
            continue
        formatted = phonenumbers.format_number(
            match.number, phonenumbers.PhoneNumberFormat.NATIONAL
        )
        if formatted in seen:
            continue
        seen.add(formatted)
        if any(k in context for k in CELL_KEYWORDS):
            if not fallback:
                fallback = formatted
            continue
        return formatted
    return fallback


def find_named_contact(text: str) -> str:
    """A person's name, only if the given page text actually names one."""
    for pattern in PERSON_PATTERNS:
        m = pattern.search(text or "")
        if m:
            return m.group(1)
    return ""


def _normalize_address(address: str) -> str:
    return re.sub(r"[^A-Z0-9 ]", "", (address or "").upper()).split(",")[0].strip()
    # (split on "," handles "965 E University Dr, Tempe, AZ" vs the permit's
    # bare street address -- both normalize to the same street text)


def find_owner_by_parcel(address: str, parcel_recipe: dict | None, fetch_rows) -> str:
    """A not-yet-sold parcel's current owner name, from the county's free
    parcel file (see propertystack/recipes/az/maricopa-county-sales.json's
    `parcel_source`/`parcel_fields`), matched to the permit's street address --
    real data only, never a guess. `fetch_rows` is injected (offline in
    tests; `find_sold.default_fetch_rows` for a live run)."""
    if not address or not parcel_recipe:
        return ""
    parcel_source = parcel_recipe.get("parcel_source")
    parcel_fields = parcel_recipe.get("parcel_fields", {})
    address_key = parcel_fields.get("address")
    owner_key = parcel_fields.get("owner")
    if not parcel_source or not address_key or not owner_key:
        return ""
    try:
        rows = fetch_rows(parcel_source) or []
    except Exception:
        return ""
    target = _normalize_address(address)
    if not target:
        return ""
    for row in rows:
        if _normalize_address(str(row.get(address_key, ""))) == target:
            owner = str(row.get(owner_key, "")).strip()
            if owner:
                return owner
    return ""


# words that show up in a placeholder ownership-entity name rather than a real
# developer/company name (e.g. "REVELRY TEMPE OWNER LLC") -- these need news
# corroboration before being trusted as "who to call".
_GENERIC_OWNER_MARKERS = ("owner", "holdings", "holdco", "investments", "ventures", "capital", "series")


def _is_generic_owner_name(name: str) -> bool:
    lowered = name.lower()
    return any(marker in lowered for marker in _GENERIC_OWNER_MARKERS)


def _result_snippet(item) -> str:
    if isinstance(item, dict):
        return item.get("snippet", "")
    return getattr(item, "snippet", "")


# a real developer/builder company name mentioned in a news headline or
# snippet, e.g. "...developed by Mark-Taylor Residential" or "ZOM Living
# broke ground on...". Only ever read from search results the F2 check has
# already confirmed are about this project -- never guessed.
_DEVELOPER_NAME_RE = re.compile(
    r"(?:developed by|developer[:\s]+|built by)\s+([A-Z][\w&.'-]+(?:\s(?:[A-Z][\w&.'-]+|and|of|the)){0,4})"
    r"|([A-Z][\w&.'-]+(?:\s[A-Z][\w&.'-]+){0,3}\s"
    r"(?:Development|Communities|Properties|Partners|Group|Companies|Residential|Homes|Builders))\b"
)


def find_developer_by_news(project_name: str, city: str, search_fn) -> str:
    """A news/press-release search for the project's own name (F10b step 2),
    kept only if the F2 "is this really about this building?" check passes
    and a real company name is actually printed on the page."""
    if not project_name:
        return ""
    results = search_fn(f"{project_name} {city} apartments developer") or []
    for item in results:
        url = _result_url(item)
        title = _result_title(item)
        if not is_about_building(project_name, "", url, title):
            continue
        for text in (title, _result_snippet(item)):
            match = _DEVELOPER_NAME_RE.search(text or "")
            if match:
                return (match.group(1) or match.group(2)).strip()
    return ""


def _owner_confirmed_by_news(owner: str, project_name: str, city: str, search_fn) -> bool:
    if not owner or not project_name:
        return False
    results = search_fn(f"{project_name} {city} apartments developer") or []
    owner_lower = owner.lower()
    for item in results:
        text = f"{_result_title(item)} {_result_snippet(item)}".lower()
        if owner_lower in text:
            return True
    return False


def find_developer_for_new_permit(
    record, parcel_recipe: dict | None, fetch_rows, search_fn
) -> tuple[str, dict | None]:
    """F10b: brand-new permit, no contractor field filled in yet. In order:
    (1) the county parcel file's current owner by address, (2) a news search
    for the project's own name. A generic ownership-entity name ("XYZ Owner
    LLC") is only trusted if news ties it to this project; otherwise a real
    developer name found in news wins."""
    owner = find_owner_by_parcel(record.address, parcel_recipe, fetch_rows)
    if owner and not _is_generic_owner_name(owner):
        return owner, {"fact": "developer", "url": "county parcel file"}

    developer = find_developer_by_news(record.name, record.city, search_fn)
    if developer:
        return developer, {"fact": "developer", "url": "news search"}

    if owner and _owner_confirmed_by_news(owner, record.name, record.city, search_fn):
        return owner, {"fact": "developer", "url": "county parcel file + news"}

    return "", None


NOT_YET_BUILT_STAGES = ("planned", "permitted", "under construction")


def fill_contacts(
    records: list,
    search_fn,
    fetch_fn,
    parcel_recipe: dict | None = None,
    parcel_fetch_rows=None,
) -> list:
    """Batch entry point: fills office_phone / website and, only when a
    permit/agenda/news page names someone, folds "(contact: Name)" onto the
    developer field. Never overwrites a phone/website already known."""
    for rec in records:
        if not rec.developer and rec.stage in NOT_YET_BUILT_STAGES:
            developer, source = find_developer_for_new_permit(
                rec, parcel_recipe, parcel_fetch_rows or (lambda source: []), search_fn
            )
            if developer:
                rec.developer = developer
                rec.sources.append(source)

        if not rec.office_phone:
            website = rec.website or find_website(rec.developer, search_fn)
            if website:
                if not rec.website:
                    rec.website = website
                html = _page_html(fetch_fn(website))
                phone = find_office_phone(html)
                if phone:
                    rec.office_phone = phone
                    rec.sources.append({"fact": "office_phone", "url": website})

        if rec.developer and "(contact:" not in rec.developer:
            for fact_key in ("permit", "agenda", "news"):
                url = rec.links.get(fact_key)
                if not url:
                    continue
                html = _page_html(fetch_fn(url))
                name = find_named_contact(html)
                if name:
                    rec.developer = f"{rec.developer} (contact: {name})"
                    rec.sources.append({"fact": "contact_name", "url": url})
                    break
    return records
