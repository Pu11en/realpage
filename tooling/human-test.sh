#!/usr/bin/env bash
# Start a fresh, sign-in-enabled CraneSignal candidate for a real human test.
#
#   bash tooling/human-test.sh       start a fresh private preview
#   bash tooling/human-test.sh stop  stop it and remove only its private state
#   bash tooling/human-test.sh check verify this command's offline safeguards
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PROJECT="cranesignal-human-test"
MAIN_ROOT="$(cd "$(git -C "$ROOT" rev-parse --path-format=absolute --git-common-dir)/.." && pwd)"
LANDING_DIR="$MAIN_ROOT/business/marketing/landing"
export CRANESIGNAL_LANDING_DIR="$LANDING_DIR"
COMPOSE=(docker compose -p "$PROJECT" -f chatbot/docker-compose.local.yml -f chatbot/docker-compose.human-test.yml)

offline_check() {
  local overlay="chatbot/docker-compose.human-test.yml"
  grep -Fq 'PROJECT="cranesignal-human-test"' "$0"
  grep -Fq -- '--volumes --remove-orphans' "$0"
  grep -Fq 'name: cranesignal-human-test-open-webui' "$overlay"
  grep -Fq 'name: cranesignal-human-test-hermes-home' "$overlay"
  grep -Fq 'WEBUI_AUTH: "True"' "$overlay"
  grep -Fq 'ENABLE_SIGNUP: "true"' "$overlay"
  grep -Fq 'ENABLE_LOGIN_FORM: "true"' "$overlay"
  grep -Fq '"8876:8080"' "$overlay"
  grep -Fq 'ports: !reset []' "$overlay"
  grep -Fq 'APP_URL: http://localhost:8876' "$overlay"
  grep -Fq 'LANDING_DIR="$MAIN_ROOT/business/marketing/landing"' "$0"
  grep -Fq 'context: ${CRANESIGNAL_LANDING_DIR}' "$overlay"
  grep -Fq 'name: cranesignal-human-test-landing-data' "$overlay"
  printf 'Human preview starts on the real landing page, then opens an isolated signed-in app.\n'
}

case "${1:-start}" in
  check)
    offline_check
    exit 0
    ;;
  stop)
    "${COMPOSE[@]}" down --volumes --remove-orphans
    echo "Stopped the landing page and private app preview, and removed only its fresh test accounts and chats."
    exit 0
    ;;
  start)
    ;;
  *)
    echo "Usage: bash tooling/human-test.sh [stop|check]" >&2
    exit 2
    ;;
esac

if [ -z "${DEEPSEEK_API_KEY:-}" ]; then
  echo "DEEPSEEK_API_KEY is not available in this shell. Nothing was started or changed."
  echo "Export the existing key, then run: bash tooling/human-test.sh"
  exit 1
fi

if [ ! -f "$LANDING_DIR/index.html" ] || [ ! -f "$LANDING_DIR/server.py" ]; then
  echo "The CraneSignal landing page is missing from $LANDING_DIR. Nothing was started."
  exit 1
fi

echo "Preparing the CraneSignal landing page and a fresh private app preview..."
# This project and these two named volumes are used nowhere else.  Clearing
# them makes every start a first-time-account test without touching ps-chat.
"${COMPOSE[@]}" down --volumes --remove-orphans

for port in 8765 8876; do
  if fuser "$port/tcp" >/dev/null 2>&1; then
    echo "Port $port is already in use by something outside this preview. Nothing was started."
    exit 1
  fi
done

"${COMPOSE[@]}" up -d --build

printf 'Waiting for CraneSignal'
for _ in $(seq 1 60); do
  if curl -sf http://localhost:8765/ | grep -q 'New apartment buildings' && \
     curl -sf -o /dev/null http://localhost:8876/privacy.html && \
     curl -sf -o /dev/null http://localhost:8876/auth; then
    echo
    echo "Ready: http://localhost:8765"
    echo "This starts on the CraneSignal landing page. Start free opens the private local app."
    echo "Sign-in is on there. Create a new local account; it is separate from your usual preview."
    echo "Stop when finished: bash tooling/human-test.sh stop"
    exit 0
  fi
  printf '.'
  sleep 2
done

echo
echo "The preview did not become ready in two minutes. It is still isolated."
echo "Inspect with: docker compose -p $PROJECT -f chatbot/docker-compose.local.yml -f chatbot/docker-compose.human-test.yml ps"
exit 1
