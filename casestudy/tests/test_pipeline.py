"""C7: one record -> public answer + diagnostics; batches export in order; expected never leaks in."""
import json
from pathlib import Path

import pytest

from casestudy.cli import main
from casestudy.contract import AssignmentAnswer
from casestudy.pipeline import RunResult, diagnostics_jsonl, run_batch, run_record, submission_jsonl, submission_line
from casestudy.tests.test_contract import semantic_checklist_sms
from casestudy.writer import WriterConfig

DATA = Path(__file__).resolve().parents[1] / "data"
LINES = [l for l in (DATA / "sample.jsonl").read_text().splitlines() if l.strip()]
SAMPLES = [json.loads(l) for l in LINES]
OFFLINE = WriterConfig(enabled=False)
PUBLIC_KEYS = {"next_message", "next_action"}


def _variant(idx, **over):
    r = json.loads(LINES[idx])
    r.update(over)
    return r


# ------------------------------------------------------------------ references

def test_sms_reference_structure_and_meaning():
    res = run_record(SAMPLES[0], config=OFFLINE)
    assert res.engine == "template" and not res.errors
    assert set(res.submission()) == PUBLIC_KEYS
    assert semantic_checklist_sms(res.answer, SAMPLES[0]["expected"])
    assert res.submission() == AssignmentAnswer.model_validate(SAMPLES[0]["expected"]).model_dump(mode="json")


def test_email_reference_structure_and_meaning():
    res = run_record(SAMPLES[1], config=OFFLINE)
    ref = SAMPLES[1]["expected"]
    nm = res.answer.next_message
    assert nm.channel == "email" and nm.send_at == ref["next_message"]["send_at"] and nm.subject
    assert nm.cta.model_dump() == ref["next_message"]["cta"]
    assert "Taylor" in nm.body and "mid-February" in nm.body and "pool" in nm.body and "STOP" in nm.body
    assert res.answer.next_action.model_dump() == ref["next_action"]
    assert set(res.submission()) == PUBLIC_KEYS


# ------------------------------------------------------------------ expected cannot influence

@pytest.mark.parametrize("idx", [0, 1])
def test_expected_cannot_influence_inference(idx):
    base = run_record(SAMPLES[idx], config=OFFLINE).submission()
    without = run_record(_variant(idx, expected=None), config=OFFLINE)
    deleted = json.loads(LINES[idx]); del deleted["expected"]
    poisoned = _variant(idx, expected={"next_message": {"channel": "voice", "send_at": "1999-01-01T00:00:00+00:00", "subject": "X", "body": "WRONG", "cta": {"type": "schedule_tour", "link": "https://evil.example"}}, "next_action": {"type": "follow_up_in_days", "value": 99}})
    assert run_record(deleted, config=OFFLINE).submission() == base
    assert without.submission() == base
    assert run_record(poisoned, config=OFFLINE).submission() == base
    assert "WRONG" not in json.dumps(run_record(poisoned, config=OFFLINE).diagnostics())


# ------------------------------------------------------------------ no diagnostic keys leak

def test_submission_has_no_diagnostic_keys():
    res = run_record(SAMPLES[0], config=OFFLINE)
    line = res.submission_line()
    obj = json.loads(line)
    assert set(obj) == PUBLIC_KEYS
    for bad in ("task_id", "why", "engine", "latency", "score", "rule", "citation"):
        assert bad not in line
    assert submission_line(res.answer) == line


def test_diagnostics_carry_required_fields():
    d = run_record(SAMPLES[1], config=OFFLINE).diagnostics()
    assert d["task_id"] == "prospect_long_horizon_day3"
    assert d["engine"] == "template" and d["fallback_reason"] == "offline mode"
    assert d["verified_states"] == ["consent_verified"] and d["unsupported_states"] == []
    assert d["reply_class"] in (None, "none")
    assert {"profile.first_name", "profile.amenity_interest", "input.move_date_target"} <= set(d["personalization_fields"])
    assert d["latency_ms"] >= 0 and d["errors"] == []
    for entry in d["why"]:
        assert {"rule", "plain_english", "citation", "confidence", "status"} <= set(entry)
        assert entry["confidence"] in ("observed", "input_required", "hypothesis", "conservative_default")
    json.dumps(d)  # serializable


# ------------------------------------------------------------------ terminal decisions

def test_stop_reply_exports_opt_out_without_message():
    r = _variant(0); r["input"]["inbound_reply"] = "STOP"
    res = run_record(r, config=OFFLINE)
    assert res.submission() == {"next_message": None, "next_action": {"type": "mark_opted_out", "reason": "inbound_opt_out"}}
    assert res.engine == "none"


def test_no_consent_exports_suppress():
    r = _variant(0, consent={"email_opt_in": False, "sms_opt_in": False, "voice_opt_in": False})
    res = run_record(r, config=OFFLINE)
    assert res.answer.next_message is None and res.answer.next_action.type == "suppress"
    assert res.answer.next_action.reason == "no_consent"


