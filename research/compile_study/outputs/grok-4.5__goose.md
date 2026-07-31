<!-- model: x-ai/grok-4.5  tier: strong  target: goose  finish: stop -->

```yaml
# Goose recipe — customer acquisition loop
# Expanded from loop format (python3 tools/loop.py conceptual source)
version: 1.0.0
title: Customer Acquisition Loop
description: >
  Weekly venture customer-acquisition loop. Regulates CAC and payback period
  via budget, pricing, and channel exit actions; estimates product-market fit
  and channel saturation from Stripe, ads, and interviews.

instructions: |
  You are operating the customer_acquisition control loop for this venture.
  Cadence intent: weekly (invoke this recipe on that rhythm; Goose does not
  schedule you).

  ## Regulators (goals)
  - CAC: target < 400. Compute from ad_spend and new_customers.
  - payback_months: target < 12.

  ## Estimates
  - product_market_fit:
      sources: customer_interviews, stripe
      method: bayesian
      explains: cac
      settled_by: "a cohort retains above 80% at month 6"
      NOTE: no calibrated_by was supplied in the source loop — treat PMF as
      uncalibrated and say so when reporting.
  - channel_saturation:
      sources: ad_platform
      method: judgement

  ## Observations (read these signals when tools allow)
  - stripe — measures CAC; prefer daily freshness
  - ad_platform — measures channel_saturation; prefer daily freshness
  - customer_interviews — measures product_market_fit; weekly; cost high
  - board_sentiment — monthly; asserted by investor (human), not measured

  ## Actions you may propose or take (via tools / human approval)
  - increase_budget:
      moves: cac
      reversibility: reversible
      delay: ~2 weeks
      consumes: runway
  - change_pricing:
      moves: payback_months
      reversibility: costly
      delay: ~4 weeks
      approval required: founder
  - exit_channel:
      reversibility: irreversible

  ## Policy (when)
  - If CAC < 400 and product_market_fit > 0.6 → increase_budget
  - If payback_months > 12 → change_pricing
  - If product_market_fit < 0.4 → escalate to founder

  ## Parties
  - founder (human): bears the company; sees cac, product_market_fit
  - growth_agent (agent): bears nothing — this is you unless reassigned
  - investor (human): bears a position in the fund; may assert board_sentiment

  ## Hard constraints (never)
  - Never allow spend to exceed committed runway.

  ## Explicitly out of scope (ignoring)
  - competitor_response
  - seasonality

  Prefer reversible moves under uncertainty. Surface delay and approval needs
  before acting. Quote regulator targets when recommending a change.

prompt: |
  Run one iteration of the customer_acquisition loop.

  1. Gather latest observations (stripe, ad_platform, customer_interviews,
     board_sentiment if available).
  2. Recompute / re-estimate:
     - cac from ad_spend and new_customers (target < 400)
     - payback_months (target < 12)
     - product_market_fit (bayesian from interviews + stripe; uncalibrated)
     - channel_saturation (judgement from ad_platform)
  3. Apply policy:
     - cac < 400 and product_market_fit above 0.6 → increase_budget
     - payback_months > 12 → change_pricing (founder approval)
     - product_market_fit below 0.4 → escalate to founder
  4. Enforce never: spend must not exceed committed runway.
  5. Ignore competitor_response and seasonality.
  6. Emit a short loop report: signals, estimates, regulator gaps, chosen
     act(s) or escalation, reversibility/delay/consumes, and what blocked you.

activities:
  - Assess CAC vs target (< 400) from ad_spend and new_customers
  - Assess payback_months vs target (< 12)
  - Estimate product_market_fit (bayesian; settled if cohort retains >80% at m6)
  - Estimate channel_saturation (judgement)
  - Propose increase_budget / change_pricing / exit_channel per policy
  - Escalate to founder when PMF is below 0.4
  - Refuse actions that would exceed committed runway

extensions: []
```

## did not survive

- **`every: weekly` (loop-level schedule)** — Goose recipes are invocable sessions, not cron. Cadence is documentation only; external scheduler must re-run the recipe.
- **`regulates.*.target` / `computed_from` as enforced control primitives** — No native regulator or metric graph; targets and formulas live only in instruction text.
- **`estimates.*.method: bayesian | judgement`** — No first-class estimator types or inference engine; methods are prompts to the model.
- **`explains: cac` (causal/explanatory link)** — No structural causal model in recipe YAML.
- **`settled_by: "a cohort retains above 80% at month 6"`** — No settlement/closing condition primitive; cannot auto-mark the estimate resolved.
- **Missing `calibrated_by` linter signal** — Goose has no loop linter; the “should warn” behavior is only restated in instructions.
- **`observes.*.every` (daily/weekly/monthly freshness)** — No sensor cadence or poller; freshness is advisory.
- **`observes.*.measures`** — No typed binding from source → quantity.
- **`observes.*.cost: high`** — No cost model for observations.
- **`asserted_by: investor`** — No assertion vs measurement distinction or party-linked claims ledger.
- **`acts.*.moves`** — No declared effect edges on a state graph.
- **`reversibility: reversible | costly | irreversible`** — Not a Goose action trait; cannot gate UX or require confirmations by policy engine.
- **`delay: 2w | 4w`** — No deferred/effect-at-time semantics.
- **`consumes: [runway]`** — No resource/stock accounting primitive.
- **`approval: founder`** — No built-in multi-party approval workflow in the recipe schema (depends on external human tool/process).
- **`when` rules as executable guards** — Encoded as prompt policy only; not a deterministic rules engine.
- **`escalate: founder`** — No escalation channel primitive (Slack/email/pager) in-spec.
- **`parties` (`human`/`agent`, `bears`, `sees`)** — No principal/agent, liability, or information-partition model in recipes.
- **`never: "spend exceeds committed runway"`** — Hard safety constraint is instructional, not a checked invariant before tool calls.
- **`ignoring: [competitor_response, seasonality]`** — No formal “do not model” elision in a world model; prompt-only.
- **Loop name → flat graph expansion (`tools/loop.py`)** — Goose does not expand nested loop IR into a monitored graph; single recipe document only.
- **Concrete tool bindings for `stripe`, `ad_platform`, interviews** — Left as `extensions: []`; real MCPs/credentials must be wired outside this spec.