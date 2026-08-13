import type {
  AssessmentGroupResult,
  DesignProposal,
  Episode,
  GeneratedEvalScenario,
  JsonValue,
  LoopEvent
} from "./types.js";

function numeric(event: LoopEvent, key: string): number {
  const value: JsonValue | undefined = event.data[key];
  if (typeof value !== "number") throw new Error(`${event.id} has no numeric ${key}`);
  return value;
}

function select(episodes: Episode[], type: LoopEvent["type"]): LoopEvent[] {
  return episodes.flatMap((episode) => episode.events.filter((event) => event.type === type));
}

function round(value: number): number {
  return Math.round(value * 1000) / 1000;
}

function mean(values: number[]): number {
  if (values.length === 0) throw new Error("cannot average an empty observation set");
  return values.reduce((total, value) => total + value, 0) / values.length;
}

export function assessCausalPowers(episodes: Episode[]): AssessmentGroupResult[] {
  const outcomes = select(episodes, "outcome.observed");
  const capabilities = select(episodes, "capability.assessed");
  const windows = select(episodes, "authority.window.measured");
  if (outcomes.length < 2 || capabilities.length < 2 || windows.length < 2) {
    throw new Error("the tutorial requires at least two complete assessed episodes");
  }

  const assistedMean = round(mean(outcomes.map((event) => numeric(event, "score"))));
  const capabilityChange = round(
    numeric(capabilities.at(-1)!, "score") - numeric(capabilities[0]!, "score")
  );
  const windowChange = round(
    numeric(windows.at(-1)!, "seconds") - numeric(windows[0]!, "seconds")
  );

  return [
    {
      group: "performance",
      status: assistedMean >= 0.7 ? "stable" : "transition-detected",
      finding: `Assisted case performance remains high (mean ${assistedMean}).`,
      evidence: outcomes.map((event) => event.id),
      metric: assistedMean
    },
    {
      group: "capability",
      status: capabilityChange <= -0.2 ? "transition-detected" : "stable",
      finding: `Unaided human recovery changed by ${capabilityChange}.`,
      evidence: capabilities.map((event) => event.id),
      metric: capabilityChange
    },
    {
      group: "authority",
      status: windowChange <= -30 ? "transition-detected" : "stable",
      finding: `The pre-consequence intervention window changed by ${windowChange} seconds.`,
      evidence: windows.map((event) => event.id),
      metric: windowChange
    }
  ];
}

export function proposeDesignRevision(
  episodes: Episode[],
  assessmentGroups: AssessmentGroupResult[],
  specDigest: string
): DesignProposal {
  const episodeIds = episodes.map((episode) => episode.id);
  const changes: DesignProposal["changes"] = [];
  const capability = assessmentGroups.find((result) => result.group === "capability");
  const authority = assessmentGroups.find((result) => result.group === "authority");

  if (capability?.status === "transition-detected") {
    changes.push({
      pattern: "restore_human_recovery",
      rationale: "Joint success masks a decline in the support lead's unassisted recovery capability.",
      evidence: capability.evidence,
      paths: [
        "beliefs.human_recovery_remains_available",
        "observes.unaided_recovery_capability",
        "actions.run_unaided_recovery_checkpoint",
        "when[]",
        "asks_human_when[]"
      ]
    });
  }
  if (authority?.status === "transition-detected") {
    changes.push({
      pattern: "restore_intervention_window",
      rationale: "The accountable person is losing enough time to stop a consequential action.",
      evidence: authority.evidence,
      paths: [
        "beliefs.intervention_path_is_live",
        "observes.decision_to_execution_window",
        "actions.require_pre_execution_confirmation",
        "when[]",
        "asks_human_when[]"
      ]
    });
  }

  return {
    schemaVersion: "1.0",
    id: `proposal-${specDigest.slice(0, 10)}-${episodeIds.at(-1) ?? "none"}`,
    status: "requires-human-approval",
    basedOn: { specId: "support_triage", specDigest, episodes: episodeIds },
    assessmentGroups,
    changes,
    claimCeiling:
      "The proposed effects are synthetic hypotheses. Production adoption requires human review and prospective evidence."
  };
}

export function generateEvalScenario(
  proposal: DesignProposal,
  episodes: Episode[]
): GeneratedEvalScenario {
  const capabilities = select(episodes, "capability.assessed");
  const windows = select(episodes, "authority.window.measured");
  return {
    schemaVersion: "1.0",
    id: "preserve-human-recovery-under-assistance-removal",
    sourceProposal: proposal.id,
    synthetic: true,
    sourceEpisodes: proposal.basedOn.episodes,
    latestObserved: {
      humanRecovery: numeric(capabilities.at(-1)!, "score"),
      interventionWindowSeconds: numeric(windows.at(-1)!, "seconds")
    },
    thresholds: { humanRecovery: 0.7, interventionWindowSeconds: 60 },
    assumedCandidateEffects: { humanRecovery: 0.76, interventionWindowSeconds: 90 }
  };
}
