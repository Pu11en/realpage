#!/usr/bin/env bash
# Check for PLAN-audit-fixes: the small tests each fix adds (tooling/qa/fixes_tests, no network),
# then the site check (every page loads, phone and desktop, still in the landing look). Under 2 minutes.
set -u
cd "$(dirname "$0")/../.."
if ls tooling/qa/fixes_tests/test_*.py >/dev/null 2>&1; then
  python3 -m pytest -q tooling/qa/fixes_tests || exit 1
fi
bash tooling/qa/check-design.sh
