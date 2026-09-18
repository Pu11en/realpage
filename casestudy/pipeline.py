"""C7: assemble one record into the public answer plus a separate diagnostics object, and run
JSONL batches.

Public path (`AssignmentAnswer`): exactly `{next_message, next_action}`; never a diagnostic key.
Diagnostics path (`RunResult.diagnostics()`): task_id, the cited `why` trail, verified and
unsupported states, reply class, personalization evidence, engine, errors, latency.

A malformed line (bad JSON, non-object, missing everything) never aborts the batch: it yields a
structured diagnostic and a safe public answer (`next_message: null`, `next_action.type:
"escalate"`). `expected` is never read by any stage; `run_record` strips it defensively anyway.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

from pydantic import ValidationError

from casestudy.contract import AssignmentAnswer
from casestudy.evaluation import evaluate_record, personalization_proxy
from casestudy.gates import GateOutcome, GateResult, run_gates
from casestudy.intent import Intent, infer_intent
from casestudy.schedule import Schedule, infer_schedule
from casestudy.templates import TemplateOutput, personalization_fields, render_templates
from casestudy.validators import Draft
from casestudy.writer import WriterConfig, WriterOutput, write

PIPELINE_VERSION = "pipeline_v1"
PLAN_CITE = "PLAN-casestudy-bot.md C7"
SHAPE_CITE = PLAN_CITE + ": no-message outcomes export next_message=null with a reason action (project-defined, not observed in sample.jsonl)"

# GateOutcome.decision / Schedule.kind -> public next_action type when no message is proposed
_NO_MESSAGE_ACTION = {"suppress": "suppress", "escalate": "escalate"}


@dataclass
class RunResult:
    task_id: str
    answer: AssignmentAnswer
    why: list[GateResult]
    decision: str
    engine: str  # model | template | none
    verified_states: list[str] = field(default_factory=list)
    unsupported_states: list[str] = field(default_factory=list)
    reply_class: Optional[str] = None
    personalization_fields: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    latency_ms: float = 0.0
    model_latency_ms: Optional[float] = None
    fallback_reason: Optional[str] = None
    malformed: bool = False
    versions: dict[str, str] = field(default_factory=dict)
    evaluation: dict[str, Any] = field(default_factory=dict)

    # ---- public path -------------------------------------------------------------
    def submission(self) -> dict[str, Any]:
        """Exactly the public shape; `mode="json"` so nothing non-JSON leaks."""
        return self.answer.model_dump(mode="json")

    def submission_line(self) -> str:
        return submission_line(self.answer)

    # ---- diagnostics path --------------------------------------------------------
    def diagnostics(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "decision": self.decision,
            "engine": self.engine,
            "malformed": self.malformed,
            "why": [
                {"rule": r.rule, "status": r.status, "plain_english": r.reason, "citation": r.citation,
                 "confidence": r.confidence, "details": _jsonable(r.details)}
                for r in self.why
            ],
            "verified_states": list(self.verified_states),
            "unsupported_states": list(self.unsupported_states),
            "reply_class": self.reply_class,
            "personalization_fields": list(self.personalization_fields),
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "latency_ms": round(self.latency_ms, 1),
            "model_latency_ms": None if self.model_latency_ms is None else round(self.model_latency_ms, 1),
            "fallback_reason": self.fallback_reason,
            "versions": dict(self.versions),
            "evaluation": _jsonable(self.evaluation),
        }


def submission_line(answer: AssignmentAnswer) -> str:
    """The one serializer every export (CLI, page, copy, download) must share."""
    return json.dumps(answer.model_dump(mode="json"), ensure_ascii=False, separators=(",", ":"))


def _jsonable(value: Any) -> Any:
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return json.loads(json.dumps(value, default=str))


def strip_expected(raw: Any) -> Any:
    """The engine must never see `expected`; it belongs to the evaluator only."""
    if isinstance(raw, dict) and "expected" in raw:
        return {k: v for k, v in raw.items() if k != "expected"}
    return raw


# --------------------------------------------------------------------------- one record

def _no_message_answer(action_type: str, reason: str) -> AssignmentAnswer:
    return AssignmentAnswer.model_validate({"next_message": None, "next_action": {"type": action_type, "reason": reason}})


def _assemble(outcome: GateOutcome, schedule: Schedule, intent: Intent, template: TemplateOutput,
              wo: WriterOutput, why: list[GateResult], errors: list[str]) -> AssignmentAnswer:
    if outcome.decision == "mark_opted_out":
        why.append(GateResult("assemble", "passed", "opt-out: no message, next_action mark_opted_out", "TCPA/CTIA honor STOP; " + SHAPE_CITE, "conservative_default"))
        return AssignmentAnswer.model_validate({"next_message": None, "next_action": intent.next_action})
    if not outcome.proceed:
        act = _NO_MESSAGE_ACTION.get(outcome.decision, "escalate")
        why.append(GateResult("assemble", "passed", f"gate decision {outcome.decision!r} ({outcome.reason}): no message; next_action {act}", SHAPE_CITE, "conservative_default", {"reason": outcome.reason}))
        return _no_message_answer(act, outcome.reason)
    if schedule.kind == "call_task":
        why.append(GateResult("assemble", "passed", "voice is the consented channel: a human call task is proposed, no automated message", "PLAN-casestudy-bot.md C2; " + SHAPE_CITE, "conservative_default"))
        return _no_message_answer("create_call_task", "voice_channel_selected")
    if wo.draft is None or schedule.send_at_iso is None or intent.cta is None or intent.next_action is None:
        missing = [n for n, v in (("draft", wo.draft), ("send_at", schedule.send_at_iso), ("cta", intent.cta), ("next_action", intent.next_action)) if v is None]
        errors.append("no_safe_message: missing " + ", ".join(missing))
        why.append(GateResult("assemble", "failed", f"could not compose a validated message (missing {', '.join(missing)}); escalating instead of guessing", SHAPE_CITE, "conservative_default", {"missing": missing}))
        return _no_message_answer("escalate", "no_validated_message")
    payload = {
        "next_message": {"channel": wo.draft.channel, "send_at": schedule.send_at_iso, "subject": wo.draft.subject,
                         "body": wo.draft.body, "cta": wo.draft.cta},
        "next_action": intent.next_action,
    }
    try:
        answer = AssignmentAnswer.model_validate(payload)
    except ValidationError as exc:
        errors.append("contract_violation: " + str(exc.errors()[:3])[:200])
        why.append(GateResult("assemble", "failed", "composed message violates the public contract; escalating", SHAPE_CITE, "conservative_default", {"errors": str(exc.errors()[:3])[:200]}))
        return _no_message_answer("escalate", "contract_violation")
    why.append(GateResult("assemble", "passed", f"public answer composed from the {wo.engine} draft; only next_message and next_action are exported", PLAN_CITE, "conservative_default", {"engine": wo.engine}))
    return answer


def run_record(raw: Any, config: Optional[WriterConfig] = None, client=None, clock=time.monotonic) -> RunResult:
    """Run every stage on one already-parsed record. Never raises."""
    t0 = clock()
    config = config or WriterConfig.from_env()
    why: list[GateResult] = []
    errors: list[str] = []
    raw = strip_expected(raw)
    task_id = raw.get("task_id") if isinstance(raw, dict) and isinstance(raw.get("task_id"), str) else "unknown_task"
    malformed = not isinstance(raw, dict)
    try:
        outcome = run_gates(raw)
        schedule = infer_schedule(outcome)
        intent = infer_intent(outcome, schedule)
        template = render_templates(outcome, schedule, intent)
        wo = write(outcome, schedule, intent, template, config=config, client=client, clock=clock)
        # A safe model draft can still be too generic for the record's declared personalization
        # threshold. In that case C9 requires the validated template fallback and a second check.
        threshold = rec.thresholds.get("personalization_score_min") if (rec := outcome.record) else None
        if wo.draft is not None and isinstance(threshold, (int, float)) and not isinstance(threshold, bool):
            proxy = personalization_proxy(rec, wo.draft)
            below = proxy["score"] is not None and proxy["score"] < float(threshold)
            if below and wo.engine == "model" and template.draft is not None:
                template_proxy = personalization_proxy(rec, template.draft)
                wo.results.append(GateResult(
                    "personalization.fallback", "passed" if template_proxy["score"] >= float(threshold) else "failed",
                    f"model proxy {proxy['score']:.4f} was below {float(threshold):.4f}; rechecked validated template proxy {template_proxy['score']:.4f}",
                    "PLAN-casestudy-bot.md C9", "conservative_default",
                    {"model_score": proxy["score"], "template_score": template_proxy["score"], "threshold": threshold},
                ))
                wo = WriterOutput(template.draft, "template", template.report, wo.results, wo.latency_ms,
                                  wo.model_latency_ms, wo.error, "personalization below threshold", wo.version)
            else:
                wo.results.append(GateResult(
                    "personalization.threshold", "failed" if below else "passed",
                    f"project proxy {proxy['score']:.4f} {'is below' if below else 'meets'} threshold {float(threshold):.4f}",
                    "PLAN-casestudy-bot.md C9; employer formula unknown", "conservative_default", proxy,
                ))
        why += outcome.results + schedule.results + intent.results + template.results + wo.results
        if wo.report is not None:
            why += wo.report.results
        if wo.error:
            errors.append("writer: " + wo.error)
        answer = _assemble(outcome, schedule, intent, template, wo, why, errors)
        rec = outcome.record
        final_message = answer.next_message
        final_personalization = []
        if rec is not None and final_message is not None:
            final_draft = Draft(
                channel=final_message.channel,
                subject=final_message.subject,
                body=final_message.body,
                cta=final_message.cta.model_dump(mode="json"),
                source=wo.engine,
                label="public_answer",
            )
            final_personalization = personalization_fields(rec, final_draft)
        final_verified = list(dict.fromkeys(
            list(outcome.verified_states) + (list(wo.report.verified_states) if wo.report is not None else [])
        ))
        result = RunResult(
            task_id=rec.task_id if rec else task_id, answer=answer, why=why, decision=outcome.decision, engine=wo.engine,
            verified_states=final_verified, unsupported_states=list(outcome.unsupported_states),
            reply_class=outcome.reply_class, personalization_fields=final_personalization,
            errors=errors, warnings=list(rec.warnings) if rec else [], latency_ms=(clock() - t0) * 1000.0,
            model_latency_ms=wo.model_latency_ms, fallback_reason=wo.fallback_reason, malformed=malformed,
            versions={"pipeline": PIPELINE_VERSION, "schedule": schedule.version, "intent": intent.version,
                      "templates": template.version, "writer": wo.version},
        )
        result.evaluation = evaluate_record(raw, result)
        return result
    except Exception as exc:  # noqa: BLE001 - one bad record must never abort the batch
        errors.append(f"internal_error: {type(exc).__name__}: {str(exc)[:160]}")
        why.append(GateResult("pipeline", "failed", "an internal error stopped this record; safe answer: escalate", PLAN_CITE + ": malformed records never abort the batch", "conservative_default", {"error": errors[-1]}))
        result = RunResult(task_id=task_id, answer=_no_message_answer("escalate", "internal_error"), why=why, decision="escalate",
                           engine="none", errors=errors, latency_ms=(clock() - t0) * 1000.0, malformed=True,
                           versions={"pipeline": PIPELINE_VERSION})
        result.evaluation = evaluate_record(raw, result)
        return result


def run_line(line: str, index: int, config: Optional[WriterConfig] = None, client=None, clock=time.monotonic) -> RunResult:
    """Parse one JSONL line and run it; unparseable lines yield a diagnostic plus a safe answer."""
    if not line.strip():
        line_number = index + 1
        why = [GateResult("parse", "failed", f"line {line_number} is blank", PLAN_CITE + ": one safe answer per input line", "conservative_default", {"line": line_number})]
        return RunResult(task_id=f"malformed_line_{line_number}", answer=_no_message_answer("escalate", "blank_input"), why=why,
                         decision="escalate", engine="none", errors=["blank_input: input line is blank"], malformed=True,
                         versions={"pipeline": PIPELINE_VERSION})
    try:
        raw = json.loads(line)
    except ValueError as exc:
        why = [GateResult("parse", "failed", f"line {index + 1} is not valid JSON: {str(exc)[:120]}", PLAN_CITE + ": malformed records never abort the batch", "conservative_default", {"line": index + 1})]
        return RunResult(task_id=f"malformed_line_{index + 1}", answer=_no_message_answer("escalate", "malformed_json"), why=why,
                         decision="escalate", engine="none", errors=[f"malformed_json: {str(exc)[:120]}"], malformed=True,
                         versions={"pipeline": PIPELINE_VERSION})
    return run_record(raw, config=config, client=client, clock=clock)


# --------------------------------------------------------------------------- batch

def run_batch(lines: Iterable[str], config: Optional[WriterConfig] = None, client=None, clock=time.monotonic) -> list[RunResult]:
    """One safe RunResult per input line, including blank lines, in input order."""
    config = config or WriterConfig.from_env()
    results: list[RunResult] = []
    for i, line in enumerate(lines):
        results.append(run_line(line, i, config=config, client=client, clock=clock))
    return results


def submission_jsonl(results: Iterable[RunResult]) -> str:
    return "".join(r.submission_line() + "\n" for r in results)


def diagnostics_jsonl(results: Iterable[RunResult]) -> str:
    return "".join(json.dumps(r.diagnostics(), ensure_ascii=False, default=str) + "\n" for r in results)
