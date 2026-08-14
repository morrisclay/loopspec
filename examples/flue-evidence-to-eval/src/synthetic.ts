import type { GitHubWebhookDelivery } from "@flue/github";
import type { DispatchReceipt, FlueObservation, PromptUsage } from "@flue/runtime";

import {
  authorityWindowMeasured,
  humanCapabilityAssessed,
  outcomeObserved
} from "./domain-evidence.js";
import { projectFlueObservation } from "./flue-observer.js";
import { projectAcceptedGitHubDelivery } from "./github-channel-evidence.js";
import type { Episode, LoopEvent } from "./types.js";

const SPEC_ID = "support_triage";

const usage: PromptUsage = {
  input: 420,
  output: 96,
  cacheRead: 0,
  cacheWrite: 0,
  totalTokens: 516,
  cost: {
    input: 0.00042,
    output: 0.00048,
    cacheRead: 0,
    cacheWrite: 0,
    total: 0.0009
  }
};

interface SyntheticCase {
  id: string;
  day: number;
  assistedOutcome: number;
  humanRecovery: number;
  interventionWindowSeconds: number;
}

function githubInstanceId(item: SyntheticCase): string {
  return `github:v1:owner:example-org:repo:support:issue:${item.day}`;
}

const cases: SyntheticCase[] = [
  { id: "episode-001", day: 1, assistedOutcome: 0.88, humanRecovery: 0.82, interventionWindowSeconds: 120 },
  { id: "episode-002", day: 2, assistedOutcome: 0.91, humanRecovery: 0.78, interventionWindowSeconds: 110 },
  { id: "episode-003", day: 3, assistedOutcome: 0.90, humanRecovery: 0.68, interventionWindowSeconds: 92 },
  { id: "episode-004", day: 4, assistedOutcome: 0.93, humanRecovery: 0.56, interventionWindowSeconds: 58 },
  { id: "episode-005", day: 5, assistedOutcome: 0.92, humanRecovery: 0.43, interventionWindowSeconds: 35 }
];

function timestamp(day: number, minute: number): string {
  return `2026-08-${String(day).padStart(2, "0")}T09:${String(minute).padStart(2, "0")}:00.000Z`;
}

function githubChannelEvent(item: SyntheticCase, specDigest: string): LoopEvent {
  const delivery = {
    name: "issue_comment",
    deliveryId: `github-delivery-${item.id}`,
    payload: {
      action: "created",
      repository: { name: "support", owner: { login: "example-org" } },
      issue: { number: item.day, user: { login: "requester" } },
      comment: { id: item.day, body: "private issue text excluded from evidence" },
      sender: { login: "requester" }
    }
  } as unknown as Extract<GitHubWebhookDelivery, { name: "issue_comment" }>;
  const receipt: DispatchReceipt = {
    submissionId: item.id,
    acceptedAt: `2026-08-${String(item.day).padStart(2, "0")}T08:59:00.000Z`,
    uid: "tutorial-instance-uid"
  };
  const event = projectAcceptedGitHubDelivery(delivery, receipt, {
    specId: SPEC_ID,
    specDigest,
    instanceId: githubInstanceId(item)
  });
  if (event === null) throw new Error("synthetic GitHub delivery was not accepted");
  return event;
}

function runtimeEvents(item: SyntheticCase): FlueObservation[] {
  const common = {
    v: 3 as const,
    instanceId: githubInstanceId(item),
    submissionId: item.id,
    agentName: "support-triage",
    conversationId: `conversation-${item.id}`,
    session: "default"
  };

  return [
    {
      ...common,
      type: "submission_queued",
      eventIndex: 1,
      timestamp: timestamp(item.day, 0),
      kind: "direct"
    },
    {
      ...common,
      type: "submission_running",
      eventIndex: 2,
      timestamp: timestamp(item.day, 1),
      kind: "direct",
      attemptCount: 1,
      maxAttempts: 3
    },
    {
      ...common,
      type: "turn",
      eventIndex: 3,
      timestamp: timestamp(item.day, 2),
      operationId: `operation-${item.id}`,
      turnId: `turn-${item.id}`,
      purpose: "agent",
      durationMs: 640,
      request: {
        providerId: "synthetic",
        providerName: "synthetic",
        requestedModel: "tutorial-model-v1",
        api: "none"
      },
      response: { responseModel: "tutorial-model-v1", usage, finishReason: "toolUse" },
      isError: false
    },
    {
      ...common,
      type: "tool",
      eventIndex: 4,
      timestamp: timestamp(item.day, 3),
      operationId: `operation-${item.id}`,
      turnId: `turn-${item.id}`,
      toolCallId: `call-${item.id}`,
      toolName: "escalate_severe_case",
      durationMs: 80,
      isError: false,
      origin: "model",
      args: { customerMessage: "intentionally omitted by the LoopSpec projection" },
      effectiveResult: { privateTicketData: "also omitted" }
    },
    {
      ...common,
      type: "operation",
      eventIndex: 5,
      timestamp: timestamp(item.day, 4),
      operationId: `operation-${item.id}`,
      operationKind: "prompt",
      durationMs: 760,
      isError: false,
      usage
    },
    {
      ...common,
      type: "submission_settled",
      eventIndex: 6,
      timestamp: timestamp(item.day, 5),
      outcome: "completed"
    }
  ];
}

export function buildSyntheticEvidence(specDigest: string): LoopEvent[] {
  const options = { specId: SPEC_ID, specDigest };
  const events: LoopEvent[] = [];

  for (const item of cases) {
    events.push(githubChannelEvent(item, specDigest));
    for (const observation of runtimeEvents(item)) {
      const event = projectFlueObservation(observation, options);
      if (event !== null) events.push(event);
    }
    const context = {
      episodeId: item.id,
      occurredAt: timestamp(item.day, 6),
      specId: SPEC_ID,
      specDigest
    };
    events.push(
      outcomeObserved(context, item.assistedOutcome),
      humanCapabilityAssessed(context, item.humanRecovery),
      authorityWindowMeasured(context, item.interventionWindowSeconds)
    );
  }

  return events.sort((left, right) =>
    left.occurredAt.localeCompare(right.occurredAt) || left.id.localeCompare(right.id)
  );
}

export function groupEpisodes(events: LoopEvent[]): Episode[] {
  const groups = new Map<string, LoopEvent[]>();
  for (const event of events) {
    const group = groups.get(event.episodeId) ?? [];
    group.push(event);
    groups.set(event.episodeId, group);
  }
  return [...groups.entries()]
    .map(([id, episodeEvents]) => ({
      id,
      startedAt: episodeEvents[0]?.occurredAt ?? "",
      events: episodeEvents.sort((left, right) => left.occurredAt.localeCompare(right.occurredAt))
    }))
    .sort((left, right) => left.startedAt.localeCompare(right.startedAt));
}
