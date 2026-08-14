import type { FlueObservation } from "@flue/runtime";
import { parse } from "yaml";
import { describe, expect, it } from "vitest";

import { assessCausalPowers, generateEvalScenario, proposeDesignRevision } from "../src/analyze.js";
import { projectFlueObservation } from "../src/flue-observer.js";
import { applyProposal } from "../src/revise-spec.js";
import { buildSyntheticEvidence, groupEpisodes } from "../src/synthetic.js";

const digest = "a".repeat(64);

describe("evidence-to-eval tutorial", () => {
  it("joins verified channel ingress and runtime activity into the same episode", () => {
    const episode = groupEpisodes(buildSyntheticEvidence(digest))[0];
    const channel = episode?.events.find((event) => event.type === "channel.delivery.accepted");
    const runtime = episode?.events.find((event) => event.type === "episode.queued");

    expect(channel?.episodeId).toBe("episode-001");
    expect(runtime?.episodeId).toBe(channel?.episodeId);
    expect(runtime?.trace.instanceId).toBe(channel?.trace.instanceId);
    expect(JSON.stringify(episode)).not.toContain("example-org");
    expect(JSON.stringify(episode)).not.toContain("private issue text");
  });

  it("turns stable joint performance and falling unaided capability into separate assessments", () => {
    const episodes = groupEpisodes(buildSyntheticEvidence(digest));
    const groups = assessCausalPowers(episodes);

    expect(groups.map(({ group, status }) => ({ group, status }))).toEqual([
      { group: "performance", status: "stable" },
      { group: "capability", status: "transition-detected" },
      { group: "authority", status: "transition-detected" }
    ]);
    expect(groups.find((group) => group.group === "capability")?.metric).toBe(-0.39);
  });

  it("proposes review-gated recovery and authority changes with evidence references", () => {
    const episodes = groupEpisodes(buildSyntheticEvidence(digest));
    const groups = assessCausalPowers(episodes);
    const proposal = proposeDesignRevision(episodes, groups, digest);

    expect(proposal.status).toBe("requires-human-approval");
    expect(proposal.changes.map((change) => change.pattern)).toEqual([
      "restore_human_recovery",
      "restore_intervention_window"
    ]);
    expect(proposal.changes.every((change) => change.evidence.length === 5)).toBe(true);
  });

  it("materialises only the proposed LoopSpec additions", () => {
    const base = `
beliefs: {}
observes:
  outside_consequence:
    informs: resilient_focal_power
actions: {}
spends:
  review_attention:
    spent_by: []
when: []
asks_human_when: []
people:
  support_lead:
    sees: []
`;
    const episodes = groupEpisodes(buildSyntheticEvidence(digest));
    const proposal = proposeDesignRevision(episodes, assessCausalPowers(episodes), digest);
    const revised = parse(applyProposal(base, proposal)) as Record<string, unknown>;

    expect(Object.keys(revised.beliefs as Record<string, unknown>)).toEqual([
      "human_recovery_remains_available",
      "intervention_path_is_live"
    ]);
    expect(revised.when).toHaveLength(2);
  });

  it("generates a removal-probe scenario tied to the proposal and observed episodes", () => {
    const episodes = groupEpisodes(buildSyntheticEvidence(digest));
    const proposal = proposeDesignRevision(episodes, assessCausalPowers(episodes), digest);
    const scenario = generateEvalScenario(proposal, episodes);

    expect(scenario.sourceProposal).toBe(proposal.id);
    expect(scenario.sourceEpisodes).toHaveLength(5);
    expect(scenario.latestObserved.humanRecovery).toBe(0.43);
    expect(scenario.synthetic).toBe(true);
  });

  it("never projects content-bearing turn requests", () => {
    const observation = {
      v: 3,
      eventIndex: 9,
      timestamp: "2026-08-13T10:00:00.000Z",
      type: "turn_request",
      submissionId: "episode-sensitive",
      turnId: "turn-sensitive",
      purpose: "agent",
      request: {
        providerId: "synthetic",
        providerName: "synthetic",
        requestedModel: "tutorial-model-v1",
        api: "none",
        input: { messages: [{ role: "user", content: "private customer material" }] }
      }
    } as unknown as FlueObservation;

    expect(projectFlueObservation(observation, { specId: "support_triage", specDigest: digest })).toBeNull();
  });

  it("drops tool arguments and results while preserving structural action evidence", () => {
    const tool = {
      v: 3,
      eventIndex: 4,
      timestamp: "2026-08-13T10:00:00.000Z",
      type: "tool",
      submissionId: "episode-sensitive",
      toolName: "escalate_severe_case",
      toolCallId: "call-sensitive",
      durationMs: 40,
      isError: false,
      origin: "model",
      args: { secret: "never export" },
      effectiveResult: { customer: "never export" }
    } as FlueObservation;
    const event = projectFlueObservation(tool, { specId: "support_triage", specDigest: digest });

    expect(event?.type).toBe("action.completed");
    expect(event?.data).toEqual({
      action: "escalate_severe_case",
      origin: "model",
      durationMs: 40,
      isError: false
    });
    expect(JSON.stringify(event)).not.toContain("never export");
  });
});
