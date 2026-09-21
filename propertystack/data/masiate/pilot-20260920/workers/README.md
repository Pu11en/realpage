# Masiate pilot worker outputs (2026-09-20)

Raw output from the parallel Masiate pilot workers. The finished results live one folder up in `pilot-20260920/`.

- `collect-<county>/`: first-pass property collection per county, plus the statewide TDLR pull.
- `review-brazos/`, `review-east/`, `review-west/`: review decisions on the collected records.
- `finish-contacts/`, `finish-coverage/`, `finish-dedup/`, `finish-evidence-qa/`: finishing passes.
- `scripts/`: the one-off scripts those workers used. They read runtime data from `~/.local/state/cranesignal/masiate/`.
