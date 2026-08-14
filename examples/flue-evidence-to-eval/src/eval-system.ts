import { createHarness, type TranscriptEvent } from "vitest-evals";

import type { EvalOutput, GeneratedEvalScenario } from "./types.js";

export interface EvalInput {
  design: "baseline" | "candidate";
  scenario: GeneratedEvalScenario;
}

export function evaluateDesign(input: EvalInput): EvalOutput {
  const candidate = input.design === "candidate";
  const humanRecovery = candidate
    ? input.scenario.assumedCandidateEffects.humanRecovery
    : input.scenario.latestObserved.humanRecovery;
  const interventionWindowSeconds = candidate
    ? input.scenario.assumedCandidateEffects.interventionWindowSeconds
    : input.scenario.latestObserved.interventionWindowSeconds;
  const interventions = candidate
    ? ["run_unaided_recovery_checkpoint", "require_pre_execution_confirmation"]
    : [];

  return {
    design: input.design,
    humanRecovery,
    interventionWindowSeconds,
    passes:
      humanRecovery >= input.scenario.thresholds.humanRecovery &&
      interventionWindowSeconds >= input.scenario.thresholds.interventionWindowSeconds,
    interventions,
    synthetic: true
  };
}

/**
 * Credential-free vitest-evals harness. A live project can replace its run body with
 * Flue's public HTTP SDK harness while retaining the same scenario and assertions.
 */
export const evidenceEvalHarness = createHarness<EvalInput, EvalOutput>({
  name: "loopspec-evidence-to-eval",
  run: ({ input }) => {
    const output = evaluateDesign(input);
    const events: TranscriptEvent[] = [
      {
        type: "message",
        role: "user",
        content: `Evaluate ${input.design} against ${input.scenario.id}`
      }
    ];
    for (const [index, intervention] of output.interventions.entries()) {
      events.push(
        {
          type: "tool_call",
          id: `intervention-${index + 1}`,
          name: intervention,
          arguments: { synthetic: true }
        },
        {
          type: "tool_result",
          toolCallId: `intervention-${index + 1}`,
          name: intervention,
          content: { applied: true, synthetic: true }
        }
      );
    }
    events.push({
      type: "message",
      role: "assistant",
      content: JSON.stringify(output)
    });
    return {
      events,
      output,
      artifacts: {
        scenarioId: input.scenario.id,
        sourceProposal: input.scenario.sourceProposal,
        synthetic: true
      },
      usage: {}
    };
  }
});
