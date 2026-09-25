# cranesignal.com — finished files, drop them in

Built 2026-09-25 from the live page. `index.html` here **is** the live page with only the
`<head>` changed: same design, same copy, same 739 words of body text, byte-identical below
`</head>`. Nothing visual changes.

## What to do

1. Copy `index.html` over `marketing/landing/index.html` in the landing repo.
2. Put `robots.txt`, `sitemap.xml` and `llms.txt` at the **site root**, so they serve at
   `https://cranesignal.com/robots.txt` and so on.
3. Deploy.
4. Check:

```bash
for p in /robots.txt /sitemap.xml /llms.txt; do
  printf "%-14s " "$p"; curl -s -o /dev/null -w "%{http_code}\n" "https://cranesignal.com$p"
done
```

5. Search Console → Sitemaps → submit `https://cranesignal.com/sitemap.xml`.
   (The domain is already verified, so it is already covered — this just adds the sitemap.)

## What changed in index.html

- **Title** was 68 characters, so Google cut "still need a manager" off the end. Now 57:
  *New Apartment Building Leads Before Lease-Up | CraneSignal* — leading with the phrase a
  buyer would actually type.
- **Added `canonical`**, so `?utm_source=...` variants stop counting as separate pages.
- **Added `og:url`, `og:image`, `og:site_name` and a Twitter card.** There was no image, so
  every share and every AI preview was a blank rectangle. It points at the 1200×630 card
  already live on the app; copy it locally and change the two URLs if you would rather.
- **Added JSON-LD** with `Organization`, `WebSite` and `Service`. The page had none at all.

## Why the JSON-LD is the one that matters

Nothing anywhere declared that CraneSignal is an entity, or that `cranesignal.com` and
`app.cranesignal.com` are the same outfit. To a model they read as two unrelated sites that
happen to share a name, which is exactly the split that stops it recommending you by name.

`@id: https://cranesignal.com/#org` is now the single identity for the brand, and `sameAs`
ties the app to it. The app already ships the matching half (deployed 2026-09-25).

Deliberately **not** added: a `FAQPage` block. Schema that states something the page does not
visibly show risks a spam verdict, and this page has no visible FAQ. If one gets written, the
schema can follow it.

## One follow-up, once this is live

The app currently declares its own `Organization` at `https://app.cranesignal.com/#org`. Once
this page ships, the app should reference `https://cranesignal.com/#org` instead, so there is
one identity rather than two that agree. One line each in `tooling/seo/build_seo_files.py` and
`tooling/seo/build_pages.py` in the `realpage` repo — say the word and it ships in minutes.
