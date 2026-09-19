"""AF-T2: Leads offers location-aware example searches for the agent."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
INDEX = (ROOT / "site/index.html").read_text(encoding="utf-8")
STYLES = (ROOT / "site/css/styles.css").read_text(encoding="utf-8")


def test_three_examples_sit_between_agent_bar_and_filters():
    search = INDEX.index('id="lead-agent-search"')
    examples = INDEX.index('id="lead-agent-examples"')
    filters = INDEX.index('<div class="filters">')

    assert search < examples < filters
    assert 'aria-label="Example questions for the agent"' in INDEX
    assert "Ask the agent:" in INDEX  # chips must not read as filters
    renderer = INDEX.split("function renderLeadExamples()", 1)[1].split("\n      }", 1)[0]
    assert "const examples = [" in renderer
    assert "`${place} buildings opening in 2027`" in renderer
    assert "`Recently sold ${locationPhrase}, 200+ units`" in renderer
    assert "`No software yet ${locationPhrase}`" in renderer
    assert 'type="button"' in renderer


def test_examples_use_the_current_state_or_region_and_refresh_on_region_change():
    renderer = INDEX.split("function renderLeadExamples()", 1)[1].split("\n      }", 1)[0]
    assert 'document.querySelector(".metro-btn.active")' in renderer
    assert "metro || (area.slug === \"all\" ? \"\" : area.label)" in renderer

    metro_picker = INDEX.split("function pickMetro(name)", 1)[1].split("\n      }", 1)[0]
    assert "renderLeadExamples()" in metro_picker


def test_example_clicks_send_through_the_shared_agent_path():
    handler = INDEX.split(
        'document.getElementById("lead-agent-examples").addEventListener("click"', 1
    )[1].split("});", 1)[0]
    assert 'event.target.closest("[data-agent-query]")' in handler
    assert "window.PSChatPanel.ask(example.dataset.agentQuery)" in handler


def test_examples_are_clickable_wrapping_chips():
    container_rule = STYLES.split(".lead-agent-examples {", 1)[1].split("}", 1)[0]
    chip_rule = STYLES.split(".lead-agent-example {", 1)[1].split("}", 1)[0]

    assert "display: flex" in container_rule
    assert "flex-wrap: wrap" in container_rule
    assert "border-radius: 999px" in chip_rule
    assert "cursor: pointer" in chip_rule
