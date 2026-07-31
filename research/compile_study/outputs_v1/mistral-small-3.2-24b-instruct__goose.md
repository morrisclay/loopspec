<!-- model: mistralai/mistral-small-3.2-24b-instruct  tier: weak  target: goose  finish: stop -->

Here's a Goose recipe implementation for the provided YAML spec, followed by a `## did not survive` section:

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

1. **`board_sentiment` observation**: The `reported_by: investor` field is not supported in Goose's observation specification. Goose doesn't have a direct equivalent for tracking who reports the data.

2. **`board_sentiment` informing nothing**: The concept of collecting data without specifying what it informs isn't directly representable in Goose's current model where observations must inform at least one belief or goal.

3. **`needs_approval: founder` in `exit_channel` action**: While the `change_pricing` action has this field, the spec mentions "The linter says so" about `exit_channel` not having it, but Goose doesn't have a way to represent this kind of linter-specific constraint.

4. **`unit: USD` in `cost_per_customer`**: While included in the output, Goose doesn't have a standardized way to represent currency units in goals.

5. **`how: judgement` and `how: bayesian` in beliefs**: While included, Goose doesn't have a formal typing system for these "how" methods - they're treated as free-form text.

6. **`cost: high` in `customer_interviews`**: While included, Goose doesn't have a standardized way to represent cost levels (high/medium/low).

7. **`origin: ourselves` in `ad_platform`**: While included, Goose doesn't have a formal typing system for origin types - they're treated as free-form text.

8. **`can_undo: costly` in `change_pricing`**: While included, Goose doesn't have a standardized way to represent different undo costs beyond boolean yes/no.

The implementation captures the core structure and most fields, but some nuanced aspects of the original spec don't have direct equivalents in Goose's current model.