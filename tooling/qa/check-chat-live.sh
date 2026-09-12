#!/usr/bin/env bash
# Drew's one-command local test for the PropertyStack panel.
#
#   bash tooling/qa/check-chat-live.sh
#
# Requires the chat stack to be up (it uses the real AI, so it makes real bot
# calls, a few cents):
#   docker compose -f chatbot/docker-compose.local.yml --env-file chatbot/.env.local -p ps-chat up -d
#
# Serves the site on 8766 if nothing is already on 8765, then drives the real
# panel in a browser and checks the answers against Drew's approved facts.
# Prints PASS/FAIL and exits non-zero on any failure. Takes about 1 minute.
set -uo pipefail

cd "$(dirname "$0")/../.."

CHAT_URL="${CHAT_URL:-http://localhost:3000}"
SITE_PORT=8766
STARTED_SITE=""

cleanup() {
  if [ -n "$STARTED_SITE" ]; then
    kill "$STARTED_SITE" 2>/dev/null || true
  fi
}
trap cleanup EXIT

if ! curl -sf -o /dev/null "$CHAT_URL/api/config"; then
  echo "The chat app is not up at $CHAT_URL."
  echo "Start it with:"
  echo "  docker compose -f chatbot/docker-compose.local.yml --env-file chatbot/.env.local -p ps-chat up -d"
  exit 1
fi

# Prefer Drew's already-running site on 8765; otherwise serve a throwaway one.
if curl -sf -o /dev/null "http://localhost:8765/master-table.html"; then
  SITE_PORT=8765
else
  python3 -m http.server "$SITE_PORT" -d site >/dev/null 2>&1 &
  STARTED_SITE=$!
  sleep 1
fi

echo "Checking the real panel on http://localhost:$SITE_PORT against $CHAT_URL ..."
echo
python3 tooling/qa/check-chat-live.py "$SITE_PORT" "$CHAT_URL"
