import { createHmac } from "node:crypto";

import { createGitHubChannel } from "@flue/github";
import type { DispatchReceipt } from "@flue/runtime";
import { describe, expect, it } from "vitest";

import { projectAcceptedGitHubDelivery } from "../src/github-channel-evidence.js";
import type { LoopEvent } from "../src/types.js";

const secret = "tutorial-webhook-secret";
const payload = {
  action: "created",
  repository: { name: "support", owner: { login: "example-org" } },
  issue: {
    number: 42,
    user: { login: "requester" },
    title: "Sensitive customer issue"
  },
  comment: {
    id: 9001,
    body: "This body is verified by the channel but must not enter the LoopSpec ledger."
  },
  sender: { login: "requester" }
};

function signedHeaders(body: string, signatureSecret = secret): Record<string, string> {
  const signature = createHmac("sha256", signatureSecret).update(body).digest("hex");
  return {
    "content-type": "application/json",
    "x-github-event": "issue_comment",
    "x-github-delivery": "delivery-9001",
    "x-hub-signature-256": `sha256=${signature}`
  };
}

describe("existing @flue/github channel", () => {
  it("joins a verified delivery to its Flue submission without retaining comment content", async () => {
    let evidence: LoopEvent | null = null;
    const receipt: DispatchReceipt = {
      submissionId: "submission-9001",
      acceptedAt: "2026-08-13T12:00:00.000Z",
      uid: "instance-uid"
    };
    const channel = createGitHubChannel({
      webhookSecret: secret,
      webhook({ delivery }) {
        if (delivery.name !== "issue_comment" || delivery.payload.action !== "created") {
          return undefined;
        }
        const ref = {
          owner: delivery.payload.repository.owner.login,
          repo: delivery.payload.repository.name,
          issueNumber: delivery.payload.issue.number
        };
        evidence = projectAcceptedGitHubDelivery(delivery, receipt, {
          specId: "support_triage",
          specDigest: "b".repeat(64),
          instanceId: channel.instanceId(ref)
        });
        return undefined;
      }
    });
    const body = JSON.stringify(payload);
    const response = await channel.route().request("/webhook", {
      method: "POST",
      headers: signedHeaders(body),
      body
    });

    expect(response.status).toBe(200);
    expect(evidence).toMatchObject({
      episodeId: receipt.submissionId,
      source: "channel",
      type: "channel.delivery.accepted",
      data: {
        provider: "github",
        eventType: "issue_comment",
        resourceKind: "issue",
        deduplicated: false
      }
    });
    expect(JSON.stringify(evidence)).not.toContain(payload.comment.body);
    expect(JSON.stringify(evidence)).not.toContain(payload.issue.title);
    expect(JSON.stringify(evidence)).not.toContain("example-org");
  });

  it("rejects an invalid GitHub signature before application code sees the payload", async () => {
    let calls = 0;
    const channel = createGitHubChannel({
      webhookSecret: secret,
      webhook() {
        calls += 1;
        return undefined;
      }
    });
    const body = JSON.stringify(payload);
    const response = await channel.route().request("/webhook", {
      method: "POST",
      headers: signedHeaders(body, "wrong-secret"),
      body
    });

    expect(response.status).toBe(401);
    expect(calls).toBe(0);
  });
});
