# Google setup for CraneSignal SEO — click-by-click

Written 2026-09-23 for David. Everything here is free; no credit card, no billing account.
Works on a phone browser, easier on a laptop. Total time ~45 min, plus waiting for DNS.

**Before you start, decide one thing: which Google account.** Use one account for all five
parts. A fresh `cranesignal...@gmail.com` is cleaner than a personal Gmail (you can add Drew
as an owner later), but your own Gmail works fine. Write down which one you used — the next
session will ask.

**What you'll end up with (paste these to me when done, EXCEPT the secret — see Part 6):**

| Item | Looks like | From |
|---|---|---|
| Google account used | `you@gmail.com` | you |
| Search Console property | `cranesignal.com` (Domain) or `https://app.cranesignal.com/` (URL prefix) | Part 1 |
| OAuth Client ID | `1234567890-abc...apps.googleusercontent.com` | Part 4 |
| OAuth Client secret | `GOCSPX-...` | Part 4 — **do not paste in Discord** |
| PageSpeed API key | `AIzaSy...` | Part 5 — **do not paste in Discord** |

---

## Part 0 — Do you have the Porkbun login?

CraneSignal's DNS is at **Porkbun** (I checked the nameservers: `maceio.ns.porkbun.com` etc.).

- **If you have the Porkbun login** → do **Part 1A** (the good path: covers `cranesignal.com`,
  `app.cranesignal.com`, and `www` in one property, and it never breaks).
