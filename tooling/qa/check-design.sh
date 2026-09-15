#!/usr/bin/env bash
# Check for PLAN-app-redesign: switch the site on (own port), run the quick site check
# (pages load, no script errors, no sideways scroll on phones) and the design check, switch it off.
set -u
cd "$(dirname "$0")/../.."
PORT="${CHECK_PORT:-8781}"
python3 -m http.server "$PORT" -d site >/dev/null 2>&1 &
SERVER=$!
trap 'kill "$SERVER" 2>/dev/null' EXIT
for _ in $(seq 1 30); do
  curl -sf "http://localhost:$PORT/index.html" >/dev/null && break
  sleep 0.5
done
python3 tooling/qa/quick-check.py "http://localhost:$PORT" || exit 1
python3 tooling/qa/design_check.py "http://localhost:$PORT"
