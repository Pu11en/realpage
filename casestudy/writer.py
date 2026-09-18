"""C6: bounded model writer.

One optional structured DeepSeek call per record, through the OpenAI-compatible endpoint. The
writer proposes a draft; the C4 validators decide. Every failure path (missing key, unverified
model, exhausted budget, timeout, empty content, truncation, invalid JSON, wrong shape, wrong CTA,
unsafe draft) falls back to the already-validated C5 template and leaves a cited trail entry.

Guarantees:
  * Configuration, not constants: `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL`. The
    model name is verified against the endpoint's model list once (preflight) before the first
    live call; an unverified model never gets a request.
  * At most one model request per record. The SDK client is built with `max_retries=0`; the writer
    never re-asks the model.
  * One monotonic end-to-end safety deadline per record, configured separately from the record's
    `p95_latency_ms` performance target. A reserve for validation and serialization is subtracted
    before the call; if the remaining budget is too small the model is skipped, and a draft that
    arrives after the deadline is discarded. Performance targets stay visible in evaluation rather
    than silently changing the provider timeout.
  * Stable prompt prefix (system + rules) with the record last, `json_object` response format,
    temperature 0, and a small `max_tokens`; a `finish_reason == "length"` reply is treated as
    truncated and rejected rather than parsed.
  * Pydantic validation of the model JSON with extra keys forbidden; the CTA must equal the
    deterministic intent CTA byte-for-byte because the model never decides CTAs or actions.
  * The model only ever sees approved profile fields and business input; unsafe profile fields are
    not sent at all.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, ValidationError

from .gates import GateOutcome, GateResult
from .intent import Intent
from .schedule import Schedule
from .templates import TemplateOutput
from .validators import APPROVED_PROFILE_FIELDS, Draft, ValidationReport, validate_draft

WRITER_VERSION = "writer_v1"
PLAN_CITE = "PLAN-casestudy-bot.md C6"
ARCH_CITE = "PLAN architecture: one optional structured model call, no retries, deterministic validation"

DEFAULT_BASE_URL = "https://api.deepseek.com"
MAX_OUTPUT_TOKENS = 400        # small; SMS <= 3 segments and a short email fit well under this
DEFAULT_BUDGET_MS = 8000       # hard provider ceiling; p95_latency_ms remains an evaluation target
RESERVE_MS = 250               # kept back for validation + serialization (conservative_default)
MIN_MODEL_BUDGET_MS = 300      # below this the call is not worth starting


def _positive_int(value: Optional[str], default: int) -> int:
    try:
        parsed = int(value or "")
    except ValueError:
        return default
    return parsed if parsed > 0 else default


# --------------------------------------------------------------------------- config / deadline

@dataclass
class WriterConfig:
    api_key: Optional[str] = None
    base_url: str = DEFAULT_BASE_URL
    model: Optional[str] = None
    max_output_tokens: int = MAX_OUTPUT_TOKENS
    budget_ms: int = DEFAULT_BUDGET_MS
    reserve_ms: int = RESERVE_MS
    enabled: bool = True

    @classmethod
    def from_env(cls, env: Optional[dict[str, str]] = None) -> "WriterConfig":
        e = os.environ if env is None else env
        return cls(
            api_key=(e.get("DEEPSEEK_API_KEY") or None),
            base_url=(e.get("DEEPSEEK_BASE_URL") or DEFAULT_BASE_URL),
            model=(e.get("DEEPSEEK_MODEL") or None),
            budget_ms=_positive_int(e.get("CASESTUDY_MODEL_BUDGET_MS"), DEFAULT_BUDGET_MS),
            enabled=(e.get("CASESTUDY_OFFLINE", "").strip().lower() not in ("1", "true", "yes")),
        )

    @property
    def configured(self) -> bool:
        return self.enabled and bool(self.api_key) and bool(self.model)


class Deadline:
    """Monotonic per-record deadline shared by the model call, validation and serialization."""

    def __init__(self, budget_ms: int, clock=time.monotonic):
        self._clock = clock
        self.start = clock()
        self.budget_ms = max(0, int(budget_ms))

    def elapsed_ms(self) -> float:
        return (self._clock() - self.start) * 1000.0

    def remaining_ms(self) -> float:
        return self.budget_ms - self.elapsed_ms()

    @property
    def exceeded(self) -> bool:
        return self.remaining_ms() <= 0


def record_budget_ms(outcome: GateOutcome, config: WriterConfig) -> int:
    """Return the hard provider deadline; the record's p95 target is evaluated separately."""
    del outcome
    return config.budget_ms


# --------------------------------------------------------------------------- client / preflight

def make_client(config: WriterConfig):
    """OpenAI-compatible client with SDK retries disabled (one request per record)."""
    from openai import OpenAI  # imported lazily so offline runs never need the SDK

    return OpenAI(api_key=config.api_key, base_url=config.base_url, max_retries=0)


