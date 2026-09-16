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


# A2: a question naming a region filters state_leads by `region`, never Plano/Richardson tables.
def test_a2_region_rule_is_present():
    text = soul_text()
    assert "Right area for sales and leads." in text
    rule = text[text.index("Right area for sales and leads."):]
    for region in ("Dallas–Fort Worth", "Houston", "Austin", "San Antonio"):
        assert region in rule[:600], f"{region} missing from the region rule"
    assert "WHERE region = 'Dallas–Fort Worth'" in rule


def test_a2_never_falls_back_to_plano_tables():
    text = soul_text()
    rule = text[text.index("Right area for sales and leads."):]
    assert "Never fall back" in rule
    assert "`leads`, `sales` or `master` tables for a region" in rule


def test_a2_first_line_names_the_region_used():
    text = soul_text()
    rule = text[text.index("Right area for sales and leads."):]
    assert "first line of the answer must say the" in rule and "region used" in rule


# A3: claims from street_talk carry the post's link on the same line, plus a post count.
SKILL = SOUL.parent / "skills" / "query-propertystack" / "SKILL.md"


def test_a3_reddit_link_rule_is_present():
    text = soul_text()
    assert "Reddit claims carry their post link." in text
    rule = text[text.index("Reddit claims carry their post link."):]
    assert "`street_talk`" in rule[:200]
    assert "as a markdown link on the same line" in rule
    assert "SELECT title, quote, url" in rule


def test_a3_answer_says_how_many_posts():
    text = soul_text()
    rule = text[text.index("Reddit claims carry their post link."):]
    assert "how many posts the answer is based on" in rule
    assert "From 2 posts" in rule


def test_a3_no_link_means_claim_left_out():
    text = soul_text()
    rule = text[text.index("Reddit claims carry their post link."):]
    assert "leave" in rule and "that claim out entirely" in rule
    assert "never quote a post you cannot link" in rule


def test_a3_skill_notes_carry_the_same_rule():
    text = SKILL.read_text(encoding="utf-8")
    row = text[text.index("| `street_talk` |"):]
    row = row[:row.index("\n")]
    assert "`url` as a link on the same line" in row
    assert "from 2 posts" in row
    assert "left out" in row


def test_a3_every_saved_post_has_a_real_thread_link():
    import csv
    csv_path = SOUL.parents[2] / "propertystack" / "data" / "street-talk" / "street_talk.csv"
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
    assert rows, "street_talk.csv has no posts"
    bad = [r["title"] for r in rows if not (r["url"].startswith("https://www.reddit.com/r/") or "youtube.com/watch" in r["url"])]
    assert not bad, f"posts without a real thread link: {bad}"
