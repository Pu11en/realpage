#!/usr/bin/env python3
"""lead-finder entry point (stub -- Part 1.1 skeleton).

Area-agnostic: takes the state to run as an argument, never a literal in
code. Later tasks fill in the real chain (record format, fetch helper, run
folder/resume/caps, then Parts 2-4).
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone

from runfolder import RunFolder, pick_state


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", help="two-letter state code or slug to run")
    parser.add_argument("--run-id", help="resume an existing run folder")
    args = parser.parse_args(argv)

    if args.state:
        state = args.state
    else:
        pick = pick_state()
        state = pick["state"]
        print(f"picked state: {state} (backup order: {pick['backup_order']})")

    run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_folder = RunFolder(state=state, run_id=run_id)
    run_folder.ensure()
    print(f"lead-finder: run folder ready at {run_folder.path}")
    print("(chain steps not yet implemented, see PLAN-lead-finder-build.md)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