_PREFLIGHT: dict[tuple[str, str], tuple[bool, str]] = {}


def verify_model(client, config: WriterConfig, force: bool = False) -> tuple[bool, str]:
    """Preflight: confirm the configured model is served by the endpoint. Cached per (url, model)."""
    if not config.model:
        return False, "DEEPSEEK_MODEL is not set"
    key = (config.base_url, config.model)
    if key in _PREFLIGHT and not force:
        return _PREFLIGHT[key]
    try:
        listing = client.models.list()
        ids = {getattr(m, "id", None) for m in getattr(listing, "data", listing) or []}
    except Exception as exc:  # noqa: BLE001 - any endpoint failure means "not verified"
        result = (False, f"model list failed: {type(exc).__name__}: {exc}"[:200])
        _PREFLIGHT[key] = result
        return result
    if config.model in ids:
        result = (True, f"model {config.model!r} listed by {config.base_url}")
    else:
        result = (False, f"model {config.model!r} not in endpoint list {sorted(i for i in ids if i)[:10]}")
    _PREFLIGHT[key] = result
    return result


def reset_preflight_cache() -> None:
    _PREFLIGHT.clear()


# --------------------------------------------------------------------------- model output schema

class ModelDraft(BaseModel):
    """The only thing the model may return. Extra keys are rejected."""

    model_config = ConfigDict(extra="forbid")

    subject: Optional[str] = None
    body: str
    cta: dict[str, Any]


# --------------------------------------------------------------------------- prompt

SYSTEM_PREFIX = """You write one leasing follow-up message for an apartment community. Return only a JSON object with exactly these keys: "subject" (string or null), "body" (string), "cta" (copy the CTA object from the input unchanged).
Rules (violations are rejected by a validator, so follow them literally):
- Use only the facts in the input. Never invent prices, hours, links, amenities, or availability.
- SMS: subject must be null; one short question with the numbered options given; the body must end with the exact sentence "Reply STOP to opt out."; keep it under 300 characters.
- Email: subject must be a short, accurate non-null line; include the tour link from the CTA if one is given; end the body with the exact sentence "To opt out of emails, click here or reply STOP."
- Fair housing: describe the property and its features. Never describe who should live there, mention families, children, religion, national origin, disability, age, or any protected class, and never use words like "adults only".
- Personalize with the first name, property name, amenity interests and move timing when they are given. Do not mention any other personal detail.
- Keep the "cta" object exactly as given. Do not add keys.
"""


def _safe_profile(rec) -> dict[str, Any]:
    profile = rec.profile if isinstance(rec.profile, dict) else {}
    return {k: v for k, v in profile.items() if k in APPROVED_PROFILE_FIELDS}


def build_messages(outcome: GateOutcome, schedule: Schedule, intent: Intent, template: Optional[Draft]) -> list[dict[str, str]]:
    """Stable prefix first, record last (prompt-cache friendly). Only approved fields are sent."""
    rec = outcome.record
    inp = rec.input if isinstance(rec.input, dict) else {}
    record_view = {
        "channel": schedule.channel,
        "flow": intent.flow,
        "horizon": intent.horizon,
        "property_name": inp.get("property_name"),
        "move_date_target": inp.get("move_date_target"),
        "language": inp.get("language"),
        "tour_link": (intent.cta or {}).get("link"),
        "profile": _safe_profile(rec),
        "cta": intent.cta,
        "reference_draft": None if template is None else {"subject": template.subject, "body": template.body},
    }
    return [
        {"role": "system", "content": SYSTEM_PREFIX},
        {"role": "user", "content": "Input (JSON):\n" + json.dumps(record_view, ensure_ascii=False, sort_keys=True)},
    ]


# --------------------------------------------------------------------------- writer

@dataclass
class WriterOutput:
    draft: Optional[Draft]
    engine: str  # model | template | none
    report: Optional[ValidationReport]
    results: list[GateResult] = field(default_factory=list)
    latency_ms: Optional[float] = None
    model_latency_ms: Optional[float] = None
    error: Optional[str] = None
    fallback_reason: Optional[str] = None
    version: str = WRITER_VERSION


def _fallback(template: TemplateOutput, results: list[GateResult], reason: str, deadline: Deadline, error: Optional[str] = None, model_ms: Optional[float] = None) -> WriterOutput:
    results.append(GateResult("writer.fallback", "passed" if template.draft is not None else "failed",
                              f"validated template used instead of the model: {reason}", PLAN_CITE, "conservative_default",
                              {"reason": reason, "error": error}))
    engine = "template" if template.draft is not None else "none"
    return WriterOutput(template.draft, engine, template.report, results, deadline.elapsed_ms(), model_ms, error, reason)


