#!/usr/bin/env bash
# Readable-chat check (PLAN-chat-readable, R1). Free, no bot calls, well under 10 s.
# Part 1: SOUL.md must have the fixed answer layout (**Next:** / **Sources:** lines).
# Part 2: custom.css must give chat message text font-size >= 17px and
#         line-height >= 1.6 (in one rule whose selector targets messages).
set -u
cd "$(dirname "$0")/../.."

python3 - <<'PY'
import re, sys

fails = []

soul = open("chatbot/hermes-profile/SOUL.md", encoding="utf-8").read()
for tag in ("**Next:**", "**Sources:**"):
    if tag not in soul:
        fails.append(f"SOUL.md has no {tag} layout line")

css = open("chatbot/branding/custom.css", encoding="utf-8").read()
css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
ok = False
for sel, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
    if not re.search(r"message|prose", sel, re.I):
        continue
    fs = re.search(r"font-size\s*:\s*([\d.]+)px", body)
    lh = re.search(r"line-height\s*:\s*([\d.]+)\s*(?:;|!|$)", body)
    if fs and lh and float(fs.group(1)) >= 17 and float(lh.group(1)) >= 1.6:
        ok = True
        break
if not ok:
    fails.append("custom.css has no chat message rule with font-size >= 17px and line-height >= 1.6")

for f in fails:
    print("FAIL:", f)
if fails:
    sys.exit(1)
print("check-readable: OK (Next/Sources layout + readable message text)")
PY
