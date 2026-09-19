"""G1-T2: deep dives find a sourced contact before explaining the lead.

These checks stay offline: they pin the operating rules shared by the Hermes
profile and its PropertyStack query skill without making web or model calls.
"""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PROFILE = ROOT / "chatbot" / "hermes-profile"
SOUL = (PROFILE / "SOUL.md").read_text(encoding="utf-8")
SKILL = (PROFILE / "skills" / "query-propertystack" / "SKILL.md").read_text(
    encoding="utf-8"
)


def section(text: str, heading: str) -> str:
    """Return a Markdown section so an unrelated mention cannot satisfy a rule."""
    start = text.index(heading) + len(heading)
    end = text.find("\n## ", start)
    return text[start:] if end == -1 else text[start:end]


SOUL_LOOKUP = section(SOUL, "## Look it up first")
SOUL_LAYOUT = section(SOUL, "## Every answer uses one of two fixed layouts")
SKILL_DEEP_DIVE = section(SKILL, "## Deep dive: who to call")
SKILL_BUDGET = section(SKILL, "## Budget")
SOUL_LOOKUP_WORDS = " ".join(SOUL_LOOKUP.split())
SOUL_LAYOUT_WORDS = " ".join(SOUL_LAYOUT.split())
SKILL_DEEP_DIVE_WORDS = " ".join(SKILL_DEEP_DIVE.split())
SKILL_BUDGET_WORDS = " ".join(SKILL_BUDGET.split())


def test_deep_dive_starts_with_contact_block_before_why_now():
    assert "start with this short **Who to call** block, before why now" in SOUL_LAYOUT_WORDS
    required_lines = (
        "**Who to call**",
        "- **Company:**",
        "- **Office phone:**",
        "- **Website:**",
        "- **Ask for:**",
        "- **Why now:**",
    )
    positions = [SOUL_LAYOUT.index(line) for line in required_lines]
    assert positions == sorted(positions)
    assert "**Answer contact-first.**" in SKILL_DEEP_DIVE


def test_lookup_uses_saved_building_data_before_web_search():
    data_first = SKILL_DEEP_DIVE.index("**Our data first.**")
    fill_gaps = SKILL_DEEP_DIVE.index("**Fill the gaps.**")
    assert data_first < fill_gaps
    for field in ("`office_phone`", "`website`", "`developer`"):
        assert field in SKILL_DEEP_DIVE[data_first:fill_gaps]
    assert "After the saved data" in SKILL_DEEP_DIVE_WORDS


def test_deep_dive_web_searches_are_limited_to_six():
    assert "at most 6 searches" in SOUL_LOOKUP_WORDS
    assert "Deep dives: at most 6 web searches" in SKILL_BUDGET_WORDS
    assert "12 tool calls total" in SOUL_LOOKUP_WORDS
    assert "12 tool calls total" in SKILL_BUDGET_WORDS


def test_phone_and_website_each_require_a_supporting_source():
    assert "Every company, phone, website and role must have a source link" in SOUL_LAYOUT_WORDS
    assert "No supporting URL after lookup = **not found**, even if an unlinked value exists in our data" in SOUL_LAYOUT_WORDS
    assert "Each contact/owner value must have its own source link beside it" in SKILL_DEEP_DIVE_WORDS
    assert "including phones/websites from our data" in SKILL_DEEP_DIVE_WORDS


def test_missing_contact_fields_remain_visible_as_not_found():
    assert "Keep all four contact fields, even when nothing is found" in SOUL_LAYOUT_WORDS
    assert "replace an unsupported value and its link with **not found**" in SOUL_LAYOUT_WORDS
    assert "retain the field with **not found**" in SKILL_DEEP_DIVE_WORDS


def test_phone_numbers_are_never_guessed():
    assert "Never guess a number" in SOUL_LAYOUT_WORDS
    assert "Never guess a number or infer a role" in SKILL_DEEP_DIVE_WORDS


def test_recent_sale_includes_a_sourced_new_owner():
    assert "For a recent sale, always include **New owner**" in SOUL_LAYOUT_WORDS
    assert "Link the source beside the buyer" in SOUL_LAYOUT_WORDS
    assert "use the recorded buyer first" in SOUL_LAYOUT_WORDS
    assert "**Recent sale.** Include **New owner**" in SKILL_DEEP_DIVE_WORDS
    assert "with the record/article that identifies that buyer" in SKILL_DEEP_DIVE_WORDS
    assert "search county deed/property records or sale news" in SKILL_DEEP_DIVE_WORDS
    assert "Never substitute" in SKILL_DEEP_DIVE_WORDS
