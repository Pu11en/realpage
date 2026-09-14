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
    })
    result = detect_software("https://example.com", web)
    assert result == {
        "software": "Entrata",
        "signal": "portal",
        "proof_url": "https://portal.example.com/entrata.com/login",
        "unknown_reason": "",
    }


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
