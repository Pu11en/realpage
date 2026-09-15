import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
LEAD_FINDER = HERE.parents[0] / "lead-finder"
for p in (HERE, LEAD_FINDER):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from detect import classify_links, classify_text, classify_in_house, detect_software, load_rules  # noqa: E402
from fetch import FetchResult  # noqa: E402
from record import LeadRecord  # noqa: E402


def _load_run_module():
    spec = importlib.util.spec_from_file_location("lead_finder_software_run", HERE / "run.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fill_software = _load_run_module().fill_software

RULES = load_rules()


def test_classify_links_portal_wins_over_asset():
    html = '<a href="https://example.com/cdn/loftliving.com/x.js">x</a><a href="https://resident.example.com/securecafe.com/login">Resident Login</a>'
    hits, kind = classify_links(html, RULES)
    assert kind == "portal"
    assert hits["Yardi"].startswith("https://resident.example.com")


def test_classify_links_asset_fallback():
    html = '<a href="https://cdn.example.com/onesite/assets.js">asset</a>'
    hits, kind = classify_links(html, RULES)
    assert kind == "asset"
    assert hits["RealPage"]


def test_classify_links_no_match():
    html = '<a href="https://example.com/about">About</a>'
    hits, kind = classify_links(html, RULES)
    assert hits == {} and kind == ""


def test_classify_text_fallback():
    html = "<p>This community is Powered by ResMan.</p>"
    assert classify_text(html, RULES) == "ResMan"


def test_classify_in_house():
    html = '<a href="https://residents.udr.com/login">Resident Login</a>'
    name, proof = classify_in_house(html, RULES)
    assert name == "in-house:UDR"
    assert "residents.udr.com" in proof


class FakeWeb:
    def __init__(self, pages: dict[str, str]):
        self.pages = pages
        self.fetched = []

    def fetch(self, url: str) -> FetchResult:
        self.fetched.append(url)
        if url not in self.pages:
            return FetchResult(url=url, ok=False, skipped_reason="blocked")
        return FetchResult(url=url, ok=True, html=self.pages[url])


def test_detect_software_portal_signal():
    web = FakeWeb({
        "https://example.com": '<a href="https://portal.example.com/entrata.com/login">Resident Login</a>',
        "https://portal.example.com/entrata.com/login": '<a href="https://portal.example.com/entrata.com/sign-in">Sign in</a>',
    })
    result = detect_software("https://example.com", web)
    assert result == {
        "software": "Entrata",
        "signal": "portal",
        "proof_url": "https://portal.example.com/entrata.com/login",
        "unknown_reason": "",
    }


def test_detect_software_portal_signal_unconfirmed_is_unknown():
    # 4.2: the resident-portal link is the only page, and it doesn't confirm the vendor.
    web = FakeWeb({
        "https://example.com": '<a href="https://portal.example.com/entrata.com/login">Resident Login</a>',
        "https://portal.example.com/entrata.com/login": "<p>Sign in with your email.</p>",
    })
    result = detect_software("https://example.com", web)
    assert result == {"software": "unknown", "signal": "none", "proof_url": "", "unknown_reason": "unconfirmed"}


def test_detect_software_portal_signal_no_second_page_is_unknown():
    # Only the homepage exists -- nothing to double-check against, so no verdict.
    web = FakeWeb({
        "https://example.com": '<a href="https://portal.example.com/entrata.com/login">Resident Login</a>',
    })
    result = detect_software("https://example.com", web)
    assert result["software"] == "unknown"
    assert result["unknown_reason"] == "unconfirmed"


def test_detect_software_hop_portal_signal():
    web = FakeWeb({
        "https://example.com": '<a href="https://example.com/resident-login">Resident Login</a>',
        "https://example.com/resident-login": '<a href="https://x.appfolio.com/portal">Sign in</a>',
    })
    result = detect_software("https://example.com", web)
    assert result["software"] == "AppFolio"
    assert result["signal"] == "hop-portal"


def test_detect_software_no_website_is_unknown_no_fetch():
    web = FakeWeb({})
    result = detect_software("", web)
    assert result == {"software": "unknown", "signal": "none", "proof_url": "", "unknown_reason": "no-website"}
    assert web.fetched == []


def test_detect_software_blocked_site():
    web = FakeWeb({})
    result = detect_software("https://blocked.example.com", web)
    assert result["software"] == "unknown"
    assert result["unknown_reason"] == "blocked"


def test_fill_software_writes_proof_and_source():
    records = [LeadRecord(area="xx", city="Somewhere", website="https://example.com")]
    web = FakeWeb({
        "https://example.com": '<a href="https://portal.example.com/rentcafe.com/login">Resident Login</a>',
        "https://portal.example.com/rentcafe.com/login": '<a href="https://portal.example.com/rentcafe.com/sign-in">Sign in</a>',
    })
    out = fill_software(records, web)
    assert out[0].software == "Yardi"
    assert out[0].links["software_proof"] == "https://portal.example.com/rentcafe.com/login"
    assert {"fact": "software", "url": "https://portal.example.com/rentcafe.com/login"} in out[0].sources


def test_fill_software_skips_records_with_no_website():
    records = [LeadRecord(area="xx", city="Somewhere")]
    web = FakeWeb({})
    out = fill_software(records, web)
    assert out[0].software == "unknown"
    assert web.fetched == []


def test_fill_software_drops_confirmed_realpage():
    # 4.2: a confirmed RealPage building is dropped, it's not a lead.
    records = [
        LeadRecord(area="xx", city="Somewhere", name="RP Building", website="https://rp.example.com"),
        LeadRecord(area="xx", city="Somewhere", name="Yardi Building", website="https://yardi.example.com"),
    ]
    web = FakeWeb({
        "https://rp.example.com": '<a href="https://portal.rp.example.com/onesite/login">Resident Login</a>',
        "https://portal.rp.example.com/onesite/login": '<a href="https://portal.rp.example.com/onesite/sign-in">Sign in</a>',
        "https://yardi.example.com": '<a href="https://portal.yardi.example.com/rentcafe.com/login">Resident Login</a>',
        "https://portal.yardi.example.com/rentcafe.com/login": '<a href="https://portal.yardi.example.com/rentcafe.com/sign-in">Sign in</a>',
    })
    out = fill_software(records, web)
    assert [r.name for r in out] == ["Yardi Building"]
    assert out[0].software == "Yardi"


def test_fill_software_unknown_after_fetch_becomes_not_picked():
    records = [LeadRecord(area="xx", city="Somewhere", website="https://plain.example.com")]
    web = FakeWeb({"https://plain.example.com": "<p>Welcome home.</p>"})
    out = fill_software(records, web)
    assert out[0].software == "not picked"


def test_fill_software_no_website_stays_unknown():
    records = [LeadRecord(area="xx", city="Somewhere")]
    web = FakeWeb({})
    out = fill_software(records, web)
    assert out[0].software == "unknown"


def test_fill_software_keeps_order_when_run_in_parallel():
    """S1: fill_software runs detect_software for several records at once
    (thread pool) -- results must still come back in the original order."""
    pages = {}
    records = []
    for i in range(8):
        site = f"https://site{i}.example.com"
        pages[site] = f'<a href="https://portal{i}.example.com/rentcafe.com/login">Resident Login</a>'
        pages[f"https://portal{i}.example.com/rentcafe.com/login"] = (
            f'<a href="https://portal{i}.example.com/rentcafe.com/sign-in">Sign in</a>'
        )
        records.append(LeadRecord(area="xx", city="Somewhere", name=f"Building {i}", website=site))
    web = FakeWeb(pages)
    out = fill_software(records, web, max_workers=4)
    assert [r.name for r in out] == [f"Building {i}" for i in range(8)]
    assert all(r.software == "Yardi" for r in out)
