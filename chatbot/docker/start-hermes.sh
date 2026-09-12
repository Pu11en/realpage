#!/usr/bin/env bash
# PropertyStack chatbot: Hermes API server on localhost + public /chat proxy on $PORT.
# Same shape as eve-agent's start script, minus Telegram.
set -euo pipefail

export HERMES_HOME="${HERMES_HOME:-/opt/data}"
PROFILE_SRC="/opt/hermes-profile"
PY=/opt/hermes/.venv/bin/python

mkdir -p "$HERMES_HOME/plugins" "$HERMES_HOME/skills" "$HERMES_HOME/logs" "$HERMES_HOME/workspace"

hermes_env="$HERMES_HOME/.env"
touch "$hermes_env"
write_env_kv() {
  key="$1"; value="$2"
  if grep -q "^${key}=" "$hermes_env" 2>/dev/null; then
    sed -i "s|^${key}=.*|${key}=${value}|" "$hermes_env"
  else
    printf '%s=%s\n' "$key" "$value" >> "$hermes_env"
  fi
}

# Internal-only key between the proxy and Hermes; regenerated per boot unless set.
export API_SERVER_KEY="${API_SERVER_KEY:-$($PY -c 'import secrets; print(secrets.token_hex(32))')}"
export API_SERVER_PORT=8642
# Railway private network / Docker compose can set API_SERVER_HOST=0.0.0.0 (key still required).
export API_SERVER_HOST="${API_SERVER_HOST:-127.0.0.1}"
write_env_kv API_SERVER_ENABLED true
write_env_kv API_SERVER_KEY "$API_SERVER_KEY"
write_env_kv API_SERVER_PORT "$API_SERVER_PORT"
write_env_kv API_SERVER_HOST "$API_SERVER_HOST"
write_env_kv HERMES_KANBAN_DISPATCH_IN_GATEWAY 0

if [ -n "${DEEPSEEK_API_KEY:-}" ]; then
  write_env_kv DEEPSEEK_API_KEY "$DEEPSEEK_API_KEY"
fi

# Repository profile is the source of truth; refresh on every boot.
cp "$PROFILE_SRC/SOUL.md" "$HERMES_HOME/SOUL.md"
cp "$PROFILE_SRC/config.yaml" "$HERMES_HOME/config.yaml"
for kind in plugins skills; do
  for d in "$PROFILE_SRC/$kind"/*; do
    [ -d "$d" ] || continue
    rm -rf "$HERMES_HOME/$kind/$(basename "$d")"
    cp -R "$d" "$HERMES_HOME/$kind/$(basename "$d")"
  done
done

/opt/hermes/.venv/bin/hermes gateway run &
"$PY" /opt/chatbot/proxy.py &
# If either process dies, exit so Railway restarts the container.
wait -n
exit 1
