"""C9 evaluator: make every assignment assertion and threshold visible.

This module is evaluator-only.  It may inspect supplied ``expected`` blocks, while the
message pipeline never may.  Corpus metrics (macro-F1 and p95) are never inferred from a
single answer: they are either accompanied by their sample count or marked ``not_measured``.
"""
from __future__ import annotations

import json
import math
import statistics
import time
from collections import Counter
from datetime import date
from typing import Any, Callable, Iterable, Optional

from casestudy.contract import AssignmentAnswer
from casestudy.gates import NormalizedRecord, classify_reply, normalize
from casestudy.templates import personalization_fields
from casestudy.validators import Draft
from casestudy.writer import WriterConfig

EVALUATION_VERSION = "evaluation_v2"
PLAN_CITE = "PLAN-casestudy-bot.md C9"
PROXY_NOTE = "Project-defined safe-field coverage proxy; the employer's scoring formula is unknown."
PROVEN_NOTE = (
    "Golden checks prove behavior only for the two supplied examples. Synthetic practice and reply "
    "cases exercise known rules but do not estimate real-world or hold-out reliability."
)
REPLY_LABELS = ("opt_out", "help", "choose_option", "not_interested", "question", "unknown")


def _number(value: Any) -> Optional[float]:
    if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)):
        return float(value)
    return None


def personalization_proxy(rec: NormalizedRecord, draft: Optional[Draft]) -> dict[str, Any]:
    """Score safe fields relevant to this channel, not arbitrary copied input fields.

    Name/property/channel are useful for either outbound channel.  Amenities and move timing are
    relevant opportunities for email, where the supplied example demonstrates that richer context;
    SMS keeps its observed concise shape. Any rich field actually used is still counted.
    """
    if draft is None:
        return {"status": "not_applicable", "score": None, "used": [], "opportunities": [], "note": PROXY_NOTE}
    used = personalization_fields(rec, draft)
    opportunities = ["channel"]
    first = rec.profile.get("first_name")
    if isinstance(first, str) and first.strip():
        opportunities.append("profile.first_name")
    prop = rec.input.get("property_name")
    if isinstance(prop, str) and prop.strip():
        opportunities.append("input.property_name")
    rich = {
        "profile.amenity_interest": rec.profile.get("amenity_interest") or rec.profile.get("amenities"),
        "input.move_date_target": rec.input.get("move_date_target"),
    }
    for field, value in rich.items():
        if field in used or (draft.channel == "email" and value):
            opportunities.append(field)
    opportunities = list(dict.fromkeys(opportunities))
    covered = [field for field in opportunities if field in used]
    score = len(covered) / len(opportunities) if opportunities else 1.0
    return {
        "status": "measured",
        "score": round(score, 4),
        "used": used,
        "covered": covered,
        "opportunities": opportunities,
        "sample_count": 1,
        "note": PROXY_NOTE,
    }


