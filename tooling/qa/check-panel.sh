#!/usr/bin/env bash
# Self-contained check for the chat panel (PLAN-v6, Part W).
# Serves the site + a stand-in chat page on their own ports, runs sweep.py
# and panel_test.py against them, then kills both. Never touches Docker,
# Google, or the real bot. Exits non-zero on any bug. Under 2 minutes.
set -u
cd "$(dirname "$0")/../.."

SITE_PORT="${CHECK_SITE_PORT:-8766}"
CHAT_PORT="${CHECK_CHAT_PORT:-3001}"

python3 -m http.server "$SITE_PORT" -d site >/dev/null 2>&1 &
SITE_PID=$!
python3 -m http.server "$CHAT_PORT" -d tooling/qa/fake-webui >/dev/null 2>&1 &
CHAT_PID=$!
trap 'kill "$SITE_PID" "$CHAT_PID" 2>/dev/null' EXIT

ok=1
for _ in $(seq 1 30); do
  curl -sf "http://localhost:$SITE_PORT/index.html" >/dev/null && curl -sf "http://localhost:$CHAT_PORT/index.html" >/dev/null && { ok=0; break; }
  sleep 0.5
done
if [ "$ok" -ne 0 ]; then
  echo "check-panel.sh: site or fake-webui never came up"
  exit 1
fi

# quick-check.py, not the full sweep.py: sweep.py also checks every external
# link on the internet, which takes many minutes and doesn't work offline.
status=0
python3 tooling/qa/quick-check.py "http://localhost:$SITE_PORT" || status=1
python3 tooling/qa/panel_test.py "http://localhost:$SITE_PORT" "http://localhost:$CHAT_PORT" || status=1

exit "$status"
