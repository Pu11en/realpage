"""A7: How it works hides raw internals and shows the same lead count as the site."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
PAGE = (ROOT / "site/under-the-hood.html").read_text(encoding="utf-8")


def test_raw_bits_hidden():
    for raw in ["area: plano-richardson", "runs/*.json", "placeholderBanner", "costPerArea", "errors)"]:
        assert raw not in PAGE, raw


def test_no_internal_todo_lists():
    assert "Review queue" not in PAGE
    assert "Run history" not in PAGE
    assert "Playbook coming" not in PAGE.replace("playbook coming", "Playbook coming")


def test_site_lead_total_is_separate_from_sample_funnel():
    assert "const total = siteLeadTotal(index.areas);" in PAGE
    assert 'pipeline.steps.filter((s) => s.name !== "score-leads")' in PAGE
