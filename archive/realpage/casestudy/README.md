# Case-study service

This is a separate, read-only proposal service. It accepts assignment JSONL at
`POST /case-study/api/run`, serves the workbench at `/case-study`, and exposes
`GET /health` for the service health check. It exports proposed messages and
actions; it never sends a message or writes to a CRM.

## Local container

From the repository root:

```bash
docker build -f casestudy/Dockerfile -t cranesignal-case-study .
docker run --rm -p 18091:8080 -e CASESTUDY_OFFLINE=true cranesignal-case-study
```

Open `http://localhost:18091/case-study`. The signed-in CraneSignal preview also
routes `/case-study*` to this service through its existing authentication gate.

## Run the demo

1. Paste assignment JSONL into the workbench or choose a `.jsonl` file. One JSON
   object goes on each line.
2. Leave **Force template fallback** clear so the configured AI writes the message,
   then select **Run assignments**. The human result appears first; the exact export
   and checks stay in the expandable section and are never mixed together.
3. Use **Copy one**, **Copy all**, or **Download**. All three use the server's
   canonical serializer; the downloaded file is named
   `case-study-submission.jsonl` and normally appears in the browser's Downloads
   folder.

To rehearse the HTTP service without credentials or live model calls, start it in
one terminal and run the checker in another:

```bash
env -u DEEPSEEK_API_KEY -u DEEPSEEK_MODEL python3 -m casestudy.web --port 18091
python3 -m casestudy.rehearsal --base-url http://127.0.0.1:18091 --output-dir /tmp/casestudy-rehearsal
```

The checker runs both supplied examples, a 12-record practice batch, forced
offline copies, and a malformed middle row. It writes and reparses every export;
every line must match the strict public contract. Run the second command twice
for the full C13 dress rehearsal.

## Recovery

- **Model or key trouble:** check **Force template fallback** and run the same input
  again. The public shape is unchanged and diagnostics show `template` for a
  message or `none` for a deterministic no-send decision.
- **Service trouble:** stop the local server with `Ctrl-C`, rerun the start
  command above, open `/health`, and expect `{"status": "ok"}`.
- **One bad row:** keep the batch intact. The bad row becomes a safe escalation
  with its own error while the other rows still export in order.
- **Need the saved result:** look for `case-study-submission.jsonl` in Downloads,
  or use **Copy all** and save the exact clipboard text as a `.jsonl` file.

The one-page interview talk track and emergency checklist are in
`casestudy/INTERVIEW-CARD.md`.

## Railway service

Create a separate Railway service named `propertystack-case-study` from this
repository. Set its Dockerfile path to `casestudy/Dockerfile`; the image command
is already `python -m casestudy.web --host 0.0.0.0`, so a Railway Start Command
override is not needed. If Railway requires an explicit Start Command, use that
same command.

Set `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL`, and optionally `DEEPSEEK_BASE_URL` on
the case-study service only. Without the key or model, requests automatically
use the validated offline templates. `CASESTUDY_MODEL_BUDGET_MS` sets the hard
provider timeout and defaults to 8,000 ms; the record's `p95_latency_ms` remains a
separate measured performance target. Optional request limits are
`CASESTUDY_MAX_REQUEST_BYTES` (default 2 MiB) and `CASESTUDY_MAX_BATCH_SIZE`
(default 100). Set the front-door site's `CASESTUDY_UPSTREAM` to
`http://propertystack-case-study.railway.internal:8080`, and configure Railway's
health check path as `/health`.
