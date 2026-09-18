#!/usr/bin/env python3
"""Check a deep-dive brief against the fixed layout.

Usage:
  validate.py BRIEF.md            check a markdown file
  validate.py -                   check text from stdin
  validate.py --self-test         run on the fixtures (1 good, 3 bad)

Rules:
  1. The 8 headings exist, in order.
  2. Every line under "Why now" and "Who to ask for" has a URL
     ("not found" lines under "Who to ask for" are allowed without one).
  3. No email or phone appears unless it is in a contacts.csv.
  4. The opener never claims to work for the company you're calling.
"""
import argparse
import csv
import glob
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
HEADINGS = [
    "Bottom line", "Who they are", "Why now", "Who to ask for",
    "30-second opener", "3 questions", "2 objections + answers", "Sources",
]
URL = re.compile(r"https?://\S+")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PHONE = re.compile(r"(?<!\d)(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}(?!\d)")
HEADING = re.compile(r"^#{1,6}\s+(.*?)\s*$")


def norm(h):
    return re.sub(r"[^a-z0-9+]+", " ", h.lower()).strip()


def digits(p):
    d = re.sub(r"\D", "", p)
    return d[1:] if len(d) == 11 and d.startswith("1") else d


def load_contacts(paths=None):
    paths = paths or glob.glob(str(ROOT / "propertystack/data/*/contacts.csv"))
    emails, phones = set(), set()
    for p in paths:
        with open(p, newline="") as f:
            for row in csv.DictReader(f):
                if row.get("email"):
                    emails.add(row["email"].strip().lower())
                if row.get("phone"):
                    phones.add(digits(row["phone"]))
    return emails, phones


def sections(text):
    """Return [(heading, [body lines])] in order of appearance."""
    out = []
    for line in text.splitlines():
        m = HEADING.match(line)
        if m:
            out.append((m.group(1), []))
        elif out:
            out[-1][1].append(line)
    return out


def validate(text, contacts):
    emails, phones = contacts
    errors = []
    secs = sections(text)
    wanted = [norm(h) for h in HEADINGS]
    found = [norm(h) for h, _ in secs if norm(h) in wanted]
    missing = [h for h in HEADINGS if norm(h) not in found]
    if missing:
        errors.append("missing headings: " + ", ".join(missing))
    elif found != wanted:
        errors.append("headings out of order: " + " > ".join(found))

    body = {norm(h): lines for h, lines in secs}
    for name in ("Why now", "Who to ask for"):
        for line in body.get(norm(name), []):
            s = line.strip()
            if not s or URL.search(s):
                continue
            if name == "Who to ask for" and "not found" in s.lower():
                continue
            errors.append(f'"{name}" line has no link: {s}')

    no_urls = URL.sub(" ", text)
    for e in EMAIL.findall(no_urls):
        if e.lower() not in emails:
            errors.append(f"email not in contacts.csv: {e}")
    for p in PHONE.findall(no_urls):
        if digits(p) not in phones:
            errors.append(f"phone not in contacts.csv: {p.strip()}")

    opener = " ".join(body.get(norm("30-second opener"), []))
    # Check for claiming to work for known property management companies
    company_brands = r"\b(?:realpage|yardi|entrata|appfolio|property shark|buildium|rent manager|property manager)\b"
    if re.search(rf"with\s+{company_brands}|from\s+{company_brands}", opener, re.I):
        errors.append('opener claims to work for a property-management company (use "[your company]" instead)')
    return errors


def self_test(contacts):
    fx = HERE / "fixtures"
    ok = True
    for path in sorted(fx.glob("*.md")):
        errs = validate(path.read_text(), contacts)
        expect_good = path.name.startswith("good")
        passed = (not errs) == expect_good
        ok &= passed
        print(f"{'ok  ' if passed else 'FAIL'} {path.name}: "
              f"{'valid' if not errs else '; '.join(errs)}")
    if len(list(fx.glob("good*.md"))) < 1 or len(list(fx.glob("bad*.md"))) < 3:
        print("FAIL need 1 good + 3 bad fixtures")
        ok = False
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("brief", nargs="?")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--contacts", action="append", help="contacts.csv (default: all areas)")
    a = ap.parse_args()
    contacts = load_contacts(a.contacts)
    if a.self_test:
        sys.exit(0 if self_test(contacts) else 1)
    if not a.brief:
        ap.error("give a brief path, '-' or --self-test")
    text = sys.stdin.read() if a.brief == "-" else Path(a.brief).read_text()
    errs = validate(text, contacts)
    for e in errs:
        print("FAIL", e)
    if not errs:
        print("ok: brief is valid")
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
