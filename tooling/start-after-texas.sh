#!/usr/bin/env bash
# Waits (up to 36h) until the Texas lead-finder build is finished AND merged into local-test,
# then starts the map-markers build (Drew's go, 2026-09-14). Log: /tmp/start-after-texas.log
REPO=/home/drewp/main-projects/realpage/.worktrees/local-test
LOOPS=/home/drewp/.local/state/ccdb/gowork-loops.json
for i in $(seq 1 2160); do
  running=$(python3 -c "import json;print(any('PLAN-lead-finder-texas' in r['plan_path'] for r in json.load(open('$LOOPS'))))" 2>/dev/null)
  merged=$(git -C "$REPO" log --oneline -40 | grep -c "gowork/plan-lead-finder-texas")
  busy=$(python3 -c "import json;print(any(r['repo_dir']=='$REPO' for r in json.load(open('$LOOPS'))))" 2>/dev/null)
  if [ "$running" = "False" ] && [ "$merged" -gt 0 ] && [ "$busy" = "False" ]; then
    curl -s -X POST "$CCDB_API_URL/api/loops" -H "Authorization: Bearer $CCDB_API_SECRET" -H "Content-Type: application/json" \
      -d '{"plan_path": "'$REPO'/PLAN-map-markers.md", "report_thread_id": 1548911246705959072, "harness": "claude", "model": "sonnet", "fallback_harness": "dsh", "fallback_model": "glm-5.3"}'
    echo " started map build $(date)"; exit 0
  fi
  sleep 60
done
echo "gave up after 36h $(date)"
