"""AF-T1: Leads can send a plain-language lead request to the agent."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
INDEX = (ROOT / "site/index.html").read_text(encoding="utf-8")
STYLES = (ROOT / "site/css/styles.css").read_text(encoding="utf-8")


def test_agent_search_is_wide_and_above_existing_filters():
    assert 'id="lead-agent-search"' in INDEX
    assert 'placeholder="Describe the leads you want…"' in INDEX
    assert INDEX.index('id="lead-agent-search"') < INDEX.index('<div class="filters">')
    rule = STYLES.split(".lead-agent-search {", 1)[1].split("}", 1)[0]
    assert "width: 100%" in rule


def test_enter_sends_nonempty_query_through_shared_agent_path():
    handler = INDEX.split(
        'document.getElementById("lead-agent-search").addEventListener("submit"', 1
    )[1].split("});", 1)[0]
    assert "event.preventDefault()" in handler
    assert '.value.trim()' in handler
    assert "if (!query) return" in handler
    assert "window.PSChatPanel.ask(query)" in handler


def test_agent_search_has_an_accessible_label_and_submit_button():
    form = INDEX.split('<form class="lead-agent-search"', 1)[1].split("</form>", 1)[0]
    assert 'for="lead-agent-query"' in form
    assert 'id="lead-agent-query"' in form
    assert 'type="submit"' in form
