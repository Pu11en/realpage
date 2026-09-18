#!/usr/bin/env bash
# Build the two release containers, then prove their configured runtime users
# are non-root.  No service ports, data volumes, model calls, or network
# requests are used after Docker has the required local base images.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CHAT_IMAGE="cranesignal-chatbot-security-check"
SITE_IMAGE="cranesignal-site-security-check"
CASE_IMAGE="cranesignal-case-study-security-check"

docker build -q -f "$ROOT/chatbot/Dockerfile" -t "$CHAT_IMAGE" "$ROOT" >/dev/null
docker build -q -f "$ROOT/site/Dockerfile" -t "$SITE_IMAGE" "$ROOT/site" >/dev/null
docker build -q -f "$ROOT/casestudy/Dockerfile" -t "$CASE_IMAGE" "$ROOT" >/dev/null

chat_user="$(docker image inspect "$CHAT_IMAGE" --format '{{.Config.User}}')"
site_user="$(docker image inspect "$SITE_IMAGE" --format '{{.Config.User}}')"
case_user="$(docker image inspect "$CASE_IMAGE" --format '{{.Config.User}}')"
[ "$chat_user" = "hermes" ] || { echo "FAIL: chatbot image user is ${chat_user:-root}" >&2; exit 1; }
[ "$site_user" = "caddy" ] || { echo "FAIL: site image user is ${site_user:-root}" >&2; exit 1; }
[ "$case_user" = "casestudy" ] || { echo "FAIL: case-study image user is ${case_user:-root}" >&2; exit 1; }

# The chatbot's inherited entrypoint is intentionally exercised here: its
# supervisor must retain the configured hermes identity when it invokes work.
chat_identity="$(docker run --rm --tmpfs /opt/data:rw,mode=0700,uid=10000,gid=10000 \
  "$CHAT_IMAGE" bash -lc 'id -un' | tail -n 1)"
[ "$chat_identity" = "hermes" ] || { echo "FAIL: chatbot ran as $chat_identity" >&2; exit 1; }

# Caddy validates its real configuration as the configured user.  Its state
# directories are temporary for this check, avoiding any user data volume.
docker run --rm --tmpfs /config:rw,mode=0777 --tmpfs /data:rw,mode=0777 \
  -e PORT=8080 -e SITE_ROOT=/srv -e CHAT_UPSTREAM=http://127.0.0.1:65535 \
  "$SITE_IMAGE" caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile >/dev/null

echo "PASS: chatbot runs as hermes; site runs as caddy; case study runs as casestudy; all container configurations are valid"
