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


def test_named_own_data_source_counts_but_vague_one_does_not():
    about = "**RealPage makes property software.**\n- **Main product**: OneSite\n**Next:** Ask who runs it nearby.\n**Sources:** RealPage research"
    assert finalize_answer(about, set()) == about
    count = "**Yardi runs 13 buildings.**\n**Sources:** Software check · County property records"
    assert finalize_answer(count, set()) == count
    vague = "**Northstar owns the building.**\n**Sources:** CraneSignal data"
    assert finalize_answer(vague, set()) == UNVERIFIED_REPLY
    claim_in_body = "**County sales records show a sale.**\n**Next:** Call them."
    assert finalize_answer(claim_in_body, set()) == UNVERIFIED_REPLY


def test_deep_dive_with_only_a_map_link_names_its_data_source():
    dive = ("**I don't have a phone for The Gio.**\n- **Size:** **730 units**\n"
            "🗺️ [Map](https://www.google.com/maps/search/?api=1&query=5000+K+Ave%2C+Plano%2C+TX)"
            " · 📂 From: County property records")
    out = finalize_answer(dive.replace("I don't have a phone for The Gio.", "The Gio: 730 units."), set(), deep_dive=True)
    assert out != UNVERIFIED_REPLY
    assert "County property records" in out
