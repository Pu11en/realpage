# Under the Hood: primary-source research

Research date: 2026-09-15

## Bottom line

There is no single official template for an AI-agent portfolio page. The strongest primary sources converge on a more useful standard: **prove one real workflow end to end, make the system understandable, show how success was measured, expose failures and traces, and demonstrate bounded authority and human control.**

For this project, the live CraneSignal agent should be the product proof. “Under the Hood” should be the engineering proof that Drew knows why it is agentic, how it works, how he knows it works, where it fails, and how another team could adopt the pattern.

## What the RealPage role asks Drew to prove

RealPage's official AI Developer IV posting asks for a senior technical leader who can architect and ship production AI systems, operate cloud-native systems, make data-driven speed/quality/cost tradeoffs, use RAG and multi-agent workflows, establish observability and evaluation, mentor engineers, and explain technical strategy to non-technical leaders. ([RealPage Req. 2025-12408](https://careers-international-realpagepms.icims.com/jobs/12408/ai-developer-iv/job))

That makes the hiring case broader than “I built a chatbot.” The page needs visible evidence of:

- a useful, shipped workflow;
- architecture and technical judgment;
- production-quality testing and operations;
- evaluation and failure analysis;
- safety, privacy, and controlled authority;
- cost and latency tradeoffs;
- reusable documentation and leadership-level communication.

## What authoritative agent guidance says to show

### 1. Show why an agent was the right design

