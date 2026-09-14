#!/usr/bin/env bash
# Plan check for PLAN-client-map: client-map tests, the panel check, then the map check.
set -euo pipefail
cd "$(dirname "$0")/../.."
python3 -m pytest -q propertystack/skills/client-map/
bash tooling/qa/check-panel.sh
python3 tooling/qa/check_map.py
