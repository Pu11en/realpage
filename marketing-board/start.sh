#!/usr/bin/env bash
# Serve the Marketing Board at http://localhost:8740
cd "$(dirname "$0")" && exec python3 -m http.server 8740 --bind 127.0.0.1
