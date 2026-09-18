## Verdict

The original plan missed the second supplied example and therefore specified the wrong email timing,
CTA shape and next action. My first revision caught those issues but overcorrected by requiring
identical prose and treating identifier-based schedule guesses as established rules; the second
review below corrects those claims before implementation.

**Reading note:** findings below preserve the first review's reasoning; where its exact-wording,
`dayN`, or delivery claims conflict with the dated correction block, that block and the current plan
take precedence. Neither review is a claim that an application was implemented or tested.

## Must fix before building

### Self-review corrections, 2026-09-17 (Astra Advisor adoption)

- **Semantic matching:** the assignment explicitly asks for semantic equivalence. Exact checks remain
  appropriate for keys/nulls/actions/CTA payloads and the supplied timestamps, but harmless body
  paraphrases must pass a meaning checklist. My earlier demand for identical punctuation was unjustified.
- **Unidentifiable schedule:** both references are on Dec 9, so a common missing evaluation clock
  explains them too. Adding `dayN` to `last_interaction` is one configurable hypothesis, not a fact.
  An identifier is a hint; explicit business fields win, opaque IDs must work, and `day10` never
  proves that the next follow-up should wait ten days. A 45-day horizon cutoff is also unproven.
- **No evaluation leakage:** a held-out `expected` must never enter the engine or model. Freeze any
  learned property facts/policy from supplied examples separately and test answer invariance when
  an evaluation record's expected answer is removed or changed.
- **Simulation boundary:** outputs propose messages/actions; they do not send, book or mutate a CRM.
  Passing the sample email is not certification of delivery-law compliance, and no imaginary footer
  service should be used to claim it is compliant. Verify legal citations before public presentation.
- **Retain approved scope:** restored shipcheck judge/human-grading reuse and Drew's live-site
  acceptance as explicit requirements. Local rehearsal is only a milestone. One optional DeepSeek
  call now means one request with SDK retries disabled, matching the handoff's chosen architecture.
- **Stop order and metric honesty:** process opt-outs even when consent is already false; numeric
  replies require prior options. Personalization is our declared proxy, F1/p95 require datasets,
  absent metrics are `not_measured`, and a second failed template cannot be called a pass.

These correct my first review. Drew subsequently clarified that the original building session should
resume implementation and user testing; the walkthrough is optional. See `CHANGES-explained.md`
for the explanations and `HANDOFF-implementation.md` for the return handoff.

### Findings from the first review

1. **Honor both supplied examples.** `sample.jsonl` has two lines, despite the old plan saying "ONE"
   (`PLAN-casestudy-bot.md:15`). The omitted `prospect_long_horizon_day3` example requires email at
   10:00 local, amenity and move-month personalization, a CTA `link`, and
   `next_action={"type":"follow_up_in_days","value":3}`. The old C2/C3/C7 design would fail all of
   those. Added C0 exact golden tests and rewrote C2, C3, C5, and C7 around both records.

2. **Do not export an invented envelope.** The ground truth is the shape inside `expected`: only
   `next_message` and `next_action`. The old C7 added `decision`, `why`, `states`, classifier, score,
   and latency, while the rulebook disagreed even on whether `why` contains strings or objects
   (`RULEBOOK-research.md:198` versus old plan C7). Extra keys can fail a strict or schema-aware
   grader. The plan now exports exact `AssignmentAnswer` objects and keeps all audit data in a
   separate diagnostics object/file.

3. **Turn every assignment field into a visible check.** `required_states` are assertions, not proof:
   echoing their names does not show they ran. `personalization_score_min` cannot be "log and still
   send" as proposed by `RULEBOOK-research.md:168`; below threshold must trigger repair/fallback.
   `reply_classification_f1_min` needs a labeled corpus, confusion matrix, a stated multiclass F1
   definition, and enough variants; one STOP fixture proves nothing. `p95_latency_ms` needs repeated
   end-to-end measurements against each record's threshold, and `safety_violations_max` must be
   counted and compared. C9 now requires all of this and fails unknown states visibly.

