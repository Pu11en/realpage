"""H4 (loosened 2026-09-15): fake links are removed, but an answer is never
wiped just because it has no web link. Our own data and general knowledge
name their source in words instead."""
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "chatbot"))

from linkfix import EMPTY_REPLY, _norm, finalize_answer  # noqa: E402

SOUL = " ".join((ROOT / "chatbot" / "hermes-profile" / "SOUL.md").read_text(encoding="utf-8").split())


def test_fake_link_is_removed_but_the_answer_stays():
    answer = "**The building sold in 2026.**\n**Sources:** [Sale record](https://unapproved.example/sale) · County sales records"
    out = finalize_answer(answer, set())
    assert "unapproved.example" not in out
    assert "The building sold in 2026." in out


def test_approved_link_is_kept_and_relabeled():
    url = "https://communityimpact.com/richardson/housing-real-estate/sherman-street/"
    grounded = f"**Two buildings sold.**\n**Sources:** [News]({url})"
    assert finalize_answer(grounded, {_norm(url)}) == grounded.replace("News", "Community Impact")


def test_answers_without_links_are_not_wiped():
    about = ("**RealPage makes property management software.**\n- **Main product**: OneSite\n"
             "**Next:** Ask who runs it nearby.\n**Sources:** General knowledge (may be out of date)")
    assert finalize_answer(about, set()) == about
    count = "**Yardi runs 13 buildings.**\n**Sources:** Software check"
    assert finalize_answer(count, set()) == count


def test_deep_dive_with_only_a_map_link_keeps_its_source_line():
    dive = ("**The Gio: 730 units.**\n- **Size:** **730 units**\n"
            "🗺️ [Map](https://www.google.com/maps/search/?api=1&query=5000+K+Ave%2C+Plano%2C+TX)"
            " · 📂 From: County property records")
    out = finalize_answer(dive, set(), deep_dive=True)
    assert "County property records" in out and "730 units" in out


def test_empty_after_cleaning_gets_a_plain_reply():
    assert finalize_answer("[x](https://fake.example/a)", set()) == EMPTY_REPLY


def test_profile_keeps_the_hard_rules_and_labels_general_knowledge():
    assert "Links only when they help" in SOUL
    assert "General knowledge (may be out of date)" in SOUL
    assert "Never invent contact info" in SOUL
    assert "Touchy topics" in SOUL
    proxy = (ROOT / "chatbot" / "proxy.py").read_text(encoding="utf-8")
    assert proxy.count("finalize_answer(") >= 4
