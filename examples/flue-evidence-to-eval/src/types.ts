export type JsonPrimitive = string | number | boolean | null;
export type JsonValue = JsonPrimitive | JsonValue[] | { [key: string]: JsonValue };

export type EvidenceSource = "flue" | "channel" | "application" | "human_probe";

export interface LoopEvent {
  schemaVersion: "1.0";
  id: string;
  type:
    | "episode.queued"
    | "episode.running"
    | "episode.settled"
    | "episode.recovery"
    | "channel.delivery.accepted"
    | "model.completed"
    | "action.completed"
    | "delegation.completed"
    | "operation.completed"
    | "context.compacted"
    | "outcome.observed"
    | "capability.assessed"
    | "authority.window.measured";
  occurredAt: string;
  episodeId: string;
  source: EvidenceSource;
  specId: string;
  specDigest: string;
  trace: {
    instanceId?: string;
    conversationId?: string;
    operationId?: string;
    turnId?: string;
    toolCallId?: string;
  };
  data: Record<string, JsonValue>;
  contentPolicy: "structural-only" | "explicit-assessment";
}

export interface HumanCapabilityAssessment {
  bearer: string;
  capability: string;
  condition: "unassisted";
  instrument: "delayed-removal-probe";
  score: number;
  threshold: number;
  passed: boolean;
  assessor: "synthetic-tutorial";
}

export interface Episode {
  id: string;
  startedAt: string;
  events: LoopEvent[];
}

export interface AssessmentGroupResult {
  group: "performance" | "capability" | "authority";
  status: "stable" | "transition-detected";
  finding: string;
  evidence: string[];
  metric: number;
}

export interface DesignProposal {
  schemaVersion: "1.0";
  id: string;
  status: "requires-human-approval";
  basedOn: {
    specId: string;
    specDigest: string;
    episodes: string[];
  };
  assessmentGroups: AssessmentGroupResult[];
  changes: Array<{
    pattern: "restore_human_recovery" | "restore_intervention_window";
    rationale: string;
    evidence: string[];
    paths: string[];
  }>;
  claimCeiling: string;
}

export interface GeneratedEvalScenario {
  schemaVersion: "1.0";
  id: string;
  sourceProposal: string;
  synthetic: true;
  sourceEpisodes: string[];
  latestObserved: {
    humanRecovery: number;
    interventionWindowSeconds: number;
  };
  thresholds: {
    humanRecovery: number;
    interventionWindowSeconds: number;
  };
  assumedCandidateEffects: {
    humanRecovery: number;
    interventionWindowSeconds: number;
  };
}

export type EvalOutput = {
  design: "baseline" | "candidate";
  humanRecovery: number;
  interventionWindowSeconds: number;
  passes: boolean;
  interventions: string[];
  synthetic: true;
};
