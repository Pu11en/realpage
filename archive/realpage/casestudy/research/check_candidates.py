"""Check that the repo-hunt notes stay well formed: every candidate has a URL, a verdict and a plain-English line."""
import re
import sys
from pathlib import Path

NOTES = Path(__file__).resolve().parent / "candidates.md"
VERDICTS = {"USE", "MIRROR PATTERN", "VENDOR DATA", "SKIP"}

text = NOTES.read_text(encoding="utf-8")
entries = re.split(r"^### ", text, flags=re.M)[1:]
bad = []
for e in entries:
    name = e.splitlines()[0].strip()
    if not re.search(r"https?://\S+", e):
        bad.append(f"{name}: no URL")
    m = re.search(r"^\*\*Verdict:\*\*\s*(.+)$", e, flags=re.M)
    if not m or m.group(1).strip().upper() not in VERDICTS:
        bad.append(f"{name}: verdict must be one of {sorted(VERDICTS)}")
    if not re.search(r"^\*\*In plain words:\*\*\s*\S", e, flags=re.M):
        bad.append(f"{name}: missing 'In plain words' line")
if bad:
    print("\n".join(bad))
    sys.exit(1)
print(f"{len(entries)} candidates, all well formed")
