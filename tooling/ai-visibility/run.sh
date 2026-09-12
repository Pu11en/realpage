#!/usr/bin/env bash
# Ask AIs about apartment software with NiubiGEO, then refresh the dashboard's
# AI Visibility tab. The AIs are local Claude / Codex sessions (local_ai.py),
# so no API credit is spent.
#
#   bash tooling/ai-visibility/run.sh            real run (local sessions, ~20-40 min)
#   bash tooling/ai-visibility/run.sh --practice free run against a fake AI
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
NIUBIGEO="${NIUBIGEO_DIR:-/home/drewp/main-projects/tools-src/niubigeo}"
RUNS="${AI_VIS_RUNS:-$HOME/.local/state/realpage-ai-visibility/runs}"
PORT="${AI_VIS_PORT:-18912}"
COMPETITORS="yardi.com,entrata.com,appfolio.com,buildium.com,resman.com"
mkdir -p "$RUNS"

[ -d "$NIUBIGEO/node_modules" ] || { echo "NiubiGEO not installed at $NIUBIGEO (git clone + npm ci)"; exit 1; }

if [ "${1:-}" = "--practice" ]; then
  python3 "$HERE/fake_ai.py" "$PORT" & SERVER=$!
  MODELS_LIST=fake-chatgpt,fake-claude
  DEMO=--demo
else
  # Real run: answers come from local Claude / Codex sessions (no API credit).
  python3 "$HERE/local_ai.py" "$PORT" 2>>"$RUNS/local-ai.log" & SERVER=$!
  MODELS_LIST="${AI_VIS_MODELS:-claude,claude-web,chatgpt}"
  DEMO=
  export PROVIDER_TIMEOUT_MS=300000 PROVIDER_HTTP_ATTEMPTS=2 AUDIT_CONCURRENCY="${AUDIT_CONCURRENCY:-4}"
fi
trap 'kill $SERVER 2>/dev/null' EXIT
sleep 1
export OPENAI_COMPATIBLE_API_KEY=local OPENAI_COMPATIBLE_BASE_URL="http://127.0.0.1:$PORT/v1"
unset OPENROUTER_API_KEY
TARGETS=(--provider openai-compatible --models "$MODELS_LIST")

cd "$NIUBIGEO"
RUNS_DIR="$RUNS" npx tsx src/cli.ts audit --domain realpage.com --name RealPage \
  --aliases "RealPage OneSite,OneSite" --competitors "$COMPETITORS" \
  "${TARGETS[@]}" --prompt-count "${AI_VIS_PROMPTS:-8}" | tee "$RUNS/last-run.log"

RUN_DIR="$(ls -td "$RUNS"/*-realpage | head -1)"
python3 "$REPO/site/data/build_ai_visibility.py" "$RUN_DIR" $DEMO
