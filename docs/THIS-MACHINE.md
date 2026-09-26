# What runs on this machine

David's Windows machine, checked 2026-09-26. Written because the assumption until now was
that real work happened on Drew's Linux box, and for the SEO/GEO half of this project that
turns out not to be necessary.

## The short version

**Everything that makes the site rank runs here.** Generating the pages, generating the
spreadsheets, generating robots/sitemap/llms.txt, running the 698-test suite, measuring what
the AI engines say, and pushing URLs to Bing — all of it, no other computer involved.

Three things do not, and only one of them matters.

## What is installed

| | |
|---|---|
| Python 3.12 | yes — with `pytest`, `pypdf`, `requests`, `beautifulsoup4`, `lxml`, `Pillow`, `playwright` |
| `git`, `gh`, `curl` | yes |
| `claude` CLI | yes — so the answer-share measurement can sample Claude |
| Gemini API key | yes, in `.env.seo` (gitignored) |
| `node` | **no** |
| `caddy` / `docker` | **no** |
| `railway` CLI | **no** |

## The run order, all of it local

```bash
python tooling/seo/build_pages.py       # 18 pages + 18 CSVs + the home page block
python tooling/seo/build_seo_files.py   # robots.txt, sitemap.xml, llms.txt, llms-full.txt
python -m pytest -q tooling/qa/fixes_tests/
python tooling/seo/indexnow.py          # tell Bing what changed
```

Both generators take `--check`, which exits 1 instead of writing when the output has drifted
from `site/data/`. The test suite runs both of those, so a stale sitemap fails a test.

Deploying `app.cranesignal.com` needs no tool at all: Railway watches `main`, so merging a
PR ships it. Verify by hand afterwards.

## The three gaps, in order of how much they matter

**1. The scrapers — this is the real one.** The half of `propertystack/` that *fetches* new
records needs `crawl4ai`, `scrapling`, `httpx`, `pdfplumber`, `PyMuPDF` and `weasyprint`,
none of which are here. So **new buildings cannot be collected on this machine.** That still
lives on Drew's box.

What *does* run here is `site/data/build_data.py`, the step that turns collected records into
the JSON the site reads. Run on 2026-09-26 it reproduced the committed data byte for byte,
which is the useful thing to know: given records, this machine can rebuild everything
downstream of them.

**2. No local preview.** `tooling/dev.sh` and the two Caddy-based tests want Caddy or Docker.
Opening a generated page straight from `site/leads/` in a browser works for reading content,
but not for anything about routing or headers. 7 tests skip.

**3. The landing page cannot be deployed from here.** `cranesignal.com` ships by
`railway up` from a local checkout of `Pu11en/cranesignal-landing`, and the CLI is not
installed. The app host is unaffected.

## About the skipped tests

`698 passed, 16 skipped` is the green state on this machine. The 16 are the Node and Caddy
tests, which skip rather than fail so that a red suite still means something — see the
commit "Make the test suite mean something again". Where those tools exist,
`CRANESIGNAL_REQUIRE_TOOLS=1` turns each skip back into a failure.

If someone reports fewer than 698 passing, the generators are probably stale: run both, then
re-run the suite.
