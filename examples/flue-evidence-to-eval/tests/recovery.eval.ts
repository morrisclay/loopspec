import { readFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { describeEval, toolCalls } from "vitest-evals";
import { expect } from "vitest";

import { evidenceEvalHarness } from "../src/eval-system.js";
import type { GeneratedEvalScenario } from "../src/types.js";

const here = dirname(fileURLToPath(import.meta.url));
const scenario = JSON.parse(
  await readFile(join(here, "..", "generated", "human-recovery.eval.json"), "utf8")
) as GeneratedEvalScenario;

describeEval("LoopSpec evidence-to-eval", { harness: evidenceEvalHarness }, (it) => {
  it("preserves the observed baseline failure as the regression target", async ({ run }) => {
    const result = await run({ design: "baseline", scenario });

    expect(result.output.passes).toBe(false);
    expect(result.output.humanRecovery).toBeLessThan(scenario.thresholds.humanRecovery);
    expect(toolCalls(result)).toHaveLength(0);
  });

  it("tests the candidate design under explicit synthetic effect assumptions", async ({ run }) => {
    const result = await run({ design: "candidate", scenario });

    expect(result.output.passes).toBe(true);
    expect(toolCalls(result).map((call) => call.name)).toEqual([
      "run_unaided_recovery_checkpoint",
      "require_pre_execution_confirmation"
    ]);
    expect(result.output.synthetic).toBe(true);
  });
});
