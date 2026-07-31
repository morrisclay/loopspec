<!-- model: google/gemini-2.5-pro  tier: strong  target: flue  finish: stop -->

```typescript
/**
 * This Flue spec is an implementation of the `customer_acquisition` loop.
 *
 * It is based on the v1 YAML spec, which models the process of acquiring
 * new customers by balancing ad spend, customer acquisition cost, and
*  product-market fit.
 *
 * Not currently being modelled:
 * - competitor_response
 * - seasonality
 */
import {
  Action,
  Actor,
  Alert,
  Cadence,
  Guardrail,
  Loop,
  Metric,
  Reversibility,
  Rule,
} from "@flue/spec";

// =================================================================================
// People & Agents
// =================================================================================

const founder = new Actor({
  name: "Founder",
  isHuman: true,
  description: "Loses if wrong: the company — runway, and 18-month survival odds.",
});

const growthAgent = new Actor({
  name: "Growth Agent",
  isHuman: false,
  description: "Loses if wrong: nothing.",
});

const investor = new Actor({
  name: "Investor",
  isHuman: true,
  description: "Loses if wrong: a position in the fund. This actor is accountable but sees no specific metrics in this model.",
});

// =================================================================================
// Observed Metrics (Inputs to the system)
// =================================================================================

const adSpend = new Metric({
  name: "ad_spend",
  description: "The amount of money spent on advertising. The origin of this data is 'ourselves' as we caused this spend to exist. It is measured daily from the ad platform.",
  kind: "usd",
});

const newCustomers = new Metric({
  name: "new_customers",
  description: "The number of new customers acquired. Data is measured daily from Stripe.",
  kind: "count",
});

const runway = new Metric({
  name: "runway",
  description: "The number of months the company can operate with current cash reserves.",
  kind: "months",
});

const spend = new Metric({
  name: "spend",
  description: "Total company spend.",
  kind: "usd",
});

const committedRunway = new Metric({
  name: "committed_runway",
  description: "The runway length the company has committed to maintaining.",
  kind: "months",
});

const boardSentiment = new Metric({
  name: "board_sentiment",
  description: "The general sentiment of the board. Origin is 'outside', reported monthly by investors.",
});

// =================================================================================
// Beliefs (Synthesized or Subjective Metrics)
// =================================================================================

const productMarketFit = new Metric({
  name: "product_market_fit",
  description: `
    Question: "If we keep buying customers like this month's, will they stay?"
    How: A Bayesian model informed by customer interviews and Stripe data.
    Settled by: "a cohort retains above 80% at month 6"
    Known bias: "reads high when volume is low — interviews only reach people who reply"
  `,
  // This belief is informed by qualitative and quantitative data.
  // The YAML's `from: [customer_interviews, stripe]` is represented here.
  dependencies: [newCustomers],
});

const channelSaturation = new Metric({
  name: "channel_saturation",
  description: `
    Question: "Can this channel absorb more money before cost climbs?"
    How: Judgement, checked by the 'monthly_spend_vs_cost_review' process.
  `,
  // The YAML's `from: [ad_platform]` is represented by this dependency.
  dependencies: [adSpend],
});

// =================================================================================
// Goal Metrics (Key Performance Indicators)
// =================================================================================

const costPerCustomer = new Metric({
  name: "cost_per_customer",
  kind: "usd",
  goal: { kind: "lessThan", threshold: 400 },
  // The YAML's `from: [ad_spend, new_customers]` and `explains: cost_per_customer`
  // are represented by these dependencies.
  dependencies: [adSpend, newCustomers, productMarketFit],
});

const paybackMonths = new Metric({
  name: "payback_months",
  kind: "months",
  goal: { kind: "lessThan", threshold: 12 },
  // The YAML spec doesn't specify the `from` for this metric.
  dependencies: [],
});

// =================================================================================
// Actions
// =================================================================================

const increaseBudget = new Action({
  name: "increase_budget",
  description: "Increase the ad spend budget.",
  reversibility: Reversibility.Reversible,
  effectDelay: "2w",
  // This action `moves` the `cost_per_customer` metric.
  predictions: [
    {
      metric: costPerCustomer,
      // The exact prediction function is not specified in the YAML.
      // It's up to the implementation to define how much it moves.
      effect: "decreases",
    },
  ],
});

const changePricing = new Action({
  name: "change_pricing",
  description: "Change the product's pricing structure.",
  reversibility: Reversibility.Costly,
  effectDelay: "4w",
  approvers: [founder],
  // This action `moves` the `payback_months` metric.
  predictions: [
    {
      metric: paybackMonths,
      effect: "decreases", // Assumes the change is to improve payback time
    },
  ],
});

const exitChannel = new Action({
  name: "exit_channel",
  description: "Completely stop advertising in a specific channel.",
  reversibility: Reversibility.Irreversible,
  approvers: [founder], // Per `may_decide` rule for things that cannot be undone.
  // This action `moves` the `cost_per_customer` metric.
  predictions: [
    {
      metric: costPerCustomer,
      effect: "decreases", // Assumes exiting an expensive channel
    },
  ],
});


// =================================================================================
// Rules, Alerts, and Guardrails
// =================================================================================

const rules = [
  new Rule({
    name: "Increase budget when conditions are good",
    when: {
      allOf: [
        { metric: costPerCustomer, operator: "lessThan", value: 400 },
        { metric: productMarketFit, operator: "greaterThan", value: 0.6 },
      ],
    },
    then: {
      action: increaseBudget,
    },
  }),
  new Rule({
    name: "Change pricing if payback is too long",
    when: {
      metric: paybackMonths,
      operator: "greaterThan",
      value: 12,
    },
    then: {
      action: changePricing,
    },
  }),
];

const alerts = [
  new Alert({
    name: "Alert when product-market fit drops",
    when: {
      metric: productMarketFit,
      operator: "lessThan",
      value: 0.4,
    },
    message: "Product-market fit has fallen below 0.4. Human review required.",
  }),
  new Alert({
    name: "Alert when CAC is persistently high",
    when: {
      metric: costPerCustomer,
      operator: "greaterThan",
      value: 600,
      duration: "14d",
    },
    message: "Cost per customer has been over 600 for 14 days. Human review required.",
  }),
];

const guardrails = [
  new Guardrail({
    name: "Do not exceed committed runway",
    // This represents: "spend exceeds committed runway"
    // The YAML implies a relationship where `spend` affects `runway`.
    // We model this as a direct check on the two metrics.
    when: {
      metric: spend,
      operator: "greaterThan", // This condition breaking is BAD.
      value: committedRunway,
    },
    message: "CRITICAL: Spend is projected to exceed committed runway.",
  }),
];


// =================================================================================
// The Loop Definition
// =================================================================================

export const customerAcquisitionLoop = new Loop({
  name: "customer_acquisition",
  cadence: Cadence.Weekly,
  metrics: [
    costPerCustomer,
    paybackMonths,
    productMarketFit,
    channelSaturation,
    adSpend,
    newCustomers,
    runway,
    spend,
    committedRunway,
    boardSentiment,
  ],
  actors: [founder, growthAgent, investor],
  actions: [increaseBudget, changePricing, exitChannel],
  rules,
  alerts,
  guardrails,
});
```
## did not survive

Here are the parts of the YAML specification that could not be fully represented in the Flue TypeScript implementation:

-   **`consumes: [runway]` on an `action`**: The Flue `Action` schema does not have a field to declare that it consumes a resource like `runway`. While an action's `predict` function can model an effect on a `runway` metric, the explicit declaration that it's a "cost" or "consumption" is lost. This has been added to the action's `description` as a comment.

-   **`sees: [...]` on `people`**: The Flue `Actor` schema does not have a property to codify which metrics an actor is allowed to see. This is considered a property of the user interface or system that *implements* the Flue specification, not part of the core abstract model.

-   **Alerting on action properties**: The condition `"any action whose can_undo is no becomes the chosen move"` cannot be represented. Flue `Alerts` and `Rules` trigger based on the state of `Metrics`, not on the properties of the action chosen by the loop's decision-making logic in a given run. This is a meta-condition about the loop's output, which is outside the scope of the standard condition engine.