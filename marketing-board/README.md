# CraneSignal ready post shelf

A one-page posting shelf for CraneSignal public posts. It works one target at a time: only the current target is active, and future targets stay locked until Drew says the current one is done.

- Open: `bash ./start.sh` then http://localhost:8740
- Edit: update the `PLATFORMS` list in `index.html`.
- Current target: set `CURRENT_PLATFORM` and mark the matching platform with `current: true`.
- One post per platform during the first pass. Extra ideas go in `parked-post-drafts.md`, not on the shelf.
- Every post is `status: "draft"` until Drew explicitly approves that platform. Approval flips it to `status: "ready"`. Nothing gets marked ready on its own.
- Multifamily Insiders is done: posted 2026-09-21, marked READY.
- The UGC video (`assets/cranesignal-ugc-video.mp4`) is the campaign asset for the first pass: it rides every platform. Video platforms post it native; text platforms (Reddit, CREtech, PropTechBuzz, Blog, Substack, Medium) attach or embed it.
- Video platforms: X, LinkedIn, TikTok, YouTube, Facebook, Threads. Text is varied per platform.
- Reddit leads with a video feedback post in r/PptyMgmtSoftware.
- Drafts belong on the shelf, but keep them complete: every part filled in, no placeholders.
- Each post can have parts like `caption`, `title`, `description`, `publicComment`, or `firstComment`.
- Target chips can name public communities or sections, but they are not ready posts.
- Public newsletter or blog-style posts are allowed when they are visible as public posts.
- Do not add email blasts, DMs, outreach, or private messages.
- Communities are added under a platform only after a real public community is found and a post is ready for it.
- SEO: titles and descriptions on web-visible posts (Blog, Medium, Substack, PropTechBuzz, CREtech, YouTube) should carry the words our buyer searches, phrased naturally.

Before posting to Reddit, Facebook groups, LinkedIn groups, Slack groups, or forums, check that place's current rules in the browser.
