"""H8: Drew's handoff must retain the real human-release gate details.

This is an offline content check. It never starts the preview, creates an
account, calls a model, or changes local data.
"""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SHEET = ROOT / "docs" / "cranesignal-human-release-test.md"


def test_human_release_sheet_has_private_address_stop_command_and_note_space():
    sheet = SHEET.read_text(encoding="utf-8")

    assert "http://localhost:8765" in sheet
    assert "private browser window" in sheet
    assert "brand-new local account" in sheet
    assert "bash tooling/human-test.sh stop" in sheet
    assert "What I was trying to do:" in sheet
    assert "Anything slow, unclear, surprising, untrustworthy, or broken:" in sheet


def test_human_release_sheet_requires_natural_use_and_keeps_push_gate_closed():
    sheet = SHEET.read_text(encoding="utf-8")

    assert "do not copy a script" in sheet
    assert "not ready to push" in sheet
    assert "unless all of these are" in sheet
    assert "readable source" in sheet
    assert "broken sign-in" in sheet
