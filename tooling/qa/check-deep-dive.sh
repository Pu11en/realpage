#!/usr/bin/env bash
# One-command check for the deep-dive-links plan (the loop bot runs Check: without a shell).
set -euo pipefail
cd "$(dirname "$0")/../.."
python3 -m pytest -q chatbot/tests
bash tooling/qa/check-panel.sh
bash tooling/qa/check-readable.sh
