# The 2026-10-09 re-measure

Written 2026-09-25, to be run **two weeks after the deploy**. Everything shipped on
2026-09-25; this is the session that finds out whether it did anything.

Runs in about 30 minutes, most of it waiting on Claude. Needs no decisions from anyone.

## What this is measuring against

`docs/seo/answer-share/2026-09-23/report.md`, taken **before** anything was deployed:

- **CraneSignal named in 0 of 56 answers.**
- CoStar 61%, Yardi Matrix 55%, RealPage 48%, Apartments.com 32%, Zillow 20%.
- "Go read the public records yourself" 27%.
- By intent: sales CoStar 90% · pipeline Yardi Matrix 75% · free-data Yardi Matrix 70% ·
  prospecting CoStar 67% · detect-software AppFolio and RealPage 100%.

## The run

```bash
cd C:/Users/david/projects/cranesignal
git pull

# 1. The AI half. Both engines, 28 questions, ~35s each for Claude, ~7s for Gemini.
#    Resumable: one JSON per answer, so a stop costs nothing.
python3 tooling/seo/sample.py

# 2. The site half -- confirm nothing regressed while nobody was looking.
bash tooling/qa/check-seo.sh --live-required
python3 -m pytest -q tooling/qa/fixes_tests
```

`sample.py` writes to `docs/seo/answer-share/<today>/`. Needs `GEMINI_API_KEY` in `.env.seo`
(gitignored, already there) and the Claude subscription for `claude -p`.

Then, by hand in a browser:

3. **Search Console** → Performance. Record total impressions, total clicks, and the queries
   list if there is one. Two weeks is early: a handful of impressions is a real signal, zero
   is not yet a failure.
4. **Search Console** → Pages. How many of the 21 URLs are indexed, and the reason given for
   any that are not.
5. **Bing Webmaster Tools** → how many pages indexed. IndexNow should have made Bing faster
   than Google here.

## What to write down

Append to `docs/seo/answer-share/<today>/report.md` or a short note beside it:

| Number | 2026-09-23 | 2026-10-09 |
|---|---|---|
| CraneSignal named, of 56 | 0 | |
| Google impressions | 0 (not verified yet) | |
| Google pages indexed, of 21 | 0 | |
| Bing pages indexed, of 21 | 0 | |
| CoStar share | 61% | |
| Yardi Matrix share | 55% | |

## How to read it

**Two weeks is early.** Expected, honestly: a few Google impressions, most pages indexed by
Bing, and **CraneSignal still named in 0 of 56**. AI citation needs the pages indexed *and*
other sites pointing at them, and none of that has had time.

- **Pages indexed but zero impressions** — normal. Google knows the pages exist and has not
  ranked them for anything yet. Wait.
- **Pages not indexed after two weeks** — read the reason in Search Console. "Discovered,
  currently not indexed" means wait. "Crawled, currently not indexed" means Google judged the
  page not worth keeping, which is the signal to worry about, and the thin-page limits in
  `PLAN-seo-geo-strategy.md` are where to look.
- **CraneSignal named even once** — genuinely good this early. Note which question and which
  engine; that intent is the wedge to push on.
- **Shares moved a few points with no CraneSignal mention** — noise. These numbers wobble
  week to week on their own. Only a repeated, sizeable change means anything.

`test_seo_sample.py` has a test asserting CraneSignal appears in **zero** answers. When it
fails, the work landed: update the baseline note in `docs/seo/HANDOFF.md` and the test, not
the other way round.

## If nothing moved

That is the expected two-week result and not a reason to change course. The decisions in
`PLAN-seo-geo-strategy.md` were made on evidence and none of it has expired. The three things
worth doing then, in order:

1. **Write the free-data page.** The measurement's clearest finding: engines name paid tools
   70% of the time on questions that explicitly ask for free data, because no free source
   exists. Nothing on the site answers that question head-on yet.
2. **Get onto the surfaces the engines already read** — Multi-Housing News, CRE Daily,
   Multifamily Dive, Reddit. "291,126 units in the Texas pipeline, every building sourced" is
   a real story. That is outreach, not code, and it is the ceiling on everything else.
3. **Re-measure again at 6 weeks** (2026-11-06). Search rankings take two to three months;
   judging at two weeks and quitting would be the actual mistake.

## Do not, at this checkpoint

- **Do not add more pages.** 18 is deliberate. Volume is what triggers the sitewide
  thin-content penalty, and none of the current pages has had time to prove itself.
- **Do not change the question bank.** Comparability across runs is the whole point. Adding
  questions is fine; editing or removing existing ones breaks the series.
- **Do not buy backlinks.** Still no.
