# Case-study interview card

## Three-minute explanation

1. **The boundary:** This is a separate proposal service. It reads assignment
   records and returns only `next_message` and `next_action`; it never sends a
   message, books a tour, or writes to a CRM.
2. **The safe workflow:** Code decides consent, stop requests, channel, timing,
   CTA, and compliance. A model may rewrite wording once, but the same validators
   check model and template drafts. If anything is missing, slow, or unsafe, the
   validated template wins.
3. **What is proven:** Both supplied examples pass structure and meaning checks.
   The reply score uses 24 labeled synthetic examples, and latency uses 100 warm
   offline runs. Those are practice measurements, not hidden-test or production
   claims; live-model quality and latency are still unmeasured.
4. **What you can inspect:** The left side is the exact submission object. The
   right side explains every rule, source, required state, constraint, threshold,
   fallback, and error without leaking any of it into the export.

## Run the live 12

1. Open `/case-study` in the signed-in CraneSignal preview.
2. Paste all 12 JSONL records, one object per line, or upload the supplied file.
3. Keep **Offline templates** checked unless a live model run is explicitly
   authorized and configured.
4. Click **Run records** and confirm the count says **12 records**.
5. Click **Download**. The exact ordered submission is saved as
   `case-study-submission.jsonl`, normally in the browser's Downloads folder.
6. If asked for one answer, select its numbered tab and use **Copy one**. For the
   entire submission use **Copy all** or the downloaded file.

## Recovery in under a minute

- **Model fails or stalls:** check **Offline templates** and click **Run records**
  again. The service keeps the same public contract and uses validated templates.
- **Service is down:** restart with
  `env -u DEEPSEEK_API_KEY -u DEEPSEEK_MODEL python3 -m casestudy.web --port 18091`,
  then open `http://127.0.0.1:18091/health` and look for `{"status":"ok"}`.
- **One row is malformed:** do not delete the batch. That row becomes a safe
  escalation with a visible error; the other rows stay ordered and export.
- **Download seems missing:** search Downloads for
  `case-study-submission.jsonl`; otherwise use **Copy all** and save it with that
  name.
- **Need a known-good check:** run
  `python3 -m casestudy.rehearsal --base-url http://127.0.0.1:18091 --output-dir /tmp/casestudy-rehearsal`.

## Honest limits to say aloud

- The two examples establish very little; timing and horizon boundaries remain
  visible, versioned hypotheses.
- English templates are the supported demo path; Spanish is flagged, not falsely
  claimed as translated.
- Actual email-delivery footer compliance, live provider behavior, and hidden-set
  performance are not proven here.
