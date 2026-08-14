import { observe, type FlueObservation } from "@flue/runtime";

import type { JsonValue, LoopEvent } from "./types.js";
import { digestIdentifier } from "./privacy.js";

export interface LoopSpecObserverOptions {
  specId: string;
  specDigest: string;
  append(event: LoopEvent): void;
}

function compactTrace(event: FlueObservation): LoopEvent["trace"] {
  const trace: LoopEvent["trace"] = {};
  if (event.instanceId !== undefined) trace.instanceId = digestIdentifier(event.instanceId);
  if (event.conversationId !== undefined) trace.conversationId = digestIdentifier(event.conversationId);
  if (event.operationId !== undefined) trace.operationId = digestIdentifier(event.operationId);
  if (event.turnId !== undefined) trace.turnId = digestIdentifier(event.turnId);
  if (event.toolCallId !== undefined) trace.toolCallId = digestIdentifier(event.toolCallId);
  return trace;
}

function eventId(event: FlueObservation, episodeId: string): string {
  return `${episodeId}:flue-v${event.v}:${event.eventIndex}:${event.type}`;
}

function projected(
  event: FlueObservation,
  options: Pick<LoopSpecObserverOptions, "specId" | "specDigest">,
  type: LoopEvent["type"],
  data: Record<string, JsonValue>
): LoopEvent | null {
  const episodeId = event.submissionId;
  if (episodeId === undefined) return null;
  return {
    schemaVersion: "1.0",
    id: eventId(event, episodeId),
    type,
    occurredAt: event.timestamp,
    episodeId,
    source: "flue",
    specId: options.specId,
    specDigest: options.specDigest,
    trace: compactTrace(event),
    data,
    contentPolicy: "structural-only"
  };
}

/**
 * Project Flue's content-bearing observation union into a small structural event.
 * Prompts, model output, reasoning, tool arguments/results, and application logs are
 * deliberately excluded. Domain outcomes enter through explicit application events.
 */
export function projectFlueObservation(
  event: FlueObservation,
  options: Pick<LoopSpecObserverOptions, "specId" | "specDigest">
): LoopEvent | null {
  switch (event.type) {
    case "submission_queued":
      return projected(event, options, "episode.queued", { kind: event.kind });
    case "submission_running":
      return projected(event, options, "episode.running", {
        kind: event.kind,
        attemptCount: event.attemptCount,
        maxAttempts: event.maxAttempts
      });
    case "submission_settled":
      return projected(event, options, "episode.settled", {
        outcome: event.outcome,
        errorType: event.error?.type ?? null
      });
    case "submission_recovery":
      return projected(event, options, "episode.recovery", {
        operation: event.operation,
        outcome: event.outcome,
        attemptCount: event.attemptCount ?? null
      });
    case "turn":
      return projected(event, options, "model.completed", {
        purpose: event.purpose,
        provider: event.request.providerName,
        model: event.request.requestedModel,
        durationMs: event.durationMs,
        isError: event.isError,
        inputTokens: event.response.usage?.input ?? null,
        outputTokens: event.response.usage?.output ?? null,
        cost: event.response.usage?.cost.total ?? null
      });
    case "tool":
      return projected(event, options, "action.completed", {
        action: event.toolName,
        origin: event.origin ?? "unknown",
        durationMs: event.durationMs,
        isError: event.isError
      });
    case "task":
      return projected(event, options, "delegation.completed", {
        delegate: event.agent ?? "unspecified",
        durationMs: event.durationMs,
        isError: event.isError
      });
    case "operation":
      return projected(event, options, "operation.completed", {
        operationKind: event.operationKind,
        durationMs: event.durationMs,
        isError: event.isError
      });
    case "compaction":
      return projected(event, options, "context.compacted", {
        messagesBefore: event.messagesBefore,
        messagesAfter: event.messagesAfter,
        durationMs: event.durationMs,
        isError: event.isError
      });
    default:
      return null;
  }
}

/** Register once at module scope in a live Flue application. Keep append synchronous. */
export function installLoopSpecObserver(options: LoopSpecObserverOptions): () => void {
  return observe((observation) => {
    const event = projectFlueObservation(observation, options);
    if (event !== null) options.append(event);
  });
}
