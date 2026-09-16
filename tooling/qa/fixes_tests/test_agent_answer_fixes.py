"""Rules the CraneSignal agent must carry so Drew's four failed answers come back good.

Each task in PLAN-agent-answer-fixes.md adds its own check here.
"""
from pathlib import Path

SOUL = Path(__file__).resolve().parents[3] / "chatbot" / "hermes-profile" / "SOUL.md"


def soul_text() -> str:
    return SOUL.read_text(encoding="utf-8")


def test_soul_file_is_there():
    assert SOUL.is_file(), f"agent rules file missing: {SOUL}"
    assert soul_text().strip(), "agent rules file is empty"


# A1: offer to check instead of "I don't have that" when we have rows to show.
def test_a1_offer_to_check_rule_is_present():
    text = soul_text()
    assert "Offer to check" in text
    assert "[🔍 Check <building>](#ask:Deep dive on <name>, <city>)" in text


def test_a1_never_open_with_i_dont_have_that_when_rows_exist():
    text = soul_text()
    assert 'Never open with "I don\'t have that" when we have rows to show.' in text
    # the offer must come after showing what we do have and naming what isn't checked
    rule = text[text.index("Offer to check"):]
    assert rule.index("leads with what we DO have") < rule.index("isn't checked") < rule.index("ends with an offer")


def test_a1_i_dont_have_that_is_scoped_to_no_rows_at_all():
    text = soul_text()
    assert "If it isn't in the data at all (no matching rows anywhere)" in text
