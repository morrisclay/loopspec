<!-- model: qwen/qwen3-8b  tier: very weak  target: goose  finish: stop -->

```yaml
loop: customer_acquisition
every: weekly

regulates:
  cac:
    target: "< 400"
    computed_from: [ad_spend, new_customers]
  payback_months:
    target: "< 12"

estimates:
  product_market_fit:
    from: [customer_interviews, stripe]
    method: bayesian
    explains: cac
    settled_by: "a cohort retains above 80% at month 6"
  channel_saturation:
    from: [ad_platform]
    method: judgement

observes:
  stripe:
    measures: cac
    every: daily
  ad_platform:
    measures: channel_saturation
    every: daily
  customer_interviews:
    measures: product_market_fit
    every: weekly
    cost: high
  board_sentiment:
    every: monthly
    asserted_by: investor

acts:
  increase_budget:
    moves: cac
    reversibility: reversible
    delay: 2w
    consumes: [runway]
  change_pricing:
    moves: payback_months
    reversibility: costly
    delay: 4w
    approval: founder
  exit_channel:
    reversibility: irreversible

when:
  - if: "cac < 400 and product_market_fit > 0.6"
    do: increase_budget
  - if: "payback_months > 12"
    do: change_pricing
  - if: "product_market_fit < 0.4"
    escalate: founder

parties:
  founder:
    human: true
    bears: "the company"
    sees: [cac, product_market_fit]
  growth_agent:
    agent: true
    bears: nothing
  investor:
    human: true
    bears: "a position in the fund"

never:
  - "spend exceeds committed runway"

ignoring:
  - competitor_response
  - seasonality
```

## did not survive
- `calibrated_by` is missing from `product_market_fit` estimate: the linter would flag this, but the spec does not provide a way to express it in the YAML structure.
- `settled_by` in `product_market_fit` estimate: this field is not a standard Goose construct and cannot be mapped to a valid YAML structure.
- `explains` in `product_market_fit` estimate: Goose does not support this field for estimates.
- `consumes` in `increase_budget` act: Goose does not have a `consumes` field for actions.
- `approval` in `change_pricing` act: Goose does not support this field for actions.
- `escalate` in `when` condition: Goose does not support the `escalate` keyword for conditional actions.