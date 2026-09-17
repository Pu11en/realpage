"""The assignment files the whole build reads from must be there and parseable."""
import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"


def test_sample_record_parses():
    lines = [l for l in (DATA / "sample.jsonl").read_text().splitlines() if l.strip()]
    assert lines, "sample.jsonl is empty"
    record = json.loads(lines[0])
    for key in ("task_id", "consent", "channel_preferences", "input", "assertions", "expected"):
        assert key in record, f"sample record is missing {key}"


def test_problem_statement_present():
    assert (DATA / "problem_statement.txt").read_text().strip()
