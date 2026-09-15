// Run a NiubiGEO audit on the frozen question list (questions.csv) so every run asks
// exactly the same questions and trends stay fair. NiubiGEO's own --prompts-file only
// accepts questions that name RealPage, so this builds the confirmed plan itself.
//
//   cd $NIUBIGEO && npx tsx <repo>/tooling/ai-visibility/frozen_audit.ts <questions.csv> <model,model,...>
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

const NIUBIGEO = process.env.NIUBIGEO_DIR || "/home/drewp/main-projects/tools-src/niubigeo";
const src = (file: string) => import(pathToFileURL(join(NIUBIGEO, "src", file)).href);

// Minimal CSV reader: handles quoted fields with commas and doubled quotes.
export function parseCsv(text: string): Record<string, string>[] {
  const rows: string[][] = [];
  let row: string[] = [], field = "", quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    if (quoted) {
      if (ch === '"' && text[i + 1] === '"') { field += '"'; i += 1; }
      else if (ch === '"') quoted = false;
      else field += ch;
    } else if (ch === '"') quoted = true;
    else if (ch === ",") { row.push(field); field = ""; }
    else if (ch === "\n" || ch === "\r") {
      if (ch === "\r" && text[i + 1] === "\n") i += 1;
      row.push(field); field = "";
      if (row.some((cell) => cell !== "")) rows.push(row);
      row = [];
    } else field += ch;
  }
  row.push(field);
  if (row.some((cell) => cell !== "")) rows.push(row);
  const [header = [], ...body] = rows;
  return body.map((cells) => Object.fromEntries(header.map((key, index) => [key, cells[index] ?? ""])));
}

async function main(): Promise<void> {
  const [questionsFile, modelsList] = process.argv.slice(2);
  if (!questionsFile || !modelsList) throw new Error("usage: frozen_audit.ts <questions.csv> <models>");
  const { loadDotEnv } = await src("config/env.ts");
  const { entityFromInput } = await src("utils/domain.ts");
  const { sha256 } = await src("utils/hash.ts");
  const { PROMPT_SET_VERSION, ANALYSIS_RULES_VERSION } = await src("core/version.ts");
  const { AuditRunner } = await src("runner/audit-runner.ts");
  const { ProjectFileStore } = await src("projects/project-store.ts");
  const { RunOrchestrator } = await src("monitoring/run-orchestrator.ts");
  const { monitoringDataDir } = await src("config/env.ts");
  const { percent } = await src("report/format.ts");
  loadDotEnv();

  const prompts = parseCsv(readFileSync(questionsFile, "utf8")).map((row) => ({
    id: row.id,
    type: row.type,
    topic: row.topic,
    language: "en",
    text: row.question,
    enabled: true,
    auditCategory: row.audit_category,
    targetIncluded: row.target_included === "true",
  }));
  const providerTargets = modelsList.split(",").map((model) => model.trim()).filter(Boolean)
    .map((model) => ({ providerId: "openai-compatible", model, webSearchEnabled: false, webSearchMode: "provider_native" }));
  const target = entityFromInput({
    type: "target", domain: "realpage.com", name: "RealPage", aliases: ["RealPage OneSite", "OneSite", "RealPage Inc."],
  });
  const competitors = ["yardi.com", "entrata.com", "appfolio.com", "buildium.com", "resman.com"]
    .map((domain) => entityFromInput({ type: "competitor", domain }));
  const hash = sha256(JSON.stringify({ prompts, models: providerTargets.map((t) => t.model) })).slice(0, 12);
  const plan = {
    id: `plan-frozen-${Date.now()}`,
    submittedDomain: "realpage.com",
    target,
    competitors,
    prompts,
    providerTargets,
    language: "en",
    autoDiscover: false,
    promptSetId: `frozen-2026-09-12-${hash}`,
    promptSetHash: hash,
    promptSetVersion: PROMPT_SET_VERSION,
    analysisRulesVersion: ANALYSIS_RULES_VERSION,
    runCountPerPrompt: 1,
    plannedAt: new Date().toISOString(),
    estimate: {
      enabledPromptCount: prompts.length,
      disabledPromptCount: 0,
      providerTargetCount: providerTargets.length,
      providerRunCount: prompts.length * providerTargets.length,
    },
  };

  const output = await new AuditRunner().run({ confirmedPlan: plan, maxTokens: 900 });
  await new RunOrchestrator(new ProjectFileStore(monitoringDataDir())).recordAuditOutput(output.audit, output.paths);
  console.log(`Audit completed: ${output.audit.id} (${prompts.length} frozen questions x ${providerTargets.length} AIs)`);
  console.log(`Mention Rate: ${percent(output.metrics.mentionRate)}`);
  console.log(`Recommendation Rate: ${percent(output.metrics.recommendationRate)}`);
  for (const slice of output.metrics.slices.filter((item: { sliceType: string }) => item.sliceType === "provider_model")) {
    console.log(`  ${slice.label}: mention=${percent(slice.mentionRate)} recommendation=${percent(slice.recommendationRate)}`);
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => { console.error(error instanceof Error ? error.message : error); process.exit(1); });
}