4. **Remove internal contradictions.** The old email validator required a physical address even
   though the supplied expected email has none, then its generic PII regex banned street addresses.
   It also applied SMS-only rules (one question and numbered options) to an expected email with a
   link and no question. C4 is now channel-specific, accepts the golden email, treats any production
   postal footer as transport-layer behavior, and uses contextual allowlists instead of banning all
   money/address text.

5. **Make the deadline and deployment state truthful.** A 1,200 ms call plus a 1,200 ms retry cannot
   fit a 2,000 ms total budget without a shared deadline. A live production check also cannot happen
   before the explicitly forbidden push. C6 now uses one monotonic budget and C11 stops at locally
   verified, ready-to-push wiring; production verification waits for Drew's authorization.

6. **Do not fabricate data absent from the input.** The expected email's
   `https://oakridge.example/tour` and "24/7 fitness center" detail are not present in that record's
   input. They are learnable only from the supplied input/expected training pair, not from a new
   property's input. C3/C5 now allow the observed Oak Ridge mapping, prefer an explicit link, and
   require a visible unresolved-link fallback for unseen properties instead of inventing a domain.

## Disagreements with the rulebook

- **Send time is not "next 09:00" universally.** The second expected email is Tuesday Dec 9 at
  10:00, although its Saturday Dec 6 interaction was before 09:00. Both examples fit a stronger
  hypothesis: parse `dayN`, add N local calendar days, use an observed channel slot (09:00 SMS,
  10:00 email), and advance when the slot has passed. That remains an inference, but unlike the old
  rule it explains both examples.

- **The proposed horizon tiers contradict input evidence.** The second task calls a roughly 68-day
  move `long_horizon`; the rulebook calls 46-120 days medium (`RULEBOOK-research.md:30,132-134`).
  Preserve the explicit task-id label; absent one, a two-tier <=45/>45 fallback is more defensible
  than inventing a medium class never observed.

- **Cadence action naming is not general.** The first record starts a named cadence, but the second
  says `follow_up_in_days` with numeric `value`. The rulebook's universal cadence-name pattern and
  `next_action` requirement to "Always include name" (`RULEBOOK-research.md:202`) are false.

- **The CTA is a union, not always options.** SMS has `{type, options}`; email has `{type, link}`.
  `RULEBOOK-research.md:200` drops the observed email form. Nulls and exact enums remain meaningful:
  SMS `subject` is present and null, timestamps have seconds and local numeric offsets, and
  `book_tour` maps to `schedule_tour`.

- **Legal safety defaults were presented as learned rules.** Frequency caps, voice handling,
  inbound-reply taxonomy, statewide quiet-hour intersections, medium horizons, and broad intent
  tables are useful defensive hypotheses, not derivable from two examples. Keep them with
  `conservative_default` labels so a reviewer can distinguish evidence from policy.

- **Personalization was under-modeled.** The second expected message uses `amenity_interest` and
  `move_date_target`; the seven-slot score in `RULEBOOK-research.md:33` ignores both and can award a
  high score to a visibly generic email. Score safe fields that are relevant to the chosen template,
  and show the evidence rather than only a float.

- **Some output facts are unidentifiable for an unseen property.** A tour URL, postal address, and
  "24/7" amenity detail cannot be recovered when the input does not contain them. Memorizing the
  observed Oak Ridge facts is legitimate use of the supplied training pair; synthesizing analogous
  facts for a new property is not. The live explanation must name that boundary.

## Revised task list

1. **Contract first (C0-C3):** freeze both exact expected objects; normalize input; implement gates;
   then derive channel, time, horizon, CTA, and action with tests that explain both goldens.
2. **Safe generation (C4-C7):** channel-specific validation, exact offline templates, bounded model
   wording, then separate public submission bytes from diagnostics. C4 and C6 were too large, so
   each now has one narrowly stated contract and explicit failure-path tests.
