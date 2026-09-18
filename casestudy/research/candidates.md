# Repo hunt: candidates for the case-study bot

One `### ` entry per candidate, in this exact shape (the checker enforces it):

    ### <repo name>
    **URL:** https://github.com/...
    **Area:** <which hunt task found it>
    **License / stars / last commit:** ...
    **What we'd take:** <file, module, pattern or data>
    **Verdict:** USE | MIRROR PATTERN | VENDOR DATA | SKIP
    **In plain words:** <one sentence a non-engineer understands>

Already covered by earlier research (do not re-add unless the verdict changes): python-phonenumbers,
tcpa-quiet-hours, fair-housing phrase lists, CommonRegex, sms-toolkit, instructor, outlines,
guardrails-ai, NeMo Guardrails, promptfoo, Python rules engines.

## Candidates

### Novu
**URL:** https://github.com/novuhq/novu
**Area:** H1 Messaging orchestration platforms
**License / stars / last commit:** MIT (core, enterprise features separately licensed) / ~40k / active (recent)
**What we'd take:** Workflow/step model (workflow → steps: channel step vs action step like delay/digest), the digest engine pattern (jobs linked via `_parentId` for aggregation), and the embeddable subscriber preferences component concept. Look under `apps/api/src/app` for digest/preference use-cases and `libs/framework` for the step DSL.
**Verdict:** MIRROR PATTERN
**In plain words:** Novu is the closest real product to what we're building — it already models "steps," "digests," and per-user preferences, so we copy its vocabulary and workflow shape rather than its code.

### Dittofeed
**URL:** https://github.com/dittofeed/dittofeed
**Area:** H1 Messaging orchestration platforms
**License / stars / last commit:** MIT / ~2.9k / active (1,757+ commits)
**What we'd take:** Event-triggered "journeys" model and git-based versioning of messaging campaigns — useful pattern for treating cadence rules as versioned config rather than hardcoded logic. No confirmed built-in quiet-hours/frequency-cap code found in the README; would need to check `packages/backend-lib` directly to confirm before relying on it.
**Verdict:** MIRROR PATTERN
**In plain words:** Dittofeed shows a clean way to define "when this happens, send this" journeys, but it doesn't clearly have quiet-hours or frequency-cap features we could just copy.

### Laudspeaker
**URL:** https://github.com/laudspeaker/laudspeaker
**Area:** H1 Messaging orchestration platforms
**License / stars / last commit:** AGPL-3.0 (with enterprise exception) / ~2.6k / repo states it is no longer actively developed
**What we'd take:** Visual journey-builder concept and its segmentation-by-engagement-history pattern, if we ever want a visual editor reference.
**Verdict:** SKIP
**In plain words:** Laudspeaker is abandoned (no longer maintained) and AGPL-licensed, so it's not safe or current enough to build on.

### listmonk
**URL:** https://github.com/knadh/listmonk
**Area:** H1 Messaging orchestration platforms
**License / stars / last commit:** AGPLv3 / ~23.5k / active
**What we'd take:** Its subscriber/list/unsubscribe data model (Postgres schema) as a reference for consent state, not for quiet-hours or throttling — those features weren't found.
**Verdict:** SKIP
**In plain words:** listmonk is a solid newsletter tool but it's about sending campaigns, not deciding channel/timing per person like our bot needs.

### Mautic
**URL:** https://github.com/mautic/mautic
**Area:** H1 Messaging orchestration platforms
**License / stars / last commit:** GPL / ~10.5k / active (7.x branch)
**What we'd take:** Campaign/segment data model as a reference for how a mature marketing-automation tool structures contacts and consent, but no confirmed quiet-hours, frequency-cap, or DND code found in this pass.
**Verdict:** SKIP
**In plain words:** Mautic is a big marketing platform but doesn't clearly show the specific "don't message too often, respect quiet hours" logic we're after.

### Apache Unomi
**URL:** https://github.com/apache/unomi
**Area:** H1 Messaging orchestration platforms
**License / stars / last commit:** Apache 2.0 / ~375 / active (2,782+ commits, requires Java 17/Karaf/Elasticsearch)
**What we'd take:** Nothing concrete found — it's a customer-data/profile backend (OASIS Context Server spec) for personalization/A-B testing, not a messaging-cadence engine.
**Verdict:** SKIP
**In plain words:** Unomi stores user profile data for personalization but doesn't handle sending messages or timing rules, so it's off-target for this bot.

### notifkit
**URL:** https://github.com/devkitshq/notifkit
**Area:** H1 Messaging orchestration platforms
**License / stars / last commit:** MIT / ~114 / active (64 commits)
**What we'd take:** This is the most directly on-target find: explicit "timezone-aware quiet hours that defer non-urgent sends," "user preferences, topic opt-outs, and consent gates," "ordered multi-channel fallback (push, then email, then sms)" with exponential backoff, "priority scheduling with sendAt," and "stateful multi-step workflows with wait/waitForEvent." Check `notifkit.dev/docs/guides/preferences.html` and `.../routing.html` for the documented logic, then the source repo for the matching implementation files.
**Verdict:** USE
**In plain words:** notifkit is a small open-source project built almost exactly for our problem — quiet hours, channel fallback order, and opt-outs — so it's worth pulling actual code or config patterns from it, though its small size (114 stars) means it should be double-checked for maturity.
