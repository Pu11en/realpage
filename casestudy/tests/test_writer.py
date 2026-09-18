"""C6: bounded writer. No test touches the network; the client is a fake."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from casestudy import writer as w
from casestudy.gates import run_gates
from casestudy.intent import infer_intent
from casestudy.schedule import infer_schedule
from casestudy.templates import render_templates
from casestudy.writer import Deadline, WriterConfig, build_messages, verify_model, write

DATA = Path(__file__).resolve().parents[1] / "data"
SAMPLES = [json.loads(l) for l in (DATA / "sample.jsonl").read_text().splitlines() if l.strip()]
CFG = WriterConfig(api_key="test-key", model="deepseek-chat", base_url="https://example.invalid")


def _pipeline(raw):
    out = run_gates(raw)
    sched = infer_schedule(out)
    intent = infer_intent(out, sched)
    return out, sched, intent, render_templates(out, sched, intent)


class FakeClock:
    def __init__(self):
        self.t = 100.0

    def __call__(self):
        return self.t

    def advance_ms(self, ms):
        self.t += ms / 1000.0


class FakeClient:
    """Records calls; `behaviour` is a callable(kwargs) -> response or raises."""

    def __init__(self, behaviour, models=("deepseek-chat",)):
        self.calls = []
        self.behaviour = behaviour
        self.models = SimpleNamespace(list=lambda: SimpleNamespace(data=[SimpleNamespace(id=m) for m in models]))
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        return self.behaviour(kwargs)


def _resp(content, finish="stop"):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content), finish_reason=finish)])


def _good_json(intent, body, subject=None):
    return json.dumps({"subject": subject, "body": body, "cta": intent.cta})


@pytest.fixture(autouse=True)
def _clear_cache():
    w.reset_preflight_cache()
    yield
    w.reset_preflight_cache()


# ------------------------------------------------------------------ success

def test_successful_sms_draft_is_used():
    out, sched, intent, tpl = _pipeline(SAMPLES[0])
    body = "Hi Taylor—welcome to Oak Ridge! Want a tour? Reply 1 for Thu, 2 for Fri. Reply STOP to opt out."
    client = FakeClient(lambda k: _resp(_good_json(intent, body)))
    res = write(out, sched, intent, tpl, CFG, client=client)
    assert res.engine == "model" and res.draft.body == body and res.draft.source == "model"
    assert res.report.passed and res.fallback_reason is None
    assert len(client.calls) == 1
    call = client.calls[0]
    assert call["model"] == "deepseek-chat" and call["temperature"] == 0
    assert call["response_format"] == {"type": "json_object"}
    assert call["extra_body"] == {"thinking": {"type": "disabled"}}
    assert call["max_tokens"] == w.MAX_OUTPUT_TOKENS and 0 < call["timeout"] <= 8.0
    assert call["messages"][0]["role"] == "system" and call["messages"][-1]["role"] == "user"
    assert any(r.rule == "writer.preflight" and r.status == "passed" for r in res.results)


def test_successful_email_draft_is_used():
    out, sched, intent, tpl = _pipeline(SAMPLES[1])
    body = ("Hi Taylor,\nSince you're planning a mid-February move, here's a look at our pool and fitness center. "
            "Book now → https://oakridge.example/tour\nTo opt out of emails, click here or reply STOP.")
    client = FakeClient(lambda k: _resp(_good_json(intent, body, "Oak Ridge: pool and fitness center tour")))
    res = write(out, sched, intent, tpl, CFG, client=client)
    assert res.engine == "model" and res.draft.subject.startswith("Oak Ridge")


# ------------------------------------------------------------------ failure paths -> template

@pytest.mark.parametrize("behaviour,reason", [
    (lambda k: (_ for _ in ()).throw(TimeoutError("read timed out")), "model request failed"),
    (lambda k: _resp(""), "model returned empty content"),
    (lambda k: _resp(None), "model returned empty content"),
    (lambda k: _resp("{not json"), "model returned invalid JSON"),
    (lambda k: _resp('{"subject": null, "body": "x", "cta": {"type": "schedule_tour", "link": "https://evil.example"}}'), "model changed the CTA"),
    (lambda k: _resp('{"body": "x", "cta": {}, "extra": 1}'), "model JSON failed schema validation"),
    (lambda k: _resp('{"subject": null, "body": "Hi Taylor—welcome", "cta": {}}', finish="length"), "model output truncated at max_tokens"),
], ids=["timeout", "empty", "none", "invalid_json", "wrong_cta", "extra_key", "truncated"])
def test_bad_model_replies_fall_back_to_template(behaviour, reason):
    out, sched, intent, tpl = _pipeline(SAMPLES[0])
    client = FakeClient(behaviour)
    res = write(out, sched, intent, tpl, CFG, client=client)
    assert res.engine == "template" and res.draft is tpl.draft
    assert res.fallback_reason == reason
    assert len(client.calls) == 1  # never retried
    fb = [r for r in res.results if r.rule == "writer.fallback"]
    assert fb and fb[0].citation


def test_unsafe_model_draft_cannot_override_validator():
    out, sched, intent, tpl = _pipeline(SAMPLES[0])
    unsafe = "Hi Taylor—Oak Ridge is adults only and perfect for singles. Reply 1 for Thu, 2 for Fri. Reply STOP to opt out."
    client = FakeClient(lambda k: _resp(_good_json(intent, unsafe)))
    res = write(out, sched, intent, tpl, CFG, client=client)
    assert res.engine == "template" and res.fallback_reason == "model draft failed a hard validator rule"
    assert "fair_housing" in (res.error or "")
    assert "adults only" not in res.draft.body


def test_sms_without_stop_sentence_is_rejected():
    out, sched, intent, tpl = _pipeline(SAMPLES[0])
    client = FakeClient(lambda k: _resp(_good_json(intent, "Hi Taylor—tour Oak Ridge? Reply 1 for Thu, 2 for Fri.")))
    res = write(out, sched, intent, tpl, CFG, client=client)
    assert res.engine == "template" and "hard validator" in res.fallback_reason


# ------------------------------------------------------------------ deadline / budget

def test_budget_exhausted_before_call_skips_model():
    out, sched, intent, tpl = _pipeline(SAMPLES[0])
    client = FakeClient(lambda k: _resp("{}"))
    cfg = WriterConfig(api_key="k", model="deepseek-chat", budget_ms=400, reserve_ms=250)
    res = write(out, sched, intent, tpl, cfg, client=client)
    assert res.engine == "template" and res.fallback_reason == "budget exhausted before the model call"
    assert client.calls == []


def test_performance_target_does_not_shorten_the_hard_safety_timeout():
    out, _, _, _ = _pipeline(SAMPLES[0])
    assert w.record_budget_ms(out, WriterConfig(budget_ms=5000)) == 5000
    assert w.record_budget_ms(out, WriterConfig(budget_ms=1500)) == 1500


def test_slow_reply_after_deadline_is_discarded():
    out, sched, intent, tpl = _pipeline(SAMPLES[0])
    clock = FakeClock()

    def slow(k):
        clock.advance_ms(2500)
        return _resp(_good_json(intent, tpl.draft.body))

    client = FakeClient(slow)
    res = write(out, sched, intent, tpl, WriterConfig(api_key="k", model="deepseek-chat", budget_ms=2000), client=client, clock=clock)
    assert res.engine == "template" and res.fallback_reason == "deadline exceeded after the model reply"
    assert res.model_latency_ms == pytest.approx(2500) and res.latency_ms >= 2500


def test_deadline_is_monotonic_and_shared():
    clock = FakeClock()
    d = Deadline(1000, clock)
    assert d.remaining_ms() == 1000 and not d.exceeded
    clock.advance_ms(999)
    assert not d.exceeded
    clock.advance_ms(2)
    assert d.exceeded and d.remaining_ms() < 0


# ------------------------------------------------------------------ configuration / preflight

def test_offline_or_unconfigured_never_builds_a_client(monkeypatch):
    out, sched, intent, tpl = _pipeline(SAMPLES[0])
    monkeypatch.setattr(w, "make_client", lambda cfg: (_ for _ in ()).throw(AssertionError("network client built")))
    res = write(out, sched, intent, tpl, WriterConfig(api_key=None, model="deepseek-chat"))
    assert res.engine == "template" and "DEEPSEEK_API_KEY" in res.fallback_reason
    res = write(out, sched, intent, tpl, WriterConfig(api_key="k", model="deepseek-chat", enabled=False))
    assert res.engine == "template" and res.fallback_reason == "offline mode"


def test_config_from_env_has_no_guessed_model():
    cfg = WriterConfig.from_env({})
    assert cfg.model is None and cfg.api_key is None and not cfg.configured
    cfg = WriterConfig.from_env({"DEEPSEEK_API_KEY": "k", "DEEPSEEK_MODEL": "deepseek-chat", "CASESTUDY_OFFLINE": "1"})
    assert not cfg.enabled and not cfg.configured
    cfg = WriterConfig.from_env({"CASESTUDY_MODEL_BUDGET_MS": "6500"})
    assert cfg.budget_ms == 6500


def test_unverified_model_gets_no_request():
    out, sched, intent, tpl = _pipeline(SAMPLES[0])
    client = FakeClient(lambda k: _resp("{}"), models=("other-model",))
    res = write(out, sched, intent, tpl, CFG, client=client)
    assert res.engine == "template" and res.fallback_reason == "model not verified by preflight"
    assert client.calls == []
    assert any(r.rule == "writer.preflight" and r.status == "failed" for r in res.results)


def test_preflight_is_cached_and_survives_list_errors():
    calls = {"n": 0}

    def listing():
        calls["n"] += 1
        return SimpleNamespace(data=[SimpleNamespace(id="deepseek-chat")])

    client = SimpleNamespace(models=SimpleNamespace(list=listing))
    assert verify_model(client, CFG)[0] and verify_model(client, CFG)[0] and calls["n"] == 1
    w.reset_preflight_cache()
    broken = SimpleNamespace(models=SimpleNamespace(list=lambda: (_ for _ in ()).throw(ConnectionError("down"))))
    ok, why = verify_model(broken, CFG)
    assert not ok and "ConnectionError" in why


def test_client_is_built_with_retries_disabled(monkeypatch):
    captured = {}

    class FakeOpenAI:
        def __init__(self, **kw):
            captured.update(kw)

    import openai
    monkeypatch.setattr(openai, "OpenAI", FakeOpenAI)
    w.make_client(CFG)
    assert captured["max_retries"] == 0 and captured["base_url"] == CFG.base_url


# ------------------------------------------------------------------ prompt hygiene

def test_prompt_sends_only_approved_profile_fields_and_record_last():
    raw = json.loads(json.dumps(SAMPLES[1]))
    raw["input"]["profile"].update({"ssn": "123-45-6789", "income": 90000, "religion": "x"})
    out, sched, intent, tpl = _pipeline(raw)
    msgs = build_messages(out, sched, intent, tpl.draft)
    assert msgs[0]["content"] == w.SYSTEM_PREFIX  # stable prefix
    user = msgs[-1]["content"]
    assert "123-45-6789" not in user and "income" not in user and "religion" not in user
    assert "Taylor" in user and json.dumps(intent.cta, sort_keys=True)[:20] in json.dumps(json.loads(user.split("\n", 1)[1]), sort_keys=True)


def test_terminal_decision_never_calls_model():
    raw = json.loads(json.dumps(SAMPLES[0]))
    raw["input"]["inbound_reply"] = "STOP"
    out, sched, intent, tpl = _pipeline(raw)
    assert tpl.draft is None
    client = FakeClient(lambda k: _resp("{}"))
    res = write(out, sched, intent, tpl, CFG, client=client)
    assert res.engine == "none" and res.draft is None and client.calls == []
