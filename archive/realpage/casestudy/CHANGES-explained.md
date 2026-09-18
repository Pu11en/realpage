# What changed, one decision at a time

Status: documents revised; no application code built and nothing pushed.
Drew initially asked for a walkthrough, then chose to return to the original building session.
This list remains available for optional explanation; it no longer blocks the implementation handoff.
No approval is inferred from reading this file or choosing an explanation format.

## 1. Teach and test both supplied examples

Before: the plan assumed there was one example, a text message.
After: it uses both supplied examples, including the email.
Why: the email needs different timing, a tour link, amenity details and a different next step.
Evidence: the two records in `data/sample.jsonl`.
Status: clear correction; both remain reference cases in the proposed build.

## 2. Keep the answer easy to submit

Before: the exported answer included internal explanations, scores and timings.
After: the default export mirrors the two observed answer sections; explanations remain beside it.
Why: Drew can copy the submission without editing out the debugging information.
Limit: the interviewer's full submission schema has not been provided; the export can be adapted.

## 3. Match meaning, without requiring identical sentences

My first revision required exact wording, which went beyond the assignment.
Corrected: test facts, decisions and required fields strictly, while allowing a message to say the
same thing naturally. Exact template snapshots can still catch accidental template changes.
Evidence: the assignment says "semantically matches."

## 4. Separate what we know from what we guessed

We know the sample text says 9 a.m. and the sample email says 10 a.m.
We do not know the universal scheduling rule, whether the task's day label controls scheduling,
or exactly where a short move horizon becomes long.
After: these are visible, adjustable assumptions; explicit input facts outrank labels in task names.
My first revision overstated how much the second example proved.

## 5. Personalize using useful facts

Before: a message could earn a high score from basic fields while ignoring the requested amenities.
After: the email checks whether relevant interests and move timing are reflected correctly.
Limit: this is our declared scoring formula; RealPage has not supplied theirs.

## 6. Give email and text their own checks

Before: email could fail text-message rules such as numbered choices or a mandatory question.
After: email can have a subject and link; text can have numbered tour options and a null subject.
Also: a simulated answer is not a real delivery system or proof of complete legal compliance.

## 7. Make the two-second limit possible

Before: two 1.2-second model attempts could already exceed two seconds.
After: at most one model request, one shared deadline, then a checked offline template.
The engine reports whether it used the model or fallback; it cannot disguise failure as success.

## 8. Measure the promises honestly

Before: several required checks were named without a complete way to measure them.
After: show each check's result, measure classifier quality on labeled replies, and measure speed
across repeated runs. Missing evidence is marked unmeasured, not passed.
Practice cases show which cases work; they cannot promise the hidden interview cases will pass.

## 9. Handle troublesome records without losing the batch

After: a malformed record gets its own error; the other answers remain exportable and ordered.
STOP is processed even if consent is already false, and a numbered reply needs previous options.
No actual messages or bookings are made: the assignment outputs proposed messages and actions.

## 10. Preserve the agreed product and prepare the handoff

Kept: DeepSeek, offline templates, the separate service, existing sign-in, shipcheck evaluation,
the Case study tab and Under the Hood story.
Clarified: local rehearsal precedes Drew's authorized deployment; live-site acceptance is still
required. The implementation instructions are ready for the original session to resume.

## Saved walkthrough state

- Current action: return the completed second opinion to the original building session.
- User preference: plain English, one item at a time, lower-cost bounded agents when useful.
- Latest direction: resume the original session to build, verify, show a preview, and iterate with Drew.
- Walkthrough: optional reference; do not require item-by-item approval before building.
