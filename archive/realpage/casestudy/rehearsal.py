"""Repeatable C13 rehearsal against the running case-study HTTP service.

The server used for this rehearsal must have no DeepSeek credentials.  The
configured-mode requests then prove the missing-key template fallback, while
the offline requests prove the explicit recovery switch.
"""
from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path
from typing import Any

from casestudy.contract import AssignmentAnswer

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "casestudy" / "data"


def _read_lines(path: Path, limit: int | None = None) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return lines if limit is None else lines[:limit]


def _request_json(url: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"} if data else {},
        method="POST" if data else "GET",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        if response.status != 200:
            raise RuntimeError(f"{url} returned HTTP {response.status}")
        return json.loads(response.read())


def _run_case(
    base_url: str,
    output_dir: Path,
    name: str,
    lines: list[str],
    *,
    offline: bool,
    malformed_index: int | None = None,
) -> dict[str, Any]:
    payload = _request_json(
        base_url.rstrip("/") + "/case-study/api/run",
        {"jsonl": "\n".join(lines) + "\n", "offline": offline},
    )
    if payload["record_count"] != len(lines):
        raise AssertionError(f"{name}: expected {len(lines)} records, got {payload['record_count']}")
    expected_mode = "offline" if offline else "configured"
    if payload["mode"] != expected_mode:
        raise AssertionError(f"{name}: expected mode {expected_mode}, got {payload['mode']}")

    exported = payload["submission_jsonl"]
    output_path = output_dir / f"{name}.jsonl"
    output_path.write_text(exported, encoding="utf-8")
    parsed_lines = output_path.read_text(encoding="utf-8").splitlines()
    if len(parsed_lines) != len(lines):
        raise AssertionError(f"{name}: saved export has {len(parsed_lines)} lines")

    rebuilt = "".join(record["submission_line"] + "\n" for record in payload["records"])
    if exported != rebuilt:
        raise AssertionError(f"{name}: batch bytes differ from per-record serializer bytes")
    for line in parsed_lines:
        AssignmentAnswer.model_validate_json(line)
    engines = {record["diagnostics"]["engine"] for record in payload["records"]}
    if not engines <= {"template", "none"}:
        raise AssertionError(f"{name}: unexpected engine(s) {sorted(engines)}; expected template or deterministic no-send")

    if malformed_index is not None:
        malformed = payload["records"][malformed_index]
        if not malformed["diagnostics"]["malformed"]:
            raise AssertionError(f"{name}: malformed middle row was not diagnosed")
        public = json.loads(malformed["submission_line"])
        if public["next_message"] is not None or public["next_action"]["type"] != "escalate":
            raise AssertionError(f"{name}: malformed middle row did not produce a safe escalation")

    diagnostics_path = output_dir / f"{name}.diagnostics.json"
    diagnostics_path.write_text(json.dumps(payload["records"], indent=2) + "\n", encoding="utf-8")
    return {"name": name, "records": len(lines), "mode": expected_mode, "export": str(output_path)}


def run_rehearsal(base_url: str, output_dir: Path) -> list[dict[str, Any]]:
    health = _request_json(base_url.rstrip("/") + "/health")
    if health != {"status": "ok"}:
        raise AssertionError(f"unexpected health response: {health!r}")
    output_dir.mkdir(parents=True, exist_ok=True)
    goldens = _read_lines(DATA / "sample.jsonl")
    practice = _read_lines(DATA / "practice.jsonl", 12)
    if len(goldens) != 2 or len(practice) != 12:
        raise AssertionError("rehearsal fixtures must contain 2 goldens and at least 12 practice rows")
    malformed = [goldens[0], "{not valid json", goldens[1]]
    cases = (
        ("goldens-configured", goldens, False, None),
        ("practice12-configured", practice, False, None),
        ("goldens-offline", goldens, True, None),
        ("practice12-offline", practice, True, None),
        ("malformed-middle-offline", malformed, True, 1),
    )
    return [
        _run_case(base_url, output_dir, name, lines, offline=offline, malformed_index=middle)
        for name, lines, offline, middle in cases
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rehearse the case-study HTTP service without live model calls")
    parser.add_argument("--base-url", default="http://127.0.0.1:18091")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    results = run_rehearsal(args.base_url, args.output_dir)
    for result in results:
        print(f"PASS {result['name']}: {result['records']} records, {result['mode']}, parsed {result['export']}")
    print(f"PASS full rehearsal: {sum(result['records'] for result in results)} record results checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
