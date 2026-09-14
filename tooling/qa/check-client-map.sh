#!/usr/bin/env bash
# Plan check for PLAN-client-map: client-map tests, then the panel check.
set -euo pipefail
cd "$(dirname "$0")/../.."
python3 -m pytest -q propertystack/skills/client-map/
bash tooling/qa/check-panel.sh
