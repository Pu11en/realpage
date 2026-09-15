#!/usr/bin/env bash
# AI Visibility check: offline tests (saved Gemini responses, no network, no key), then the page check.
set -euo pipefail
cd "$(dirname "$0")/../.."
env -u GEMINI_API_KEY python3 -m pytest -q -p no:cacheprovider tooling/ai-visibility/tests
python3 tooling/qa/check_ai_visibility_page.py
