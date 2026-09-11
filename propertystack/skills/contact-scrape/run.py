"""Skill: contact-scrape — phone/email for each apartment community, from its own website.

Reads master.csv (output of build-table), Jina-reads the website for rows with
website_confidence high/medium (same gate detect-software uses — low/medium sites
aren't worth the fetch), and regex-extracts a phone number and email address from
the page text. Rows with no usable website, or where nothing was found, are still
written with blank phone/email so contacts.csv always has one row per building.

Junk emails (Wix privacy proxies, Sentry, schema.org, etc.) are filtered by domain —
these leak through as the first regex match on template-heavy sites and are never a
real leasing office contact.

Usage: python3 skills/contact-scrape/run.py --area plano-richardson
"""
import argparse, collections, csv, datetime as dt, re, sys, pathlib
import concurrent.futures as cf
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from lib.paths import area_dir
from lib.runlog import RunLog
from lib.jina import Jina

COLS = ["apt_id", "phone", "email", "source_url", "checked_at", "notes"]

PHONE_RE = re.compile(r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

# Template/tooling addresses that regex-match on nearly every site but are never a
# real leasing-office contact.
EMAIL_REJECT_DOMAINS = [
    "sentry.io", "sentry-next.io", "wixpress.com", "example.com", "godaddy.com",
    "schema.org", "w3.org", "google.com", "gstatic.com", "cloudflare.com",
    "godaddy.net", "domain.com", "yourdomain.com", "wordpress.com", "squarespace.com",
]


def clean_phone(raw):
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        return None
    return f"({digits[0:3]}) {digits[3:6]}-{digits[6:10]}"


def pick_phone(text):
    for m in PHONE_RE.finditer(text):
        p = clean_phone(m.group())
        if p:
            return p
    return ""


def pick_email(text):
    for m in EMAIL_RE.finditer(text):
        addr = m.group().lower()
        domain = addr.split("@", 1)[1]
        if any(domain == d or domain.endswith("." + d) for d in EMAIL_REJECT_DOMAINS):
            continue
        return addr
    return ""


def scrape(row, jina, today):
    if row["website_confidence"] not in ("high", "medium") or not row["website"]:
        return {"apt_id": row["apt_id"], "phone": "", "email": "", "source_url": "",
                "checked_at": "", "notes": "no-website"}
    url = row["website"]
    try:
        page = jina.read(url)
    except Exception as e:
        return {"apt_id": row["apt_id"], "phone": "", "email": "", "source_url": url,
                "checked_at": today, "notes": f"error: {e}"[:100]}
    phone, email = pick_phone(page), pick_email(page)
    notes = "" if (phone or email) else "no-contact-found"
    return {"apt_id": row["apt_id"], "phone": phone, "email": email, "source_url": url,
            "checked_at": today, "notes": notes}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--area", required=True)
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--suffix", default="",
                     help="Read <N>-buildings<suffix>.csv + <N>-websites<suffix>.csv "
                          "instead of master.csv (no master<suffix>.csv required), and "
                          "write contacts<suffix>.csv instead of contacts.csv.")
    a = ap.parse_args()
    with RunLog("contact-scrape", a.area) as log:
        d = area_dir(a.area)
        if a.suffix:
            b_f = d / f"1-buildings{a.suffix}.csv"
            w_f = d / f"2-websites{a.suffix}.csv"
            bldgs = list(csv.DictReader(open(b_f, encoding="utf-8-sig")))
            sites_by_id = {r["apt_id"]: r for r in csv.DictReader(open(w_f, encoding="utf-8-sig"))}
            rows = []
            for b in bldgs:
                site = sites_by_id.get(b["apt_id"], {})
                rows.append({"apt_id": b["apt_id"],
                             "website": site.get("website", ""),
                             "website_confidence": site.get("confidence", "")})
            log.rec["inputs"] = [str(p.relative_to(p.parents[2])) for p in (b_f, w_f)]
        else:
            in_f = d / "master.csv"
            rows = list(csv.DictReader(open(in_f, encoding="utf-8-sig")))
            log.rec["inputs"] = [str(in_f.relative_to(in_f.parents[2]))]
        jina = Jina()
        today = dt.date.today().isoformat()
        with cf.ThreadPoolExecutor(a.workers) as ex:
            out = list(ex.map(lambda r: scrape(r, jina, today), rows))
        out_f = d / f"contacts{a.suffix}.csv"
        with open(out_f, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=COLS)
            w.writeheader()
            w.writerows(out)
        log.rec["outputs"] = [str(out_f.relative_to(out_f.parents[2]))]
        found_phone = sum(1 for r in out if r["phone"])
        found_email = sum(1 for r in out if r["email"])
        notes_counts = collections.Counter(r["notes"] for r in out if r["notes"])
        log.rec["counts"] = {"total": len(out), "phone": found_phone, "email": found_email,
                             "notes": dict(notes_counts.most_common())}
        log.rec["api_calls"] = dict(jina.calls)
        print(log.rec["counts"], log.rec["api_calls"])


if __name__ == "__main__":
    main()
