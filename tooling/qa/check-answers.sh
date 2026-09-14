#!/usr/bin/env bash
# Answer checker (PLAN-chat-finish T2). Costs a few cents per run (real bot calls).
# Asks 5 set questions in parallel against the local bot and fails any answer
# that is too long, shows a raw code or file name, has a call script or no bold.
#
#   bash tooling/qa/check-answers.sh
#
# Needs the local stack up: bash tooling/dev.sh
set -u
cd "$(dirname "$0")/../.."
exec python3 tooling/qa/check_answers.py "$@"
