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
