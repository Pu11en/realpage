#!/usr/bin/env bash
# Ask AIs about apartment software with NiubiGEO, then refresh the dashboard's
# AI Visibility tab. Every run asks the same frozen questions (questions.csv,
# the 2026-09-12 list) so trends are fair. Answers come from local_ai.py:
# Gemini by default (gemini = memory, gemini-web = Google Search grounding).
#
#   bash tooling/ai-visibility/run.sh            real run (Gemini, throttled, ~15-25 min)
#   bash tooling/ai-visibility/run.sh --practice free run against a fake AI
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
NIUBIGEO="${NIUBIGEO_DIR:-/home/drewp/main-projects/tools-src/niubigeo}"
RUNS="${AI_VIS_RUNS:-$HOME/.local/state/realpage-ai-visibility/runs}"
PORT="${AI_VIS_PORT:-18912}"
QUESTIONS="${AI_VIS_QUESTIONS:-$HERE/questions.csv}"
mkdir -p "$RUNS"

[ -d "$NIUBIGEO/node_modules" ] || { echo "NiubiGEO not installed at $NIUBIGEO (git clone + npm ci)"; exit 1; }

if [ "${1:-}" = "--practice" ]; then
  python3 "$HERE/fake_ai.py" "$PORT" & SERVER=$!
  MODELS_LIST=fake-chatgpt,fake-claude
  DEMO=--demo
else
  # Real run: local_ai.py answers (Gemini by default; claude/claude-web/chatgpt still work).
  export AI_VIS_SOURCES="$RUNS/gemini-sources.pending.jsonl"; rm -f "$AI_VIS_SOURCES"
  python3 "$HERE/local_ai.py" "$PORT" 2>>"$RUNS/local-ai.log" & SERVER=$!
  MODELS_LIST="${AI_VIS_MODELS:-gemini,gemini-web}"
  DEMO=
  export PROVIDER_TIMEOUT_MS=300000 PROVIDER_HTTP_ATTEMPTS=2 AUDIT_CONCURRENCY="${AUDIT_CONCURRENCY:-4}"
fi
trap 'kill $SERVER 2>/dev/null' EXIT
sleep 1
export OPENAI_COMPATIBLE_API_KEY=local OPENAI_COMPATIBLE_BASE_URL="http://127.0.0.1:$PORT/v1"
unset OPENROUTER_API_KEY

cd "$NIUBIGEO"
RUNS_DIR="$RUNS" npx tsx "$HERE/frozen_audit.ts" "$QUESTIONS" "$MODELS_LIST" | tee "$RUNS/last-run.log"

RUN_DIR="$(ls -td "$RUNS"/*-realpage | head -1)"
# gemini-web's source links for each answer belong with this run
[ -f "${AI_VIS_SOURCES:-/nonexistent}" ] && mv "$AI_VIS_SOURCES" "$RUN_DIR/gemini-sources.jsonl"
python3 "$REPO/site/data/build_ai_visibility.py" "$RUN_DIR" $DEMO
