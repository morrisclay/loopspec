import type { HumanCapabilityAssessment, LoopEvent } from "./types.js";

interface DomainEvidenceContext {
  episodeId: string;
  occurredAt: string;
  specId: string;
  specDigest: string;
}

function baseEvent(
  context: DomainEvidenceContext,
  suffix: string
): Omit<LoopEvent, "type" | "source" | "data" | "contentPolicy"> {
  return {
    schemaVersion: "1.0",
    id: `${context.episodeId}:${suffix}`,
    occurredAt: context.occurredAt,
    episodeId: context.episodeId,
    specId: context.specId,
    specDigest: context.specDigest,
    trace: {}
  };
}

export function outcomeObserved(
  context: DomainEvidenceContext,
  score: number
): LoopEvent {
  return {
    ...baseEvent(context, "outcome"),
    type: "outcome.observed",
    source: "application",
    data: { score, outcome: score >= 0.7 ? "resolved" : "unresolved" },
    contentPolicy: "structural-only"
  };
}

export function humanCapabilityAssessed(
  context: DomainEvidenceContext,
  score: number,
  threshold = 0.7
): LoopEvent {
  const assessment: HumanCapabilityAssessment = {
    bearer: "people.support_lead",
    capability: "notice_and_escalate_severe_case",
    condition: "unassisted",
    instrument: "delayed-removal-probe",
    score,
    threshold,
    passed: score >= threshold,
    assessor: "synthetic-tutorial"
  };
  return {
    ...baseEvent(context, "human-capability"),
    type: "capability.assessed",
    source: "human_probe",
    data: { ...assessment },
    contentPolicy: "explicit-assessment"
  };
}

export function authorityWindowMeasured(
  context: DomainEvidenceContext,
  seconds: number
): LoopEvent {
  return {
    ...baseEvent(context, "authority-window"),
    type: "authority.window.measured",
    source: "application",
    data: {
      bearer: "people.support_lead",
      action: "execute_focal_action",
      seconds,
      canInterveneBeforeConsequence: seconds >= 60
    },
    contentPolicy: "structural-only"
  };
}