def _content_of(response) -> tuple[Optional[str], Optional[str]]:
    choices = getattr(response, "choices", None) or []
    if not choices:
        return None, None
    ch = choices[0]
    msg = getattr(ch, "message", None)
    content = getattr(msg, "content", None) if msg is not None else None
    return content, getattr(ch, "finish_reason", None)


def write(outcome: GateOutcome, schedule: Schedule, intent: Intent, template: TemplateOutput,
          config: Optional[WriterConfig] = None, client=None, clock=time.monotonic) -> WriterOutput:
    """Propose a draft with at most one model request; otherwise return the validated template."""
    config = config or WriterConfig.from_env()
    deadline = Deadline(record_budget_ms(outcome, config), clock)
    results: list[GateResult] = []

    if template.draft is None:
        results.append(GateResult("writer", "skipped", "no template draft (terminal decision or call task); the model is never asked to invent one", ARCH_CITE, "conservative_default"))
        return WriterOutput(None, "none", None, results, deadline.elapsed_ms())
    if not config.configured:
        why = "offline mode" if not config.enabled else "DEEPSEEK_API_KEY or DEEPSEEK_MODEL not set"
        return _fallback(template, results, why, deadline)

    if client is None:
        try:
            client = make_client(config)
        except Exception as exc:  # noqa: BLE001
            return _fallback(template, results, "client construction failed", deadline, f"{type(exc).__name__}: {exc}")
    ok, why = verify_model(client, config)
    results.append(GateResult("writer.preflight", "passed" if ok else "failed", why, PLAN_CITE + ": preflight-verified model", "conservative_default", {"model": config.model, "base_url": config.base_url}))
    if not ok:
        return _fallback(template, results, "model not verified by preflight", deadline, why)

    remaining = deadline.remaining_ms() - config.reserve_ms
    if remaining < MIN_MODEL_BUDGET_MS:
        return _fallback(template, results, "budget exhausted before the model call", deadline,
                         f"remaining {deadline.remaining_ms():.0f} ms minus reserve {config.reserve_ms} ms")

    messages = build_messages(outcome, schedule, intent, template.draft)
    t0 = clock()
    try:
        response = client.chat.completions.create(
            model=config.model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=config.max_output_tokens,
            timeout=remaining / 1000.0,
        )
    except Exception as exc:  # noqa: BLE001 - timeouts, connection errors, API errors: all fall back
        model_ms = (clock() - t0) * 1000.0
        return _fallback(template, results, "model request failed", deadline, f"{type(exc).__name__}: {str(exc)[:160]}", model_ms)
    model_ms = (clock() - t0) * 1000.0
    results.append(GateResult("writer.request", "passed", f"one model request, {model_ms:.0f} ms, no retries", ARCH_CITE, "conservative_default", {"model": config.model, "latency_ms": round(model_ms)}))

    if deadline.remaining_ms() < config.reserve_ms:
        return _fallback(template, results, "deadline exceeded after the model reply", deadline, f"elapsed {deadline.elapsed_ms():.0f} ms of {deadline.budget_ms}", model_ms)

    content, finish = _content_of(response)
    if finish == "length":
        return _fallback(template, results, "model output truncated at max_tokens", deadline, f"finish_reason=length, max_tokens={config.max_output_tokens}", model_ms)
    if not content or not content.strip():
        return _fallback(template, results, "model returned empty content", deadline, f"finish_reason={finish}", model_ms)
    try:
        payload = json.loads(content)
    except ValueError as exc:
        return _fallback(template, results, "model returned invalid JSON", deadline, str(exc)[:160], model_ms)
    try:
        parsed = ModelDraft.model_validate(payload)
    except ValidationError as exc:
        return _fallback(template, results, "model JSON failed schema validation", deadline, str(exc.errors()[:3])[:200], model_ms)
    if parsed.cta != (intent.cta or {}):
        return _fallback(template, results, "model changed the CTA", deadline, f"expected {intent.cta}, got {parsed.cta}", model_ms)

    draft = Draft(schedule.channel, parsed.body, parsed.subject, intent.cta, source="model", label=f"model.{intent.flow}")
    report = validate_draft(draft, outcome.record)
    if not report.passed:
        return _fallback(template, results, "model draft failed a hard validator rule", deadline,
                         "; ".join(r.rule for r in report.hard_failures), model_ms)
    if deadline.exceeded:
        return _fallback(template, results, "deadline exceeded during validation", deadline, f"elapsed {deadline.elapsed_ms():.0f} ms", model_ms)
    results.append(GateResult("writer", "passed", "model draft passed every hard validator rule and the shared deadline", PLAN_CITE, "conservative_default", {"label": draft.label}))
    return WriterOutput(draft, "model", report, results, deadline.elapsed_ms(), model_ms)
