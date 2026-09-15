#!/usr/bin/env bash
# AI Visibility check: offline tests only (saved Gemini responses, no network, no key).
set -euo pipefail
cd "$(dirname "$0")/../.."
env -u GEMINI_API_KEY python3 -m pytest -q -p no:cacheprovider tooling/ai-visibility/tests
