#!/usr/bin/env bash
# Rebuild the Under the Hood data files, validate them, and confirm the page
# serves and references them. No network. Under 2 minutes.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SITE="$ROOT/site"
PORT=8797
FAIL=0

echo "== build data =="
python3 "$SITE/data/build_buildbot.py" || { echo "FAIL: build_buildbot.py"; FAIL=1; }
python3 "$SITE/data/build_evals.py" || { echo "FAIL: build_evals.py"; FAIL=1; }

echo "== validate JSON =="
for f in buildbot.json evals.json chat-stats.json; do
  if ! python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$SITE/data/$f"; then
    echo "FAIL: $f does not parse"
    FAIL=1
  fi
done

echo "== serve + curl =="
( cd "$SITE" && python3 -m http.server "$PORT" >/tmp/uth-server.log 2>&1 & echo $! > /tmp/uth-server.pid )
sleep 1
SERVER_PID="$(cat /tmp/uth-server.pid 2>/dev/null || true)"

check_200() {
  local path="$1"
  local code
  code="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$PORT/$path")"
  if [ "$code" != "200" ]; then
    echo "FAIL: $path returned $code"
    FAIL=1
  else
    echo "ok: $path -> 200"
  fi
}

check_200 "under-the-hood.html"
check_200 "data/buildbot.json"
check_200 "data/evals.json"
check_200 "data/chat-stats.json"

if [ -n "${SERVER_PID:-}" ]; then
  kill "$SERVER_PID" >/dev/null 2>&1
fi
rm -f /tmp/uth-server.pid /tmp/uth-server.log

echo "== page references data files =="
for f in "data/buildbot.json" "data/evals.json" "data/chat-stats.json"; do
  if ! grep -q "$f" "$SITE/under-the-hood.html"; then
    echo "FAIL: under-the-hood.html does not reference $f"
    FAIL=1
  else
    echo "ok: page references $f"
  fi
done

if [ "$FAIL" -ne 0 ]; then
  echo "check-under-the-hood: FAILED"
  exit 1
fi
echo "check-under-the-hood: PASSED"
