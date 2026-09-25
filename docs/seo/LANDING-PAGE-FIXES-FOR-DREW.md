# cranesignal.com — the SEO fixes, ready to paste

Written 2026-09-25. For Drew: these apply to the landing page in the `business/` repo
(`business/marketing/landing/index.html`), which is not in the `realpage` repo, so nobody
else can ship them.

`app.cranesignal.com` already has all of this — merged and deployed today (PR #1). The
landing page is now the weaker of the two, and it is the page that ranks for the brand name.

## What the live page gets right

Genuinely good, and worth saying because it means this is a small job:

- **Server-rendered.** 732 words of real text with one `<h1>`, nine `<h2>`s and sixteen
  `<h3>`s, all present without JavaScript. The app had none of that before today.
- Title and meta description are real and specific.
- Three Open Graph tags present.
- No `noindex` accident, no `X-Robots-Tag`. 404s return 404.

## What is missing

| Gap | Effect |
|---|---|
| No `robots.txt` | AI crawlers have no stated policy. GPTBot, ClaudeBot, PerplexityBot and the search-index crawlers are the ones that produce citations. |
| No `sitemap.xml` | Google has no list of pages and no freshness signal. |
| No `llms.txt` | Nothing tells an answer engine what this site is the primary source of. |
| **No JSON-LD at all** | **The biggest one.** There is no `Organization` anywhere on the brand domain, so nothing declares that CraneSignal is an entity, or that `cranesignal.com` and `app.cranesignal.com` are the same outfit. This is the thing that makes a model unsure who you are. |
| No `canonical` | Any parameter variant (`?utm_source=...`) can be treated as a separate page. |
| No `og:image`, no `og:url`, no Twitter card | Every share and AI preview is a blank rectangle. |
| Title is 68 characters | Google cuts around 60, so "still need a manager" is dropped from the result. |

## Fix 1 — replace the `<head>` metadata

In `index.html`, replace the `<title>` + meta block with this. The existing `<link rel="icon">`
and the two font preloads stay exactly as they are.

```html
<title>New Apartment Building Leads Before Lease-Up | CraneSignal</title>
<meta name="description" content="A sourced list of new and recently sold apartment buildings in your metro, with who owns them, who manages them, and why to call now. Free, every fact links to a public record.">
<link rel="canonical" href="https://cranesignal.com/">
<meta property="og:type" content="website">
<meta property="og:site_name" content="CraneSignal">
<meta property="og:url" content="https://cranesignal.com/">
<meta property="og:title" content="New Apartment Building Leads Before Lease-Up | CraneSignal">
<meta property="og:description" content="A sourced list of new and recently sold apartment buildings in your metro, with new leads added all the time. Every fact links to a public record.">
<meta property="og:image" content="https://app.cranesignal.com/img/og-default.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://app.cranesignal.com/img/og-default.png">
<meta name="theme-color" content="#1a3d8f">
```

The new title is 57 characters and leads with the phrase a buyer would type. The share image
is already live at that URL (1200×630, built from the site's own colours and real totals); copy
it into the landing repo and change the two URLs if you would rather serve it locally.

## Fix 2 — add the JSON-LD block

Paste this immediately before `</head>`. This is the highest-value change on the page.

`@id: https://cranesignal.com/#org` becomes the one canonical identity for the brand, and
`sameAs` declares that the app is the same outfit. Everything else on both hosts can then
reference it instead of each page inventing its own.

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://cranesignal.com/#org",
      "name": "CraneSignal",
      "url": "https://cranesignal.com/",
      "logo": "https://app.cranesignal.com/img/og-default.png",
      "description": "Sourced leads on apartment buildings that are newly permitted, under construction, or recently sold, for people who sell to apartment owners.",
      "sameAs": ["https://app.cranesignal.com/"]
    },
    {
      "@type": "WebSite",
      "@id": "https://cranesignal.com/#site",
      "url": "https://cranesignal.com/",
      "name": "CraneSignal",
      "publisher": { "@id": "https://cranesignal.com/#org" },
      "inLanguage": "en-US"
    },
    {
      "@type": "Service",
      "name": "Apartment construction and sales lead list",
      "provider": { "@id": "https://cranesignal.com/#org" },
      "areaServed": { "@type": "Country", "name": "United States" },
      "description": "Every lead in every covered area: stage, units, opening or sale date, owner or developer, the office phone when it is public, and a source link for every fact.",
      "offers": {
        "@type": "Offer",
        "price": "0",
        "priceCurrency": "USD",
        "description": "Free, no account required. A free account adds the manager name and direct phone."
      }
    }
  ]
}
</script>
```

**Do not add a `FAQPage` block unless the questions and answers appear word for word on the
page.** Structured data that says something the page does not show risks a spam verdict, and
it would cost more than it earns.

## Fix 3 — three files at the site root

**`robots.txt`** — the three kinds of AI crawler are separate user-agents with different
consequences. Training crawlers teach future models your brand; the search-index and
live-fetch ones are where citations actually come from. Allowing only the first group is the
common mistake.

```
# CraneSignal -- cranesignal.com

