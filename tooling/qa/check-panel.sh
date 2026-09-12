#!/usr/bin/env bash
# Self-contained check for the chat panel (PLAN-v6, Part W).
# Serves the site + a stand-in chat page on their own ports, runs sweep.py
# and panel_test.py against them, then kills both. Never touches Docker,
# Google, or the real bot. Exits non-zero on any bug. Under 2 minutes.
set -u
cd "$(dirname "$0")/../.."

# Picking a free port with a short-lived probe still leaves a race window,
# and this machine runs other sessions' servers concurrently, so a fixed
# default port can silently hit someone else's app instead of ours (seen:
# 8766/3001 collided with an unrelated Excalidraw server). Default to 0
# (kernel-assigned free port) unless the caller pins one explicitly.
SITE_PORT="${CHECK_SITE_PORT:-0}"
CHAT_PORT="${CHECK_CHAT_PORT:-0}"

free_port() {
  python3 -c 'import socket; s=socket.socket(); s.bind(("localhost",0)); print(s.getsockname()[1]); s.close()'
}

pick_port_and_serve() {
  local port="$1" dir="$2"
  if [ "$port" = "0" ]; then
    port=$(free_port)
  fi
  python3 -m http.server "$port" -d "$dir" >/dev/null 2>&1 &
  echo "$! $port"
}

pick_port_and_serve_fake_webui() {
  local port="$1"
  if [ "$port" = "0" ]; then
    port=$(free_port)
  fi
  python3 tooling/qa/fake-webui/server.py "$port" >/dev/null 2>&1 &
  echo "$! $port"
}

read -r SITE_PID SITE_PORT < <(pick_port_and_serve "$SITE_PORT" site)
read -r CHAT_PID CHAT_PORT < <(pick_port_and_serve_fake_webui "$CHAT_PORT")
trap 'kill "$SITE_PID" "$CHAT_PID" 2>/dev/null' EXIT

if [ -z "$SITE_PORT" ] || [ -z "$CHAT_PORT" ]; then
  echo "check-panel.sh: couldn't determine the port the server picked"
  exit 1
fi

ok=1
for _ in $(seq 1 30); do
  curl -sf "http://localhost:$SITE_PORT/index.html" 2>/dev/null | grep -q "PropertyStack\|chat-panel\|data-chat-toggle" \
    && curl -sf "http://localhost:$CHAT_PORT/index.html" 2>/dev/null | grep -q "fake-webui" \
    && { ok=0; break; }
  sleep 0.5
done
if [ "$ok" -ne 0 ]; then
  echo "check-panel.sh: site or fake-webui never came up (or another process is squatting on the port)"
  exit 1
fi

# quick-check.py, not the full sweep.py: sweep.py also checks every external
# link on the internet, which takes many minutes and doesn't work offline.
status=0
python3 tooling/qa/quick-check.py "http://localhost:$SITE_PORT" || status=1
python3 tooling/qa/panel_test.py "http://localhost:$SITE_PORT" "http://localhost:$CHAT_PORT" || status=1

exit "$status"
