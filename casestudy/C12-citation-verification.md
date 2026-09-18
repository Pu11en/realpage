# C12 citation verification

Checked 2026-09-17 against primary or first-party sources. This is a source-and-scope review, not legal advice.

## Claims safe to publish

### Fair Housing Act advertising rule — verified

- **Claim:** 42 U.S.C. § 3604(c) prohibits making, printing, or publishing a notice, statement, or advertisement about the sale or rental of a dwelling that indicates a preference, limitation, or discrimination based on race, color, religion, sex, handicap, familial status, or national origin, or an intention to do so.
- **Source:** [U.S. House, 42 U.S.C. § 3604](https://uscode.house.gov/view.xhtml?edition=prelim&f=treesort&jumpTo=true&num=0&req=%28title%3A42+section%3A3604+edition%3Aprelim%29+OR+%28granuleid%3AUSC-prelim-title42-section3604%29)
- **Status:** Verified. The statute uses the word **“handicap”**; “disability” is a modern paraphrase, not a quotation.
- **Scope note:** The law does not categorically forbid every mention of a protected class. The operative test is whether the housing statement indicates a preference, limitation, or discrimination. Treat the project's broader protected-word/proxy lexicon as a conservative screening policy; phrases such as “great schools,” “safe neighborhood,” and “young professionals” are not enumerated in § 3604(c) itself and need separate HUD/case-specific support if described as independently illegal.

### FCC consent revocation for covered calls and texts — verified

- **Claim:** For calls or texts covered by 47 C.F.R. § 64.1200(a)(1)–(3) or (c)(2), a recipient may revoke consent by any reasonable method. Replying with STOP, QUIT, END, REVOKE, OPT OUT, CANCEL, or UNSUBSCRIBE is reasonable per se; other wording also counts when a reasonable person would understand it as revocation. A covered sender must honor the request within a reasonable time not exceeding ten business days.
- **Source:** [eCFR, 47 C.F.R. § 64.1200(a)(10)–(11)](https://www.ecfr.gov/current/title-47/chapter-I/subchapter-B/part-64/subpart-L/section-64.1200)
- **Status:** Verified, with the rule's stated scope. A one-time, nonmarketing confirmation text is permitted under § 64.1200(a)(12); a confirmation sent within five minutes receives the rule's presumption.
- **Presentation note:** The implementation's immediate suppression is stricter than the ten-business-day outside limit and should be called a conservative product decision.

### Federal contact window — verified, but publish the exact scope

- **Claim:** 47 C.F.R. § 64.1200(c)(1) bars a telephone solicitation to a residential subscriber before 8 a.m. or after 9 p.m. at the called party's location. Paragraph (e) applies paragraphs (c) and (d) to covered telephone solicitations or telemarketing calls or text messages sent to wireless numbers.
- **Source:** [eCFR, 47 C.F.R. § 64.1200(c)(1), (e)](https://www.ecfr.gov/current/title-47/chapter-I/subchapter-B/part-64/subpart-L/section-64.1200)
- **Status:** Verified. Do not restate this as a federal 9 a.m.–8 p.m. rule: that narrower window is the project's policy.

### Anthropic workflow/routing guidance — verified

- **Claim:** Anthropic distinguishes workflows (predefined code paths) from agents (model-directed processes), recommends starting with the simplest solution, and says workflows offer predictability for well-defined tasks. Its routing pattern classifies input and directs it to a specialized follow-up process; routing is a fit when categories are distinct and classification can be accurate.
- **Source:** [Anthropic, “Building effective agents”](https://www.anthropic.com/engineering/building-effective-agents)
- **Status:** Verified.
- **Scope note:** Calling this case a fixed workflow is a well-supported **design inference**, not a result Anthropic reached about this project. The article does not establish that skipping deterministic branches is the “single biggest” latency improvement, require exactly one model call, or specifically endorse this gate sequence. Label those as project architecture decisions motivated by the guidance.

### IFScale — verified, with narrower conclusions

- **Claim:** IFScale tested 20 models from seven providers on a business-report task containing as many as 500 keyword-inclusion instructions. The paper reports 68% accuracy for the best frontier models at 500 instructions, degradation patterns as instruction density rises, and bias toward earlier instructions.
- **Source:** [Jaroslawicz et al., “How Many Instructions Can LLMs Follow at Once?”, arXiv:2507.11538](https://arxiv.org/abs/2507.11538)
- **Status:** Verified. Use **68%**, not “about 69%,” when giving the paper's number.
- **Scope note:** IFScale supports the qualitative design inference “keep prompts focused and enforce deterministic requirements in code.” It does **not** establish a six-constraint limit, show that models “forget earlier instructions” (the reported bias is toward earlier instructions), or prove that moving compliance checks to code guarantees legal compliance. Remove those formulations or source them separately and clearly label the architectural conclusion as an inference.

## Claims to correct, remove, or relabel

### Texas statute number and Sunday hours

- **Correct authority:** Texas Business & Commerce Code **§ 301.051(b)(2)** says a covered telephone solicitor may call after noon and before 9 p.m. Sunday, or after 9 a.m. and before 9 p.m. on a weekday or Saturday.
- **Source:** [Texas Legislature, Business & Commerce Code Chapter 301](https://statutes.capitol.texas.gov/Docs/BC/pdf/BC.301.pdf)
- **Status:** The hours are verified, but existing references to **§ 305.053** are incorrect and should be replaced.
- **Scope:** Section 301.051(a) excludes calls made at the consumer's express request and calls to a consumer with whom the solicitor has a prior or existing business relationship. The text governs a “consumer telephone call” and does not expressly say that this Texas window applies to SMS. Do not present it as a universal legal mandate for opted-in prospect texts.
- **Required relabel:** “09:00–20:00 Monday–Saturday / 12:00–20:00 Sunday” is a **conservative project-wide demo window inspired by federal and Texas call rules**, not “the Texas legal window” and not a proven nationwide intersection. Texas's stated closing boundary is before 9 p.m.; the project's 8 p.m. ceiling is stricter. The claim that this window is “safe in every state” must be removed absent a complete, current fifty-state analysis; some jurisdictions may prohibit Sunday solicitations rather than merely delay them.

### STOP sentence in every SMS

- **Existing claim:** Every marketing SMS must end with the exact sentence “Reply STOP to opt out.”
- **Status:** Remove as a universal TCPA/FCC requirement. Section 64.1200(a)(10) makes STOP a per-se reasonable revocation method, but it does not generally require that exact sentence, exact placement, or inclusion in every marketing text.
- **Required relabel:** The exact trailing sentence is a **project copy standard/conservative default** that makes opt-out discoverable and produces stable assignment output. Do not call it legally mandatory without a separate source applicable to the particular messaging program.

### Marketing-SMS consent

- **Existing claim:** “Marketing SMS needs prior express written consent” without qualification.
- **Status:** Narrow the claim. Section 64.1200(a)(2) requires prior express written consent for advertising or telemarketing calls using an automatic telephone dialing system or artificial/prerecorded voice to the listed lines; FCC rules treat covered texts as calls in specified contexts. Applicability depends on how the message is sent and other facts.
- **Required relabel:** The pipeline's rule that **all** SMS requires an explicit `sms_opt_in` is a conservative fail-closed project policy. Cite the regulation for the covered category, but do not say the cited paragraph alone makes written opt-in universally necessary for every possible one-to-one text.

### Fair-housing validator wording

- **Existing claim:** § 3604(c) means the body may never reference a protected class or any item in the project's proxy list.
- **Status:** Overbroad as a description of the statute.
- **Required relabel:** The hard ban and proxy lexicon are conservative automated safeguards designed to avoid statements that could indicate a prohibited preference. The statute supports the protected categories and the preference/limitation/discrimination test, not each lexicon entry or an automatic legal conclusion from a word hit.

### Architecture and prompt-load claims

- **Existing claim:** This is “exactly” Anthropic's single-call case; routing guidance proves model calls should be skipped on deterministic branches; IFScale proves reliability breaks after about six simultaneous constraints and that models forget earlier rules.
- **Status:** Overstated or unsupported by the cited sources.
- **Required relabel:** Describe the fixed workflow, single bounded drafting call, deterministic early exits, and code validators as **project decisions consistent with** Anthropic's simplicity/workflow guidance and **motivated by** IFScale's observed degradation under very high instruction density. Delete the six-rule threshold unless a different paper is cited, and change “forgets earlier rules” to the paper's actual observation of bias toward earlier instructions.

## URL reachability

All recommended URLs above returned HTTP 200 on 2026-09-17:

- U.S. House, 42 U.S.C. § 3604
- eCFR, 47 C.F.R. § 64.1200
- Texas Legislature, Business & Commerce Code Chapter 301 PDF
- Anthropic, “Building effective agents”
- arXiv:2507.11538

The current eCFR text is preferable to presenting the original FCC order as the current rule. If legislative history is needed, [FCC 24-24](https://docs.fcc.gov/public/attachments/FCC-24-24A1.pdf) also returned HTTP 200, but its rollout history is more complicated than the present-tense product story requires.