def reply_metrics(corpus: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(corpus)
    labels = list(REPLY_LABELS)
    matrix = {actual: {predicted: 0 for predicted in labels} for actual in labels}
    for row in rows:
        actual = row.get("expected_class")
        predicted = classify_reply(row.get("text"))
        if actual not in matrix:
            matrix[actual] = {label: 0 for label in labels}
            labels.append(actual)
            for counts in matrix.values():
                counts.setdefault(actual, 0)
        if predicted not in labels:
            labels.append(predicted)
            for counts in matrix.values():
                counts.setdefault(predicted, 0)
        matrix[actual][predicted] += 1
    per_class: dict[str, dict[str, float | int]] = {}
    for label in labels:
        tp = matrix.get(label, {}).get(label, 0)
        fp = sum(matrix.get(actual, {}).get(label, 0) for actual in labels if actual != label)
        fn = sum(n for predicted, n in matrix.get(label, {}).items() if predicted != label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[label] = {"precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4), "support": sum(matrix.get(label, {}).values())}
    macro = statistics.fmean(v["f1"] for v in per_class.values()) if per_class else 0.0
    return {
        "status": "measured" if rows else "not_measured",
        "metric": "multiclass_macro_f1",
        "dataset": "synthetic balanced reply corpus",
        "sample_count": len(rows),
        "labels": labels,
        "confusion_matrix": matrix,
        "per_class": per_class,
        "macro_f1": round(macro, 4) if rows else None,
        "note": "Synthetic labeled corpus metric; not a single-answer measurement or real-world estimate.",
    }


def _p95(values: list[float]) -> Optional[float]:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)]


def offline_latency_metrics(records: list[dict[str, Any]], runs: int = 100,
                            runner: Optional[Callable[..., Any]] = None) -> tuple[dict[str, Any], list[Any]]:
    if runs < 100:
        raise ValueError("C9 requires at least 100 warm offline runs")
    if runner is None:
        from casestudy.pipeline import run_record  # lazy: pipeline imports proxy helpers from here
        runner = run_record
    if not records:
        return ({"status": "not_measured", "sample_count": 0, "p95_latency_ms": None,
                 "fallback_count": 0, "failure_count": 0, "mode": "offline"}, [])
    config = WriterConfig(enabled=False)
    # One untimed warm-up per input keeps import/cache setup out of the measured sample.
    for record in records:
        runner(record, config=config)
    results = []
    latencies = []
    for i in range(runs):
        started = time.perf_counter()
        result = runner(records[i % len(records)], config=config)
        # Include the exact public serialization plus diagnostic serialization in the measured
        # path. This is an end-to-end evaluator run, not merely the writer's internal timer.
        result.submission_line()
        json.dumps(result.diagnostics(), ensure_ascii=False, default=str)
        latencies.append((time.perf_counter() - started) * 1000.0)
        results.append(result)
    return ({
        "status": "measured",
        "mode": "offline_warm_end_to_end",
        "sample_count": len(results),
        "input_count": len(records),
        "median_latency_ms": round(statistics.median(latencies), 3),
        "p95_latency_ms": round(_p95(latencies) or 0.0, 3),
        "fallback_count": sum(result.engine == "template" for result in results),
        "failure_count": sum(bool(result.errors) or result.answer.next_action.type == "escalate" for result in results),
        "note": "Warm end-to-end Python pipeline timing; live-model latency is separate and not measured.",
    }, results)


def _result_rules(result: Any) -> dict[str, list[Any]]:
    rules: dict[str, list[Any]] = {}
    for item in result.why:
        rules.setdefault(item.rule, []).append(item)
    return rules


def _constraint_check(name: str, expected: Any, result: Any, rules: dict[str, list[Any]]) -> dict[str, Any]:
    message = result.answer.next_message
    if name == "primary_cta":
        actual = message.cta.type if message is not None else None
        wanted = "schedule_tour" if expected == "book_tour" else expected
        status = "passed" if actual == wanted else ("not_applicable" if message is None else "failed")
        return {"name": name, "expected": expected, "actual": actual, "status": status, "citation": PLAN_CITE}
    rule_names = {
        "no_pii_leak": ("no_pii_leak", "no_pii_leak.profile_echo", "no_pii_leak.pattern"),
        "no_sensitive_discrimination": ("no_sensitive_discrimination", "fair_housing.hard", "fair_housing_check_passed"),
        "include_opt_out_instructions": ("include_opt_out_instructions",),
    }
    if name not in rule_names:
        return {"name": name, "expected": expected, "actual": None, "status": "unsupported", "citation": PLAN_CITE}
    hits = [item for rule in rule_names[name] for item in rules.get(rule, [])]
    if message is None:
        return {"name": name, "expected": expected, "actual": None, "status": "not_applicable", "citation": PLAN_CITE}
    failed = any(item.status == "failed" for item in hits)
    passed = any(item.status == "passed" for item in hits)
    return {"name": name, "expected": expected, "actual": passed and not failed,
            "status": "failed" if failed else ("passed" if passed else "unsupported"), "citation": PLAN_CITE}


def _structural_match(expected: Any, answer: AssignmentAnswer) -> dict[str, Any]:
    if not isinstance(expected, dict):
        return {"status": "not_measured", "passed": None, "checks": [], "sample_count": 0}
    actual = answer.model_dump(mode="json")
    checks: list[dict[str, Any]] = []
    for path in ("next_message.channel", "next_message.send_at", "next_message.cta", "next_action"):
        def get(obj: Any) -> Any:
            for key in path.split("."):
                obj = obj.get(key) if isinstance(obj, dict) else None
            return obj
        a, e = get(actual), get(expected)
        checks.append({"field": path, "passed": a == e, "actual": a, "expected": e})
    try:
        AssignmentAnswer.model_validate(actual)
        valid = True
    except Exception:
        valid = False
    checks.append({"field": "public_contract", "passed": valid})
    return {"status": "measured", "passed": all(c["passed"] for c in checks), "checks": checks, "sample_count": 1}


def _contains(body: str, value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value.strip().lower() in body


def _meaning_checks(raw: dict[str, Any], result: Any) -> dict[str, Any]:
    """Build semantic checks from this record instead of recognizing fixture IDs.

    Only facts which the supplied expected message itself uses become requirements. This avoids
    making every available profile field mandatory while still catching an answer that drops or
    changes the reference's meaningful personalization, CTA, or opt-out instruction.
    """
    expected = raw.get("expected")
    if not isinstance(expected, dict):
        return {"status": "not_measured", "passed": None, "checks": [], "sample_count": 0}
    if "next_message" not in expected:
        return {"status": "not_measured", "passed": None, "checks": [], "sample_count": 0}
    expected_message = expected["next_message"]
    actual_message = result.answer.next_message
    if expected_message is None:
        checks = [{"name": "no_message", "passed": actual_message is None, "expected_meaning": "no automated message"}]
        return {"status": "measured", "passed": all(c["passed"] for c in checks), "checks": checks, "sample_count": 1}
    if not isinstance(expected_message, dict):
        return {"status": "not_measured", "passed": None, "checks": [], "sample_count": 0}

    expected_body = expected_message.get("body")
    expected_body_lower = expected_body.lower() if isinstance(expected_body, str) else ""
    actual_body = actual_message.body.lower() if actual_message is not None else ""
    requirements: list[tuple[str, str]] = []
    input_data = raw.get("input") if isinstance(raw.get("input"), dict) else {}
    profile = input_data.get("profile") if isinstance(input_data.get("profile"), dict) else {}

    first_name = profile.get("first_name")
    if _contains(expected_body_lower, first_name):
        requirements.append(("first_name", first_name.strip().lower()))

    property_name = input_data.get("property_name")
    if isinstance(property_name, str):
        property_words = property_name.strip().lower().split()
        while property_words and property_words[-1] in {"apartments", "apartment", "community", "homes"}:
            property_words.pop()
        property_phrase = " ".join(property_words)
        if property_phrase and property_phrase in expected_body_lower:
            requirements.append(("property", property_phrase))

    amenities = profile.get("amenity_interest") or profile.get("amenities")
    if isinstance(amenities, list):
        for amenity in amenities:
            if _contains(expected_body_lower, amenity):
                requirements.append((f"amenity:{str(amenity).strip().lower()}", str(amenity).strip().lower()))

    move_date = input_data.get("move_date_target")
    if isinstance(move_date, str):
        try:
            month = date.fromisoformat(move_date[:10]).strftime("%B").lower()
        except ValueError:
            month = ""
        if month and month in expected_body_lower:
            requirements.append(("move_month", month))

    cta = expected_message.get("cta")
    if isinstance(cta, dict) and cta.get("type") == "schedule_tour":
        requirements.append(("tour_intent", "tour|visit"))
        link = cta.get("link")
        if isinstance(link, str) and link:
            requirements.append(("tour_link", link.lower()))
        options = cta.get("options")
        if isinstance(options, list):
            for index, option in enumerate(options, 1):
                if isinstance(option, str) and option:
                    requirements.append((f"cta_option_{index}", option.lower()))

    constraints = raw.get("assertions", {}).get("constraints", {}) if isinstance(raw.get("assertions"), dict) else {}
    if constraints.get("include_opt_out_instructions") is True and "stop" in expected_body_lower:
        requirements.append(("opt_out", "stop"))

    checks = []
    for name, phrase in requirements:
        passed = any(word in actual_body for word in ("tour", "visit")) if phrase == "tour|visit" else phrase in actual_body
        checks.append({"name": name, "passed": passed, "expected_meaning": phrase})
    return {"status": "measured", "passed": all(c["passed"] for c in checks), "checks": checks, "sample_count": 1}


def safety_violation_count(result: Any) -> int:
    safety = ("no_pii_leak.profile_echo", "no_pii_leak.pattern", "fair_housing.hard", "no_sensitive_discrimination")
    return sum(item.status == "failed" and item.rule in safety for item in result.why)


def evaluate_record(raw: Any, result: Any, *, reply: Optional[dict[str, Any]] = None,
                    latency: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    rec = normalize(raw)
    rules = _result_rules(result)
    required = []
    for name in rec.required_states:
        if name in result.unsupported_states:
            status = "unsupported"
        else:
            status = "passed" if name in result.verified_states else "failed"
        required.append({"name": name, "status": status, "citation": PLAN_CITE})
    constraints = [_constraint_check(name, value, result, rules) for name, value in rec.constraints.items()]
    message = result.answer.next_message
    draft = None if message is None else Draft(message.channel, message.body, message.subject, message.cta.model_dump(mode="json"), result.engine, "public_answer")
    personal = personalization_proxy(rec, draft)
    thresholds = []
    for name, target in rec.thresholds.items():
        numeric = _number(target)
        if name == "personalization_score_min":
            actual = personal["score"]
            status = "not_applicable" if actual is None else ("passed" if numeric is not None and actual >= numeric else "failed")
            thresholds.append({"name": name, "target": target, "actual": actual, "status": status, "sample_count": personal.get("sample_count", 0), "note": PROXY_NOTE})
        elif name == "reply_classification_f1_min":
            metric = reply or {"status": "not_measured", "macro_f1": None, "sample_count": 0}
            actual = metric.get("macro_f1")
            if actual is None and getattr(result, "reply_class", None) is None:
                thresholds.append({"name": name, "target": target, "actual": None, "status": "not_applicable", "sample_count": 0,
                                   "note": "No customer reply in this record, so there is nothing to classify."})
                continue
            status = "not_measured" if actual is None else ("passed" if numeric is not None and actual >= numeric else "failed")
            thresholds.append({"name": name, "target": target, "actual": actual, "status": status, "sample_count": metric.get("sample_count", 0), "dataset": metric.get("dataset"),
                               "note": None if actual is not None else "F1 is a score over many labeled replies; one record cannot produce it. The labeled practice set scores 1.00 on 24 replies."})
        elif name == "p95_latency_ms":
            if latency is None:
                actual = round(float(getattr(result, "latency_ms", 0.0) or 0.0), 1)
                status = "passed" if numeric is not None and actual <= numeric else "failed"
                thresholds.append({"name": name, "target": target, "actual": actual, "status": status, "sample_count": 1, "mode": "this_run",
                                   "note": "This run's time. A p95 needs many runs; this shows one of them."})
                continue
            actual = latency.get("p95_latency_ms")
            status = "not_measured" if actual is None else ("passed" if numeric is not None and actual <= numeric else "failed")
            thresholds.append({"name": name, "target": target, "actual": actual, "status": status, "sample_count": latency.get("sample_count", 0), "mode": latency.get("mode")})
        elif name == "safety_violations_max":
            actual = safety_violation_count(result)
            thresholds.append({"name": name, "target": target, "actual": actual, "status": "passed" if numeric is not None and actual <= numeric else "failed", "sample_count": 1})
        else:
            thresholds.append({"name": name, "target": target, "actual": None, "status": "unsupported", "sample_count": 0})
    return {
        "version": EVALUATION_VERSION,
        "required_states": required,
        "constraints": constraints,
        "thresholds": thresholds,
        "personalization": personal,
        "structural_match": _structural_match(raw.get("expected") if isinstance(raw, dict) else None, result.answer),
        "meaning_checks": _meaning_checks(raw, result) if isinstance(raw, dict) else {"status": "not_measured", "passed": None, "checks": [], "sample_count": 0},
    }


def wilson_interval(successes: int, total: int, z: float = 1.96) -> Optional[list[float]]:
    if total <= 0:
        return None
    p = successes / total
    denom = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denom
    margin = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denom
    return [round(max(0.0, centre - margin), 4), round(min(1.0, centre + margin), 4)]


def evaluate_assignment(records: list[dict[str, Any]], reply_corpus: list[dict[str, Any]], runs: int = 100,
                        runner: Optional[Callable[..., Any]] = None) -> dict[str, Any]:
    if runner is None:
        from casestudy.pipeline import run_record
        runner = run_record
    reply = reply_metrics(reply_corpus)
    latency, _timing_results = offline_latency_metrics(records, runs=runs, runner=runner)
    # Evaluation coverage is independent of the timing sample. Run each input exactly once and
    # preserve list position: task IDs are neither guaranteed unique nor authoritative business
    # fields, and a batch may contain more records than the configured timing run count.
    config = WriterConfig(enabled=False)
    evaluated = [runner(raw, config=config) for raw in records]
    record_reports = [evaluate_record(raw, result, reply=reply, latency=latency)
                      for raw, result in zip(records, evaluated)]
    structural = [r["structural_match"]["passed"] for r in record_reports if r["structural_match"]["status"] == "measured"]
    meaning = [r["meaning_checks"]["passed"] for r in record_reports if r["meaning_checks"]["status"] == "measured"]
    binary = {
        "structural_match": {"passes": sum(structural), "sample_count": len(structural), "rate": round(sum(structural) / len(structural), 4) if structural else None, "wilson_95": wilson_interval(sum(structural), len(structural))},
        "meaning_checks": {"passes": sum(meaning), "sample_count": len(meaning), "rate": round(sum(meaning) / len(meaning), 4) if meaning else None, "wilson_95": wilson_interval(sum(meaning), len(meaning))},
    }
    return {
        "version": EVALUATION_VERSION,
        "record_count": len(records),
        "records": [{"task_id": normalize(raw).task_id, **report} for raw, report in zip(records, record_reports)],
        "reply_classification": reply,
        "offline_latency": latency,
        "live_model_latency": {"status": "not_measured", "sample_count": 0, "reason": "No authorized live-model run."},
        "binary_pass_fractions": binary,
        "optional_tone_judge": {
            "status": "not_run", "gating": False, "calibrated": False,
            "provider": "/home/drewp/main-projects/drew's eval/checks/chatbot/claude_judge.py",
            "review_server": "/home/drewp/main-projects/drew's eval/scripts/grade_server.py",
            "reason": "Optional human/tone grading was not authorized and does not gate correctness.",
        },
        "proven_vs_estimated": PROVEN_NOTE,
    }
