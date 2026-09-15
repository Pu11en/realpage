#!/usr/bin/env bash
# realpage.com library check: offline tests only (saved fixtures, no network, no keys).
set -euo pipefail
cd "$(dirname "$0")/../.."
env -u GEMINI_API_KEY -u JINA_API_KEY python3 -m pytest -q -p no:cacheprovider tooling/realpage-library/tests
