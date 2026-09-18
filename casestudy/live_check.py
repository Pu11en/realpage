"""Run records through the real AI writer and compare each result with the record's answer key.

    python3 -m casestudy.live_check [input.jsonl]      # default: casestudy/data/sample.jsonl

Uses the production DeepSeek settings from Railway (`railway variables`), so each record is one
paid model call. The pipeline itself never sees the `expected` block; this script only reads it
afterwards to grade. Prints a plain-English report; never sends anything.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from casestudy.pipeline import run_batch
from casestudy.writer import WriterConfig

SMS_OPT_OUT = "Reply STOP to opt out."
EMAIL_OPT_OUT = "To opt out of emails, click here or reply STOP."


def railway_env() -> dict:
    out = subprocess.run(["railway", "variables", "--kv"], capture_output=True, text=True,
                         cwd=Path(__file__).parent, check=True).stdout
    env = dict(line.split("=", 1) for line in out.splitlines() if "=" in line)
    return {k: v for k, v in env.items() if k.startswith("DEEPSEEK_")}


def mark(ok) -> str:
    return "PASS" if ok else "FAIL"


def grade(got: dict, expected: dict) -> list[tuple[str, bool, str]]:
    rows = []
    gm, em = got.get("next_message"), expected.get("next_message")
    if em is None or gm is None:
        rows.append(("Send or not", (gm is None) == (em is None),
                     f"expected {'no message' if em is None else 'a message'}, got {'no message' if gm is None else 'a message'}"))
    else:
        rows.append(("Channel", gm.get("channel") == em.get("channel"), f"expected {em.get('channel')}, got {gm.get('channel')}"))
        rows.append(("Send time", gm.get("send_at") == em.get("send_at"), f"expected {em.get('send_at')}, got {gm.get('send_at')}"))
        rows.append(("Subject", (gm.get("subject") is None) == (em.get("subject") is None),
                     f"expected {em.get('subject')!r}, got {gm.get('subject')!r}"))
        rows.append(("CTA", gm.get("cta") == em.get("cta"), f"expected {em.get('cta')}, got {gm.get('cta')}"))
        body = gm.get("body") or ""
        line = SMS_OPT_OUT if gm.get("channel") == "sms" else EMAIL_OPT_OUT
        rows.append(("Opt-out line", line in body, f"needs {line!r}"))
        link = (em.get("cta") or {}).get("link")
        if link:
            rows.append(("Tour link in body", link in body, link))
    rows.append(("Next action", got.get("next_action") == expected.get("next_action"),
                 f"expected {expected.get('next_action')}, got {got.get('next_action')}"))
    return rows


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    path = Path(argv[0]) if argv else Path(__file__).parent / "data" / "sample.jsonl"
    lines = [l for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    config = WriterConfig.from_env(railway_env())
    results = run_batch(lines, config=config)
    for n, (line, r) in enumerate(zip(lines, results), 1):
        record = json.loads(line)
        got = json.loads(r.submission_line())
        print(f"\n=== Record {n}: {record.get('task_id')} ===")
        print(f"Engine: {r.engine}   Fallback: {r.fallback_reason or 'none'}   Errors: {r.errors or 'none'}")
        msg = got.get("next_message")
        if msg:
            print(f"Subject: {msg.get('subject')}")
            print(f"AI message:\n  {msg.get('body')}")
        expected = record.get("expected")
        if not expected:
            print("No answer key in this record.")
            continue
        if expected.get("next_message"):
            print(f"Answer-key message:\n  {expected['next_message'].get('body')}")
        for name, ok, detail in grade(got, expected):
            print(f"  [{mark(ok)}] {name}: {detail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
