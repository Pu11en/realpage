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
  grep -Fq '"8765:8080"' "$overlay"
  grep -Fq 'ports: !reset []' "$overlay"
  printf 'Human preview command is isolated, starts with sign-in enabled, and uses localhost:8765.\n'
}

case "${1:-start}" in
  check)
    offline_check
    exit 0
    ;;
  stop)
    "${COMPOSE[@]}" down --volumes --remove-orphans
    echo "Stopped the private human-test preview and removed only its fresh test accounts and chats."
    exit 0
    ;;
  start)
    ;;
  *)
    echo "Usage: bash tooling/human-test.sh [stop|check]" >&2
    exit 2
    ;;
esac

if fuser 8765/tcp >/dev/null 2>&1; then
  echo "Port 8765 is already in use. Nothing was stopped or changed."
  echo "Stop the process using that port, then run: bash tooling/human-test.sh"
  exit 1
fi

if [ -z "${DEEPSEEK_API_KEY:-}" ]; then
  echo "DEEPSEEK_API_KEY is not available in this shell. Nothing was started or changed."
  echo "Export the existing key, then run: bash tooling/human-test.sh"
  exit 1
fi

echo "Preparing a fresh private CraneSignal preview with sign-in enabled..."
# This project and these two named volumes are used nowhere else.  Clearing
# them makes every start a first-time-account test without touching ps-chat.
"${COMPOSE[@]}" down --volumes --remove-orphans
"${COMPOSE[@]}" up -d --build

printf 'Waiting for CraneSignal'
for _ in $(seq 1 60); do
  if curl -sf -o /dev/null http://localhost:8765/privacy.html && \
     curl -sf -o /dev/null http://localhost:8765/auth; then
    echo
    echo "Ready: http://localhost:8765"
    echo "Sign-in is on. Create a new local account; it is separate from your usual local preview."
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
