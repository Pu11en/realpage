#!/usr/bin/env bash
# Ask five AIs (via OpenRouter) about apartment software with NiubiGEO, then
# refresh the dashboard's AI Visibility tab. Costs a little OpenRouter credit.
#
#   bash tooling/ai-visibility/run.sh            real run (paid, small)
#   bash tooling/ai-visibility/run.sh --practice free run against a fake AI
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
NIUBIGEO="${NIUBIGEO_DIR:-/home/drewp/main-projects/tools-src/niubigeo}"
RUNS="${AI_VIS_RUNS:-$HOME/.local/state/realpage-ai-visibility/runs}"
MODELS="${AI_VIS_MODELS:-openai/gpt-4o-mini,anthropic/claude-haiku-4.5,google/gemini-2.5-flash-lite,perplexity/sonar,deepseek/deepseek-chat}"
COMPETITORS="yardi.com,entrata.com,appfolio.com,buildium.com,resman.com"
mkdir -p "$RUNS"

[ -d "$NIUBIGEO/node_modules" ] || { echo "NiubiGEO not installed at $NIUBIGEO (git clone + npm ci)"; exit 1; }

if [ "${1:-}" = "--practice" ]; then
  python3 "$HERE/fake_ai.py" 18911 & FAKE=$!
  trap 'kill $FAKE 2>/dev/null' EXIT
  sleep 1
  export OPENAI_COMPATIBLE_API_KEY=practice OPENAI_COMPATIBLE_BASE_URL=http://127.0.0.1:18911/v1
  TARGETS=(--targets openai-compatible:fake-chatgpt,openai-compatible:fake-claude)
  DEMO=--demo
else
  # Key comes from Drew's private key file; never printed.
  OPENROUTER_API_KEY="$(grep -m1 '^OPENROUTER_API_KEY=' "$HOME/.config/allwork/keys.env" | cut -d= -f2- | tr -d '"'"'")"
  [ -n "$OPENROUTER_API_KEY" ] || { echo "No OPENROUTER_API_KEY in ~/.config/allwork/keys.env"; exit 1; }
  export OPENROUTER_API_KEY
  TARGETS=(--provider openrouter --models "$MODELS")
  DEMO=
fi

cd "$NIUBIGEO"
RUNS_DIR="$RUNS" npx tsx src/cli.ts audit --domain realpage.com --name RealPage \
  --aliases "RealPage OneSite,OneSite" --competitors "$COMPETITORS" \
  "${TARGETS[@]}" --prompt-count "${AI_VIS_PROMPTS:-8}" | tee "$RUNS/last-run.log"

RUN_DIR="$(ls -td "$RUNS"/*-realpage | head -1)"
python3 "$REPO/site/data/build_ai_visibility.py" "$RUN_DIR" $DEMO
