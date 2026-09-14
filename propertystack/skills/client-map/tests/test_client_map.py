"""Client map (C1) tests: saved fixtures only, no network."""
import pathlib, sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import run  # noqa: E402


def test_budget_stops_cleanly_at_cap():
    b = run.SearchBudget(cap=3)
    for _ in range(3):
        b.use()
    assert b.used == 3 and b.left == 0
    with pytest.raises(run.CapReached):
        b.use()
    assert b.used == 3


def test_budget_never_above_150():
    assert run.SearchBudget(cap=10_000).cap == run.MAX_SEARCHES == 150


def test_search_loop_stops_at_cap_without_error():
    calls = []
    targets = [{"city": f"C{i}", "state": "TX"} for i in range(5)]
    hits, used = run.search_targets(targets, lambda q: calls.append(q) or [], run.SearchBudget(cap=2))
    assert used == 2 and len(calls) == 2 and hits == []


@pytest.mark.parametrize("url,vendor", [
    ("https://dorianandencore.loftliving.com/login", "RealPage"),
    ("https://oakpark.activebuilding.com/", "RealPage"),
    ("https://onesite.realpage.com/residentportal/x", "RealPage"),
    ("https://legacynorthapts.residentportal.com/auth", "Entrata"),
    ("https://axis110.securecafe.com/residentservices/", "Yardi"),
    ("https://example-apts.com/", ""),
])
def test_vendor_of(url, vendor):
    assert run.vendor_of(url) == vendor


def test_realpage_proof_rejects_entrata():
    assert run.is_realpage_proof("https://a.loftliving.com/login")
    assert not run.is_realpage_proof("https://a.residentportal.com/auth")
    assert not run.is_realpage_proof("https://www.realpage.com/blog")  # marketing site is no proof


def test_dedupe_same_portal_or_same_address():
    rows = [
        {"name": "A", "address": "1 Main St, Austin, TX", "proof_url": "https://a.loftliving.com/login"},
        {"name": "A dup", "address": "", "proof_url": "https://A.loftliving.com/pay"},
        {"name": "B", "address": "1  main st., austin, tx", "proof_url": "https://b.activebuilding.com/"},
        {"name": "C", "address": "9 Elm Ave, Austin, TX", "proof_url": "https://c.activebuilding.com/"},
    ]
    assert [r["name"] for r in run.dedupe(rows)] == ["A", "C"]


def test_counts_per_state_and_city():
    rows = [
        {"city": "Austin", "state": "TX"}, {"city": "Austin", "state": "TX"},
        {"city": "Dallas", "state": "TX"}, {"city": "Phoenix", "state": "AZ"},
    ]
    c = run.counts(rows)
    assert c["TX"]["total"] == 3 and c["TX"]["cities"] == {"Austin": 2, "Dallas": 1}
    assert c["AZ"] == {"total": 1, "cities": {"Phoenix": 1}}
    assert list(c) == ["TX", "AZ"]  # most buildings first


# ---------- C3: hits -> buildings (saved search snippets, fake crawl) ----------
def test_portal_key_shared_host_uses_site_id():
    assert run.portal_key("https://Siena.loftliving.com/support") == "siena.loftliving.com"
    assert run.portal_key("https://oll-leasing.loftliving.com/oll/?siteId=5304205&x=1") == "oll-leasing.loftliving.com?siteId=5304205"
    assert run.portal_key("https://loftliving.com/") == ""


def test_dedupe_shared_host_by_site_id():
    rows = [{"name": "G", "proof_url": "https://oll-leasing.loftliving.com/oll/?siteId=1"},
            {"name": "H", "proof_url": "https://oll-leasing.loftliving.com/oll/?siteId=2"},
            {"name": "G2", "proof_url": "https://oll-leasing.loftliving.com/oll/?siteId=1&u=3"}]
    assert [r["name"] for r in run.dedupe(rows)] == ["G", "H"]


def test_building_from_portal_hit():
    hit = {"url": "https://sienaapartments.loftliving.com/support/pincode", "title": "Siena Apartments",
           "description": "Siena Apartments. 5230 Bryant Irvin Road, Fort Worth, TX 76132|(817) 361-9998. Need an Account?"}
    b = run.building_from_hit(hit)
    assert (b["name"], b["street"], b["city"], b["state"], b["zip"]) == \
        ("Siena Apartments", "5230 Bryant Irvin Road", "Fort Worth", "TX", "76132")


def test_building_from_leasing_hit_with_generic_title():
    hit = {"url": "https://oll-leasing.loftliving.com/oll/?siteId=5304205&UnitId=346", "title": "Apartment not found - Online Leasing",
           "description": "The Griffin Apartments 7040 John T White Rd, Fort Worth, TX 76120. Find Apartment"}
    b = run.building_from_hit(hit)
    assert b["name"] == "The Griffin Apartments" and b["city"] == "Fort Worth"


def test_third_party_hit_crawls_portal_link():
    hit = {"url": "https://www.yellowpages.com/fort-worth-tx/bpp/the-savoy", "title": "The Savoy - Yellow Pages",
           "description": "https://thesavoyapartments.loftliving.com/login. Categories. Apartments"}
    seen = []
    fetch = lambda u: seen.append(u) or ("The Savoy Apartments", "## The Savoy Apartments\n7501 Kingswood Drive, Fort Worth, TX 76133|(817)")
    b = run.building_from_hit(hit, fetch)
    assert seen == ["https://thesavoyapartments.loftliving.com/login"]
    assert b["name"] == "The Savoy Apartments" and b["proof_url"] == seen[0]


def test_no_proof_or_entrata_gives_nothing():
    assert run.building_from_hit({"url": "https://loftliving.com/", "title": "LOFT", "description": "app"}) is None
    assert run.building_from_hit({"url": "https://x.residentportal.com/", "title": "X",
                                  "description": "1 Main St, Austin, TX 78701"}) is None


def test_city_case_normalized():
    hit = {"url": "https://baysidegarden.loftliving.com/support/pincode", "title": "Bayside Garden Apartments",
           "description": "Bayside Garden Apartments. 100 Main St, TACOMA, WA 98402|(253)"}
    assert run.building_from_hit(hit)["city"] == "Tacoma"
