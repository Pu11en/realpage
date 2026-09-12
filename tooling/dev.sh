#!/usr/bin/env bash
# One command for local PropertyStack development, no sign-in anywhere.
#   bash tooling/dev.sh         start (or refresh after code changes) and print the address
#   bash tooling/dev.sh stop    stop everything it started
# Site: http://localhost:8765 · chat app: http://localhost:3000 · bot: http://localhost:18080
# Needs DEEPSEEK_API_KEY in your shell; JINA_API_KEY is read from the repo's .env.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
COMPOSE=(docker compose -f chatbot/docker-compose.local.yml -f chatbot/docker-compose.dev.yml -p ps-chat)
PIDFILE=/tmp/ps-dev-site.pid

if [ "${1:-}" = stop ]; then
  "${COMPOSE[@]}" --env-file chatbot/.env.local down 2>/dev/null || "${COMPOSE[@]}" down
  fuser -k 8765/tcp >/dev/null 2>&1 || true; rm -f "$PIDFILE"
  echo "stopped"; exit 0
fi

: "${DEEPSEEK_API_KEY:?DEEPSEEK_API_KEY is not set in this shell}"
[ -f .env ] && export JINA_API_KEY="${JINA_API_KEY:-$(grep '^JINA_API_KEY=' .env | cut -d= -f2-)}"
ENVFILE=(); [ -f chatbot/.env.local ] && ENVFILE=(--env-file chatbot/.env.local)
"${COMPOSE[@]}" "${ENVFILE[@]}" up -d --build

# Always serve THIS checkout's site: stop any old copy (e.g. from a finished
# build run) that still holds the port and would show stale code.
fuser -k 8765/tcp >/dev/null 2>&1 || true; sleep 1
nohup python3 -m http.server 8765 -d "$ROOT/site" >/tmp/ps-dev-site.log 2>&1 &
echo $! > "$PIDFILE"

printf 'waiting for the chat app'
for _ in $(seq 1 60); do
  curl -sf -o /dev/null http://localhost:3000/api/config && curl -sf -o /dev/null http://localhost:18080/health && break
  printf '.'; sleep 3
done
echo
echo "Ready: open http://localhost:8765 and click Ask (no sign-in)."
