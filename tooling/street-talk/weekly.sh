#!/usr/bin/env bash
# Street Talk weekly refresh: the three Reddit/YouTube collectors, then the build, then a local commit.
# Never pushes. No timer is set up here -- call this from the weekly Texas refresh once that exists.
#
# Safety: read-only GETs, 3 s between Reddit requests (collect.py), at most 80 Reddit requests for the
# whole run (budgets below add up to 80), and the first 403/429 stops every remaining Reddit part.
# A blocked part's partial file is renamed <part>.blocked.json so the build keeps last week's posts
# for that part and the tab says the refresh failed.
#
#   bash tooling/street-talk/weekly.sh            # full run
#   bash tooling/street-talk/weekly.sh --no-commit
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
DATE="${STREET_TALK_DATE:-$(date +%F)}"
RAW="$ROOT/propertystack/data/street-talk/raw/$DATE"
COMMIT=1
[ "${1:-}" = "--no-commit" ] && COMMIT=0

# part:budget -- total 80 (the per-run Reddit cap).
PLAN="rivals:20 buildings:40 unhappy:20"
blocked=""
for item in $PLAN; do
  part="${item%%:*}"; budget="${item##*:}"
  if [ -n "$blocked" ]; then
    echo "skip $part: Reddit blocked earlier in this run ($blocked)"
    continue
  fi
  python3 tooling/street-talk/collect.py --part "$part" --budget "$budget" --date "$DATE"
  code=$?
  if [ "$code" -eq 2 ]; then
    blocked="$part"
    [ -f "$RAW/$part.json" ] && mv "$RAW/$part.json" "$RAW/$part.blocked.json"
    echo "$part: Reddit blocked -- keeping last week's $part posts"
  elif [ "$code" -ne 0 ]; then
    echo "$part: collector failed (exit $code) -- keeping last week's $part posts"
  fi
done

python3 tooling/street-talk/build.py || { echo "build failed -- saved tab data unchanged"; exit 1; }

if [ "$COMMIT" -eq 1 ]; then
  paths=(propertystack/data/street-talk site/data/street-talk.json)
  git add -- "${paths[@]}"
  if git diff --cached --quiet -- "${paths[@]}"; then
    echo "nothing new to commit"
  else
    git commit -q -m "Street Talk weekly refresh $DATE${blocked:+ (Reddit blocked at $blocked; older posts kept)}" -- "${paths[@]}" \
      && echo "committed Street Talk refresh $DATE"
  fi
fi
[ -z "$blocked" ]