def test_bad_timezone_exports_escalate():
    r = _variant(0); r["input"]["timezone"] = "Mars/Olympus"
    res = run_record(r, config=OFFLINE)
    assert res.answer.next_message is None and res.answer.next_action.type == "escalate"


def test_voice_only_exports_call_task():
    r = _variant(0, consent={"email_opt_in": False, "sms_opt_in": False, "voice_opt_in": True}, channel_preferences=["voice"])
    res = run_record(r, config=OFFLINE)
    assert res.answer.next_message is None and res.answer.next_action.type == "create_call_task"


def test_unsupported_required_state_is_visible():
    r = _variant(0); r["assertions"]["required_states"] = r["assertions"]["required_states"] + ["quantum_check"]
    d = run_record(r, config=OFFLINE).diagnostics()
    assert d["unsupported_states"] == ["quantum_check"]
    assert any(w["rule"] == "required_state" and w["status"] == "unsupported" for w in d["why"])


# ------------------------------------------------------------------ malformed input never aborts

def test_malformed_records_yield_safe_answers_and_keep_order():
    lines = [LINES[0], "{not json", "[1,2,3]", '"just a string"', "{}", LINES[1]]
    results = run_batch(lines, config=OFFLINE)
    assert len(results) == 6
    assert results[0].task_id == "prospect_welcome_day0" and results[5].task_id == "prospect_long_horizon_day3"
    for r in results[1:5]:
        assert r.answer.next_message is None and r.answer.next_action.type in ("escalate", "suppress")
        assert r.errors or r.decision != "proceed"
    assert results[1].malformed and results[1].errors[0].startswith("malformed_json")
    assert results[2].malformed and results[3].malformed
    for line in submission_jsonl(results).splitlines():
        AssignmentAnswer.model_validate(json.loads(line))


def test_internal_error_is_contained(monkeypatch):
    import casestudy.pipeline as p
    monkeypatch.setattr(p, "infer_schedule", lambda o: (_ for _ in ()).throw(RuntimeError("boom")))
    res = run_record(SAMPLES[0], config=OFFLINE)
    assert res.answer.next_action.type == "escalate" and res.answer.next_action.reason == "internal_error"
    assert any("boom" in e for e in res.errors)


# ------------------------------------------------------------------ batch of 12

def _twelve():
    out = []
    for i in range(12):
        r = json.loads(LINES[i % 2]); r["task_id"] = f"{r['task_id']}_copy{i}"
        out.append(json.dumps(r))
    return out


def test_twelve_line_batch_exports_twelve_ordered_lines(tmp_path):
    lines = _twelve()
    results = run_batch(lines + ["", "   "], config=OFFLINE)
    assert [r.task_id for r in results] == [json.loads(l)["task_id"] for l in lines]
    sub = submission_jsonl(results)
    assert len(sub.splitlines()) == 12
    diag = diagnostics_jsonl(results)
    assert [json.loads(l)["task_id"] for l in diag.splitlines()] == [r.task_id for r in results]
    for line in sub.splitlines():
        assert set(json.loads(line)) == PUBLIC_KEYS


def test_cli_offline_writes_both_files(tmp_path, capsys):
    inp = tmp_path / "in.jsonl"; inp.write_text("\n".join(_twelve()) + "\n")
    sub = tmp_path / "sub.jsonl"; diag = tmp_path / "diag.jsonl"
    assert main([str(inp), "--offline", "--submission-out", str(sub), "--diagnostics-out", str(diag)]) == 0
    sub_lines = sub.read_text().splitlines(); diag_lines = diag.read_text().splitlines()
    assert len(sub_lines) == 12 and len(diag_lines) == 12
    assert all(json.loads(d)["engine"] == "template" for d in diag_lines)
    assert all(json.loads(d)["fallback_reason"] == "offline mode" for d in diag_lines)
    # CLI bytes equal the library serializer byte-for-byte
    results = run_batch(_twelve(), config=OFFLINE)
    assert sub.read_text() == submission_jsonl(results)
    assert "12 record(s)" in capsys.readouterr().err


def test_cli_stdin_to_stdout(monkeypatch):
    import io
    out = io.StringIO()
    assert main(["-", "--offline"], stdin=io.StringIO(LINES[0] + "\n"), stdout=out) == 0
    assert json.loads(out.getvalue().strip()) == run_record(SAMPLES[0], config=OFFLINE).submission()


def test_offline_flag_never_builds_a_client(monkeypatch, tmp_path):
    import casestudy.writer as w
    monkeypatch.setenv("DEEPSEEK_API_KEY", "k"); monkeypatch.setenv("DEEPSEEK_MODEL", "m")
    monkeypatch.setattr(w, "make_client", lambda c: (_ for _ in ()).throw(AssertionError("network client built")))
    inp = tmp_path / "in.jsonl"; inp.write_text(LINES[0] + "\n")
    sub = tmp_path / "s.jsonl"
    assert main([str(inp), "--offline", "--submission-out", str(sub)]) == 0
    assert json.loads(sub.read_text())["next_message"]["channel"] == "sms"
