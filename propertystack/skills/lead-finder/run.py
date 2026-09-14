#!/usr/bin/env python3
"""lead-finder entry point (stub -- Part 1.1 skeleton).

Area-agnostic: takes the state to run as an argument, never a literal in
code. Later tasks fill in the real chain (record format, fetch helper, run
folder/resume/caps, then Parts 2-4).
"""
from __future__ import annotations

import argparse


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", help="two-letter state code or slug to run")
    parser.add_argument("--run-id", help="resume an existing run folder")
    parser.parse_args(argv)
    print("lead-finder: not yet implemented (skeleton only, see PLAN-lead-finder-build.md)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
