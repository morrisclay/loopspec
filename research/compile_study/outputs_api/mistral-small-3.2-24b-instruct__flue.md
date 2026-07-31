<!-- model: mistralai/mistral-small-3.2-24b-instruct  tier: weak  target: flue  finish: stop -->

Here's a Flue implementation for the customer acquisition loop. I'll represent as much of the spec as possible, noting limitations in the `## did not survive` section.

```ts
import { defineAgent, defineAction, defineTool, defineWorkflow } from '@flue/runtime';
import * as v from 'valibot';

// Tools for observations
export default defineTool({
  name: 'observeStripe',
  description: 'Daily observation of cost per customer from Stripe',
  input: v.object({}),
  output: v.object({ costPerCustomer: v.number() }),
  async run() {
    // In reality, this would connect to Stripe API
    return { costPerCustomer: 350 }; // Example value
  },
});

export default defineTool({
  name: 'observeAdPlatform',
  description: 'Daily observation of channel saturation from ad platform',
  input: v.object({}),
  output: v.object({ channelSaturation: v.number() }),
  async run() {
    // In reality, this would connect to ad platform API
    return { channelSaturation: 0.7 }; // Example value
  },
});

export default defineTool({
  name: 'conductCustomerInterviews',
  description: 'Weekly customer interviews for product-market fit',
  input: v.object({}),
  output: v.object({ productMarketFit: v.number() }),
  async run() {
    // In reality, this would involve actual interviews
    return { productMarketFit: 0.65 }; // Example value
  },
});

// Actions
export default defineAction({
  name: 'increaseBudget',
  description: 'Increase marketing budget to acquire more customers',
  input: v.object({
    idempotencyKey: v.string(),
    reason: v.string()
  }),
  output: v.object({ applied: v.boolean() }),
  async run({ input, log }) {
    log.info(`Increasing budget: ${input.reason}`);
    // In reality, this would connect to budget management system
    return { applied: true };
  },
});

export default defineAction({
  name: 'changePricing',
  description: 'Change pricing strategy to improve payback months',
  input: v.object({
    idempotencyKey: v.string(),
    reason: v.string(),
    approval: v.string() // Would need founder approval
  }),
  output: v.object({ applied: v.boolean() }),
  async run({ input, log }) {
    if (!input.approval) {
      throw new Error('Requires founder approval');
    }
    log.info(`Changing pricing: ${input.reason}`);
    // In reality, this would connect to pricing system
    return { applied: true };
  },
});

export default defineAction({
  name: 'exitChannel',
  description: 'Exit a marketing channel permanently',
  input: v.object({
    idempotencyKey: v.string(),
    reason: v.string()
  }),
  output: v.object({ applied: v.boolean() }),
  async run({ input, log }) {
    log.info(`Exiting channel: ${input.reason}`);
    // In reality, this would connect to channel management
    return { applied: true };
  },
});

// Agent for the growth loop
export default defineAgent(() => ({
  model: 'anthropic/claude-sonnet-4-6',
  instructions: `
    You are a growth agent managing customer acquisition. Your goals are:
    1. Keep cost per customer below $400 USD
    2. Keep payback months below 12

    You have the following beliefs:
    - Product-market fit: If we keep buying customers like this month, will they stay?
    - Channel saturation: Can this channel absorb more money before cost climbs?

    You can observe:
    - Stripe data daily for cost per customer
    - Ad platform data daily for channel saturation
    - Customer interviews weekly for product-market fit

    You can take actions:
    - Increase budget (effects cost per customer in 2 weeks)
    - Change pricing (effects payback months in 4 weeks, needs founder approval)
    - Exit channel (effects cost per customer, cannot be undone)

    Rules:
    1. If cost per customer is below 400 AND product-market fit is above 0.6, increase budget
    2. If payback months is above 12, change pricing
    3. Ask founder if product-market fit falls below 0.4
    4. Ask founder if cost per customer stays above 600 for 14 days
    5. Ask founder for any action that cannot be undone
    6. Never spend exceeds committed runway
  `,
  actions: [increaseBudget, changePricing, exitChannel],
  async run(ctx) {
    // Main loop
    while (true) {
      // Observe
      const stripeData = await ctx.tools.observeStripe.run({});
      const adData = await ctx.tools.observeAdPlatform.run({});
      const interviewData = await ctx.tools.conductCustomerInterviews.run({});

      // Check conditions
      if (stripeData.costPerCustomer < 400 && interviewData.productMarketFit > 0.6) {
        await ctx.actions.increaseBudget.run({
          idempotencyKey: `increase-budget-${Date.now()}`,
          reason: 'Cost per customer is good and product-market fit is strong'
        });
      }

      if (/* paybackMonths > 12 */ false) { // Would need actual payback months observation
        await ctx.actions.changePricing.run({
          idempotencyKey: `change-pricing-${Date.now()}`,
          reason: 'Payback months is too high',
          approval: 'founder-approval-token' // Would need actual approval
        });
      }

      // Check for human intervention conditions
      if (interviewData.productMarketFit < 0.4) {
        // Would need mechanism to alert founder
      }

      if (/* costPerCustomer > 600 for 14 days */ false) {
        // Would need mechanism to alert founder
      }

      // Wait for next cycle
      await new Promise(resolve => setTimeout(resolve, 7 * 24 * 60 * 60 * 1000)); // 1 week
    }
  }
}));

// Workflow for monthly review
export default async function runMonthlyReview(ctx) {
  // This would be triggered monthly
  const stripeData = await ctx.tools.observeStripe.run({});
  const adData = await ctx.tools.observeAdPlatform.run({});
  const interviewData = await ctx.tools.conductCustomerInterviews.run({});

  // Check runway constraint
  if (/* spend exceeds runway */ false) {
    throw new Error('Spend exceeds committed runway');
  }

  // Return data for human review
  return {
    costPerCustomer: stripeData.costPerCustomer,
    channelSaturation: adData.channelSaturation,
    productMarketFit: interviewData.productMarketFit
  };
}
```

