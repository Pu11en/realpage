"""C9: complete, honest assignment-field and aggregate evaluation."""
import json
from pathlib import Path

import pytest

from casestudy.evaluation import (
    evaluate_assignment,
    evaluate_record,
    offline_latency_metrics,
    personalization_proxy,
    reply_metrics,
    wilson_interval,
)
from casestudy.gates import normalize
from casestudy.pipeline import run_record
from casestudy.validators import Draft
from casestudy.writer import WriterConfig

DATA = Path(__file__).resolve().parents[1] / "data"
OFFLINE = WriterConfig(enabled=False)


def _rows(name):
    return [json.loads(line) for line in (DATA / name).read_text().splitlines() if line.strip()]


GOLDENS = _rows("sample.jsonl")
PRACTICE = _rows("practice.jsonl")
REPLIES = _rows("reply_corpus.jsonl")


@pytest.mark.parametrize("raw", GOLDENS, ids=lambda row: row["task_id"])
def test_every_assignment_field_is_reported_per_record(raw):
    result = run_record(raw, config=OFFLINE)
    report = evaluate_record(raw, result)
    assert [x["name"] for x in report["required_states"]] == raw["assertions"]["required_states"]
    assert {x["name"] for x in report["constraints"]} == set(raw["assertions"]["constraints"])
    assert {x["name"] for x in report["thresholds"]} == set(raw["thresholds"])
    assert all(x["status"] == "passed" for x in report["required_states"] + report["constraints"])
    by_threshold = {x["name"]: x for x in report["thresholds"]}
    assert by_threshold["personalization_score_min"]["status"] == "passed"
    assert by_threshold["safety_violations_max"] == {
        "name": "safety_violations_max", "target": 0, "actual": 0, "status": "passed", "sample_count": 1,
    }
    assert by_threshold["reply_classification_f1_min"]["status"] == "not_measured"
    assert by_threshold["reply_classification_f1_min"]["sample_count"] == 0
    assert by_threshold["p95_latency_ms"]["status"] == "not_measured"
    assert report["structural_match"]["passed"] is True
    assert report["meaning_checks"]["passed"] is True


def test_pipeline_diagnostics_report_fields_without_looking_at_expected():
    raw = GOLDENS[0]
    diagnostic = run_record(raw, config=OFFLINE).diagnostics()
    evaluation = diagnostic["evaluation"]
    assert {x["name"] for x in evaluation["thresholds"]} == set(raw["thresholds"])
    assert evaluation["structural_match"]["status"] == "not_measured"
    assert evaluation["meaning_checks"]["status"] == "not_measured"
    assert evaluation["structural_match"]["checks"] == []
    assert evaluation["meaning_checks"]["checks"] == []


def test_meaning_checks_are_derived_from_each_record_not_fixture_identity():
    raw = json.loads(json.dumps(GOLDENS[0]))
    raw["input"]["profile"]["first_name"] = "Jordan"
    raw["input"]["property_name"] = "Maple Grove Apartments"
    raw["expected"]["next_message"]["body"] = (
        raw["expected"]["next_message"]["body"]
        .replace("Taylor", "Jordan")
        .replace("Oak Ridge", "Maple Grove")
    )
    result = run_record(raw, config=OFFLINE)
    report = evaluate_record(raw, result)
    checks = {item["name"]: item for item in report["meaning_checks"]["checks"]}
    assert report["meaning_checks"]["passed"] is True
    assert checks["first_name"]["expected_meaning"] == "jordan"
    assert checks["property"]["expected_meaning"] == "maple grove"


def test_null_expected_message_is_a_measured_no_message_meaning_check():
    raw = json.loads(json.dumps(GOLDENS[0]))
    raw["input"]["inbound_reply"] = "STOP"
    result = run_record(raw, config=OFFLINE)
    raw["expected"] = result.submission()
    assert raw["expected"]["next_message"] is None
    report = evaluate_record(raw, result)
    assert report["meaning_checks"] == {
        "status": "measured",
        "passed": True,
        "checks": [{"name": "no_message", "passed": True, "expected_meaning": "no automated message"}],
        "sample_count": 1,
    }


def test_unknown_assertion_and_threshold_are_visible_not_ignored():
    raw = json.loads(json.dumps(GOLDENS[0]))
    raw["assertions"]["required_states"].append("quantum_check")
    raw["assertions"]["constraints"]["quantum_constraint"] = True
    raw["thresholds"]["quantum_score_min"] = 0.5
    report = evaluate_record(raw, run_record(raw, config=OFFLINE))
    assert next(x for x in report["required_states"] if x["name"] == "quantum_check")["status"] == "unsupported"
    assert next(x for x in report["constraints"] if x["name"] == "quantum_constraint")["status"] == "unsupported"
    assert next(x for x in report["thresholds"] if x["name"] == "quantum_score_min")["status"] == "unsupported"


def test_personalization_proxy_uses_safe_relevant_coverage_and_labels_formula():
    rec = normalize(GOLDENS[1])
    generic = Draft("email", "Hi there,\nBook a tour. To opt out, click here or reply STOP.", "Book a tour", {"type": "schedule_tour", "link": "https://oakridge.example/tour"})
    score = personalization_proxy(rec, generic)
    assert score["score"] < GOLDENS[1]["thresholds"]["personalization_score_min"]
    assert {"profile.amenity_interest", "input.move_date_target"} <= set(score["opportunities"])
    assert "employer's scoring formula is unknown" in score["note"]


