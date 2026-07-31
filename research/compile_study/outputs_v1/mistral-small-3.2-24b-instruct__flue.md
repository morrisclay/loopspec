<!-- model: mistralai/mistral-small-3.2-24b-instruct  tier: weak  target: flue  finish: stop -->

Here's a Flue (TypeScript) implementation of the customer acquisition loop. I've translated the YAML spec into Flue's declarative syntax, with notes about what couldn't be fully represented.

```typescript
import { Flue } from "flue";

const customerAcquisitionLoop = new Flue({
  name: "customer_acquisition",
  schedule: "weekly",

  // Goals
  goals: {
    cost_per_customer: {
      keep: { below: 400, unit: "USD" },
      from: ["ad_spend", "new_customers"]
    },
    payback_months: {
      keep: { below: 12 }
    }
  },

  // Beliefs
  beliefs: {
    product_market_fit: {
      question: "If we keep buying customers like this month's, will they stay?",
      from: ["customer_interviews", "stripe"],
      how: "bayesian",
      explains: "cost_per_customer",
      settled_by: "a cohort retains above 80% at month 6",
      known_bias: "reads high when volume is low — interviews only reach people who reply"
    },
    channel_saturation: {
      question: "Can this channel absorb more money before cost climbs?",
      from: ["ad_platform"],
      how: "judgement",
      checked_by: "monthly_spend_vs_cost_review"
    }
  },

  // Observations
  observations: {
    stripe: {
      informs: "cost_per_customer",
      frequency: "daily",
      origin: "outside",
      method: "measured"
    },
    ad_platform: {
      informs: "channel_saturation",
      frequency: "daily",
      origin: "ourselves",
      method: "measured"
    },
    customer_interviews: {
      informs: "product_market_fit",
      frequency: "weekly",
      cost: "high",
      origin: "outside",
      method: "reported",
      reported_by: "customers"
    },
    board_sentiment: {
      frequency: "monthly",
      origin: "outside",
      method: "reported",
      reported_by: "investor"
    }
  },

  // Actions
  actions: {
    increase_budget: {
      affects: "cost_per_customer",
      undoable: true,
      effectAfter: "2w",
      consumes: ["runway"]
    },
    change_pricing: {
      affects: "payback_months",
      undoable: "costly",
      effectAfter: "4w",
      requiresApproval: "founder"
    },
    exit_channel: {
      affects: "cost_per_customer",
      undoable: false
    }
  },

  // Decision Rules
  when: [
    {
      if: "cost_per_customer < 400 && product_market_fit > 0.6",
      then: "increase_budget"
    },
    {
      if: "payback_months > 12",
      then: "change_pricing"
    }
  ],

  // Human Intervention Points
  asks_human_when: [
    "product_market_fit < 0.4",
    "cost_per_customer > 600 for 14 days",
    "any action with undoable: false becomes the chosen move"
  ],

  // People
  people: {
    founder: {
      isHuman: true,
      risk: "the company — runway, and 18-month survival odds",
      visibility: ["cost_per_customer", "product_market_fit"],
      canDecide: ["pricing", "anything that cannot be undone"]
    },
    growth_agent: {
      isAgent: true,
      risk: "nothing",
      visibility: ["cost_per_customer", "product_market_fit", "channel_saturation"]
    },
    investor: {
      isHuman: true,
      risk: "a position in the fund"
    }
  },

  // Constraints
  constraints: [
    "spend <= committed_runway"
  ],

  // Not Modeling
  not_modeling: [
    "competitor_response",
    "seasonality"
  ]
});

export default customerAcquisitionLoop;
```

## did not survive

1. **Unit specification in goals**: Flue doesn't have a built-in way to specify units (USD) for goal values. The unit information is dropped.

2. **Complex conditional logic in `asks_human_when`**: The last condition "any action whose can_undo is no becomes the chosen move" is complex and might require custom implementation in Flue's runtime rather than being declaratively specified.

3. **Detailed approval requirements**: The `needs_approval` field is simplified to `requiresApproval` without specifying the approval hierarchy or process.

4. **Origin types**: The distinction between "outside" and "ourselves" origins is preserved in the implementation but Flue doesn't have special handling for these semantic differences.

5. **Reporting method nuances**: The distinction between "measured" and "reported" is preserved but Flue doesn't have different processing for these observation types.

6. **Human visibility constraints**: The investor's "sees nothing" is represented by omitting visibility, but Flue doesn't have explicit visibility restrictions.

7. **Effect timing precision**: The "effect_after" times are preserved as strings but Flue doesn't have built-in handling for these time delays in its decision logic.

8. **Undoability nuances**: The "can_undo: costly" is simplified to a boolean-like "undoable: 'costly'" since Flue doesn't have a cost-based undoability system.