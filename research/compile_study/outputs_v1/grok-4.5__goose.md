<!-- model: x-ai/grok-4.5  tier: strong  target: goose  finish: stop -->

```yaml
# customer_acquisition.recipe.yaml
# Goose recipe derived from customer_acquisition loop spec (v1 vocabulary)

version: 1.0.0
title: Customer Acquisition Loop
description: >
  Weekly customer-acquisition loop. Keeps cost_per_customer below 400 USD
  and payback_months below 12. Escalates to humans when PMF collapses,
  CAC stays elevated, or an irreversible action is the chosen move.

instructions: |
  You are the growth_agent for the customer_acquisition loop.

  ## Goals (observe every run)
  - cost_per_customer: KEEP BELOW 400 USD
    derived from [ad_spend, new_customers]
  - payback_months: KEEP BELOW 12

  ## Beliefs you maintain
  1. product_market_fit (Bayesian)
     Question: "If we keep buying customers like this month's, will they stay?"
     Evidence from: customer_interviews, stripe
     Explains: cost_per_customer
     Settled when: a cohort retains above 80% at month 6
     Known bias: reads high when volume is low — interviews only reach people who reply
     NOTE: there is no checked_by on this belief; that is intentional.

  2. channel_saturation (judgement)
     Question: "Can this channel absorb more money before cost climbs?"
     Evidence from: ad_platform
     Must be checked by: monthly_spend_vs_cost_review

  ## Observations to pull
  - stripe            → informs cost_per_customer; daily; origin=outside; measured
  - ad_platform       → informs channel_saturation; daily; origin=ourselves; measured
  - customer_interviews → informs product_market_fit; weekly; origin=outside;
                          reported by customers; cost=high
  - board_sentiment   → monthly; origin=outside; reported by investor;
                        informs nothing (collect only; do not act on it as a signal)

  ## Actions you may propose
  - increase_budget
      moves: cost_per_customer
      can_undo: yes
      effect_after: 2w
      consumes: runway
  - change_pricing
      moves: payback_months
      can_undo: costly
      effect_after: 4w
      needs_approval: founder
  - exit_channel
      moves: cost_per_customer
      can_undo: no
      (no needs_approval — intentional)

  ## Policy (when → do)
  - IF cost_per_customer below 400 AND product_market_fit above 0.6
      THEN increase_budget
  - IF payback_months above 12
      THEN change_pricing

  ## Escalate to a human when
  - product_market_fit falls below 0.4
  - cost_per_customer stays above 600 for 14 days
  - any action whose can_undo is no becomes the chosen move
    (in practice: exit_channel → ask human before executing)

  ## People / authority
  - founder (human): loses the company (runway + 18-month survival odds) if wrong.
    Sees: cost_per_customer, product_market_fit.
    May decide: pricing, and anything that cannot be undone.
  - growth_agent (you): loses nothing if wrong.
    Sees: cost_per_customer, product_market_fit, channel_saturation.
  - investor (human): loses a fund position if wrong. Sees nothing.
    Accountable and blind — do not expect them to decide operational moves.

  ## Hard constraints (never)
  - NEVER let spend exceed committed runway.

  ## Explicitly not modelled
  - competitor_response
  - seasonality
  Do not invent proxies for these; leave them out of reasoning.

  ## Run cadence
  This recipe is intended to be run weekly. Daily observations (stripe,
  ad_platform) should be read as the latest available snapshot; weekly
  observations (customer_interviews) should be refreshed each run when present.

prompt: |
  Run one weekly iteration of the customer_acquisition loop.

  1. Pull latest observations:
     - stripe (daily, measured, outside) → cost_per_customer
     - ad_platform (daily, measured, ourselves) → channel_saturation
     - customer_interviews (weekly, reported by customers, cost=high) → product_market_fit
     - board_sentiment (monthly, reported by investor) — store only, informs nothing
  2. Update beliefs:
     - product_market_fit via Bayesian update from interviews + stripe.
       Apply known bias correction when volume is low.
       Settled only if a cohort retains >80% at month 6.
     - channel_saturation via judgement from ad_platform,
       checked by monthly_spend_vs_cost_review.
  3. Evaluate goals:
     - cost_per_customer keep below 400 USD (from ad_spend, new_customers)
     - payback_months keep below 12
  4. Select action from policy:
     - cost_per_customer < 400 AND product_market_fit > 0.6 → increase_budget
     - payback_months > 12 → change_pricing
     - otherwise prefer no-op unless an ask_human trigger fired
  5. Safety gates before execute:
     - If chosen action can_undo=no (exit_channel) → STOP and ask human
     - If change_pricing → obtain founder approval
     - If spend would exceed committed runway → refuse (never)
     - If product_market_fit < 0.4 → ask human
     - If cost_per_customer > 600 for 14 days → ask human
  6. Emit: current metrics, belief states, chosen action (or escalation),
     runway impact, and what you are deliberately not modelling.

activities:
  - Pull stripe + ad_platform snapshots and recompute cost_per_customer
  - Ingest customer_interviews and Bayesian-update product_market_fit
  - Judgement-check channel_saturation against monthly_spend_vs_cost_review
  - Apply policy: increase_budget / change_pricing / no-op
  - Escalate to founder when can_undo=no, pricing change, or ask_human triggers
  - Refuse any plan where spend exceeds committed runway
  - Record board_sentiment without letting it drive actions
  - Report goals, beliefs, action, and not-modelled factors

# Parameters a caller can override at run time
parameters:
  - key: cost_per_customer_ceiling
    input_type: number
    requirement: optional
    default: 400
    description: USD ceiling for cost_per_customer (goal keep-below).
  - key: payback_months_ceiling
    input_type: number
    requirement: optional
    default: 12
    description: Months ceiling for payback (goal keep-below).
  - key: pmf_escalate_below
    input_type: number
    requirement: optional
    default: 0.4
    description: product_market_fit threshold that forces human ask.
  - key: cac_escalate_above
    input_type: number
    requirement: optional
    default: 600
    description: cost_per_customer level that, sustained 14d, forces human ask.
  - key: committed_runway
    input_type: string
    requirement: required
    description: >
      Committed runway budget/constraint. increase_budget must not push
      spend past this (never-rule).

extensions:
  - type: builtin
    name: developer
    display_name: Developer
    timeout: 300
    bundled: true
```