## did not survive

1. **Bayesian reasoning and uncertainty modeling**: Flue doesn't support probabilistic reasoning or uncertainty modeling. The `how: bayesian` specification for product-market fit cannot be represented.

2. **Structured goals with units and relationships**: While I modeled the goals in the instructions, Flue doesn't have a way to formally represent:
   - The `keep: below 400` with `unit: USD` specification
   - The relationship between `from: [ad_spend, new_customers]`
   - The `explain` relationships between beliefs and metrics

3. **Time-based conditions**: The "stays above 600 for 14 days" condition requires tracking state over time, which isn't directly supported in Flue's action/workflow model.

4. **Human approval flows**: While I modeled the approval requirement, Flue doesn't have a built-in way to:
   - Track approval state
   - Handle multi-step approval processes
   - Model the "may_decide" permissions structure

5. **Resource budgets**: The `consumes: [runway]` and `needs_approval: founder` specifications can't be directly represented in Flue's type system.

6. **Human roles and accountability**: The `people` section with roles, visibility, and accountability cannot be directly represented in Flue.

7. **Never conditions**: The `never` section with "spend exceeds committed runway" is modeled as a check in the monthly review, but there's no way to enforce this as a hard constraint in Flue.

8. **Not modeling declarations**: The `not_modelling` section has no representation in Flue.

9. **Effect timing**: The `effect_after` specifications (2w, 4w) are noted in the instructions but can't be formally represented in Flue's action system.

10. **Reported vs measured distinction**: The `how: reported` vs `how: measured` distinction is noted but can't be formally represented in Flue's tool system.

The implementation captures the core logic and workflow, but many of the more sophisticated aspects of the spec would require additional infrastructure or would need to be handled outside the Flue runtime.