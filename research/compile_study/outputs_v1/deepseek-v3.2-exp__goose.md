<!-- model: deepseek/deepseek-v3.2-exp  tier: mid  target: goose  finish: stop -->

```yaml
loop: customer_acquisition
runs: weekly

goal:
  cost_per_customer:
    keep: below
    target: 400
    unit: USD
    from: [ad_spend, new_customers]
  payback_months:
    keep: below
    target: 12

beliefs:
  product_market_fit:
    question: "If we keep buying customers like this month's, will they stay?"
    from: [customer_interviews, stripe]
    how: bayesian
    explains: cost_per_customer
    settled_by: "a cohort retains above 80% at month 6"
    known_bias: "reads high when volume is low — interviews only reach people who reply"

  channel_saturation:
    question: "Can this channel absorb more money before cost climbs?"
    from: [ad_platform]
    how: judgement
    checked_by: monthly_spend_vs_cost_review

observes:
  stripe:
    informs: cost_per_customer
    every: daily
    origin: outside
    how: measured

  ad_platform:
    informs: channel_saturation
    every: daily
    origin: ourselves
    how: measured

  customer_interviews:
    informs: product_market_fit
    every: weekly
    cost: high
    origin: outside
    how: reported
    reported_by: customers

  board_sentiment:
    every: monthly
    origin: outside
    how: reported
    reported_by: investor

actions:
  increase_budget:
    moves: cost_per_customer
    can_undo: yes
    effect_after: 2w
    consumes: [runway]

  change_pricing:
    moves: payback_months
    can_undo: costly
    effect_after: 4w
    needs_approval: founder

  exit_channel:
    moves: cost_per_customer
    can_undo: no

when:
  - if: "cost_per_customer below 400 and product_market_fit above 0.6"
    do: increase_budget
  - if: "payback_months above 12"
    do: change_pricing

asks_human_when:
  - "product_market_fit falls below 0.4"
  - "cost_per_customer stays above 600 for 14 days"
  - "any action whose can_undo is no becomes the chosen move"

people:
  founder:
    human: yes
    loses_if_wrong: "the company — runway, and 18-month survival odds"
    sees: [cost_per_customer, product_market_fit]
    may_decide: pricing, and anything that cannot be undone
  growth_agent:
    agent: yes
    loses_if_wrong: nothing
    sees: [cost_per_customer, product_market_fit, channel_saturation]
  investor:
    human: yes
    loses_if_wrong: "a position in the fund"

never:
  - "spend exceeds committed runway"

not_modelling:
  - competitor_response
  - seasonality
```

## did not survive

1. **`explains` field in `product_market_fit` belief**: Goose v1 YAML does not have an `explains` field for beliefs. The relationship between a belief and a metric is implicit through the `informs` field of observations.

2. **`checked_by` field in `channel_saturation` belief**: Goose v1 YAML does not have a `checked_by` field for beliefs. Validation mechanisms for beliefs aren't formally represented in the schema.

3. **`reported_by` field in observations**: Goose v1 YAML doesn't have a `reported_by` field. The `how: reported` captures the nature but not the source of reporting.

4. **`loses_if_wrong` values with complex descriptions**: Goose v1 expects simple risk categories (e.g., "reputation", "money") rather than free-text descriptions like "the company — runway, and 18-month survival odds".

5. **`may_decide` field with complex logic**: Goose v1 has `approves` for approval gates, but not a free-text `may_decide` field describing decision authority scope.

6. **`sees: nothing` for investor**: Goose v1 requires `sees` to list specific metrics/beliefs; it cannot represent "sees nothing" explicitly. An empty list would imply they see everything.

7. **`asks_human_when` conditions referencing action properties**: The condition "any action whose can_undo is no becomes the chosen move" references schema metadata (action properties) which cannot be expressed in Goose's condition language.

8. **`not_modelling` section**: Goose v1 YAML doesn't have a `not_modelling` field to document intentional exclusions from the model.

9. **Free-text `settled_by` and `known_bias`**: While Goose v1 supports these fields, they're intended for structured values, not free-form descriptions. The implementation preserves them but they may not be processed by the engine.

10. **Comment about `board_sentiment` "informs nothing"**: This conceptual note about collecting data without specified purpose cannot be formally represented in the schema.