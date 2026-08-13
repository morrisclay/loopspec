import { createHash } from "node:crypto";

import type { GitHubWebhookDelivery } from "@flue/github";
import type { DispatchReceipt } from "@flue/runtime";

import type { LoopEvent } from "./types.js";
import { digestIdentifier } from "./privacy.js";

type GitHubIssueCommentDelivery = Extract<GitHubWebhookDelivery, { name: "issue_comment" }>;
type GitHubReviewCommentDelivery = Extract<
  GitHubWebhookDelivery,
  { name: "pull_request_review_comment" }
>;

export type SupportedGitHubDelivery = GitHubIssueCommentDelivery | GitHubReviewCommentDelivery;

interface GitHubEvidenceOptions {
  specId: string;
  specDigest: string;
  instanceId: string;
}

function resourceDigest(owner: string, repo: string, number: number): string {
  return createHash("sha256").update(`${owner}/${repo}#${number}`).digest("hex").slice(0, 16);
}

/**
 * Join a verified GitHub channel delivery to the Flue submission admitted for it.
 * Call this only inside @flue/github's verified webhook callback, after dispatch().
 */
export function projectAcceptedGitHubDelivery(
  delivery: SupportedGitHubDelivery,
  receipt: DispatchReceipt,
  options: GitHubEvidenceOptions
): LoopEvent | null {
  if (delivery.payload.action !== "created") return null;

  const repository = delivery.payload.repository;
  const number =
    delivery.name === "issue_comment"
      ? delivery.payload.issue.number
      : delivery.payload.pull_request.number;
  const resourceKind =
    delivery.name === "pull_request_review_comment" ||
    (delivery.name === "issue_comment" && delivery.payload.issue.pull_request !== undefined)
      ? "pull_request"
      : "issue";

  return {
    schemaVersion: "1.0",
    id: `${receipt.submissionId}:github:${delivery.deliveryId}`,
    type: "channel.delivery.accepted",
    occurredAt: receipt.acceptedAt,
    episodeId: receipt.submissionId,
    source: "channel",
    specId: options.specId,
    specDigest: options.specDigest,
    trace: { instanceId: digestIdentifier(options.instanceId) },
    data: {
      provider: "github",
      eventType: delivery.name,
      deliveryId: delivery.deliveryId,
      resourceKind,
      resourceDigest: resourceDigest(repository.owner.login, repository.name, number),
      deduplicated: receipt.deduplicated ?? false
    },
    contentPolicy: "structural-only"
  };
}
