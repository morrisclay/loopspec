import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { assessCausalPowers, generateEvalScenario, proposeDesignRevision } from "./analyze.js";
import { LoopSpecCliEngine } from "./loopspec-engine.js";
import { applyProposal } from "./revise-spec.js";
import { buildSyntheticEvidence, groupEpisodes } from "./synthetic.js";

const here = dirname(fileURLToPath(import.meta.url));
const root = dirname(here);
const repositoryRoot = join(root, "..", "..");
const basePath = join(root, "loops", "support-triage.base.yaml");
const generated = join(root, "generated");

function digest(content: string): string {
  return createHash("sha256").update(content).digest("hex");
}

function json(value: unknown): string {
  return `${JSON.stringify(value, null, 2)}\n`;
}

async function main(): Promise<void> {
  const baseYaml = await readFile(basePath, "utf8");
  const specDigest = digest(baseYaml);
  const evidence = buildSyntheticEvidence(specDigest);
  const episodes = groupEpisodes(evidence);
  const assessments = assessCausalPowers(episodes);
  const proposal = proposeDesignRevision(episodes, assessments, specDigest);
  const scenario = generateEvalScenario(proposal, episodes);
  const candidateYaml = applyProposal(baseYaml, proposal);
  const candidatePath = join(generated, "support-triage.candidate.yaml");

  await mkdir(generated, { recursive: true });
  await writeFile(candidatePath, candidateYaml);

  const engine = new LoopSpecCliEngine({
    executable: process.env.PYTHON ?? "python3",
    prefixArgs: [join(repositoryRoot, "tools", "loopspec.py")],
    cwd: repositoryRoot
  });
  const check = await engine.check(candidatePath);
  if (!check.valid) throw new Error(`candidate LoopSpec is invalid: ${check.errors.join("; ")}`);
  if (check.findings.length > 0) {
    throw new Error(`candidate LoopSpec has ${check.findings.length} unresolved finding(s)`);
  }
  const expansion = await engine.expand(candidatePath);
  if (!expansion.valid) throw new Error(`candidate expansion failed: ${expansion.errors.join("; ")}`);
  const semanticDiff = await engine.diff(basePath, candidatePath);
  if (!semanticDiff.valid) throw new Error(`semantic diff failed: ${semanticDiff.errors.join("; ")}`);

  await Promise.all([
    writeFile(join(generated, "events.jsonl"), `${evidence.map((event) => JSON.stringify(event)).join("\n")}\n`),
    writeFile(join(generated, "episodes.json"), json(episodes)),
    writeFile(join(generated, "assessment-groups.json"), json(assessments)),
    writeFile(join(generated, "revision-proposal.json"), json(proposal)),
    writeFile(join(generated, "human-recovery.eval.json"), json(scenario)),
    writeFile(join(generated, "canonical-ir.json"), json(expansion)),
    writeFile(join(generated, "semantic-diff.json"), json(semanticDiff))
  ]);

  const transitions = assessments.filter((item) => item.status === "transition-detected");
  const summary = [
    "# Evidence-to-eval tutorial result",
    "",
    `- Episodes: ${episodes.length}`,
    `- Structural events: ${evidence.length}`,
    `- Assessment groups: ${assessments.length}`,
    `- Transitions detected: ${transitions.map((item) => item.group).join(", ")}`,
    `- Proposed design patterns: ${proposal.changes.map((item) => item.pattern).join(", ")}`,
    `- Review status: ${proposal.status}`,
    "- Claim ceiling: candidate effects remain explicitly synthetic",
    ""
  ].join("\n");
  await writeFile(join(generated, "SUMMARY.md"), summary);

  console.log("LoopSpec × Flue: evidence-to-eval");
  console.log(`1. Projected ${evidence.length} privacy-minimised events into ${episodes.length} episodes.`);
  for (const assessment of assessments) {
    console.log(`2. ${assessment.group.padEnd(10)} ${assessment.status}: ${assessment.finding}`);
  }
  console.log(`3. Proposed ${proposal.changes.length} review-gated LoopSpec changes.`);
  console.log(
    `4. Typed CLI protocol v${check.protocol_version} validated the candidate with zero findings.`
  );
  console.log(
    `5. Generated a removal-probe eval and ${Object.values(semanticDiff.summary).reduce((a, b) => a + b, 0)} semantic change records.`
  );
}

await main();