- **If Drew has it** → either send him Part 1A (it's four steps), or do **Part 1B** instead,
  which only covers `app.cranesignal.com` and needs a code change from me first.

Porkbun login: https://porkbun.com/account/login

---

## Part 1A — Search Console, Domain property (needs Porkbun)

1. Open **https://search.google.com/search-console** and sign in with the account you chose.
2. First time: it shows a "Welcome to Search Console" screen with two boxes side by side.
   Use the **left** box, titled **Domain**. (The right one, "URL prefix", is Part 1B.)
   If you've used Search Console before, click the property dropdown, top-left → **+ Add property**.
3. In the Domain box type exactly:
   ```
   cranesignal.com
   ```
   No `https://`, no `www`, no `app.`. Click **Continue**.
4. A popup appears: **"Verify domain ownership via DNS record"**. It shows a line like:
   ```
   google-site-verification=AbCdEf1234567890...
   ```
   Click **Copy**. Leave this tab open — you come back to it in step 9.
5. New tab: **https://porkbun.com/account/login** → sign in.
6. Top-right **ACCOUNT** → **Domain Management**. Find `cranesignal.com` in the list.
7. Click the **Details** dropdown for that domain, then the **edit icon next to "DNS Records"**.
8. On the "Manage DNS Records" screen, add a record:
   - **Type:** `TXT - Text record`
   - **Host:** *leave completely blank* (blank = the root domain. Not `@`, not `www`.)
   - **Answer:** paste the whole `google-site-verification=...` line from step 4
   - **TTL:** leave the default (600) if the field is there
   - Click **Add**.
   Do **not** delete any existing TXT records — a domain can have several.
9. Back in the Search Console tab, click **Verify**.
   - Verified → done, skip to Part 2.
   - "Ownership verification failed" → normal, DNS is slow. Click **Verify** again in 15 min,
     an hour, and once more after a few hours. It almost always lands within an hour.
     The property stays in your list; you can re-verify any time.

**What this gets you:** search performance for `cranesignal.com`, `app.cranesignal.com` and
`www.cranesignal.com` all in one place.

---

## Part 1B — Search Console, URL prefix (only if you can't touch DNS)

**Tell me first** — this needs a `<meta>` tag added to the site's pages and deployed before it
can verify, which is my job and takes a deploy. Sequence:

1. You: https://search.google.com/search-console → **URL prefix** (the right-hand box) → type
   exactly `https://app.cranesignal.com/` → **Continue**.
2. On the verification screen open **HTML tag** and copy the whole line:
   `<meta name="google-site-verification" content="..." />`
3. Send me that line (this one is safe to paste — it's public once the page ships).
4. I add it to every page in `site/`, Drew deploys, then you click **Verify**.

Downside: covers only `app.cranesignal.com`. The landing page `cranesignal.com` stays
unmeasured until someone does Part 1A.

---

## Part 2 — Bing Webmaster Tools (5 minutes, do it right after Part 1)

Not optional-feeling extra: Bing's index is what **ChatGPT search and Copilot** read. For the
GEO half of this project it matters as much as Google.

1. **https://www.bing.com/webmasters** → **Sign in** → choose **Sign in with Google**, same account.
2. It offers **"Import your sites from Google Search Console"** → click **Import** → **Continue**
   → allow access → select `cranesignal.com` → **Import**.
3. That's it. Verification carries over from Google. Nothing else to configure.

(If Part 1 hasn't verified yet, come back and do this afterwards.)

---

## Part 3 — Create the Google Cloud project and turn on two APIs

This is what lets the local SEO dashboard (CrawlSEO) read your Search Console numbers.
**Free.** The two APIs below have no charge and need no billing account.

1. **https://console.cloud.google.com** → sign in with the same account.
2. First visit only: accept the Terms of Service, pick your country, click **Agree and continue**.
   If it shows a "Try for free / activate billing" banner — **ignore and close it**. You never
   need it for this.
3. Top-left, next to the "Google Cloud" logo, there's a **project picker** (says "Select a
   project" or a project name). Click it → **NEW PROJECT** (top right of the popup).
4. **Project name:** `cranesignal-seo`. Leave Organization/Location as-is. Click **CREATE**.
   Wait ~20 seconds, then use the project picker again and **select `cranesignal-seo`**.
   Everything after this must happen with that project selected — check the top bar.
5. Enable API #1 — Search Console:
   **https://console.cloud.google.com/apis/library/searchconsole.googleapis.com**
   Confirm `cranesignal-seo` is in the top bar, then click **ENABLE**.
6. Enable API #2 — PageSpeed:
   **https://console.cloud.google.com/apis/library/pagespeedonline.googleapis.com**
   Click **ENABLE**.

---

## Part 4 — The OAuth client (the login for the dashboard)

Google renamed this area to **Google Auth Platform** in 2025–26, so older guides online show
menus that no longer exist. These are the current ones.

1. Go to **https://console.cloud.google.com/auth/overview** (project `cranesignal-seo` selected).
2. If it says **"Google Auth Platform not configured yet"** → click **GET STARTED** and fill the
   4-step wizard:
   - **App Information** → App name: `CrawlSEO local` · User support email: your address → **Next**
   - **Audience** → choose **External** → **Next**
     (External just means "a normal Google account signs in". You'll restrict it to yourself in
     step 4 below, so nobody else can use it.)
   - **Contact Information** → your email → **Next**
   - **Finish** → tick the Google API Services User Data Policy box → **CONTINUE** → **CREATE**
3. Left menu → **Data Access** → **ADD OR REMOVE SCOPES**. In the filter box type
   `webmasters`, tick:
   ```
   .../auth/webmasters.readonly
   ```
   → **UPDATE** → **SAVE**. (This is the permission "read my Search Console data".)
4. Left menu → **Audience**. Under **Test users** click **+ ADD USERS**, type your own Google
   address, **SAVE**. Leave Publishing status as **Testing** — that keeps the app private to you.
   ⚠️ Known quirk: in Testing mode the login expires **every 7 days**, so you'll re-click
   "Sign in with Google" in the dashboard about once a week. That's normal and fine.
5. Left menu → **Clients** → **+ CREATE CLIENT**:
   - **Application type:** `Web application`
   - **Name:** `CrawlSEO local`
   - **Authorised redirect URIs** → **+ ADD URI** — add these **two**, exactly, no trailing slash:
     ```
     http://localhost:3100/api/auth/callback/google
     http://localhost:3000/api/auth/callback/google
     ```
     (Two because I may have to move the dashboard's port; having both saves a round trip.)
   - **CREATE**
6. A panel shows **Client ID** and **Client secret**. Click **DOWNLOAD JSON** and keep the file.
   Don't close without saving it — you can always come back via **Clients** → your client name.

---

## Part 5 — PageSpeed API key

1. **https://console.cloud.google.com/apis/credentials** (project `cranesignal-seo`).
2. **+ CREATE CREDENTIALS** → **API key**. It appears immediately — click **Copy**.
3. Click **Edit API key** (or the pencil next to it) and lock it down:
   - **API restrictions** → **Restrict key** → tick **PageSpeed Insights API** only → **SAVE**.
4. Keep the key with the JSON file from Part 4.

---

## Part 6 — Getting the credentials to me safely

**Do not paste the client secret or API key into Discord.** Put them in a file on this PC that
git already ignores. Open Notepad, paste this, fill in your values, and save it as

```
C:\Users\david\projects\cranesignal\.env.seo
```

(In Notepad's Save dialog set "Save as type" to **All Files**, or it becomes `.env.seo.txt`.)

```
# Google, created 2026-09-23 by <which gmail>
GOOGLE_CLIENT_ID=paste-here
GOOGLE_CLIENT_SECRET=paste-here
GOOGLE_PAGESPEED_KEY=paste-here
```

Then just tell me in Discord: **"`.env.seo` is ready"** plus the two safe facts — which Google
account you used, and whether Part 1A verified or you fell back to 1B. I'll wire it up from there
and confirm the file is gitignored before anything is committed.

---

## Part 7 — Later, after the site fixes deploy (I'll tell you when)

Don't do this yet — the sitemap doesn't exist until my T3 work ships.

1. Search Console → left menu **Sitemaps** → "Add a new sitemap" → type `sitemap.xml` → **SUBMIT**.
2. Search Console → search bar at the top (**URL inspection**) → paste
   `https://app.cranesignal.com/index.html` → wait for the check → **REQUEST INDEXING**.
   Repeat for `/under-the-hood.html` and each `/leads/<state>.html` page.

---

## What to expect, so nothing looks broken

- **Part 1 verification:** minutes to an hour. Retry, don't restart.
- **Search Console data:** starts appearing **2–3 days** after verification, and it will be
  **near zero** at first. That's the baseline, not a failure — the site currently has no
  robots.txt, no sitemap, and pages that are empty to a crawler until my fixes ship.
- **Anything ranking:** 2–3 months, and only after the static-page work (T4) is approved.
- **Cost:** zero. If any screen asks for a card, you're on the wrong screen — stop and ping me.

---

## Quick link list

| What | Link |
|---|---|
| Search Console | https://search.google.com/search-console |
| Porkbun login | https://porkbun.com/account/login |
| Bing Webmaster Tools | https://www.bing.com/webmasters |
| Cloud Console (home) | https://console.cloud.google.com |
| Enable Search Console API | https://console.cloud.google.com/apis/library/searchconsole.googleapis.com |
| Enable PageSpeed API | https://console.cloud.google.com/apis/library/pagespeedonline.googleapis.com |
| Google Auth Platform | https://console.cloud.google.com/auth/overview |
| Credentials / API keys | https://console.cloud.google.com/apis/credentials |
