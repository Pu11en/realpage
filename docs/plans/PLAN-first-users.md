# Getting the first users

Written 2026-09-25, after the SEO work shipped. SEO is a two-to-three month channel and it
is now running on its own. This plan is about the weeks in between.

## The honest situation

**What exists:** 1,861 sourced buildings across Texas and Arizona, free, with a PDF call
list and a CSV anyone can download without an account. A landing page, an app, a chat agent.

**What is missing:** people who know it exists. One public post has gone out (Multifamily
Insiders, 2026-09-21). Search will not deliver anyone for months.

**What is already researched and not yet used:** `docs/2026-09-20-maintenance-software-icp.md`
names the buyer precisely — companies selling software *to* apartment operators, not the
operators themselves — and lists specific first targets **with phone numbers and email
addresses already found**: AppWork, Leonardo247, Maintenance Care and others. That research
is the most valuable unused asset in the repo.

It also states the pitch, and it is a good one:

> "We found Texas apartment communities with maintenance pain signals and can give you a few
> accounts your sales team should look at for free."

Nobody has sent that yet.

## The bottleneck, named

The posting shelf (`marketing-board/`) has 14 platforms with drafts sitting ready and a rule
that each one waits for Drew's explicit approval, one at a time. Four days in, one post has
shipped. That pace is a choice about quality, not a mistake — but it means **the public-post
channel cannot be the only thing running**, because at one post per platform it is months of
calendar time for a few hundred impressions.

Direct outreach to the named vendors is the channel that can produce a user this week. It
needs a human to send it. What it does not have, and what makes the difference between a
reply and silence, is **something concrete attached**.

## What to build: the vendor sample pack

One page, per vendor, that Drew can attach to an email or paste into a message.

Not the whole database. Not a login. Twelve to fifteen specific buildings chosen for *that
vendor's* reason to care, each with the address, the stage, the date, and the public record
it came from — so the reader can check any line in thirty seconds and find it true.

For a maintenance-software vendor like AppWork or Leonardo247, the selection is buildings
that are **about to open**: 105 are expected to open in 2027–2028, and a building that has not
opened has not chosen its maintenance software, its vendors, or its service contracts. That is
the whole thesis of the product, stated as a list of twelve addresses.

The pack ends with one line: the full list is free at app.cranesignal.com, no account.

**Why this and not a nicer landing page:** the reply rate on "here are twelve buildings your
team should call, and here is where each one came from" is not comparable to "check out my
site". The data is the pitch. Everything else is packaging.

### Build notes

- Generator in `tooling/outreach/`, reading the same `site/data/areas/*.json` everything else
  reads. One HTML page per pack, printable to PDF, no JavaScript, same rules as the SEO pages:
  every row carries its source link, blanks mean the record is silent.
- Selection is by **rule, not by hand** — "opening in the next 18 months, 100+ units, in the
  metros this vendor sells into" — so a second pack for a different vendor is one command, and
  so the choice is defensible when a reader asks why these twelve.
- Reuse `pretty()`, `fmt_date()` and the source-link logic from `tooling/seo/build_pages.py`
  rather than writing a second copy.
- Tests: every row has a working source link, no row is older than the stated window, the pack
  names its as-of date, no RealPage text.

## The order to do things in

1. **Vendor sample packs** — the thing that makes outreach convert. Half a day.
2. **Drew sends ten.** The ICP doc already has the names, numbers and addresses. Ten emails
   with a real pack attached is a realistic morning, and ten is enough to learn whether the
   pitch lands.
3. **Watch what comes back.** Ten sends with zero replies says the pitch is wrong, which is
   worth knowing in a week rather than a quarter. Any reply is a conversation with a named
   buyer, which is worth more than every impression the posting shelf will earn this month.
4. **Keep the posting shelf moving at its own pace.** It is not the fast channel, but it
   compounds and it is already built.

## What was fixed today, because it blocks all of this

The 18 SEO pages had **no call to action at all**. Someone arriving on the Houston page could
read 443 buildings and leave, because nothing told them what to do next. Every page now
deep-links the app at its own state, says what is free without an account, and links the
ask-for-your-metro form. Live and verified.

This matters more for outreach than for search: a pack that says "the full list is free at
app.cranesignal.com" sends the reader to a page that now has a next step instead of a dead end.

## What not to do

- **Do not buy a lead list of vendors.** The ICP research already named them, with contacts,
  from public sources. Buying would be slower and worse.
- **Do not build a paid tier yet.** Nobody has used it. Pricing a thing nobody wants is the
  classic way to learn nothing.
- **Do not widen coverage to more states to seem bigger.** Texas and Arizona are enough to
  prove the pitch. A vendor who sells nationally still only needs twelve buildings to judge
  whether the data is real.
- **Do not send the whole database.** The pack works because it is short and checkable.
