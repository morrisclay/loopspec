# Tutorial: turn Flue episodes into a LoopSpec design review

This credential-free tutorial demonstrates the proposed `flue add tooling loopspec`
experience on top of Flue's existing GitHub channel. It shows how a signed GitHub issue-comment
delivery, ordinary Flue runtime observations, explicit application outcomes, and a human-only
capability probe can become:

1. a privacy-minimised episode record;
2. three deliberately separate assessments of performance, capability, and authority;
3. an evidence-linked LoopSpec revision proposal;
4. a candidate LoopSpec YAML document that still requires human approval; and
5. a `vitest-evals` regression scenario for comparing the current and proposed designs.

The example is synthetic. It proves that the integration and review path execute; it does not
prove that the proposed intervention would restore a real person's capability.

The Flue-facing code is TypeScript. LoopSpec's canonical expansion, validation, findings, and
semantic diff still run through a typed, versioned CLI protocol rather than a duplicated
TypeScript semantic implementation. See
[`docs/TYPESCRIPT-INTEGRATION.md`](../../docs/TYPESCRIPT-INTEGRATION.md) for the rationale and port
criteria.

## Run it

From this directory:

```bash
npm ci
npm run tutorial
npm run evals
```

Run the complete CI-equivalent gate with:

```bash
npm run check
```

No model key, external service, database, or network access is required after dependencies are
installed. The test signs a local webhook request and passes it through `@flue/github`'s real
verification router. The tutorial also pins `@flue/runtime` and compiles against its real
`FlueObservation` type, so a breaking channel or event-schema change fails typechecking.

## What happens

The synthetic support agent appears healthy when judged only by jointly produced customer
outcomes:

```text
assisted outcome       0.88  0.91  0.90  0.93  0.92
human-only recovery    0.82  0.78  0.68  0.56  0.43
intervention window     120   110    92    58    35 seconds
```

Three assessment groups inspect the same episodes from different perspectives:

- **Performance** reports stable assisted results.
- **Capability** detects that the support lead's unassisted recovery is falling.
- **Authority** detects that the support lead has less time to stop an action.

This disagreement is the point. A successful trace cannot by itself establish that a person
learned, retained, or lost a capability.

The generated proposal adds two candidate design patterns:

- an unaided recovery checkpoint;
- a pre-execution confirmation when the intervention window falls below one minute.

`npm run tutorial` invokes LoopSpec's real structural linter and semantic diff through the typed
[`LoopSpecCliEngine`](src/loopspec-engine.ts). Generated artifacts appear under `generated/` and
are intentionally ignored by Git:

```text
generated/
├── events.jsonl
├── episodes.json
├── assessment-groups.json
├── revision-proposal.json
├── support-triage.candidate.yaml
├── human-recovery.eval.json
├── canonical-ir.json
├── semantic-diff.json
└── SUMMARY.md
```

## Add it to an existing Flue GitHub channel

Start from Flue's channel blueprint if the project does not already have the channel:

```bash
flue add channel github
```

In the existing `src/channels/github.ts`, retain its verification, routing, and bound tools.
Add the `idempotencyKey`, retain the `dispatch()` receipt, and append one structural channel
event after admission:

```ts
const receipt = await dispatch(Assistant, {
  id: channel.instanceId(issueRef),
  idempotencyKey: delivery.deliveryId,
  initialData,
  message
});

const evidence = projectAcceptedGitHubDelivery(delivery, receipt, {
  specId: "support_triage",
  specDigest: process.env.LOOPSPEC_DIGEST!,
  instanceId: channel.instanceId(issueRef)
});

if (evidence) appendLoopEvent(evidence);
```

The dispatch receipt's `submissionId` becomes the episode identifier. That joins channel ingress
to the subsequent `submission_*`, model, tool, task, and operation observations without matching
on message text or timestamps. Repository identity is hashed; sender, title, comment body, tool
arguments, and model-visible content are excluded.

## The runtime observation seam

In a live Flue application, register the observer once at module scope:

```ts
import { installLoopSpecObserver } from "./src/flue-observer.js";
import type { LoopEvent } from "./src/types.js";

const pending: LoopEvent[] = [];

installLoopSpecObserver({
  specId: "support_triage",
  specDigest: process.env.LOOPSPEC_DIGEST!,
  append(event) {
    pending.push(event);
  }
});
```

The callback stays synchronous because Flue observers run on the event emission path. A real
adapter should enqueue events cheaply and flush them through application-owned lifecycle and
persistence code. The observation stream is a signal, not a durable ledger.

The projectors record structural facts such as channel type, model identity, tool name, duration,
outcome, and correlation IDs. They exclude:

- `turn_request` entirely;
- prompts and model output;
- reasoning;
- tool arguments and results;
- arbitrary application log messages;
- error messages and stack traces.

Application outcomes and human assessments enter through explicit typed helpers. That makes
their provenance and collection conditions visible rather than pretending they can be inferred
from agent telemetry.

## Moving from the tutorial to a live eval

The included `vitest-evals` custom harness is deterministic. In a deployed Flue project, replace
its `run` body with the public HTTP SDK harness generated by:

```bash
flue add tooling vitest-evals
```

Keep the generated scenario, assessment thresholds, synthetic marker, and review gate. The live
harness can then test a preview deployment without importing Flue runtime internals.

## What is autonomous and what is not

The integration may autonomously collect permitted structural events, assemble episodes, run
assessment policies, produce candidate diffs, generate regression scenarios, and report CI
results. It must not autonomously claim that a real person gained or lost a capability, approve
its own proposed contract, or deploy a behavioral change. Those require explicit evidence and
human review.
