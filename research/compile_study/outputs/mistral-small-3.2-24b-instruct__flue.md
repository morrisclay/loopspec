<!-- model: mistralai/mistral-small-3.2-24b-instruct  tier: weak  target: flue  finish: stop -->

Here's a Flue (TypeScript) implementation of the customer acquisition loop spec:

```typescript
import { Flue } from "flue";

const customerAcquisitionLoop = new Flue({
  name: "customer_acquisition",
  interval: "weekly",
  metrics: {
    cac: {
      target: "< 400",
      dependsOn: ["ad_spend", "new_customers"]
    },
    payback_months: {
      target: "< 12"
    }
  },
  estimates: {
    product_market_fit: {
      sources: ["customer_interviews", "stripe"],
      method: "bayesian",
      explains: "cac",
      settledBy: "a cohort retains above 80% at month 6"
    },
    channel_saturation: {
      sources: ["ad_platform"],
      method: "judgement"
    }
  },
  observations: {
    stripe: {
      measures: ["cac"],
      interval: "daily"
    },
    ad_platform: {
      measures: ["channel_saturation"],
      interval: "daily"
    },
    customer_interviews: {
      measures: ["product_market_fit"],
      interval: "weekly",
      cost: "high"
    },
    board_sentiment: {
      interval: "monthly",
      assertedBy: "investor"
    }
  },
  actions: {
    increase_budget: {
      affects: "cac",
      reversibility: "reversible",
      delay: "2w",
      consumes: ["runway"]
    },
    change_pricing: {
      affects: "payback_months",
      reversibility: "costly",
      delay: "4w",
      approval: "founder"
    },
    exit_channel: {
      reversibility: "irreversible"
    }
  },
  rules: [
    {
      condition: "cac < 400 && product_market_fit > 0.6",
      action: "increase_budget"
    },
    {
      condition: "payback_months > 12",
      action: "change_pricing"
    },
    {
      condition: "product_market_fit < 0.4",
      escalate: "founder"
    }
  ],
  parties: {
    founder: {
      human: true,
      responsibility: "the company",
      visibility: ["cac", "product_market_fit"]
    },
    growth_agent: {
      agent: true,
      responsibility: "nothing"
    },
    investor: {
      human: true,
      responsibility: "a position in the fund"
    }
  },
  constraints: {
    never: ["spend exceeds committed runway"]
  },
  ignored: ["competitor_response", "seasonality"]
});

export default customerAcquisitionLoop;
```

## did not survive

1. **Calibrated_by field**: The original spec had a comment about `calibrated_by` being missing, but Flue doesn't have a direct equivalent concept. The `settledBy` field in the implementation serves a similar purpose but isn't a direct translation.

2. **Approval process details**: The `approval: founder` in the original spec is represented as a string in Flue, but Flue doesn't have a formal approval workflow system like the original spec might imply.

3. **Time units in delays**: The original spec uses "2w" and "4w" for weeks, while Flue expects string representations of time which might need additional parsing.

4. **Cost specification**: The `cost: high` in observations is represented as a string, but Flue doesn't have a formal cost enumeration system.

5. **Asserted_by**: The `asserted_by: investor` is represented as a string, but Flue doesn't have a formal assertion system.

6. **Bears responsibility**: The `bears` field in parties is represented as a string, but Flue doesn't have a formal responsibility system.

7. **Sees visibility**: The `sees` field in parties is represented as an array of strings, but Flue doesn't have a formal visibility control system.

8. **Agent vs human distinction**: The `agent: true` in parties is represented as a boolean, but Flue doesn't have a formal agent system with different capabilities than humans.

9. **Never constraints**: The `never` section is represented as an array of strings, but Flue doesn't have a formal constraint system with enforcement.

10. **Ignoring section**: The `ignoring` section is represented as an array of strings, but Flue doesn't have a formal system for tracking ignored factors.