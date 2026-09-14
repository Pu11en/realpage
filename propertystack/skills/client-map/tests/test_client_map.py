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
