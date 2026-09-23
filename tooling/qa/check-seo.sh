#!/usr/bin/env bash
# SEO checks. The offline half must pass: the generated files are current and the
# metadata tests are green. The live half is reported but does not fail the script
# unless --live-required is passed, because the branch is normally ahead of deploy.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PY="${PYTHON:-}"
if [ -z "$PY" ]; then
  for c in python3 python py; do
    if command -v "$c" >/dev/null 2>&1 && "$c" -c "import pytest" >/dev/null 2>&1; then PY="$c"; break; fi
  done
fi
[ -n "$PY" ] || { echo "no python with pytest found (set PYTHON=...)"; exit 2; }

live_required=0
[ "${1:-}" = "--live-required" ] && live_required=1
fail=0

echo "== generated files are current"
"$PY" "$ROOT/tooling/seo/build_seo_files.py" --check || fail=1

echo "== offline tests"
"$PY" -m pytest -q "$ROOT/tooling/qa/fixes_tests/test_seo_files.py" || fail=1

HOST="${SEO_HOST:-https://app.cranesignal.com}"
echo "== live: $HOST"
live_missing=0
if curl -sf -o /dev/null --max-time 10 "$HOST/index.html"; then
  for path in /robots.txt /sitemap.xml /llms.txt; do
    code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$HOST$path")
    if [ "$code" = "200" ]; then echo "  ok   $path"; else echo "  not live yet: $path -> $code"; live_missing=1; fi
  done
  home=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$HOST/")
  if [ "$home" = "200" ]; then echo "  ok   / serves 200 directly"; else echo "  not live yet: / -> $home"; live_missing=1; fi
  [ "$live_missing" = "1" ] && echo "  (expected until this branch is deployed)"
else
  echo "  skipped: site unreachable"
fi
[ "$live_required" = "1" ] && [ "$live_missing" = "1" ] && fail=1

if [ "$fail" = "0" ]; then echo "SEO checks passed"; else echo "SEO checks FAILED"; fi
exit "$fail"