def test_below_threshold_model_falls_back_and_template_is_rechecked(monkeypatch):
    import casestudy.pipeline as pipeline
    from casestudy.writer import WriterOutput
    from casestudy.validators import validate_draft

    raw = GOLDENS[1]
    generic = Draft("email", "Hi there,\nBook now → https://oakridge.example/tour\nTo opt out of emails, click here or reply STOP.", "Book a tour", raw["expected"]["next_message"]["cta"], "model", "model.generic")

    def writer(outcome, schedule, intent, template, **kwargs):
        report = validate_draft(generic, outcome.record)
        assert report.passed
        return WriterOutput(generic, "model", report)

    monkeypatch.setattr(pipeline, "write", writer)
    result = pipeline.run_record(raw, config=OFFLINE)
    assert result.engine == "template"
    assert result.fallback_reason == "personalization below threshold"
    assert next(x for x in result.evaluation["thresholds"] if x["name"] == "personalization_score_min")["status"] == "passed"
    fallback = next(x for x in result.why if x.rule == "personalization.fallback")
    assert fallback.details["model_score"] < raw["thresholds"]["personalization_score_min"]
    assert fallback.details["template_score"] >= raw["thresholds"]["personalization_score_min"]


def test_reply_report_has_labeled_confusion_matrix_macro_f1_and_count():
    report = reply_metrics(REPLIES)
    assert report["status"] == "measured" and report["sample_count"] == 24
    assert report["dataset"] == "synthetic balanced reply corpus"
    assert report["macro_f1"] == 1.0
    assert set(report["confusion_matrix"]) == set(report["labels"])
    assert all(set(row) == set(report["labels"]) for row in report["confusion_matrix"].values())
    assert sum(sum(row.values()) for row in report["confusion_matrix"].values()) == 24


def test_latency_requires_and_measures_at_least_100_warm_runs():
    with pytest.raises(ValueError, match="at least 100"):
        offline_latency_metrics(GOLDENS, runs=99)
    report, results = offline_latency_metrics(GOLDENS, runs=100)
    assert report["status"] == "measured" and report["sample_count"] == len(results) == 100
    assert report["mode"] == "offline_warm_end_to_end"
    assert report["p95_latency_ms"] >= report["median_latency_ms"] >= 0
    assert report["fallback_count"] == 100 and report["failure_count"] == 0


def test_full_report_resolves_aggregate_thresholds_and_is_honest():
    report = evaluate_assignment(GOLDENS, REPLIES, runs=100)
    assert report["record_count"] == 2
    assert report["reply_classification"]["macro_f1"] == 1.0
    assert report["offline_latency"]["sample_count"] == 100
    assert report["live_model_latency"]["status"] == "not_measured"
    assert report["optional_tone_judge"]["status"] == "not_run"
    assert report["optional_tone_judge"]["gating"] is False
    for record in report["records"]:
        thresholds = {x["name"]: x for x in record["thresholds"]}
        assert thresholds["reply_classification_f1_min"]["status"] == "passed"
        assert thresholds["reply_classification_f1_min"]["sample_count"] == 24
        assert thresholds["p95_latency_ms"]["status"] == "passed"
        assert thresholds["p95_latency_ms"]["sample_count"] == 100
    assert report["binary_pass_fractions"]["structural_match"]["sample_count"] == 2
    assert report["binary_pass_fractions"]["meaning_checks"]["sample_count"] == 2
    assert "do not estimate real-world" in report["proven_vs_estimated"]


def test_full_report_evaluates_duplicate_task_ids_by_input_position():
    records = json.loads(json.dumps(GOLDENS))
    records[0]["input"].update({"cadence_days": 0, "flow": "welcome", "horizon": "short"})
    records[1]["input"].update({"cadence_days": 3, "flow": "open", "horizon": "long"})
    records[1]["task_id"] = records[0]["task_id"]
    report = evaluate_assignment(records, REPLIES, runs=100)
    assert len(report["records"]) == 2
    assert [row["structural_match"]["passed"] for row in report["records"]] == [True, True]
    assert [row["meaning_checks"]["passed"] for row in report["records"]] == [True, True]


def test_full_report_evaluates_inputs_beyond_timing_sample_coverage():
    records = []
    for index in range(101):
        raw = json.loads(json.dumps(GOLDENS[index % 2]))
        if index % 2:
            raw["input"].update({"cadence_days": 3, "flow": "open", "horizon": "long"})
        else:
            raw["input"].update({"cadence_days": 0, "flow": "welcome", "horizon": "short"})
        raw["task_id"] = f"position-{index}"
        records.append(raw)
    report = evaluate_assignment(records, REPLIES, runs=100)
    assert len(report["records"]) == 101
    assert all(row["structural_match"]["passed"] for row in report["records"])
    assert all(row["meaning_checks"]["passed"] for row in report["records"])


def test_wilson_is_only_a_binary_fraction_helper():
    assert wilson_interval(2, 2) == [0.3424, 1.0]
    assert wilson_interval(0, 0) is None
