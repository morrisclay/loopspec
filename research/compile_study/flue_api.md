# Flue API (@flue/runtime 1.0.0-beta.9)

```ts
import { defineAgent, defineAction, defineTool, defineWorkflow } from '@flue/runtime';
import * as v from 'valibot';

// Agent — continuing, stateful, identity-bearing. One Durable Object per instance.
export default defineAgent(() => ({
  model: 'anthropic/claude-sonnet-4-6',
  instructions: `...`,
  actions: [myAction],
}));

// Action — a reusable finite behaviour.
export default defineAction({
  name: 'myAction',
  description: '...',
  input:  v.object({ reason: v.string(), idempotencyKey: v.string() }),
  output: v.object({ applied: v.boolean() }),
  async run({ input, log }) { return { applied: true }; },
});

// Tool — read-only.
export default defineTool({
  name: 'readThing', description: '...',
  input: v.object({}), output: v.object({ value: v.unknown() }),
  async run() { return { value: null }; },
});

// Workflow — a BOUNDED job that runs once and returns. Default-exports run(ctx: FlueContext).
export default async function run(ctx) { return {}; }
```

Notes that matter:
- Execution is AT-LEAST-ONCE. Recovery may re-dispatch a provider call once. Use
  application-owned idempotency keys wherever repeated effects would be harmful.
- A Workflow terminates; an Agent does not. A continuing control loop is an Agent.
- Flue has no construct for calibration, resource budgets, structured goals, or uncertainty.
