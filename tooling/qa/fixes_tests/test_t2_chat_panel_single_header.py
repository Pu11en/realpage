"""T2: the chat panel (and its "Ask CraneSignal" header bar) is built at most once per page, even if
the script runs twice, initChatPanel() is called more than once, or a stray duplicate #chat-panel node
ever ends up in the DOM."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
JS = (ROOT / "site/js/chat-panel.js").read_text(encoding="utf-8")


def test_script_guards_against_running_twice():
    head = JS.split("const STORAGE_OPEN", 1)[0]
    assert "window.__chatPanelLoaded" in head
    assert re.search(r"if \(window\.__chatPanelLoaded\) return;", head)


def test_wire_triggers_does_not_double_bind_listeners():
    fn = JS.split("function wireTriggers", 1)[1].split("function ", 1)[0]
    assert "dataset.chatWired" in fn
    assert re.search(r"if \(el\.dataset\.chatWired\) return;", fn)


def test_build_panel_drops_stray_duplicate_headers():
    fn = JS.split("function buildPanel", 1)[1].split("function ", 1)[0]
    assert 'document.querySelectorAll("#chat-panel")' in fn
    assert "el.remove()" in fn
