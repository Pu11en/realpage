#!/usr/bin/env bash
# Street Talk check: offline tests on saved sample files (never calls Reddit or YouTube).
set -euo pipefail
cd "$(dirname "$0")/../.."
set +e
env -u DSH_REDDIT_COOKIE python3 -m pytest -q -p no:cacheprovider tooling/street-talk/tests
code=$?
set -e
# pytest exit 5 = no tests collected: treat as a pass.
if [ "$code" -ne 0 ] && [ "$code" -ne 5 ]; then exit "$code"; fi
