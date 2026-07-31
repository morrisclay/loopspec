<!-- model: mistralai/mistral-small-3.2-24b-instruct  tier: weak  target: goose  finish: stop -->

Here's a Goose recipe implementation for the provided loop specification. Goose is a workflow orchestration tool that can express most of this, but there are some limitations in the target format.

```yaml
name: customer_acquisition
description: A venture's customer acquisition loop

# Goose doesn't have a direct equivalent for the 'every' field at the loop level
# We'll represent the timing through individual task schedules

# Regulates section - Goose doesn't have direct equivalents for targets
# We'll represent these as metrics to monitor
metrics:
  cac:
    description: "Customer Acquisition Cost should be < 400"
    type: float
    # No direct way to express the target in Goose
  payback_months:
    description: "Payback period should be < 12 months"
    type: float

# Estimates section - Goose doesn't have direct equivalents for estimation methods
# We'll represent these as data sources
data_sources:
  stripe:
    type: api
    schedule: daily
    # No direct way to express the bayesian method in Goose
  ad_platform:
    type: api
    schedule: daily
  customer_interviews:
    type: manual
    schedule: weekly
    cost: high
  board_sentiment:
    type: manual
    schedule: monthly
    asserted_by: investor

# Acts section - Goose has actions but with different semantics
actions:
  increase_budget:
    description: "Increase budget to improve CAC"
    # No direct way to express reversibility, delay, or approval in Goose
    # We'll represent the approval as a condition
    conditions:
      - "cac < 400 and product_market_fit > 0.6"
    # No direct way to express consumes: runway
  change_pricing:
    description: "Change pricing to improve payback period"
    conditions:
      - "payback_months > 12"
  exit_channel:
    description: "Exit a marketing channel"
    # No direct way to express irreversibility

# When section - Goose has workflows but with different semantics
workflows:
  monitor_cac:
    triggers:
      - schedule: daily
    steps:
      - check_condition: "cac < 400 and product_market_fit > 0.6"
        if_true:
          - action: increase_budget
  monitor_payback:
    triggers:
      - schedule: daily
    steps:
      - check_condition: "payback_months > 12"
        if_true:
          - action: change_pricing
  monitor_pmf:
    triggers:
      - schedule: weekly
    steps:
      - check_condition: "product_market_fit < 0.4"
        if_true:
          - notify: founder

# Parties section - Goose has roles but with different semantics
roles:
  founder:
    type: human
    description: "Bears the company responsibility"
    permissions:
      - view: [cac, product_market_fit]
  growth_agent:
    type: agent
    description: "Bears no responsibility"
  investor:
    type: human
    description: "Holds a position in the fund"

# Constraints - Goose has constraints but with different semantics
constraints:
  - "spend must not exceed committed runway"

# No direct equivalent for ignoring in Goose
```

## did not survive

1. **Loop-level timing (`every: weekly`)**: Goose doesn't have a concept of a loop-level timing specification. Timing is specified per task/workflow.

2. **Target values with computed_from**: The `target` and `computed_from` relationship isn't directly expressible in Goose. We can represent the metrics but not their target relationships.

3. **Estimation methods (`method: bayesian`, `method: judgement`)**: Goose doesn't have a concept of estimation methods or how data is processed.

4. **Explains and settled_by**: These relationships between estimates and other metrics aren't directly expressible in Goose.

5. **Reversibility, delay, and approval**: These action attributes don't have direct equivalents in Goose's action model.

6. **Consumes relationship**: The `consumes: runway` relationship isn't directly expressible in Goose.

7. **Irreversibility**: The `irreversible` flag for actions isn't directly expressible in Goose.

8. **Ignoring section**: There's no direct equivalent in Goose for ignoring certain factors.

9. **Calibrated_by**: While the original spec mentions this is missing (and the linter would catch it), Goose doesn't have a concept of calibration requirements.

The Goose implementation captures the core workflow and monitoring aspects but loses much of the nuanced relationships and constraints from the original specification.