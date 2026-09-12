#!/usr/bin/env bash
# Self-contained site check for /gowork: switch the site on, run the quick check, switch it off.
# Uses its own port so it never clashes with a copy you already have running on 8765.
set -u
cd "$(dirname "$0")/../.."
PORT="${CHECK_PORT:-8799}"
python3 -m http.server "$PORT" -d site >/dev/null 2>&1 &
SERVER=$!
trap 'kill "$SERVER" 2>/dev/null' EXIT
for _ in $(seq 1 30); do
  curl -sf "http://localhost:$PORT/index.html" >/dev/null && break
  sleep 0.5
done
python3 tooling/qa/quick-check.py "http://localhost:$PORT"