Anthropic distinguishes fixed workflows from agents that dynamically direct their tools, and recommends the simplest solution that works because agentic complexity adds latency, cost, and compounding-error risk. It also recommends transparent plans, ground-truth checks from the environment, stopping conditions, sandbox testing, and human checkpoints. ([Anthropic: Building effective agents](https://www.anthropic.com/engineering/building-effective-agents))

**Page evidence:** one sentence naming the open-ended job the agent handles, followed by one plain architecture picture. Show the deterministic pieces too: source lookup, link validation, read-only access, checks, and human approval. This demonstrates judgment rather than “agent” branding.

### 2. Prove the outcome, not just the final prose

Anthropic's agent-evaluation guidance says an agent trial includes a complete trace—outputs, tool calls, intermediate results, and outcome—and recommends combining code-based, model-based, and human graders. It stresses that the real outcome can differ from what the agent claims it accomplished and that nondeterministic agents need multiple trials. For research agents, it specifically calls for groundedness, coverage, and source-quality checks. ([Anthropic: Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents))

**Page evidence:** show one expandable real trace from recruiter question → sources/tools → answer → checks. Report a dated evaluation set with sample size, task-success result, source/grounding result, safety result, and human-vs-AI grading agreement. Include multiple trials for any head-to-head model or tool claim.

### 3. Treat evaluation as a release gate and an operating loop

Microsoft's official agent guide recommends establishing a baseline and acceptance threshold before release, combining a use-case rubric with safety evaluators, showing aggregate and row-level results, using evaluations as CI/CD gates, and monitoring production traces continuously. ([Microsoft Foundry: Evaluate your AI agents](https://learn.microsoft.com/en-us/azure/foundry/observability/how-to/evaluate-agent))

Google's architecture guidance adds continuous quality, safety, instruction-following, and grounding evaluation; human feedback; adversarial testing; and monitoring request rate, errors, latency, resource use, tokens, and user ratings. It also recommends controlled release and rollback plans. ([Google Cloud: AI/ML operational excellence](https://docs.cloud.google.com/architecture/framework/perspectives/ai-ml/operational-excellence))

**Page evidence:** show the pass threshold and what happens when it fails, not merely a score. Show p50/p95 response time, failures, token/model usage or cost where actually measured, and how thumbs-down cases become regression tests.

### 4. Demonstrate layered safety in code, not only a safety promise

OpenAI recommends layered guardrails, standard authentication and authorization, strict access controls, output validation, and human intervention after retry limits or before high-risk actions. ([OpenAI: A practical guide to building AI agents](https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/))

OWASP's current guidance says prompt injection cannot be eliminated by RAG or prompting alone. It recommends deterministic output validation, least-privilege access, human approval for privileged actions, separation of untrusted content, and adversarial testing. Its excessive-agency guidance recommends minimizing tools, functionality, permissions, and autonomy, with downstream authorization rather than asking the model to police itself. ([OWASP: Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/), [OWASP: Excessive Agency](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/))

**Page evidence:** show that the sales agent is truly read-only, name the few tools it can use, show deterministic source/link validation, state what personal data is masked or never stored, and publish the latest adversarial-test result with one failure example.

### 5. Document scope, evidence, limits, and human responsibility

NIST's AI Risk Management Framework calls for documented business value, scope, knowledge limits, human oversight, test sets, metrics, deployment-like evaluation conditions, production monitoring, and limitations. It also says rigorous testing should report uncertainty and benchmarks and can benefit from independent review. ([NIST AI RMF Core](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/))

**Page evidence:** every headline metric needs its sample size, date, method, and link to the underlying result. Include “what failed / what is not proven” and state exactly where a human decides whether work ships.

## What separates top-tier proof from a normal portfolio

- **Normal:** a polished diagram. **Top-tier:** the diagram maps to a clickable real trace and source files.
- **Normal:** “92% accurate.” **Top-tier:** 92 of 100 on a dated, defined test set, broken down by failure type, with human calibration and representative examples.
- **Normal:** “safe and private.” **Top-tier:** read-only permissions, bounded tools, redaction/retention rules, adversarial cases, and a human gate that are demonstrably enforced.
- **Normal:** a model/framework list. **Top-tier:** a short decision record explaining why this workflow, tool boundary, and model were chosen, including cost, latency, and build-vs-buy tradeoffs.
- **Normal:** only successes. **Top-tier:** failed checks, false alarms, fixes, residual limitations, and rerun evidence.
- **Normal:** a one-off demo. **Top-tier:** versioned prompts/configuration, repeatable checks, a release threshold, feedback-to-regression loop, and a small adoption guide another engineer actually followed.

## Recommended recruiter flow

### First screen: the 60–90 second case

1. **Outcome:** “CraneSignal researches which apartment buildings a property-software rep should call and builds a source-backed briefing for outreach.”
2. **Live proof:** three recruiter-safe suggested questions and a prominent “Ask the agent” action.
3. **Architecture:** user question → bounded research tools/data → source-backed answer, with evaluation/logging below and human approval at the shipping boundary.
4. **Three defensible proof tiles:** task/eval success, response speed, and safety/grounding. Every tile shows `n`, date, and method.
5. **One line of judgment:** why an agent is used for open-ended research while deterministic code handles permissions, validation, and release.

### Expand only for depth

- **One run, end to end:** the prompt, tools, sources, answer, timing, and checks.
- **How I know it works:** eval set, pass threshold, human agreement, failure taxonomy, and before/after rerun.
- **Safety boundaries:** read-only tools, least privilege, personal-data treatment, prompt-injection tests, and human gate.
- **Production judgment:** p50/p95 latency, actual cost or “not measured,” retry/cap behavior, build-vs-buy, and rollback/release process.
- **How another team adopts it:** short playbook, first checked task, and honest result of a fresh-user test.
- **What failed and what remains:** three concrete failures, their status, and limits that are still open.

## Implications for the current page and remaining plan

1. **Do not headline `1 / 6 eval checks passing`.** Fix and rerun stale checks first; until then, show the already defensible `92 / 100 hard questions handled` with its failure breakdown, or label the suite “being repaired” inside the detail section.
2. **Do not headline `94% passed first try` yet.** The current builder infers this when a progress entry lacks words such as “retry” or “STUCK”; that is a useful internal estimate, not strong recruiter-grade evidence. Replace it with a trace-backed measure or remove it.
3. **Do not imply all 142 checked plan items were completed by AI** unless authorship is provable from run records. “142 completed build steps” is supportable; “done by AI” needs attributable logs.
4. **Keep the live agent at the top.** It is the clearest proof of a useful, end-to-end system, especially once Reddit and AI Visibility data are available to it.
5. **Add one real trace before adding more dashboard tiles.** A trace with sources, tools, time, answer, and validation provides more senior-level evidence than a larger metric wall.
6. **Finish only the minimum credible evaluation loop:** repair the stale checks; run the safety/grounding/off-topic suite; preserve evidence; show failures; calibrate the AI grader against Drew's 17 human labels; and connect negative feedback to future tests.
7. **Show cost only when genuinely measured.** Current `$0.00` check fields mean “no paid cost recorded,” not necessarily zero total cost. Relabel or omit until measurement is sound.
8. **Treat the playbook as leadership proof, not filler.** A concise setup guide plus one fresh-user attempt directly supports RealPage's senior communication and mentoring expectations.

The best “top 1%” signal is not more technical detail. It is a small amount of **auditable evidence** presented so a recruiter understands the outcome immediately and an engineer can verify the judgment underneath it.