3. **Evidence (C8-C9):** use at least 16 single-purpose practice cases plus a balanced reply corpus;
   grade exact fields, required states, every constraint/threshold, macro-F1, safety count, and
   repeated p95. The former "12" list actually named 14 cases if Phoenix/LA and Saturday/Sunday are
   counted separately, while the rulebook heading said 14 above a 16-row table.
4. **Demo path (C10-C11):** prove arbitrary-batch paste, exact copy/download, partial-error handling,
   offline mode, auth, container isolation, restart, and missing-key recovery locally. Production is
   explicitly deferred until the authorized push.
5. **Story and rehearsal (C12-C13):** Under the Hood consumes the independent decision log and labels
   observed versus assumed claims; rehearsal covers goldens, 12 records, offline mode, malformed
   middle input, export parsing, and a one-page recovery card.

**Hold-out call:** keep consent/channel ordering, pre/post-slot timing, DST, STOP, and sensitive-profile
cases. Add the supplied email flow as a release gate, multi-digit `day10`, missing tour link, unknown
required state, below-minimum personalization, and a malformed middle batch record. Deprioritize
voice-only and the combined six-month/missing/past-date scenario; they are less likely than failures
already exposed by the assignment itself and can stay in the expanded suite rather than the first 12.

## Cut list

Cut the live tone judge first: with no calibration labels it is presentation, not evidence. Cut UI
decoration and broad persona/intent coverage next; keep only both observed flows plus focused safety
cases. Do not spend interview-eve time integrating a full rules engine, Presidio, embeddings, area-
code timezone inference, or a large fair-housing model. If still behind, shorten Under the Hood to
the decision log and measured results, but never cut exact golden tests, offline templates, per-field
threshold checks, batch export, or the recovery rehearsal.

## Live-demo risks

- **Wrong despite looking polished:** the second supplied example fails. Mitigation: exact two-record
  golden test is the first build task and a release gate.
- **Copy/export rejected:** diagnostics or missing nulls leak into the submission. Mitigation: one
  strict public schema, no extra keys, byte-identical CLI/UI export, and reparse downloaded JSONL.
- **Model timeout or invalid JSON:** a retry overruns 2 seconds. Mitigation: shared monotonic deadline,
  prevalidated offline fallback, visible engine badge, and missing-key/network-off rehearsal.
- **One bad hold-out aborts all 12:** parser raises or the page loses completed results. Mitigation:
  per-line isolation, ordered results, structured error card, request/batch limits, and malformed-
  middle-record test.
- **Deployment/auth failure on screen:** route loops, service sleeps, key is absent, or a restart
  loses the page. Mitigation: health/auth/restart checks, warm-up before interview, local fallback,
  and a recovery card with exact restart/offline/export steps.

The single case most likely to fail was not hypothetical: it was the second supplied example,
`prospect_long_horizon_day3`, because four central plan assumptions contradicted its expected block.

### Changes made to `PLAN-casestudy-bot.md`

This list records the first pass; the self-review block above records every subsequent correction.

- Corrected the sample count and promoted both expected blocks to immutable golden fixtures.
- Added observed/input-required/conservative-default confidence labels.
- Split exact assignment output from diagnostic metadata and made extra public keys invalid.
- Re-derived time, horizon, CTA, personalization, and next-action behavior from both examples.
- Made validation channel-specific and removed the impossible email-address/PII contradiction.
- Added a shared latency budget, configurable model preflight, and explicit fallback tests.
- Made all required states, constraints, and thresholds visible, measured acceptance checks.
- Replaced the miscounted practice set with focused fixtures plus a balanced classifier corpus.
- Added batch-order, partial-error, exact export, browser, auth, restart, and offline recovery checks.
- Reconciled no-push with deployment by stopping at locally verified, ready-to-push wiring.
