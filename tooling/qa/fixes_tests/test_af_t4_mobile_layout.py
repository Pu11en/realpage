"""AF-T4: Agent-first Early Leads controls stack cleanly on phones."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
INDEX = (ROOT / "site/index.html").read_text(encoding="utf-8")
STYLES = (ROOT / "site/css/styles.css").read_text(encoding="utf-8")
MOBILE = STYLES.split("@media (max-width: 900px) {", 1)[1].split(
    "\n}\n\n.placeholder-banner", 1
)[0]


def mobile_rule(selector):
    return MOBILE.split(f"{selector} {{", 1)[1].split("}", 1)[0]


def test_agent_search_stacks_with_a_full_width_touch_target():
    search_rule = mobile_rule(".lead-agent-search")
    button_rule = mobile_rule(".lead-agent-search button")

    assert "flex-direction: column" in search_rule
    assert "width: 100%" in button_rule
    assert "min-height: 44px" in button_rule


def test_example_chips_stack_and_keep_long_location_text_readable():
    examples_rule = mobile_rule(".lead-agent-examples")
    chip_rule = mobile_rule(".lead-agent-example")

    assert "flex-direction: column" in examples_rule
    assert "width: 100%" in chip_rule
    assert "min-height: 44px" in chip_rule
    assert "white-space: normal" in chip_rule
    assert "overflow-wrap: anywhere" in chip_rule


def test_folded_filters_fill_phone_width_without_changing_control_order():
    toggle_rule = mobile_rule(".filters-toggle")
    filters_rule = mobile_rule(".filters")
    fields_rule = mobile_rule(".filters input, .filters select")

    assert "width: 100%" in toggle_rule
    assert "min-height: 44px" in toggle_rule
    assert "flex-direction: column" in filters_rule
    assert "width: 100%" in fields_rule
    assert INDEX.index('id="lead-agent-search"') < INDEX.index('id="lead-agent-examples"')
    assert INDEX.index('id="lead-agent-examples"') < INDEX.index('id="filters-toggle"')
