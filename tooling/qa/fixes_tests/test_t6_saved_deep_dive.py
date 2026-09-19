"""T6: a second contact request for the same building and question
shows the saved copy instead of silently sending the question again."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CHAT_PANEL_JS = (ROOT / "site/js/chat-panel.js").read_text(encoding="utf-8")
PROPERTY_HTML = (ROOT / "site/property.html").read_text(encoding="utf-8")
INDEX_HTML = (ROOT / "site/index.html").read_text(encoding="utf-8")


def test_deep_dive_remembers_by_building_id():
    # Without an id key per building, a second click can't tell "same
    # building, same question" from a fresh one.
    assert "function savedDeepDive(id)" in CHAT_PANEL_JS
    assert "function rememberDeepDive(id, text)" in CHAT_PANEL_JS
    assert 'localStorage.setItem(deepDiveKey(id)' in CHAT_PANEL_JS


def test_second_click_shows_saved_notice_instead_of_retyping():
    fn = CHAT_PANEL_JS.split("function deepDive(id, text)", 1)[1].split("\n  function ", 1)[0]
    assert "saved.text === text" in fn
    assert "Saved deep dive from" in fn
    assert "Press ↻ to redo it" in fn
    # The saved path must not fall through to re-sending the question.
    assert fn.index("Saved deep dive from") < fn.index("hideDeepDiveNotice(panel)")


def test_redo_button_resends_the_saved_question():
    assert "chat-panel-deepdive-redo" in CHAT_PANEL_JS
    assert 'panel.querySelector("#chat-panel-deepdive-redo").addEventListener' in CHAT_PANEL_JS


def test_callers_pass_the_building_id():
    assert "window.PSChatPanel.deepDive(id, window.PSChatPanel.deepDivePrompt(" in PROPERTY_HTML
    assert PROPERTY_HTML.count("window.PSChatPanel.deepDive(id, window.PSChatPanel.deepDivePrompt(") == 2
    assert "window.PSChatPanel.deepDive(l.id, window.PSChatPanel.deepDivePrompt(" in INDEX_HTML
