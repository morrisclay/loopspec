<!-- model: qwen/qwen3-8b  tier: very weak  target: flue  finish: stop -->

## Implementation

```ts
import { defineAgent, defineAction, defineTool, defineWorkflow } from '@flue/runtime';
import * as v from 'valibot';

// Agent — continuing, stateful, identity-bearing. One Durable Object per instance.
export default defineAgent(() => ({
  model: 'anthropic/claude-sonnet-4-6',
  instructions: `Monitor cost_per_customer and product_market_fit. If cost_per_customer is below 400 and product_market_fit is above 0.6, trigger increase_budget. If payback_months exceeds 12, trigger change_pricing. Ask the founder when product_market_fit falls below 0.4, or when cost_per_customer stays above 600 for 14 days. Always ensure spend does not exceed runway. Use the tools to get the latest data from stripe, ad_platform, customer interviews, etc.`,
  actions: [increaseBudgetAction, changePricingAction, exitChannelAction],
}));

// Actions — reusable finite behaviours
export const increaseBudgetAction = defineAction({
  name: 'increaseBudget',
  description: 'Increase the ad budget to acquire more customers.',
  input: v.object({ reason: v.string(), idempotencyKey: v.string() }),
  output: v.object({ applied: v.boolean() }),
  async run({ input, log }) {
    // Logic to increase budget
    return { applied: true };
  },
});

export const changePricingAction = defineAction({
  name: 'changePricing',
  description: 'Adjust pricing to affect payback months.',
  input: v.object({ reason: v.string(), idempotencyKey: v.string() }),
  output: v.object({ applied: v.boolean() }),
  async run({ input, log }) {
    // Logic to change pricing
    return { applied: true };
  },
});

export const exitChannelAction = defineAction({
  name: 'exitChannel',
  description: 'Exit the current advertising channel.',
  input: v.object({ reason: v.string(), idempotencyKey: v.string() }),
  output: v.object({ applied: v.boolean() }),
  async run({ input, log }) {
    // Logic to exit channel
    return { applied: true };
  },
});

// Tools — read-only data sources
export const readStripeTool = defineTool({
  name: 'readStripe',
  description: 'Fetch the current cost per customer from Stripe.',
  input: v.object({}),
  output: v.object({ value: v.number() }),
  async run() {
    // Fetch data from Stripe
    return { value: 350 }; // Example value
  },
});

export const readAdPlatformTool = defineTool({
  name: 'readAdPlatform',
  description: 'Fetch channel saturation data from the ad platform.',
  input: v.object({}),
  output: v.object({ value: v.number() }),
  async run() {
    // Fetch data from ad platform
    return { value: 0.7 }; // Example value
  },
});

export const readCustomerInterviewsTool = defineTool({
  name: 'readCustomerInterviews',
  description: 'Fetch product market fit data from customer interviews.',
  input: v.object({}),
  output: v.object({ value: v.number() }),
  async run() {
    // Fetch data from customer interviews
    return { value: 0.75 }; // Example value
  },
});

export const readBoardSentimentTool = defineTool({
  name: 'readBoardSentiment',
  description: 'Fetch board sentiment data.',
  input: v.object({}),
  output: v.object({ value: v.string() }),
  async run() {
    // Fetch board sentiment
    return { value: 'positive' }; // Example value
  },
});

// Workflow — bounded job that runs once
export default async function run(ctx) {
  // Workflow logic, if any
  return {};
}
```

## did not survive

- **consumes** in actions: The Flue API lacks a construct to represent resource consumption in actions.
- **can_undo** and **needs_approval** in actions: These properties cannot be expressed in the Flue API's action definition schema.
- **effect_after** in actions: The Flue API does not support specifying delays between action initiation and effect.
- **not_modelling** of competitor_response and seasonality: These external factors cannot be represented in the Flue API's modeling capabilities.
- **never** constraint on spend exceeding runway: While the Flue API can include this as a constraint in instructions, it lacks a direct mechanism to enforce it programmatically.
- **asks_human_when** conditions: The Flue API does not provide a structured way to handle human prompts or approvals in the action workflow.