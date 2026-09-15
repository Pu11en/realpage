import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
LEAD_FINDER = HERE.parents[0] / "lead-finder"
for p in (HERE, LEAD_FINDER):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from contact import (
    fill_contacts,
    find_developer_by_news,
    find_developer_for_new_permit,
    find_named_contact,
    find_office_phone,
    find_owner_by_parcel,
    find_website,
)
from record import LeadRecord

PARCEL_RECIPE = {
    "parcel_source": {"url": "https://example.test/parcel.zip"},
    "parcel_fields": {"address": "SitusAddress", "owner": "OwnerName"},
}


def make_record(**kw):
    base = dict(area="zz", city="Rivertown", developer="Acme Development")
    base.update(kw)
    return LeadRecord(**base)


def test_find_office_phone_prefers_non_fax():
    html = "Fax: (212) 555-0111. Office: (212) 555-0144."
    assert find_office_phone(html) == "(212) 555-0144"


def test_find_office_phone_skips_fax_only_number():
    html = "Fax: (212) 555-0111."
    assert find_office_phone(html) == ""


def test_find_office_phone_uses_cell_as_fallback_only():
    html = "Cell: (212) 555-0188."
    assert find_office_phone(html) == "(212) 555-0188"


def test_find_office_phone_no_numbers():
    assert find_office_phone("no numbers here") == ""


def test_find_office_phone_dedupes_repeated_number():
    html = "Call us: (212) 555-0144. Same office: (212) 555-0144."
    assert find_office_phone(html) == "(212) 555-0144"


def test_find_office_phone_prefers_office_over_repeated_cell():
    html = "Cell: (212) 555-0188. Cell: (212) 555-0188. Office: (212) 555-0144."
    assert find_office_phone(html) == "(212) 555-0144"


def test_find_website_returns_first_result_url():
    results = [
        {"url": "https://acmedev.example.com", "title": "Acme Development -- apartment communities"},
        {"url": "https://other.example.com", "title": "Other Co"},
    ]
    assert find_website("Acme Development", lambda q: results) == "https://acmedev.example.com"


def test_find_website_skips_result_not_about_the_developer():
    results = [
        {"url": "https://unrelated.example.com", "title": "Unrelated apartments for rent"},
        {"url": "https://acmedev.example.com", "title": "Acme Development -- apartment communities"},
    ]
    assert find_website("Acme Development", lambda q: results) == "https://acmedev.example.com"


def test_find_website_skips_listing_domain():
    results = [{"url": "https://www.apartments.com/acme-development", "title": "Acme Development"}]
    assert find_website("Acme Development", lambda q: results) == ""


def test_find_website_blank_developer():
    assert find_website("", lambda q: [{"url": "https://x.example.com"}]) == ""


def test_find_website_no_results():
    assert find_website("Acme Development", lambda q: []) == ""


def test_find_named_contact_matches_property_manager():
    text = "For leasing questions, Property Manager: Jane Doe can help."
    assert find_named_contact(text) == "Jane Doe"


def test_find_named_contact_no_match():
    assert find_named_contact("Nothing relevant here.") == ""


def test_fill_contacts_fills_phone_from_developer_website():
    rec = make_record(website="https://acmedev.example.com")
    fetch_fn = lambda url: {"html": "Office: (212) 555-0144.", "ok": True}
    search_fn = lambda q: []
    fill_contacts([rec], search_fn, fetch_fn)
    assert rec.office_phone == "(212) 555-0144"
    assert {"fact": "office_phone", "url": "https://acmedev.example.com"} in rec.sources


def test_fill_contacts_searches_for_website_when_blank():
    rec = make_record()
    search_fn = lambda q: [
        {"url": "https://acmedev.example.com", "title": "Acme Development -- apartment communities"}
    ]
    fetch_fn = lambda url: {"html": "Office: (212) 555-0144.", "ok": True}
    fill_contacts([rec], search_fn, fetch_fn)
    assert rec.website == "https://acmedev.example.com"
    assert rec.office_phone == "(212) 555-0144"


def test_fill_contacts_does_not_overwrite_known_phone():
    rec = make_record(website="https://acmedev.example.com", office_phone="(212) 555-0100")
    fetch_fn = lambda url: {"html": "Office: (212) 555-0144.", "ok": True}
    fill_contacts([rec], lambda q: [], fetch_fn)
    assert rec.office_phone == "(212) 555-0100"


def test_fill_contacts_names_contact_only_from_permit_agenda_or_news_link():
    rec = make_record(links={"permit": "https://city.example.com/permit/123"})

    def fetch_fn(url):
        if "permit" in url:
            return {"html": "Project Manager: Jane Doe filed this permit.", "ok": True}
        return {"html": "", "ok": True}

    fill_contacts([rec], lambda q: [], fetch_fn)
    assert rec.developer == "Acme Development (contact: Jane Doe)"
    assert {"fact": "contact_name", "url": "https://city.example.com/permit/123"} in rec.sources


def test_fill_contacts_no_named_contact_when_no_linked_pages_name_one():
    rec = make_record(links={"permit": "https://city.example.com/permit/123"})
    fetch_fn = lambda url: {"html": "No names on this generic permit page.", "ok": True}
    fill_contacts([rec], lambda q: [], fetch_fn)
    assert rec.developer == "Acme Development"


