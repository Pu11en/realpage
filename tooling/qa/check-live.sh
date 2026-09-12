#!/usr/bin/env bash
# Live PropertyStack check (Railway): pages up, chat app + chatbot healthy,
# signed-in users in the chat database, and recent errors in each service's logs.
# Needs the Railway CLI logged in. Free: no bot calls.
#   bash tooling/qa/check-live.sh
set -uo pipefail
SITE=https://propertystack-production.up.railway.app
LINK=$(mktemp -d); trap 'rm -rf "$LINK"' EXIT
cd "$LINK" && railway link -p propertystack >/dev/null 2>&1 || { echo "railway link failed"; exit 1; }

echo "== Pages"
for p in / /master-table.html /software-share.html /api/config; do
  printf '  %-22s %s\n' "$p" "$(curl -s -o /dev/null -w '%{http_code}' "$SITE$p")"
done
printf '  %-22s %s\n' "chat frame (/)" "$(curl -s -H 'Sec-Fetch-Dest: iframe' "$SITE/" | grep -o '<title>[^<]*' | head -1)"
printf '  %-22s %s\n' "chatbot /health" "$(curl -s https://propertystack-chatbot-production.up.railway.app/health)"

echo "== Google sign-in"
LOC=$(curl -s -o /dev/null -w '%{redirect_url}' "$SITE/oauth/google/login")
GPAGE=$(curl -sL -A 'Mozilla/5.0 Chrome/120' "$LOC")
if [[ "$GPAGE" == *redirect_uri_mismatch* ]]; then
  echo "  BLOCKED: add $SITE/oauth/google/callback to the Google OAuth client's redirect URIs"
else
  echo "  ok (Google accepts the redirect address)"
fi

echo "== Users in the chat database"
timeout 90 railway ssh --service propertystack-chat "python3 -c \"
import sqlite3
c = sqlite3.connect('/app/backend/data/webui.db')
rows = c.execute('select email, role, datetime(created_at, \\\"unixepoch\\\"), datetime(last_active_at, \\\"unixepoch\\\") from user order by created_at').fetchall()
print('  users:', len(rows))
for r in rows: print('  ', *r)
print('  chats:', c.execute('select count(*) from chat').fetchone()[0])
\"" 2>&1 | grep -v '^$'

echo "== Recent errors (last 300 log lines per service)"
for s in propertystack propertystack-chat propertystack-chatbot; do
  n=$(railway logs --service "$s" 2>/dev/null | tail -300 | grep -v 'tools.registry' | grep -ciE 'traceback|\berror\b|exception|  5[0-9][0-9] ')
  echo "  $s: $n"
  railway logs --service "$s" 2>/dev/null | tail -300 | grep -v 'tools.registry' | grep -iE 'traceback|\berror\b|exception' | tail -3 | cut -c1-200 | sed 's/^/     /'
done
