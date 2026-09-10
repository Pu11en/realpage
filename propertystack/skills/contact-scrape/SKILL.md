---
name: contact-scrape
description: PropertyStack — phone/email for each apartment community, scraped from its own website via Jina. Use after build-table, before the frontend needs contacts.csv.
---

# contact-scrape

**Reads:** `data/<area>/master.csv`
**Writes:** `data/<area>/contacts.csv` (columns in `CONTRACTS.md`) + a run log in `runs/`

## Run
`python3 skills/contact-scrape/run.py --area plano-richardson`

## What it does
1. For each row in `master.csv` with `website_confidence` high or medium (same gate
   `detect-software` uses), Jina-reads the site and regex-extracts a phone number
   and an email address from the page text.
2. Rows with no usable website, or where nothing was found, still get a row with
   blank `phone`/`email` and a `notes` value (`no-website` or `no-contact-found`),
   so `contacts.csv` always has exactly one row per building.
3. Junk emails from template/tooling domains (Wix privacy proxy, Sentry, schema.org,
   ...) are filtered — see `EMAIL_REJECT_DOMAINS`.
4. Runs 5 requests in parallel (`--workers`, default 5). ~$0.20 total (one Jina
   Reader call per high/medium-confidence site — same page detect-software already
   fetched, not cached, so this is a second full Reader pass).

## Check after running
- Counts (`phone`/`email` found, `notes` breakdown) are printed and logged (`runs/`).
- Spot-check a handful of found phone numbers/emails by opening `source_url` —
  regex can grab a fax number or a generic corporate contact instead of the leasing
  office's.

## Limits
- Never invents contact info — only passes through what Jina actually scraped, per
  the chatbot's hard guardrail. If nothing is found, `notes` says so.
- One phone and one email per building (first regex match after filtering), not
  every contact on the page.
- Same website-confidence gate as `detect-software`: `low`/`none` sites are skipped.
