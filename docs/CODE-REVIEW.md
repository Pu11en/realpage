# Reviewing changes with Open Code Review

Set up 2026-09-26 at David's request. [alibaba/open-code-review](https://github.com/alibaba/open-code-review)
— Apache-2.0, Go, Alibaba's internal review tool open-sourced. Run by hand on this machine;
nothing about it is scheduled.

## Why this one

Two things made it fit rather than just be available.

**Delegation mode needs no API key.** `ocr delegate` does the deterministic half — working out
which files changed, which of them are worth reviewing, and which rules apply — and hands that
to whatever agent is already in the session. No OpenAI or Anthropic key, no quota spent. That
matters here because there is a Claude *subscription* and a Gemini key, and no Anthropic API
key at all.

**It separates the parts that must not go wrong from the parts a model is good at.** File
selection, line mapping and rule resolution are ordinary code; judgement is the model's. Its
own README is blunt about the trade-off: higher precision than a general agent, lower recall,
on purpose. That is the right bias for a repo with one person reading the output.

## Install

Already installed at `~/.local/bin/ocr.exe` (v1.12.9, windows-amd64). The published
`sha256sum.txt` was checked against the download before it was run:
`ae6f4785fea34a5cfef93ad22d8e7fb8032bbd12c45f2cbcc98cbe1b38cceff1`.

There is no Go, npm or make on this machine, so the release binary is the route — not
`npm install -g` or building from source. Re-check the hash on any upgrade.

## Running it

```bash
ocr delegate preview --from main --to HEAD    # what changed, and what is worth reviewing
ocr delegate rule <file> <file>               # the rules that apply to those files
```

Then review those files against those rules. `ocr review` and `ocr scan` do it without an
agent, but both need an LLM endpoint configured.

Review the **generator**, not its output. A `--from main --to HEAD` on a normal day here lists
~37 changed files, and most are the 18 generated pages plus their CSVs and the area JSON. A
finding against a generated file cannot be acted on, because the next build overwrites it.
`.opencodereview/rule.json` says so per path, so `ocr` now marks them rather than leaving you
to notice.

## The repo's own rules

`.opencodereview/rule.json` holds six path-scoped rules. **Every one of them comes from a
defect that actually shipped**, not from a style preference:

| Path | What it guards | The defect behind it |
|---|---|---|
| `site/leads/**`, `site/data/areas/*.json` | Don't review generated output | 37-file diffs where ~30 files are build products |
| `site/data/build_data.py` | Reader-facing URLs, honest labels | 446 rows with an unopenable href; a 212 MB zip labelled "Website" |
| `tooling/seo/build_pages.py` | Page ceiling, computed claims, schema | A page naming a state it had no buildings in, in FAQ schema |
| `chatbot/linkfix.py` | Allowlists match a boundary, not a prefix | `_is_repo` approved `realpage-not-ours` |
| `tooling/qa/fixes_tests/**` | No assertion that cannot fail | Two `assert X if COND else True` where COND was never true |

Add to it when something ships that a rule would have caught. A rule with a real failure
behind it gets read; a generic one gets skipped.

## What the first run found

Run against this session's work (`cc85b9e..HEAD`), on code written the same day:

1. **`_is_repo()` matched on a bare prefix**, so `github.com/Pu11en/realpage-not-ours` and
   `realpageXYZ` were treated as the agent's approved source. Everything that allowlist
   approves skips the check that a tool actually returned the link, so a look-alike had a free
   pass through the only thing stopping an invented URL reaching a visitor.
2. **Two assertions that could never fail** — `assert X if COND else True`, where one COND
   tested a key that lives on a different schema node and the other a byte comparison that is
   always false on Windows.
3. **A label built by `rsplit(".")` on a whole URL**, so a dot anywhere in the query string won
   the split: `.../data.zip?token=abc.def` would have been labelled "Bulk records (DEF)" — in
   the one function whose job is to stop misleading labels.

All three fixed, each with a test.

One thing it flagged that was **correctly not a defect**: `csv_cell()` builds a 13-entry dict
per call, 24,193 times for the Texas page. The performance rule says confirm the scale first —
measured at 0.09 s for the whole state, on a script run by hand. Left alone. That restraint is
the point of the tool's precision bias.
