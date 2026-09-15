"""A3: with the chat docked on desktop, Early Leads rows become cards so Software and Why stay in view,
and the Chat menu link never shows as a second selected tab."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CSS = (ROOT / "site/css/chat-panel.css").read_text(encoding="utf-8")
JS = (ROOT / "site/js/chat-panel.js").read_text(encoding="utf-8")


def test_leads_table_becomes_cards_when_panel_open():
    assert re.search(r"body\.chat-panel-open \.leads-table thead \{ display: none; \}", CSS)
    assert re.search(r"body\.chat-panel-open \.leads-table td \{ display: block; width: 100%; \}", CSS)
    assert 'body.chat-panel-open .leads-table td[data-label]::before' in CSS


def test_chat_link_never_marked_selected():
    fn = JS.split("function markChatTabActive", 1)[1].split("function buildPanel", 1)[0]
    assert 'classList.toggle("active"' not in fn and 'classList.add("active"' not in fn
    assert 'classList.remove("active")' in fn
    assert "Close chat" in fn
