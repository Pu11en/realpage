#!/usr/bin/env bash
# "Run AI visibility": real Gemini run, rebuild the tab + chatbot note, commit locally, print a summary.
# Never pushes -- Drew checks localhost first and says "push it".
#
#   bash tooling/ai-visibility/run-and-report.sh
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
cd "$REPO"

bash "$HERE/run.sh" >/tmp/ai-visibility-run.log 2>&1 || { tail -20 /tmp/ai-visibility-run.log; exit 1; }
python3 "$HERE/to_research.py" >/dev/null

git add site/data/ai-visibility.json site/data/ai-visibility-history archive/realpage/09-ai-visibility/summary.md
git diff --cached --quiet || git commit -qm "AI Visibility: Gemini run $(date +%F)"
python3 "$HERE/report.py"
