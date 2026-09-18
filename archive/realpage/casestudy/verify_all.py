"""Final verification: run every known record through the live pipeline and check hard rules on every answer.

    python3 -m casestudy.verify_all            # live AI (Railway settings); one paid call per message
    python3 -m casestudy.verify_all --offline  # templates only, free

Rules checked on EVERY output (independent of the pipeline's own validators):
  shape, consent for the chosen channel, SMS subject null + STOP line, email subject + opt-out line,
  exact CTA link in email body, send time inside 09:00-20:00 customer-local and after last contact,
  no sensitive profile values in the text, opt-out replies produce mark_opted_out, and answer-key /
  practice-expectation matches where they exist.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from casestudy.gates import classify_reply
from casestudy.pipeline import run_batch
from casestudy.writer import WriterConfig

DATA = Path(__file__).parent / "data"
FILES = ["sample.jsonl", "practice.jsonl", "curveballs.jsonl", "curveballs2.jsonl", "hidden_guess.jsonl",
         "holdout_practice.jsonl", "holdout_practice_2.jsonl", "astra_predicted_holdout.jsonl"]
SENSITIVE = {"phone", "email", "last_name", "income", "street_address", "religion", "familial_status", "age",
             "accommodation", "ssn"}
CH_KEY = {"sms": "sms_opt_in", "email": "email_opt_in", "voice": "voice_opt_in"}


def check(raw, answer, practice_exp, use_key=True):
    problems = []
    if set(answer) != {"next_message", "next_action"}:
        problems.append(f"shape {sorted(answer)}")
    m, act = answer.get("next_message"), answer.get("next_action") or {}
    if not isinstance(raw, dict):
        return problems
    consent = raw.get("consent") or {}
    inp = raw.get("input") or {}
    reply = inp.get("inbound_reply") or raw.get("inbound_reply")
    if reply and classify_reply(reply) == "opt_out" and act.get("type") != "mark_opted_out":
        problems.append("opt-out reply not honored")
    if m:
        if consent.get(CH_KEY.get(m["channel"], "")) is not True:
            problems.append(f"sent {m['channel']} without boolean consent")
        body = m.get("body") or ""
        if m["channel"] == "sms":
            if m.get("subject") is not None:
                problems.append("sms has subject")
            if not body.rstrip().endswith("Reply STOP to opt out."):
                problems.append("sms missing STOP line")
        if m["channel"] == "email":
            if not m.get("subject"):
                problems.append("email missing subject")
            if "To opt out of emails, click here or reply STOP." not in body:
                problems.append("email missing opt-out line")
            link = (m.get("cta") or {}).get("link")
            if link and link not in body:
                problems.append("email body missing exact CTA link")
        try:
            tz = ZoneInfo(inp["timezone"])
            at = datetime.fromisoformat(m["send_at"]).astimezone(tz)
            if not (9 <= at.hour < 20 or (at.hour == 20 and at.minute == 0)):
                problems.append(f"send time {at:%a %H:%M} outside 09-20 local")
            last = inp.get("last_interaction")
            if last and at <= datetime.fromisoformat(last.replace("Z", "+00:00")):
                problems.append("send time not after last contact")
        except Exception as exc:  # noqa: BLE001
            problems.append(f"send time unreadable: {exc}")
        prof = inp.get("profile") or {}
        for k, v in prof.items():
            if k in SENSITIVE and isinstance(v, str) and len(v) > 2 and v.lower() in body.lower():
                problems.append(f"sensitive {k} leaked")
    exp = raw.get("expected") if use_key else None
    if exp:
        em = exp.get("next_message")
        if (m is None) != (em is None):
            problems.append("answer key: send/no-send differs")
        elif m and em:
            for k in ("channel", "send_at", "cta"):
                if m.get(k) != em.get(k):
                    problems.append(f"answer key: {k} differs")
        if act != exp.get("next_action"):
            problems.append("answer key: next_action differs")
    if practice_exp:
        st = practice_exp.get("expected_structure", {})
        if "has_message" in st and bool(m) != st["has_message"]:
            problems.append("practice: send/no-send differs")
        if "next_action" in st and act != st["next_action"]:
            problems.append(f"practice: next_action {act} != {st['next_action']}")
        if m and st.get("channel") and m["channel"] != st["channel"]:
            problems.append("practice: channel differs")
    return problems


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--offline" in argv:
        config = WriterConfig(enabled=False)
    else:
        from casestudy.live_check import railway_env
        config = WriterConfig.from_env(railway_env())
    exps = {json.loads(l)["task_id"]: json.loads(l) for l in (DATA / "practice_expectations.jsonl").read_text().splitlines() if l.strip()}
    total = bad = ai = fallback = 0
    for f in FILES:
        lines = [l for l in (DATA / f).read_text(encoding="utf-8").splitlines() if l.strip()]
        for line, r in zip(lines, run_batch(lines, config=config)):
            total += 1
            ai += r.engine == "model"
            fallback += r.engine == "template"
            try:
                raw = json.loads(line)
            except ValueError:
                raw = None
            answer = json.loads(r.submission_line())
            probs = check(raw, answer, exps.get(r.task_id) if f == "practice.jsonl" else None, use_key=f != "astra_predicted_holdout.jsonl")  # Astra's key is a guess, rules still apply
            if raw is None and answer["next_action"].get("type") != "escalate":
                probs.append("broken record not escalated")
            if probs:
                bad += 1
                print(f"FAIL {f} {r.task_id}: {'; '.join(probs)}")
    print(f"\n{total} records checked; {bad} with problems; AI wording used {ai}; checked backup used {fallback}.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
