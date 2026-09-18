# Case Study live output review handoff

## Purpose

- Review the **actual results Drew sees on the live Case Study page**, one record at a time.
- Explain each result in plain English before discussing code or architecture.
- Decide whether each result is **correct, wrong, or confusing** and say exactly why.
- Separate problems in the AI wording from problems in deterministic decisions such as consent, channel, timing, CTA, and next action.
- Do not rebuild, redesign, or run additional paid model tests unless Drew explicitly asks.

## Current live state

- The live page is `https://app.cranesignal.com/case-study` and requires Drew to sign in.
- DeepSeek is the default writer when **Force template fallback** is unchecked.
- Deterministic code decides whether contact is allowed, which channel to use, when to send, the CTA, and the next action.
- DeepSeek writes only the message wording; validators reject unsafe or malformed drafts and use a checked template as a fallback.
- The human result appears first. Exact JSON and diagnostics are under **View exact submission and checks**.
- The app intentionally does not store submitted records or results, so a reviewer cannot retrieve a previous browser run from server logs.
- Current production commit: `c379226429c477c46b43643af4e00478a74e9899`.
- The production smoke test returned `engine: model`, no fallback, no errors, and 1,887.4 ms end to end.
- The full local case study suite has 223 passing tests.

## How to run the review

1. Ask Drew to run **one input at a time** with **Force template fallback unchecked**.
2. For each result, ask him to send either one full screenshot or copy both the human result and expanded exact submission and checks.
3. Restate the result simply: send or do not send, channel, time, exact message, and next action.
4. Grade these parts separately:
   - **Permission:** Was automated contact allowed by the consent fields?
   - **Channel:** Did it choose the first preferred channel that has consent?
   - **Timing:** Does the scheduled time follow the supplied example or a clearly stated project assumption?
   - **Message:** Is it factual, natural, appropriately personalized, and free of invented claims?
   - **Opt out:** Does an SMS end with `Reply STOP to opt out.` and an email include the required email opt-out line?
   - **CTA:** Does it preserve the exact deterministic options or tour link?
   - **Next action:** Does it start the correct cadence, schedule the correct follow-up, suppress contact, create a call task, or escalate?
   - **Engine:** Does diagnostics say `model`, `template`, or `none`, and does that match the visible explanation?
5. Give one verdict: **Good**, **Wrong**, or **Confusing**.
6. If wrong, name the smallest responsible layer: input parsing, consent gate, scheduler, intent/action, AI writer, validator/fallback, or presentation.
7. Keep a numbered list of findings, but do not change code until Drew says the review set is complete.

## Supplied-example expectations

### Example 1

- Send a text message to Taylor.
- Schedule it for December 9, 2025 at 9:00 AM Central.
- Keep the subject null.
- Ask whether Thursday or Friday works and preserve CTA options `Thu` and `Fri`.
- End with `Reply STOP to opt out.`
- Start `prospect_welcome_short_horizon`.

### Example 2

- Send an email to Taylor.
- Schedule it for December 9, 2025 at 10:00 AM Central.
- Use a relevant subject.
- Mention the requested pool and fitness interests without inventing unsupported property facts.
- Preserve the exact tour link `https://oakridge.example/tour`.
- Include `To opt out of emails, click here or reply STOP.`
- Follow up in 3 days.

### Important evaluation rule

- The supplied JSONL contains an `expected` section, but the pipeline removes it before making decisions or calling the model.
- Similar wording is acceptable when the meaning, constraints, CTA, timing, and next action are correct.
- A template fallback is safe but should be called out because Drew wants to evaluate the AI path.
- One successful example does not prove all 12 hidden records will work.

## Boundaries for the new session

- Do not claim to see a browser result Drew has not pasted or attached.
- Do not expose or copy API keys.
- Do not push, deploy, or change code during the review unless Drew explicitly asks after seeing the findings.
- Do not make new paid DeepSeek calls merely to recreate a missing result; ask Drew to rerun it in the live page.
- Do not grade only the prose. The deterministic decision fields matter as much as the message wording.
- Keep explanations short and human-readable, and review one output at a time unless Drew asks for a batch summary.

## Copy-paste prompt for the fresh session

```text
Review the actual live outputs from my Case Study agent one at a time. Read casestudy/HANDOFF-output-review.md first. I will paste or screenshot each live result because the app does not save runs. For every result, explain in plain English what the agent decided, grade it Good, Wrong, or Confusing, check permission, channel, time, message, opt-out, CTA, next action, and engine, and keep a numbered findings list. Do not change code, push, deploy, or make extra paid model calls until I tell you the review set is complete.
```
