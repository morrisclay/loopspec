<!-- model: qwen/qwen3-8b  tier: very weak  target: goose  finish: stop -->

```yaml
loop: customer_acquisition
runs: weekly

goal:
  cost_per_customer:
    keep: below 400
    unit: USD
    from: [ad_spend, new_customers]
  payback_months:
    keep: below 12

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
  - if: "cost_per_customer < 400 and product_market_fit > 0.6"
    do: increase_budget
  - if: "payback_months > 12"
    do: change_pricing

asks_human_when:
  - "product_market_fit falls below 0.4"
  - "cost_per_customer stays above 600 for 14 days"

people:
  founder:
    human: yes
    loses_if_wrong: "the company — runway, and 18-month survival odds"
    sees: [cost_per_customer, product_market_fit]
    may_decide: pricing
  growth_agent:
    agent: yes
    loses_if_wrong: nothing
    sees: [cost_per_customer, product_market_fit, channel_saturation]
  investor:
    human: yes
    loses_if_wrong: "a position in the fund"
    sees: []

never:
  - "spend exceeds committed runway"

not_modelling:
  - competitor_response
  - seasonality
```

## did not survive
- The `asks_human_when` condition `"any action whose can_undo is no becomes the chosen move"` cannot be expressed in the target format, as the YAML does not support conditional logic based on action properties.
- The `may_decide` field in the `people` section cannot be fully represented, as the target format does not explicitly support specifying decisions beyond listed actions.
- The `sees` field in the `people` section for the `investor` is omitted (set to an empty list) due to the target format not allowing the `sees` field to be `null` or unlisted.