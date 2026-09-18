"""Command line: read assignment JSONL, write submission JSONL and (optionally) diagnostics JSONL.

    python3 -m casestudy.cli input.jsonl --offline --submission-out out.jsonl --diagnostics-out diag.jsonl

Never sends anything; never pushes or deploys. `--offline` forces the validated templates.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from casestudy.pipeline import diagnostics_jsonl, run_batch, submission_jsonl
from casestudy.writer import WriterConfig


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="casestudy", description="Case-study message agent: JSONL in, submission JSONL out.")
    p.add_argument("input", nargs="?", default="-", help="input JSONL path, or - for stdin (default)")
    p.add_argument("--offline", action="store_true", help="never call the model; use validated templates")
    p.add_argument("--submission-out", metavar="PATH", help="write public submission JSONL here (default: stdout)")
    p.add_argument("--diagnostics-out", metavar="PATH", help="write per-record diagnostics JSONL here")
    return p


def main(argv=None, stdin=None, stdout=None) -> int:
    args = build_parser().parse_args(argv)
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    text = stdin.read() if args.input == "-" else Path(args.input).read_text(encoding="utf-8")
    env = dict(os.environ)
    if args.offline:
        env["CASESTUDY_OFFLINE"] = "1"
    results = run_batch(text.splitlines(), config=WriterConfig.from_env(env))
    sub = submission_jsonl(results)
    if args.submission_out:
        Path(args.submission_out).write_text(sub, encoding="utf-8")
    else:
        stdout.write(sub)
    if args.diagnostics_out:
        Path(args.diagnostics_out).write_text(diagnostics_jsonl(results), encoding="utf-8")
    failed = sum(1 for r in results if r.errors)
    print(f"{len(results)} record(s); {failed} with errors; engines: " + ", ".join(sorted({r.engine for r in results})), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
