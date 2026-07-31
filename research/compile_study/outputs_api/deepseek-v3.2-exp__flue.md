<!-- model: deepseek/deepseek-v3.2-exp  tier: mid  target: flue  finish: stop -->

Looking at this spec and the Flue API, I can see several mismatches. Here's my implementation attempt:

```typescript
import { defineAgent, defineAction, defineTool } from '@flue/runtime';
import * as v from 'valibot';

// Tool: Read Stripe data
export const readStripe = defineTool({
  name: 'readStripe',
  description: 'Read Stripe metrics for customer acquisition costs',
  input: v.object({}),
  output: v.object({
    ad_spend: v.number(),
    new_customers: v.number(),
    retention_rate: v.optional(v.number())
  }),
  async run() {
    // Implementation would connect to Stripe API
    return { ad_spend: 0, new_customers: 0 };
  }
});

// Tool: Read ad platform data
export const readAdPlatform = defineTool({
  name: 'readAdPlatform',
  description: 'Read advertising platform metrics',
  input: v.object({}),
  output: v.object({
    spend: v.number(),
    conversions: v.number(),
    cost_per_acquisition: v.optional(v.number())
  }),
  async run() {
    // Implementation would connect to ad platform API
    return { spend: 0, conversions: 0 };
  }
});

// Tool: Read customer interviews (simulated/high-cost)
export const readCustomerInterviews = defineTool({
  name: 'readCustomerInterviews',
  description: 'Collect and analyze customer interview data',
  input: v.object({}),
  output: v.object({
    product_market_fit_score: v.number(),
    interview_count: v.number()
  }),
  async run() {
    // High-cost operation - would conduct actual interviews
    return { product_market_fit_score: 0.5, interview_count: 0 };
  }
});

// Tool: Read board sentiment
export const readBoardSentiment = defineTool({
  name: 'readBoardSentiment',
  description: 'Collect board/investor sentiment',
  input: v.object({}),
  output: v.object({
    sentiment_score: v.number(),
    feedback: v.string()
  }),
  async run() {
    // Would collect from meetings/surveys
    return { sentiment_score: 0.5, feedback: '' };
  }
});

// Action: Increase budget
export const increaseBudget = defineAction({
  name: 'increaseBudget',
  description: 'Increase advertising budget',
  input: v.object({ 
    reason: v.string(),
    idempotencyKey: v.string(),
    amount: v.optional(v.number())
  }),
  output: v.object({ applied: v.boolean(), new_budget: v.number() }),
  async run({ input, log }) {
    // Implementation would update ad platform budgets
    log(`Increasing budget: ${input.reason}`);
    return { applied: true, new_budget: 0 };
  }
});

// Action: Change pricing
export const changePricing = defineAction({
  name: 'changePricing',
  description: 'Change product pricing',
  input: v.object({ 
    reason: v.string(),
    idempotencyKey: v.string(),
    new_price: v.number()
  }),
  output: v.object({ applied: v.boolean(), needs_approval: v.boolean() }),
  async run({ input, log }) {
    log(`Requesting pricing change to ${input.new_price}: ${input.reason}`);
    // This action requires founder approval
    return { applied: false, needs_approval: true };
  }
});

// Action: Exit channel
export const exitChannel = defineAction({
  name: 'exitChannel',
  description: 'Exit an advertising channel',
  input: v.object({ 
    reason: v.string(),
    idempotencyKey: v.string(),
    channel: v.string()
  }),
  output: v.object({ applied: v.boolean() }),
  async run({ input, log }) {
    log(`Exiting channel ${input.channel}: ${input.reason}`);
    // This action cannot be undone
    return { applied: true };
  }
});

// Main Agent
export default defineAgent(() => ({
  model: 'anthropic/claude-sonnet-4-6',
  instructions: `You are a customer acquisition optimization agent. Your goals are:
  1. Keep cost per customer below $400 USD
  2. Keep payback months below 12
  
  You monitor:
  - Stripe data (daily) for actual costs and customer counts
  - Ad platform data (daily) for channel performance
  - Customer interviews (weekly) for product-market fit
  - Board sentiment (monthly) for investor perspective
  
  Available actions:
  - increase_budget: Can be undone, affects cost_per_customer
  - change_pricing: Requires founder approval, affects payback_months
  - exit_channel: Cannot be undone, affects cost_per_customer
  
  Decision rules:
  1. If cost_per_customer < 400 AND product_market_fit > 0.6 → increase_budget
  2. If payback_months > 12 → change_pricing
  
  Alert humans when:
  - product_market_fit < 0.4
  - cost_per_customer > 600 for 14 days
  - Any irreversible action (exit_channel) is being considered
  
  Never exceed committed runway.
  
  Important notes:
  - Product-market fit has known bias: reads high when volume is low
  - Channel saturation is judged based on ad platform data
  - Execution is at-least-once: use idempotency keys for all actions`,
  
  actions: [increaseBudget, changePricing, exitChannel],
  
  tools: [readStripe, readAdPlatform, readCustomerInterviews, readBoardSentiment]
}));
```

## did not survive

1. **Temporal constraints and scheduling** - The spec specifies `runs: weekly`, `every: daily`, `every: weekly`, `every: monthly`, and `effect_after` timings. Flue has no built-in scheduling or temporal awareness - agents run continuously when triggered.

2. **Structured goals with units and calculations** - The spec defines goals with units (`USD`) and calculations (`from: [ad_spend, new_customers]`). Flue has no construct for defining or tracking structured goals - these must be implemented in agent logic.

3. **Belief system with properties** - The spec defines beliefs with `question`, `from`, `how`, `explains`, `settled_by`, `known_bias`, and `checked_by`. Flue has no belief system - all reasoning must be in agent instructions.

4. **Observation metadata** - The spec defines observations with `origin`, `how`, `reported_by`, and `cost`. Flue tools have no metadata about cost or origin - all tools are treated equally.

5. **Action metadata** - The spec defines actions with `moves`, `can_undo`, `effect_after`, `consumes`, and `needs_approval`. Flue actions only have name, description, and I/O schema - metadata must be encoded in instructions.

6. **Conditional logic system** - The spec defines `when` rules with conditions and actions. Flue has no declarative rule system - conditions must be implemented in agent reasoning.

7. **Human alert system** - The spec defines `asks_human_when` triggers. Flue has no built-in human notification system - this must be implemented via external integrations.

8. **Role-based access control** - The spec defines `people` with `sees`, `may_decide`, and `loses_if_wrong`. Flue has no role system or permission model.

9. **Constraint system** - The spec defines `never` constraints. Flue has no constraint checking system - these must be implemented in agent logic.

10. **Calibration and uncertainty** - The spec mentions `how: bayesian` and `how: judgement`. Flue has no support for modeling uncertainty or calibration.

11. **Resource budgets** - The spec mentions `runway` and `cost: high`. Flue has no resource budgeting or cost tracking.

12. **Structured accountability** - The spec defines `loses_if_wrong` for different roles. Flue has no accountability tracking.

13. **Explicit non-modeling** - The spec declares `not_modelling` items. Flue has no way to declare modeling boundaries.

14. **Bias awareness** - The spec notes `known_bias` in beliefs. Flue has no bias tracking or correction mechanisms.

The implementation captures the core domain concepts but loses all the structured metadata, scheduling, constraints, and governance aspects of the spec. The agent must implement all reasoning, scheduling, and constraint checking in its instructions and tool usage.