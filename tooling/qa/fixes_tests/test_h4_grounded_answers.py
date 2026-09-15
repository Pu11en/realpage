"""H4: factual chat replies need a readable source a person can open."""
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "chatbot"))

from linkfix import UNVERIFIED_REPLY, _norm, finalize_answer  # noqa: E402

FIXTURES = ROOT / "tooling" / "qa" / "fixtures" / "h4-grounding.json"
SOUL = (ROOT / "chatbot" / "hermes-profile" / "SOUL.md").read_text(encoding="utf-8")


def test_two_saved_grounding_failures_become_a_plain_unverified_reply():
    fixtures = json.loads(FIXTURES.read_text(encoding="utf-8"))
    assert len(fixtures) == 2
    for fixture in fixtures:
        seen = {_norm(url) for url in fixture["approved_urls"]}
        assert fixture["expected"] == "unverified"
        assert finalize_answer(fixture["saved_answer"], seen) == UNVERIFIED_REPLY


def test_approved_readable_source_is_kept_but_an_honest_unknown_is_not_overwritten():
    url = "https://communityimpact.com/richardson/housing-real-estate/sherman-street/"
    grounded = f"**Two buildings sold.**\n**Sources:** [News]({url})"
    assert finalize_answer(grounded, {_norm(url)}) == grounded.replace("News", "Community Impact")
    unknown = "**I don't have that.** It would need a county sale record."
    assert finalize_answer(unknown, set()) == unknown


def test_profile_and_proxy_require_the_deterministic_final_check():
    assert "Final verification rule" in SOUL
    assert "couldn't verify that claim with a readable source" in SOUL
    proxy = (ROOT / "chatbot" / "proxy.py").read_text(encoding="utf-8")
    assert proxy.count("finalize_answer(") >= 4
