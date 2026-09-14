#!/usr/bin/env bash
# Plan check for PLAN-lead-finder-build: every lead-finder* skill's tests, no network,
# plus check-panel.sh so a Part 1.1 change can't quietly break the site. Under 2 minutes.
set -euo pipefail
cd "$(dirname "$0")/../.."
for dir in propertystack/skills/lead-finder*/; do
  if [ -d "${dir}tests" ]; then
    python3 -m pytest -q "${dir}tests"
  fi
done
bash tooling/qa/check-panel.sh