User-agent: *
Allow: /

# Training
User-agent: GPTBot
Allow: /
User-agent: ClaudeBot
Allow: /
User-agent: Google-Extended
Allow: /
User-agent: Applebot-Extended
Allow: /
User-agent: CCBot
Allow: /

# Search index -- citations in ChatGPT, Claude and Perplexity search
User-agent: OAI-SearchBot
Allow: /
User-agent: Claude-SearchBot
Allow: /
User-agent: PerplexityBot
Allow: /
User-agent: Bingbot
Allow: /

# Live fetch -- a page load at the moment someone asks a question
User-agent: ChatGPT-User
Allow: /
User-agent: Claude-User
Allow: /
User-agent: Perplexity-User
Allow: /

Sitemap: https://cranesignal.com/sitemap.xml
```

**`sitemap.xml`** — update `lastmod` when the page changes. An honest date is a freshness
signal; a date bumped without a content change backfires when detected.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://cranesignal.com/</loc>
    <lastmod>2026-09-25</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>
```

**`llms.txt`** — the guide an answer engine reads to decide what this site is the primary
source of.

```markdown
# CraneSignal

> A free, sourced list of apartment buildings in the United States that are newly permitted,
> under construction, or recently sold. Every building links the public record it came from.

CraneSignal exists for people who sell to apartment owners: software companies, service
providers, vendors and their sales teams. It answers one question -- which buildings are
about to need something, and why now -- from public records only.

## Pages

- [CraneSignal](https://cranesignal.com/): what it is and who it is for.
- [The lead list](https://app.cranesignal.com/index.html): every building, by state.
- [Construction pipeline by metro](https://app.cranesignal.com/leads/tx.html): building-level
  detail for Dallas-Fort Worth, Houston, Austin, San Antonio and Phoenix.
- [How it was built and checked](https://app.cranesignal.com/under-the-hood.html)
- [Full data summary](https://app.cranesignal.com/llms-full.txt)

## Where the data comes from

State and city construction permit records, county appraisal-district sale records, and public
announcements. No proprietary feeds, no purchased lists, no scraped logins. A fact with no
public source is left blank rather than estimated.

## Citing this

Counts change as new records appear. Quote the "last updated" date with any number.
Building-level claims should link that building's own source record.
```

## Fix 4 — after it deploys

1. Search Console is already verified for the whole domain (DNS, done 2026-09-25), so
   `cranesignal.com` is already covered. Submit the new sitemap:
   Sitemaps → `https://cranesignal.com/sitemap.xml`.
2. Bing Webmaster Tools is already imported from Search Console.
3. Check the three files actually serve:

```bash
for p in /robots.txt /sitemap.xml /llms.txt; do
  printf "%-14s " "$p"; curl -s -o /dev/null -w "%{http_code}\n" "https://cranesignal.com$p"
done
```

## One thing to decide

`app.cranesignal.com` currently declares its own `Organization` at
`https://app.cranesignal.com/#org`. Once the landing page ships the block in Fix 2, the app
should reference `https://cranesignal.com/#org` instead, so there is exactly one identity
rather than two that happen to share a name. That is a one-line change in
`tooling/seo/build_seo_files.py` and `tooling/seo/build_pages.py` in the `realpage` repo —
tell whoever is working on it and it ships in minutes. Until then the two are linked by
`sameAs`, which is weaker but not wrong.