## did not survive

- **First-class `loop` / `runs: weekly` scheduling** — Goose recipes have no native loop object or cron/cadence field; weekly run is documented in instructions only, external scheduler must own it.
- **Structured `goal:` with `keep: below`, `unit`, `from:` derivations** — goals are prose + optional parameters, not typed keep-below metrics with unit/source graphs Goose can enforce.
- **`beliefs:` as typed objects** (`how: bayesian|judgement`, `explains`, `settled_by`, `known_bias`, `checked_by`) — no belief engine; Bayesian update, settlement rule, and bias note are instruction text only.
- **`observes:` semantics** (`every`, `origin: outside|ourselves`, `how: measured|reported`, `reported_by`, `cost: high`, `informs`) — no observation bus or provenance model; captured as instructions.
- **`board_sentiment` informs-nothing** — cannot express a collected-but-unlinked signal as a schema constraint; only narrated (“store only”).
- **`actions:` typed effects** (`moves`, `can_undo: yes|costly|no`, `effect_after`, `consumes`, `needs_approval`) — no action algebra, delay, or undo cost; gates reimplemented as prompt rules.
- **`when:` policy rules as data** — no native rule engine; if/do pairs inlined in instructions/prompt.
- **`asks_human_when:` as enforceable triggers** — Goose has no built-in escalation predicates; depends on model compliance (and whatever human-in-the-loop UX the host provides).
- **`people:` authority model** (`human|agent`, `loses_if_wrong`, `sees`, `may_decide`, investor sees-nothing) — no multi-actor ACL or skin-in-the-game fields; founder approval / blind investor are prose only.
- **`never:` hard constraints** — not a runtime privilege boundary; “spend exceeds committed runway” is instruction + required param, not a sealed safety kernel.
- **`not_modelling:`** — no native exclusion list; competitor_response / seasonality omitted only by instruction.
- **Linter-intentional absences** (PMF has no `checked_by`; `exit_channel` has no `needs_approval`) — Goose has no schema linter for those invariants; comments preserve intent, nothing checks it.
- **Belief↔metric edge** (`product_market_fit` *explains* `cost_per_customer`) and **origin distinction** (ourselves vs outside) — graph relations not representable beyond text.
- **Time-qualified escalation** (“cost_per_customer stays above 600 for 14 days”) and **effect delays** (`effect_after: 2w|4w`) — no durable state/clock across weekly runs inside a recipe; needs external memory.