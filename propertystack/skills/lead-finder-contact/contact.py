"""Part 4.4 -- who to call, any area.

`find_website`: for a developer/owner name, one search for their site.
`find_office_phone`: pulls phone numbers out of page HTML with `phonenumbers`,
preferring an office/leasing line over a fax or cell line (never returning a
number found next to "fax").
`find_named_contact`: a person's name only when a permit, agenda or news page
actually names one (never guessed from a developer's generic "About Us" page).
`fill_contacts`: the batch entry point over `LeadRecord`s.
"""
from __future__ import annotations

import re

import phonenumbers

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


def find_website(developer: str, search_fn) -> str:
    """One search for a developer/owner's own website. Never guesses a URL."""
    if not developer:
        return ""
    results = search_fn(f"{developer} apartments website") or []
    for item in results:
        url = _result_url(item)
        if url:
            return url
    return ""


def find_office_phone(html: str) -> str:
    """First phone number that isn't next to "fax"; a cell/mobile number is
    kept only as a fallback if nothing better is found."""
    if not html:
        return ""
    fallback = ""
    for match in phonenumbers.PhoneNumberMatcher(html, "US"):
        context = html[max(0, match.start - PHONE_CONTEXT_WINDOW) : match.start].lower()
        if any(k in context for k in FAX_KEYWORDS):
            continue
        formatted = phonenumbers.format_number(
            match.number, phonenumbers.PhoneNumberFormat.NATIONAL
        )
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


def fill_contacts(records: list, search_fn, fetch_fn) -> list:
    """Batch entry point: fills office_phone / website and, only when a
    permit/agenda/news page names someone, folds "(contact: Name)" onto the
    developer field. Never overwrites a phone/website already known."""
    for rec in records:
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
