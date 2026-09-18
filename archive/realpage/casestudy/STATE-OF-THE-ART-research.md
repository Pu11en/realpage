# How to build and evaluate this well — current practice (researched 2026-09-17)

## 1. Architecture

- **Workflows vs agents.** Anthropic, "Building Effective Agents" (Dec 19, 2024): workflows = "LLMs and tools orchestrated through predefined code paths"; agents = "LLMs dynamically direct their own processes." Explicit advice: "find the simplest solution possible… optimizing single LLM calls with retrieval and in-context examples is usually enough"; agents "trade latency and cost for better task performance." The named workflow patterns are prompt chaining, **routing**, parallelization, orchestrator-workers, evaluator-optimizer. (https://www.anthropic.com/engineering/building-effective-agents)
- **2025-2026 successors.** Anthropic "Effective context engineering for AI agents" (Sep 2025) and "Harness design for long-running application development" (Mar 2026) reframe the same idea as *harness engineering*: the model is a stateless reasoner, the harness "translates probabilistic reasoning into dependable, deterministic action" (survey: arXiv 2606.20683, Jun 2026; CAAF "Harness as an Asset: Enforcing Determinism," arXiv 2604.17025, Apr 2026). A May 2026 practitioner summary of Anthropic's playbook: use an agent loop only "where you cannot hardcode the path but can still verify progress." (https://mer.vin/2026/05/when-not-to-build-ai-agents-anthropics-workflow-vs-agent-playbook/)
- **Deterministic control plane for consequential actions.** "A Deterministic Control Plane for LLM Coding Agents" (arXiv 2606.26924, Jun 2026), "AgentTrust" (arXiv 2606.08539, Jun 2026), "Type-Checked Compliance: Deterministic Guardrails for Agentic Financial Systems" (arXiv 2604.01483, Apr 2026), and "PolicyGuard" (arXiv 2606.29225, Jun 2026) all converge on: agent proposes an *intent*, a deterministic policy engine (OPA/Rego, Cedar, typed checks) admits or rejects it before execution.
- **Verdict for this shape:** the task has a fixed decision path (consent → channel → quiet hours → draft → validate → next action). That is a **routing workflow with one structured LLM call**, not an agent loop. The LLM contributes wording and a reply classification; everything else is code. This is exactly Anthropic's "single LLM call is usually enough" case.

## 2. Structured output reliability

- **Ladder of guarantees.** OpenAI Structured Outputs (Aug 2024) reached 100% schema adherence on their evals via constrained sampling, vs ~80% for `json_object` mode and <40% for prompt-only on older models. (https://openai.com/index/introducing-structured-outputs-in-the-api/) DeepSeek only offers `json_object`: prompt must contain the word "json" plus an example, set `max_tokens` high enough to avoid truncation, and the docs warn "the API may occasionally return empty content." No `json_schema`/strict mode. (https://api-docs.deepseek.com/guides/json_mode/)
- **Accuracy cost of constraints.** "Let Me Speak Freely?" (arXiv 2408.02442, Aug 2024): strict JSON-mode hurts reasoning tasks, helps classification. JSONSchemaBench (arXiv 2501.10868, Jan-Feb 2025) benchmarks Guidance/Outlines/llama.cpp/XGrammar/OpenAI/Gemini on 10K real schemas across coverage, efficiency, and quality. "The Hidden Cost of Structured Generation" (arXiv 2603.03305, Mar 2026): constrained decoding on GSM8K costs 3.6-8.2x latency; helps small models (0%→75%) but can crater large reasoning models (92.5%→35%) when grammar is strict. Takeaway: constraints are a safety net for schema, not for correctness; keep the schema small and flat.
- **Recommended fallback ladder for DeepSeek (our case):**
  1. `response_format: json_object` + word "json" + one example in system prompt, temperature 0, `max_tokens` bounded.
  2. Parse → Pydantic validate. On failure, one retry that feeds the validation errors back (instructor pattern; instructor has a DeepSeek integration). (https://python.useinstructor.com/integrations/deepseek/)
  3. On empty content / second failure / timeout → deterministic template message. Never a third call inside the latency budget.
- Constraint budget matters: "How Many Instructions Can LLMs Follow at Once?" (IFScale, arXiv 2507.11538, Jul 2025): even frontier models hit ~69% at 500 instructions, with bias toward earlier instructions; "Phase Transitions in Compositional Constraint Satisfaction" (arXiv 2608.12426, Aug 2026): reliable following breaks down beyond 5-6 simultaneous constraints, <50% probe success at 7. So the prompt should carry a handful of wording constraints; the rest belong in code.

## 3. Evaluation

- **Code first, judge second.** Hamel Husain, Evals FAQ (2025, updated): "Use a code-based eval when a deterministic rule can identify the failure… A check with one rule may need only a few examples." LLM judges "require 100+ labeled examples, ongoing weekly maintenance." Braintrust (Feb 26, 2026): code checks "everything that can be measured directly"; judge "only subjective dimensions." (https://hamel.dev/blog/posts/evals-faq/, https://www.braintrust.dev/articles/what-is-llm-as-a-judge)
- **Binary over Likert.** Hamel: "Binary evaluations force clearer thinking and more consistent labeling"; Likert points are "subjective and inconsistent across annotators." (https://hamel.dev/blog/posts/evals-faq/why-do-you-recommend-binary-passfail-evaluations-instead-of-1-5-ratings-likert-scales.html)
- **Aligning a judge.** Hamel's loop: read ~100 traces, annotate ≥30 yourself, label 100-200 per failure mode, split 10-20/40-45/40-45, report judge TPR/TNR on held-out. Shankar et al., "Who Validates the Validators?" / EvalGen (UIST 2024): **criteria drift**, "users need criteria to grade outputs, but grading outputs helps users define criteria," so criteria cannot be fully fixed before grading. Databricks MLflow `align()` / MemAlign (late 2025-2026) reports 30-50% agreement lift after human-feedback alignment. (https://arxiv.org/abs/2404.12272, https://www.databricks.com/blog/memalign-building-better-llm-judges-human-feedback-scalable-memory)
- **Judge biases.** Tripathi et al., "Pairwise or Pointwise?" (COLM 2025, arXiv 2504.14716): pairwise preferences flip ~35% under distractor features vs 9% for absolute scores; pointwise is more robust to manipulation. "Am I More Pointwise or Pairwise?" (arXiv 2602.02219, Feb 2026, EMNLP Findings 2026): rubric-based scoring has *position bias in the rubric options themselves*; permute option order a few times. Survey (arXiv 2411.15594, v6 2025): position, verbosity, self-preference are the big three.
- **Reporting.** "How to Correctly Report LLM-as-a-Judge Evaluations" (arXiv 2511.21140, Nov 2025, ICML 2026): correct scores by judge TPR/TNR and give CIs that include calibration-set uncertainty.
- **What 12 examples can claim.** Bowyer, Aitchison, Ivanova, "Don't Use the CLT in LLM Evals With Fewer Than a Few Hundred Datapoints" (ICML 2025, arXiv 2503.01747): CLT error bars "dramatically underestimate uncertainty"; use Beta-Binomial/Wilson. Concretely: 12/12 pass gives a 95% Wilson lower bound of ~0.74; 11/12 gives ~0.65. "Adding Error Bars to Evals" (Miller, Anthropic, arXiv 2411.00640, Nov 2024): always report CIs. So 12 examples can establish "zero observed violations" and "passes each named case"; it cannot establish a violation *rate* below ~25%, and it cannot distinguish two systems differing by less than several examples.

## 4. Semantic matching of a short SMS against a reference

- **BERTScore / cosine failure modes:** antonym insensitivity ("best"/"worst" stay close), quantity blindness ("2%" vs "20%"), weak penalty for wrong entity/date/unit (Galileo BERTScore guide, 2025; EmergentMind BERTScore summary). For a 160-char SMS these are exactly the tokens that matter (unit number, time, opt-out text), so cosine is a *recall* filter at best.
- **Checklist extraction from the reference** is the current recommended approach: Check-Eval "Reference-Guided" mode (arXiv 2407.14467, Jul 2024), TICK (arXiv 2410.03608, Oct 2024), RocketEval (ICLR 2025, arXiv 2503.05142: instance-specific checklist graded by a lightweight LLM, reweighted against labels), AutoChecklist (arXiv 2603.07019, Mar 2026). Convert the expected message into 3-6 yes/no items (greeting uses first name; mentions tour on <day>; includes STOP text; no price; under 160 chars) and score = fraction satisfied.
- **What a careful engineer does for a single short reference:** (a) deterministic must-haves (opt-out text, required tokens, length, forbidden phrases) as hard asserts; (b) checklist items extracted once from the reference and stored as test fixtures; (c) a pointwise binary LLM judge only for "would a leasing agent send this?" tone; (d) embedding cosine reported but never gating. Hamel and Braintrust both say the same: rules for what is measurable, judge for tone only.

## 5. Compliance-critical generation

- **Regulatory facts to encode as code.** TCPA quiet hours 8am-9pm *recipient* local time; revocation via "any reasonable means" with 10-business-day honor window effective Apr 11, 2025; the one-to-one consent rule was vacated (11th Cir., Jan 2025) and removed by the FCC (Sep 2025) but prior express written consent still required; $500-$1,500 per message statutory damages, no cap. Twilio's compliance toolkit implements quiet hours and opt-out as platform features, i.e. as code. (https://www.apten.ai/blog/ai-compliance-guide-2026-tcpa-fcc-state-laws, https://www.twilio.com/docs/messaging/features/compliance-toolkit)
- **Fair housing.** Zillow open-sourced a Fair Housing Classifier (2024) as an LLM guardrail, flagging protected-class language such as "safe neighborhood," "great schools," "ideal for young professionals." Practitioner consensus: "LLMs cannot determine Fair Housing compliance… without structured audit rules." HUD 2024 guidance treats algorithmic discrimination as illegal regardless of intent. (https://www.zillowgroup.com/news/zillows-fair-housing-classifier/)
- **Policy as code.** OPA/Rego and Cedar as the admission layer for agent actions (CodiLime, Quarkus LangChain4j OPA guardrails, 2025; Adapticom "Hybrid Deterministic-AI Agents" Apr 11, 2026). Typed/formal checks: Lean 4 guardrails (arXiv 2604.01483, Apr 2026).
- **Order: both, with code as the last word.** Pre-generation constraints reduce retries; post-generation validation is what guarantees the invariant. Evidence that prompt constraints degrade quality: IFScale (Jul 2025) and the constraint phase-transition paper (Aug 2026) show hard-success collapses past ~6 constraints; "Let Me Speak Freely" shows format constraints hurt reasoning. So keep the prompt to a few high-value constraints (tone, length, required facts) and enforce the compliance list in code, then regenerate once with the specific violation named (Anthropic's evaluator-optimizer pattern, bounded to one iteration).

## 6. Latency

- **Skip the model on deterministic branches.** No-consent, quiet-hours-defer, opted-out, and "no action" paths need zero LLM tokens; only the "send now" branch drafts. This is the single biggest p95 lever and is the routing pattern from Anthropic (Dec 2024).
- **Prompt caching.** Anthropic docs (2026): cache reads at 0.1x input price, 5-min TTL, min 512-1,024 tokens depending on model; Anthropic's original announcement cited up to 85% latency reduction on long prompts. DeepSeek has automatic context caching on repeated prefixes. Put the rulebook and examples in a stable prefix, the record last.
- **Small `max_tokens` and flat schema.** Output tokens dominate wall clock; an SMS draft + classification + next action fits in ~120 tokens. Constrained decoding adds 3.6-8.2x latency in the strict case (arXiv 2603.03305, Mar 2026), another reason to use plain json_object with a tiny schema.
- **Hard timeout + template fallback.** Practitioner guidance (StackAI 2025, DEV "LLM Latency Budget" 2025): set a per-call deadline well under the budget (~1,200 ms), alert when timeout rate >2%, and fall back to a templated message that already passes the validators. Streaming does not help here since the output must be validated before send; use it only if you want TTFT telemetry.
- **Parallel/speculative.** Fire the draft call and the deterministic checks concurrently; if the draft fails validation, the single regenerate call is the p95 tail, so cap it with the same deadline and fall through to template.

## 7. Five quotable senior-engineer points

1. "The rules live outside the model because instruction-following degrades past about six simultaneous constraints and the model forgets earlier ones (IFScale, arXiv 2507.11538, Jul 2025; arXiv 2608.12426, Aug 2026). A $1,500-per-text statute cannot depend on attention."
2. "A 'personalization score' is a proxy: it measures whether record fields appear correctly in the text, so I implement it as field-coverage assertions plus a checklist judge, not cosine similarity, which cannot tell '2 pm' from '3 pm' (Check-Eval/RocketEval, 2024-2025; BERTScore quantity blindness)."
3. "An F1 threshold implies a classifier with a confusion matrix, which implies a labeled positive class and a decision threshold. With 12 records you have maybe 4 positives, so one flipped label moves F1 by ~0.2; the honest deliverable is the confusion matrix and the threshold, not the point score (Hamel Husain, Evals FAQ; arXiv 2511.21140, Nov 2025)."
4. "Twelve examples cannot establish a rate. Zero violations in 12 gives a 95% Wilson lower bound of about 74% compliance; the CLT bars would lie (Bowyer et al., ICML 2025). What 12 examples *can* do is prove each named hard rule fires, which is why the safety checks are deterministic and unit-tested, not sampled."
5. "With 10,000 records I would: run the same pipeline, log every draft and validator verdict as a trace, do error analysis on ~100 traces to discover failure modes (Hamel's saturation loop), train the judge on 100-200 labels per mode and report its TPR/TNR, add Beta-Binomial CIs, and shadow-send before live-send. The architecture does not change; the evidence does."

## What this means for our build tonight

1. One deterministic router, one LLM call, no agent loop (Anthropic Dec 2024; harness papers 2026).
2. Deterministic branches (no consent, quiet hours, opt-out, no-action) return without touching DeepSeek (latency, §6).
3. DeepSeek `json_object` + "json" in prompt + example + temp 0 + small `max_tokens`; Pydantic validate; one error-fed retry; then template (§2).
4. Flat schema with ≤6 fields; ≤6 wording constraints in the prompt; every compliance rule in code (IFScale, §5).
5. Validators run on the draft *and* the template; regenerate at most once with the violation named (evaluator-optimizer, bounded).
6. Per-call deadline ~1,200 ms, total budget 2,000 ms, template fallback pre-validated (§6).
7. Stable system-prefix (rules, examples) first, record last, to hit provider prefix caching (§6).
8. Semantic match = hard asserts (opt-out text, required fields, length, banned phrases) + reference-derived yes/no checklist + pointwise binary tone judge with permuted rubric order; cosine logged, never gating (§3-4).
9. Reply classification reported as a confusion matrix with the threshold, plus F1; note that 12 records cannot bound the rate (§7 points 3-4).
10. Report every metric on the 12 with Wilson/Beta intervals and state plainly what is proven (named rules fire) vs estimated (rates) (Bowyer ICML 2025; Miller 2024).

## Sources

- Anthropic, Building Effective Agents (Dec 19, 2024): https://www.anthropic.com/engineering/building-effective-agents
- Anthropic, Prompt caching docs (2026): https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- Hamel Husain, AI Evals FAQ: https://hamel.dev/blog/posts/evals-faq/
- Hamel Husain, Binary vs Likert: https://hamel.dev/blog/posts/evals-faq/why-do-you-recommend-binary-passfail-evaluations-instead-of-1-5-ratings-likert-scales.html
- Braintrust, What is an LLM-as-a-judge (Feb 26, 2026): https://www.braintrust.dev/articles/what-is-llm-as-a-judge
- Shankar et al., Who Validates the Validators? / EvalGen (UIST 2024): https://arxiv.org/abs/2404.12272
- Databricks, MemAlign (2025-2026): https://www.databricks.com/blog/memalign-building-better-llm-judges-human-feedback-scalable-memory
- Tripathi et al., Pairwise or Pointwise? (COLM 2025): https://arxiv.org/abs/2504.14716
- Xu et al., Am I More Pointwise or Pairwise? (Feb 2026, EMNLP Findings 2026): https://arxiv.org/abs/2602.02219
- A Survey on LLM-as-a-Judge (v6, 2025): https://arxiv.org/html/2411.15594v6
- How to Correctly Report LLM-as-a-Judge Evaluations (Nov 2025, ICML 2026): https://arxiv.org/abs/2511.21140
- Bowyer et al., Don't Use the CLT in LLM Evals (ICML 2025): https://arxiv.org/abs/2503.01747
- Miller, Adding Error Bars to Evals (Nov 2024): https://arxiv.org/pdf/2411.00640
- Let Me Speak Freely? (Aug 2024): https://arxiv.org/html/2408.02442v1
- JSONSchemaBench (Jan-Feb 2025): https://arxiv.org/abs/2501.10868
- The Hidden Cost of Structured Generation (Mar 2026): https://arxiv.org/pdf/2603.03305
- OpenAI, Introducing Structured Outputs (Aug 2024): https://openai.com/index/introducing-structured-outputs-in-the-api/
- DeepSeek, JSON Output docs: https://api-docs.deepseek.com/guides/json_mode/
- instructor, DeepSeek integration: https://python.useinstructor.com/integrations/deepseek/
- IFScale, How Many Instructions Can LLMs Follow at Once? (Jul 2025): https://www.alphaxiv.org/abs/2507.11538
- Phase Transitions in Compositional Constraint Satisfaction (Aug 2026): https://pith.science/paper/2608.12426
- Check-Eval (Jul 2024): https://arxiv.org/html/2407.14467v1
- TICK (Oct 2024): https://arxiv.org/abs/2410.03608
- RocketEval (ICLR 2025): https://arxiv.org/abs/2503.05142
- AutoChecklist (Mar 2026): https://arxiv.org/html/2603.07019
- Galileo, BERTScore explained: https://galileo.ai/blog/bert-score-explained-guide
- Zillow Fair Housing Classifier: https://www.zillowgroup.com/news/zillows-fair-housing-classifier/
- Apten, 2026 AI compliance guide (TCPA): https://www.apten.ai/blog/ai-compliance-guide-2026-tcpa-fcc-state-laws
- Twilio, Compliance toolkit: https://www.twilio.com/docs/messaging/features/compliance-toolkit
- CodiLime, OPA for AI agents: https://codilime.com/blog/why-use-open-policy-agent-for-your-ai-agents/
- Adapticom, Hybrid deterministic-AI guardrails (Apr 11, 2026): https://adapticominc.com/Library/2026-04-11_BestPracticesForHybridDeterministic-AIAgentsGuardrailsAndOutputValidationPatterns.html
- A Deterministic Control Plane for LLM Coding Agents (Jun 2026): https://arxiv.org/pdf/2606.26924
- PolicyGuard (Jun 2026): https://arxiv.org/pdf/2606.29225
- Type-Checked Compliance, Lean 4 guardrails (Apr 2026): https://arxiv.org/pdf/2604.01483
- CAAF, Harness as an Asset (Apr 2026): https://arxiv.org/pdf/2604.17025
- Survey on Agent System and Harness Design (Jun 2026): https://arxiv.org/pdf/2606.20683
- Anthropic workflow-vs-agent playbook summary (May 2026): https://mer.vin/2026/05/when-not-to-build-ai-agents-anthropics-workflow-vs-agent-playbook/
- StackAI, Reduce AI latency in production (2025): https://www.stackai.com/insights/reduce-ai-latency-in-production-optimize-token-usage-caching-and-serving-for-faster-llm-performance
- DEV, LLM Latency Budget (2025): https://dev.to/jackm-singularity/llm-latency-budget-make-ai-features-feel-fast-without-burning-money-3mc3