def test_fill_contacts_skips_blocked_fetch_result():
    rec = make_record(website="https://acmedev.example.com")
    fetch_fn = lambda url: {"html": "Office: (212) 555-0144.", "ok": False}
    fill_contacts([rec], lambda q: [], fetch_fn)
    assert rec.office_phone == ""


# -- F10b: developer + phone for brand-new permits --------------------------


def test_find_owner_by_parcel_matches_on_address():
    rows = [
        {"SitusAddress": "965 E UNIVERSITY DR", "OwnerName": "REVELRY TEMPE LP"},
        {"SitusAddress": "701 W RIO SALADO PKWY", "OwnerName": "OTHER LLC"},
    ]
    fetch_rows = lambda source: rows
    assert find_owner_by_parcel("965 E University Dr", PARCEL_RECIPE, fetch_rows) == "REVELRY TEMPE LP"


def test_find_owner_by_parcel_no_match():
    fetch_rows = lambda source: [{"SitusAddress": "1 OTHER ST", "OwnerName": "SOMEONE LLC"}]
    assert find_owner_by_parcel("965 E University Dr", PARCEL_RECIPE, fetch_rows) == ""


def test_find_owner_by_parcel_no_recipe():
    assert find_owner_by_parcel("965 E University Dr", None, lambda s: []) == ""


def test_find_owner_by_parcel_fetch_error_returns_blank():
    def boom(source):
        raise RuntimeError("network down")

    assert find_owner_by_parcel("965 E University Dr", PARCEL_RECIPE, boom) == ""


def test_find_developer_by_news_extracts_company_from_headline():
    results = [
        {
            "url": "https://realestatenews.example.com/revelry-tempe-breaks-ground",
            "title": "REVELRY Tempe apartments developed by Mark-Taylor Residential",
        }
    ]
    assert find_developer_by_news("REVELRY", "Tempe", lambda q: results) == "Mark-Taylor Residential"


def test_find_developer_by_news_rejects_unrelated_result():
    results = [{"url": "https://unrelated.example.com", "title": "Some other apartments developer"}]
    assert find_developer_by_news("REVELRY", "Tempe", lambda q: results) == ""


def test_find_developer_by_news_no_project_name():
    assert find_developer_by_news("", "Tempe", lambda q: [{"url": "x", "title": "x"}]) == ""


def test_find_developer_for_new_permit_prefers_real_parcel_owner():
    rec = make_record(name="REVELRY", city="Tempe", address="965 E University Dr", developer="", stage="permitted")
    fetch_rows = lambda source: [{"SitusAddress": "965 E UNIVERSITY DR", "OwnerName": "Mark-Taylor Residential"}]
    developer, source = find_developer_for_new_permit(rec, PARCEL_RECIPE, fetch_rows, lambda q: [])
    assert developer == "Mark-Taylor Residential"
    assert source["fact"] == "developer"


def test_find_developer_for_new_permit_falls_back_to_news_for_generic_owner():
    rec = make_record(name="REVELRY", city="Tempe", address="965 E University Dr", developer="", stage="permitted")
    fetch_rows = lambda source: [{"SitusAddress": "965 E UNIVERSITY DR", "OwnerName": "REVELRY TEMPE OWNER LLC"}]
    news_results = [
        {
            "url": "https://realestatenews.example.com/revelry-tempe",
            "title": "REVELRY Tempe apartments developed by Mark-Taylor Residential",
        }
    ]
    developer, source = find_developer_for_new_permit(rec, PARCEL_RECIPE, fetch_rows, lambda q: news_results)
    assert developer == "Mark-Taylor Residential"


def test_find_developer_for_new_permit_confirms_generic_owner_via_news():
    rec = make_record(name="REVELRY", city="Tempe", address="965 E University Dr", developer="", stage="permitted")
    fetch_rows = lambda source: [{"SitusAddress": "965 E UNIVERSITY DR", "OwnerName": "REVELRY TEMPE OWNER LLC"}]
    news_results = [
        {"url": "https://azbex.com/revelry-tempe", "title": "REVELRY Tempe filed by Revelry Tempe Owner LLC"}
    ]
    developer, source = find_developer_for_new_permit(rec, PARCEL_RECIPE, fetch_rows, lambda q: news_results)
    assert developer == "REVELRY TEMPE OWNER LLC"


def test_find_developer_for_new_permit_never_guesses():
    rec = make_record(name="REVELRY", city="Tempe", address="965 E University Dr", developer="", stage="permitted")
    developer, source = find_developer_for_new_permit(rec, None, lambda s: [], lambda q: [])
    assert developer == ""
    assert source is None


def test_fill_contacts_fills_developer_for_permitted_record_with_no_developer():
    rec = make_record(
        name="REVELRY", city="Tempe", address="965 E University Dr", developer="", stage="permitted"
    )
    fetch_rows = lambda source: [{"SitusAddress": "965 E UNIVERSITY DR", "OwnerName": "Mark-Taylor Residential"}]
    fill_contacts([rec], lambda q: [], lambda u: {"html": "", "ok": True}, parcel_recipe=PARCEL_RECIPE, parcel_fetch_rows=fetch_rows)
    assert rec.developer == "Mark-Taylor Residential"


def test_fill_contacts_leaves_developer_blank_for_leasing_record():
    rec = make_record(name="Some Building", city="Tempe", developer="", stage="leasing")
    fill_contacts([rec], lambda q: [], lambda u: {"html": "", "ok": True})
    assert rec.developer == ""
