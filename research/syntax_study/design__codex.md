# Loopfile 1.0: a readable specification for agent loops

## The syntax in 30 seconds

A Loopfile is YAML. Its top level contains shared named things:

- `observations` are data that actually arrives.
- `metrics` are quantities calculated from observations.
- `beliefs` are claims the system cannot see directly.
- `actions` are the choices the system can execute.
- `loops` say who runs, what success means, when to hand off, and how to choose an action.
- `participants`, `hard_rules`, `messages`, and `known_gaps` make consequences, limits, multi-agent communication, and omissions visible.

References, rather than nesting, connect these things. That makes a file readable top-to-bottom, lets several loops share the same metric or action, and gives a diagram generator its edges without any layout instructions.

Two distinctions are intentionally impossible to collapse:

```yaml
origin:
  kind: loop-produced       # Did our own action cause this data to exist?
obtained_as:
  kind: measured            # Was its value measured, reported, or calculated?
```

Thus ad spend can be both **loop-produced** and **measured**, while a customer's survey answer can be both **outside** and **reported**.

Conditions and calculations use CEL (Common Expression Language). Durations and money are readable strings such as `90 days` and `400 USD`. Numbers in expressions use the unit declared on their observation or metric.

## Full example: startup customer acquisition

This is a complete Loopfile. The only deployment-specific values are credentials and URLs named by environment variables.

```yaml
loop_spec: "1.0"
name: startup-customer-acquisition
summary: Keep paid-social customer acquisition cost at or below 400 USD without buying growth that the product or margins cannot sustain.

runtime:
  timezone: America/Los_Angeles
  state:
    kind: sqlite
    path: ./state/acquisition-loop.db
    keep_history_for: 400 days
  on_error:
    attempts: 3
    backoff: 10 seconds
    then: stop_without_action

connections:
  warehouse:
    kind: sql
    driver: postgres
    dsn_from_env: WAREHOUSE_DSN

  growth_ops:
    kind: http
    base_url_from_env: GROWTH_OPS_URL
    auth:
      kind: bearer
      token_from_env: GROWTH_OPS_TOKEN

  analyst_model:
    kind: llm
    base_url: https://api.openai.com/v1
    api_key_from_env: OPENAI_API_KEY
    model_from_env: LOOP_MODEL
    temperature: 0

participants:
  acquisition_agent:
    kind: agent
    role: Reads acquisition evidence, updates the product-market-fit belief, and chooses allowed actions.
    loses_if_wrong:
      - Its authority to change acquisition settings.
      - Trust recorded in its operating review.
    receives:
      - what:
          - observations.paid_ad_spend_28d
          - observations.new_paid_customers_28d
          - observations.activation_rate_14d
          - observations.pmf_pulse_reports
          - observations.retention_90d
          - observations.current_starter_price
          - observations.current_daily_ad_budget
          - observations.paid_social_status
          - metrics.customer_acquisition_cost_28d
          - metrics.gross_margin_fraction
          - beliefs.product_market_fit
        when: each run
        via: shared_state

  founder:
    kind: human
    role: Owns pricing and irreversible channel decisions.
    loses_if_wrong:
      - Runway if acquisition spend is wasted.
      - Revenue and customer trust if pricing is mishandled.
      - Time and future channel access if paid social is exited too early.
    receives:
      - what: [approval_packet, hand_off_packet, run_error]
        when: only when one is created
        via: console

  customers:
    kind: group
    role: Buy and use the product; some voluntarily answer the PMF pulse.
    loses_if_wrong:
      - Money from a price that exceeds the value received.
      - Time invested in a product that may not be sustained.
    receives:
      - what: [actions.change_starter_price]
        when: before checkout after an approved price change
        via: live pricing page

observations:
  paid_ad_spend_28d:
    description: Settled paid-social spend in the trailing 28 days.
    value: {type: number, unit: USD, minimum: 0}
    arrives: {every: 1 day, at: "07:00", lag: 1 day, max_age: 36 hours}
    cost: {money: 0 USD, staff_time: 0 minutes, per: arrival}
    origin:
      kind: loop-produced
      produced_by: [set_daily_ad_budget, exit_paid_social]
    obtained_as:
      kind: measured
      by: ad-platform settlement records
      method: Sum settled spend, excluding credits and pending charges.
    informs: []
    read:
      connection: warehouse
      query: |
        SELECT COALESCE(SUM(spend_usd), 0)::float AS value
        FROM ad_spend
        WHERE channel = 'paid_social'
          AND settled_at >= now() - interval '28 days';
      take: row.value

  new_paid_customers_28d:
    description: Distinct first-time paying customers attributed to paid social in the trailing 28 days.
    value: {type: integer, unit: customers, minimum: 0}
    arrives: {every: 1 day, at: "07:05", lag: 1 day, max_age: 36 hours}
    cost: {money: 0 USD, staff_time: 0 minutes, per: arrival}
    origin:
      kind: outside
      source: Customer purchases recorded by Stripe.
    obtained_as:
      kind: measured
      by: successful first-payment events
      method: Count distinct customer IDs; use the frozen first-touch attribution table.
    informs: [product_market_fit]
    read:
      connection: warehouse
      query: |
        SELECT COUNT(DISTINCT customer_id)::int AS value
        FROM first_payments
        WHERE first_touch_channel = 'paid_social'
          AND paid_at >= now() - interval '28 days'
          AND payment_status = 'settled';
      take: row.value

  activation_rate_14d:
    description: Fraction of new accounts that complete the activation checklist within 14 days.
    value: {type: number, unit: fraction, minimum: 0, maximum: 1}
    arrives: {every: 1 day, at: "07:10", lag: 1 day, max_age: 36 hours}
    cost: {money: 0 USD, staff_time: 0 minutes, per: arrival}
    origin:
      kind: outside
      source: Customer behavior in the product.
    obtained_as:
      kind: calculated
      by: warehouse
      based_on: [account_created events, activation_checklist_completed events]
    informs: [product_market_fit]
    read:
      connection: warehouse
      query: |
        SELECT COALESCE(AVG(activated_within_14d::int), 0)::float AS value
        FROM account_activation_cohorts
        WHERE created_at >= now() - interval '42 days'
          AND created_at < now() - interval '14 days';
      take: row.value

  pmf_pulse_reports:
    description: The latest week's answers to “How disappointed would you be if this product disappeared?”
    value:
      type: array
      items:
        type: object
        fields:
          response_id: {type: string}
          answer: {type: string, enum: [not_disappointed, somewhat_disappointed, very_disappointed]}
          comment: {type: string}
    arrives: {every: 1 week, at: "Monday 07:15", lag: 1 day, max_age: 8 days}
    cost: {money: 25 USD, staff_time: 30 minutes, per: arrival}
    origin:
      kind: outside
      source: Current paying customers.
    obtained_as:
      kind: reported
      by: customers
      reporter_stake: Respondents may hope for roadmap attention, discounts, or continued service, and non-respondents are invisible.
    informs: [product_market_fit]
    read:
      connection: warehouse
      query: |
        SELECT response_id, answer, comment
        FROM pmf_pulse_responses
        WHERE submitted_at >= now() - interval '7 days'
        ORDER BY submitted_at DESC;
      take: rows

  newest_weekly_cohort:
    description: The week identifier for which a new product-market-fit forecast should be recorded.
    value: {type: string, format: date}
    arrives: {every: 1 week, at: "Monday 07:20", lag: 0 days, max_age: 8 days}
    cost: {money: 0 USD, staff_time: 0 minutes, per: arrival}
    origin:
      kind: outside
      source: New paying customers entering a weekly cohort.
    obtained_as:
      kind: calculated
      by: warehouse
      based_on: [successful first-payment events]
    informs: []
    read:
      connection: warehouse
      query: |
        SELECT date_trunc('week', now())::date::text AS value;
      take: row.value

  retention_90d:
    description: The most recently matured weekly cohort and its fraction still active after 90 days.
    value:
      type: object
      fields:
        cohort_week: {type: string, format: date}
        retention_rate: {type: number, unit: fraction, minimum: 0, maximum: 1}
    arrives: {every: 1 week, at: "Monday 07:25", lag: 90 days, max_age: 8 days}
    cost: {money: 0 USD, staff_time: 15 minutes, per: arrival}
    origin:
      kind: outside
      source: Customer activity or cancellation 90 days after first payment.
    obtained_as:
      kind: calculated
      by: warehouse
      based_on: [successful first-payment events, account_active events, cancellations]
    informs: [product_market_fit]
    read:
      connection: warehouse
      query: |
        SELECT cohort_week::date::text AS cohort_week,
               AVG(active_on_day_90::int)::float AS retention_rate
        FROM paid_customer_retention
        WHERE cohort_week <= date_trunc('week', now() - interval '90 days')
        GROUP BY cohort_week
        ORDER BY cohort_week DESC
        LIMIT 1;
      take: row

  current_starter_price:
    description: Monthly USD price currently shown to new Starter-plan customers.
    value: {type: number, unit: USD/month, minimum: 0}
    arrives: {every: 1 hour, lag: 0 minutes, max_age: 2 hours}
    cost: {money: 0 USD, staff_time: 0 minutes, per: arrival}
    origin:
      kind: loop-produced
      produced_by: [change_starter_price]
    obtained_as:
      kind: measured
      by: live billing configuration
      method: Read the active new-customer price, not invoices from grandfathered cohorts.
    informs: [product_market_fit]
    read:
      connection: warehouse
      query: |
        SELECT monthly_usd::float AS value
        FROM live_prices
        WHERE plan = 'starter' AND audience = 'new_customers';
      take: row.value

  current_daily_ad_budget:
    description: The paid-social platform's accepted daily budget.
    value: {type: number, unit: USD/day, minimum: 0}
    arrives: {every: 1 hour, lag: 5 minutes, max_age: 2 hours}
    cost: {money: 0 USD, staff_time: 0 minutes, per: arrival}
    origin:
      kind: loop-produced
      produced_by: [set_daily_ad_budget, exit_paid_social]
    obtained_as:
      kind: measured
      by: live ad-platform configuration
      method: Read the accepted account-level budget after platform validation.
    informs: []
    read:
      connection: warehouse
      query: |
        SELECT daily_budget_usd::float AS value
        FROM ad_channel_settings
        WHERE channel = 'paid_social';
      take: row.value

  paid_social_status:
    description: Whether paid social is operating or has been permanently exited.
    value: {type: string, enum: [active, exited]}
    arrives: {every: 1 hour, lag: 5 minutes, max_age: 2 hours}
    cost: {money: 0 USD, staff_time: 0 minutes, per: arrival}
    origin:
      kind: loop-produced
      produced_by: [exit_paid_social]
    obtained_as:
      kind: measured
      by: acquisition operations registry
      method: Read the channel lifecycle state.
    informs: []
    read:
      connection: warehouse
      query: |
        SELECT lifecycle_state AS value
        FROM acquisition_channels
        WHERE channel = 'paid_social';
      take: row.value

  unit_service_cost:
    description: Expected monthly infrastructure and support cost for one active Starter customer.
    value: {type: number, unit: USD/month, minimum: 0}
    arrives: {every: 1 week, at: "Monday 06:00", lag: 7 days, max_age: 14 days}
    cost: {money: 0 USD, staff_time: 60 minutes, per: arrival}
    origin:
      kind: outside
      source: Cloud invoices and support time.
    obtained_as:
      kind: calculated
      by: finance warehouse model
      based_on: [cloud invoices, support time reports, active customer count]
    informs: []
    read:
      connection: warehouse
      query: |
        SELECT estimated_monthly_usd::float AS value
        FROM starter_unit_cost
        ORDER BY week DESC
        LIMIT 1;
      take: row.value

metrics:
  customer_acquisition_cost_28d:
    description: Settled paid-social spend divided by new paid customers attributed to paid social.
    unit: USD/customer
    calculate: observations.paid_ad_spend_28d.value / observations.new_paid_customers_28d.value
    valid_when: observations.new_paid_customers_28d.value >= 10

  gross_margin_fraction:
    description: Gross margin at the price offered to new Starter customers.
    unit: fraction
    calculate: (observations.current_starter_price.value - observations.unit_service_cost.value) / observations.current_starter_price.value
    valid_when: observations.current_starter_price.value > 0

beliefs:
  product_market_fit:
    statement: The current Starter product solves a durable enough problem for small teams that paid cohorts can retain without exceptional founder effort.
    output:
      confidence: {type: number, unit: probability, minimum: 0, maximum: 1}
      summary: {type: string, maximum_length: 600}
    form:
      every: 1 day
      uses:
        - new_paid_customers_28d
        - activation_rate_14d
        - pmf_pulse_reports
        - retention_90d
        - current_starter_price
      connection: analyst_model
      prompt: |
        Estimate the probability that the statement is true.
        Treat survey answers as interested-party reports, not measurements.
        Separate changes caused by price from evidence about product value.
        Use the supplied past forecast score as evidence about your own reliability.
        Return only {"confidence": number, "summary": string}.
    reality_check:
      forecast:
        key: observations.newest_weekly_cohort.value
        when: changed(observations.newest_weekly_cohort.value)
        event: outcome.retention_rate >= 0.25
        probability: belief.confidence
      outcome:
        observation: retention_90d
        match: outcome.cohort_week == forecast.key
        due_after: 90 days
      score:
        method: brier
        over: last 20 resolved forecasts
        acceptable: value <= 0.22

actions:
  set_daily_ad_budget:
    description: Set a new account-level paid-social daily budget.
    parameters:
      daily_usd: {type: number, unit: USD/day, minimum: 0, maximum: 1666}
    effects:
      - changes: current_daily_ad_budget
        expected: Becomes parameters.daily_usd after the platform accepts it.
        visible_after: 5 minutes
      - changes: paid_ad_spend_28d
        expected: Over time, moves toward 28 times the accepted daily budget, subject to auction delivery.
        visible_after: 1–28 days
      - changes: customer_acquisition_cost_28d
        expected: Usually decreases when budget is cut above the efficient frontier; the sign is not guaranteed.
        estimate: 5–20 percent over a full attribution window.
        visible_after: 7–28 days
    reversible:
      kind: "yes"
      by: Run this action again with the previous daily budget.
      within: any time
    approval: {required: false}
    run:
      connection: growth_ops
      request:
        method: POST
        path: /v1/ad-channels/paid-social/budget
        body: {daily_usd: "${parameters.daily_usd}"}
      idempotency_key: "${run.id}"
      success_when: response.status == 200

  change_starter_price:
    description: Change the monthly Starter price shown to new customers; existing contracts remain grandfathered.
    parameters:
      monthly_usd: {type: number, unit: USD/month, minimum: 49, maximum: 199}
    effects:
      - changes: current_starter_price
        expected: Becomes parameters.monthly_usd for new checkouts.
        visible_after: 10 minutes
      - changes: customer_acquisition_cost_28d
        expected: A lower price may improve paid conversion and lower acquisition cost.
        estimate: Unknown until at least one full buying cycle.
        visible_after: 14–28 days
      - changes: gross_margin_fraction
        expected: Falls when price falls.
        visible_after: 10 minutes
    reversible:
      kind: partly
      by: Restore the prior price for future checkouts.
      within: any time
      cannot_restore: The price and expectations shown to customers during the changed-price cohort.
    approval:
      required: true
      by: founder
      via: console
      show:
        - proposed parameters
        - beliefs.product_market_fit
        - metrics.customer_acquisition_cost_28d
        - metrics.gross_margin_fraction
        - all hard-rule results
        - reversibility
      expires_after: 24 hours
      if_no_answer: do_not_run
    run:
      connection: growth_ops
      request:
        method: POST
        path: /v1/prices/starter
        body:
          audience: new_customers
          monthly_usd: "${parameters.monthly_usd}"
      idempotency_key: "${run.id}"
      success_when: response.status == 200

  exit_paid_social:
    description: Permanently close paid social, terminate the agency contract, archive the ad account, and delete its accumulated audiences.
    parameters: {}
    effects:
      - changes: paid_social_status
        expected: Becomes exited.
        visible_after: 1 hour
      - changes: current_daily_ad_budget
        expected: Becomes 0 USD/day.
        visible_after: 1 hour
      - changes: paid_ad_spend_28d
        expected: Falls to 0 USD as the trailing window empties.
        visible_after: 28 days
      - changes: customer_acquisition_cost_28d
        expected: Stops being produced for paid social after the trailing window empties.
        visible_after: 28 days
    reversible:
      kind: "no"
      reason: The agency termination, account history, and deleted audiences cannot be restored by this system.
    approval:
      required: true
      by: founder
      via: console
      show:
        - proposed action
        - observations.paid_ad_spend_28d
        - observations.new_paid_customers_28d
        - metrics.customer_acquisition_cost_28d
        - beliefs.product_market_fit
        - all hard-rule results
        - reversibility
      expires_after: 24 hours
      if_no_answer: do_not_run
    run:
      connection: growth_ops
      request:
        method: POST
        path: /v1/ad-channels/paid-social/permanent-exit
        body:
          archive_account: true
          delete_audiences: true
          terminate_agency: true
      idempotency_key: "${run.id}"
      success_when: response.status == 202

hard_rules:
  fresh_evidence:
    description: Never act using stale spend, customer, price, budget, or unit-cost data.
    must: |
      observations.paid_ad_spend_28d.age <= duration("36h") &&
      observations.new_paid_customers_28d.age <= duration("36h") &&
      observations.current_starter_price.age <= duration("2h") &&
      observations.current_daily_ad_budget.age <= duration("2h") &&
      observations.unit_service_cost.age <= duration("14d")
    applies_before: every_action
    on_failure:
      stop: true
      tell: founder
      show: [failed rule, observation ages]

  monthly_spend_cap:
    description: A proposed daily ad budget must not imply more than 50,000 USD in 30 days.
    must: proposed.action != "set_daily_ad_budget" || proposed.parameters.daily_usd * 30 <= 50000
    applies_before: [set_daily_ad_budget]
    on_failure:
      stop: true
      tell: founder
      show: [failed rule, proposed action]

  minimum_new_customer_margin:
    description: Never offer a new-customer price below 60 percent gross margin.
    must: |
      proposed.action != "change_starter_price" ||
      (proposed.parameters.monthly_usd - observations.unit_service_cost.value)
        / proposed.parameters.monthly_usd >= 0.60
    applies_before: [change_starter_price]
    on_failure:
      stop: true
      tell: founder
      show: [failed rule, proposed action, observations.unit_service_cost]

  evidence_before_exit:
    description: Exiting paid social requires a meaningful sample and very poor trailing economics.
    must: |
      proposed.action != "exit_paid_social" ||
      (observations.new_paid_customers_28d.value >= 30 &&
       observations.paid_ad_spend_28d.value >= 20000 &&
       metrics.customer_acquisition_cost_28d.value > 650)
    applies_before: [exit_paid_social]
    on_failure:
      stop: true
      tell: founder
      show: [failed rule, observations.paid_ad_spend_28d, observations.new_paid_customers_28d]

messages: {}

loops:
  acquisition:
    description: Daily loop for paid-social acquisition economics.
    run_by: acquisition_agent
    runs: {every: 1 day, at: "09:00"}
    read:
      - paid_ad_spend_28d
      - new_paid_customers_28d
      - activation_rate_14d
      - pmf_pulse_reports
      - newest_weekly_cohort
      - retention_90d
      - current_starter_price
      - current_daily_ad_budget
      - paid_social_status
      - unit_service_cost
    update_beliefs: [product_market_fit]
    goal:
      metric: customer_acquisition_cost_28d
      target: {at_most: 400}
    may_choose: [set_daily_ad_budget, change_starter_price, exit_paid_social]

    hand_off_when:
      - when: |
          metrics.customer_acquisition_cost_28d.valid &&
          metrics.customer_acquisition_cost_28d.value > 400 &&
          beliefs.product_market_fit.confidence < 0.45
        to: founder
        ask: Decide whether the problem is acquisition, product, or segment before more money or a price change.
        show:
          - metrics.customer_acquisition_cost_28d
          - beliefs.product_market_fit
          - observations.activation_rate_14d
          - observations.pmf_pulse_reports
        resume_when: founder records a diagnosis and explicitly resumes the loop

      - when: |
          beliefs.product_market_fit.past_accuracy.count >= 10 &&
          beliefs.product_market_fit.past_accuracy.value > 0.22
        to: founder
        ask: Review the belief method because its recorded confidence no longer tracks cohort outcomes.
        show: [beliefs.product_market_fit, its last 20 resolved forecasts]
        resume_when: founder accepts a revised prompt or explicitly accepts the risk

      - when: |
          !metrics.customer_acquisition_cost_28d.valid &&
          observations.new_paid_customers_28d.value < 10
        to: founder
        ask: Choose whether to wait for a usable sample or use a different acquisition measure.
        show: [observations.paid_ad_spend_28d, observations.new_paid_customers_28d]
        resume_when: at least 10 attributed customers exist or founder changes the spec

    decide:
      method: ordered_rules
      rules:
        - when: |
            observations.paid_social_status.value == "active" &&
            metrics.customer_acquisition_cost_28d.valid &&
            metrics.customer_acquisition_cost_28d.value > 650 &&
            observations.paid_ad_spend_28d.value >= 20000 &&
            observations.new_paid_customers_28d.value >= 30
          choose: exit_paid_social
          with: {}
          reason: The channel has enough evidence to meet the permanent-exit threshold.

        - when: |
            metrics.customer_acquisition_cost_28d.valid &&
            metrics.customer_acquisition_cost_28d.value > 400 &&
            observations.current_daily_ad_budget.value > 500
          choose: set_daily_ad_budget
          with:
            daily_usd: max(500, observations.current_daily_ad_budget.value * 0.80)
          reason: First reduce the reversible source of marginal spend.

        - when: |
            metrics.customer_acquisition_cost_28d.valid &&
            metrics.customer_acquisition_cost_28d.value > 400 &&
            observations.current_daily_ad_budget.value <= 500 &&
            beliefs.product_market_fit.confidence >= 0.65
          choose: change_starter_price
          with:
            monthly_usd: max(79, observations.current_starter_price.value - 10)
          reason: Budget is already at its floor and product-market-fit evidence is strong enough to test conversion through price.

      otherwise:
        wait: 1 day
        reason: The target is met or no authorized action has adequate evidence.

known_gaps:
  attribution:
    not_modelled: Interactions between paid social, word of mouth, founder sales, and other marketing touches.
    risk: The loop may credit or blame paid social for customers it did not cause.
    revisit_when: A multi-touch experiment or randomized holdout is available.

  segment_mix:
    not_modelled: Different acquisition cost and retention behavior across industries, company sizes, and countries.
    risk: An apparently healthy average may hide a failing or unusually strong segment.
    revisit_when: Any segment reaches 50 paid customers in a 28-day window.

  long_term_price_effects:
    not_modelled: Brand, referral, support-load, and expansion-revenue effects beyond 90 days.
    risk: A price decrease can look helpful inside the loop while reducing long-run company value.
    revisit_when: Two price cohorts have 180 days of history.
```

The important visual facts are visible without following the SQL: the loop is trying to keep `customer_acquisition_cost_28d` at most 400; PMF is a probability, not a directly observed field; its confidence is scored against later retention cohorts; spend and configuration observations are visibly caused by the loop; survey answers are visibly reports from people with a stake; pricing and permanent exit cannot execute without the founder.

## Short multi-agent example

This second file shows two agents sharing both metrics and the same action. Named actions are serialized by the runtime: if two loops choose `set_promo_discount` concurrently, the later request waits, refreshes its observations and metrics, and decides again. Messages create explicit loop-to-loop edges; sharing state alone does not imply communication.

```yaml
loop_spec: "1.0"
name: growth-and-stock
summary: Let growth pursue trials without letting its promotion empty inventory.

runtime:
  timezone: UTC
  state: {kind: sqlite, path: ./state/growth-and-stock.db, keep_history_for: 90 days}
  on_error: {attempts: 3, backoff: 5 seconds, then: stop_without_action}

connections:
  shop:
    kind: http
    base_url_from_env: SHOP_API_URL
    auth: {kind: bearer, token_from_env: SHOP_API_TOKEN}

participants:
  growth_agent:
    kind: agent
    role: Pursues new trials.
    loses_if_wrong: [Permission to change promotions.]
    receives:
      - {what: [metrics.daily_trials, metrics.inventory_cover, messages.stock_warning], when: each run, via: shared_state}
  stock_agent:
    kind: agent
    role: Protects inventory availability.
    loses_if_wrong: [Its service-level score.]
    receives:
      - {what: [metrics.inventory_cover, metrics.daily_trials, messages.promo_intent], when: each run, via: shared_state}
  operator:
    kind: human
    role: Resolves cases in which growth and availability cannot both be protected.
    loses_if_wrong: [Sales from stockouts or excessive inventory.]
    receives:
      - {what: [hand_off_packet, run_error], when: only when created, via: console}

observations:
  trials_last_day:
    description: Completed trials in the last 24 hours.
    value: {type: integer, unit: trials, minimum: 0}
    arrives: {every: 15 minutes, lag: 5 minutes, max_age: 30 minutes}
    cost: {money: 0 USD, staff_time: 0 minutes, per: arrival}
    origin: {kind: outside, source: Visitor behavior.}
    obtained_as: {kind: measured, by: checkout events, method: Count completed trial checkouts.}
    informs: []
    read:
      connection: shop
      request: {method: GET, path: "/v1/metrics/trials?window=24h"}
      take: response.body.value

  inventory_days:
    description: Sellable inventory divided by units sold per day.
    value: {type: number, unit: days, minimum: 0}
    arrives: {every: 15 minutes, lag: 5 minutes, max_age: 30 minutes}
    cost: {money: 0 USD, staff_time: 0 minutes, per: arrival}
    origin: {kind: outside, source: Warehouse counts and customer orders.}
    obtained_as: {kind: calculated, by: shop API, based_on: [sellable units, trailing sales]}
    informs: []
    read:
      connection: shop
      request: {method: GET, path: /v1/metrics/inventory-days}
      take: response.body.value

  current_discount:
    description: Promotion discount currently shown in the shop.
    value: {type: number, unit: percent, minimum: 0, maximum: 25}
    arrives: {every: 15 minutes, lag: 1 minute, max_age: 30 minutes}
    cost: {money: 0 USD, staff_time: 0 minutes, per: arrival}
    origin: {kind: loop-produced, produced_by: [set_promo_discount]}
    obtained_as: {kind: measured, by: live shop configuration, method: Read the active promotion.}
    informs: []
    read:
      connection: shop
      request: {method: GET, path: /v1/promotion}
      take: response.body.discount_percent

metrics:
  daily_trials:
    description: Completed trials in the last day.
    unit: trials/day
    calculate: observations.trials_last_day.value
    valid_when: observations.trials_last_day.age <= duration("30m")
  inventory_cover:
    description: Days of inventory at the recent sales rate.
    unit: days
    calculate: observations.inventory_days.value
    valid_when: observations.inventory_days.age <= duration("30m")

beliefs: {}

actions:
  set_promo_discount:
    description: Set the shop-wide promotion; both loops are allowed to choose it.
    parameters:
      percent: {type: number, unit: percent, minimum: 0, maximum: 25}
    effects:
      - {changes: daily_trials, expected: Usually rises as the discount rises., visible_after: 1 day}
      - {changes: inventory_cover, expected: Usually falls as the discount rises., visible_after: 1–7 days}
      - {changes: current_discount, expected: Becomes parameters.percent., visible_after: 1 minute}
    reversible: {kind: "yes", by: Restore the prior percentage., within: any time}
    approval: {required: false}
    run:
      connection: shop
      request:
        method: PUT
        path: /v1/promotion
        body: {discount_percent: "${parameters.percent}"}
      idempotency_key: "${run.id}"
      success_when: response.status == 200

hard_rules:
  never_promote_near_stockout:
    description: No loop may raise the discount below 12 days of inventory.
    must: |
      proposed.action != "set_promo_discount" ||
      proposed.parameters.percent <= observations.current_discount.value ||
      metrics.inventory_cover.value >= 12
    applies_before: [set_promo_discount]
    on_failure: {stop: true, tell: operator, show: [failed rule, proposed action, metrics.inventory_cover]}

messages:
  promo_intent:
    description: Growth tells stock what it chose, or that it chose to wait.
    from: growth
    to: [stock]
    when: after_each_run
    include: [metrics.daily_trials, metrics.inventory_cover, proposed action]
    delivery: {via: shared_state}
    triggers_run: false
  stock_warning:
    description: Stock makes current inventory pressure explicit to growth.
    from: stock
    to: [growth]
    when: metrics.inventory_cover.value < 16
    include: [metrics.inventory_cover, observations.current_discount]
    delivery: {via: shared_state}
    triggers_run: true

loops:
  growth:
    description: Raise trials when inventory can support it.
    run_by: growth_agent
    runs: {every: 1 hour}
    read: [trials_last_day, inventory_days, current_discount]
    update_beliefs: []
    goal: {metric: daily_trials, target: {at_least: 100}}
    may_choose: [set_promo_discount]
    hand_off_when:
      - {when: "metrics.daily_trials.value < 100 && metrics.inventory_cover.value < 12", to: operator, ask: Choose between growth and availability., show: [metrics.daily_trials, metrics.inventory_cover], resume_when: operator explicitly resumes}
    decide:
      method: ordered_rules
      rules:
        - when: metrics.daily_trials.value < 100 && metrics.inventory_cover.value >= 16
          choose: set_promo_discount
          with: {percent: "min(25, observations.current_discount.value + 5)"}
          reason: There is room to trade inventory for trials.
      otherwise: {wait: 1 hour, reason: Target is met or inventory is too tight.}

  stock:
    description: Preserve at least 14 days of inventory.
    run_by: stock_agent
    runs: {every: 1 hour}
    read: [inventory_days, trials_last_day, current_discount]
    update_beliefs: []
    goal: {metric: inventory_cover, target: {at_least: 14}}
    may_choose: [set_promo_discount]
    hand_off_when:
      - {when: "metrics.inventory_cover.value < 7", to: operator, ask: Decide whether to stop sales or expedite supply., show: [metrics.inventory_cover], resume_when: operator explicitly resumes}
    decide:
      method: ordered_rules
      rules:
        - when: metrics.inventory_cover.value < 14 && observations.current_discount.value > 0
          choose: set_promo_discount
          with: {percent: 0}
          reason: Remove promotional demand while inventory is below target.
      otherwise: {wait: 1 hour, reason: Inventory target is met.}

known_gaps:
  inbound_supply:
    not_modelled: Supplier delivery uncertainty.
    risk: Inventory cover may improve or collapse for reasons neither agent anticipated.
    revisit_when: Supplier event data is available.
```

## Normative behavior

A generated runtime performs one loop run in this fixed order:

1. Acquire the named `read` observations that are due, validate their value shapes, and append immutable arrival records.
2. Evaluate each metric's `valid_when`; calculate its value only when valid, then expose both the value and `valid` flag.
3. Form named beliefs, record any due forecasts, resolve arrived outcomes, and update past-accuracy scores.
4. Evaluate `hand_off_when` from top to bottom. On a match, create a hand-off packet, stop this loop without acting, and wait for `resume_when`.
5. Evaluate `decide.rules` from top to bottom; the first match wins. `otherwise` is mandatory.
6. Validate action parameters and evaluate every applicable `hard_rule`. A failed rule always prevents execution, even when it conflicts with the goal.
7. Obtain required approval. No answer, expiry, or a mismatched approver means no action.
8. Re-read observations used by applicable hard rules, re-calculate them, re-check every hard rule, execute once with the idempotency key, and record the result.
9. Deliver due messages. A triggered run is coalesced with any already-pending run.

Observations, forecasts, approvals, hand-offs, decisions, hard-rule results, action attempts, and messages are append-only history. Current values are derived views. Implementations must not treat an action's declared `effects` as observed fact.

Named actions have a runtime-wide lock. A second loop requesting the same action waits for the first to finish, refreshes its inputs, and decides again. This deliberately simple rule prevents stale simultaneous writes; it does not pretend to settle disagreements between agents.

CEL expressions see these roots:

- `observations.<id>.value`, `.observed_at`, and `.age`
- `metrics.<id>.value` and `.valid`
- `beliefs.<id>.confidence`, other declared output fields, and `.past_accuracy.value`/`.count`
- `parameters` while validating or running an action
- `proposed.action`, `.parameters`, and `.approval` in hard rules
- `belief`, `forecast`, and `outcome` in a reality check
- `response.status`, `.headers`, and `.body` after an HTTP call
- `row` and `rows` after a SQL query
- `run.id` for one stable run identifier

In addition to standard CEL, Loopfile defines `changed(value)`, `duration(string)`, `min`, and `max`. `changed` is true when the current immutable arrival differs from the latest prior arrival. `${expression}` interpolates a CEL result into a request. Unit strings document and lint values; expressions use the declared unit's numeric value and may only combine dimensionally compatible numbers.

SQL reads expose the first row as `row` and all rows as `rows`. HTTP reads expose `response`. An empty SQL result, an invalid `take`, a non-successful action, or an unavailable required observation follows `runtime.on_error` and always fails closed.

## Complete key list

`*` means required. `?` means optional. A map written as `<id>` may contain any stable lower-snake-case identifier. IDs must be unique within their section. Unknown keys are errors, except keys beginning `x-`, which implementations preserve and ignore.

### Document and runtime

| Path | Meaning |
|---|---|
| `loop_spec*` | Exact version string, currently `"1.0"`. |
| `name*` | File name for people and generated programs. |
| `summary*` | One-sentence purpose. |
| `runtime*` | Runtime settings. |
| `runtime.timezone*` | IANA timezone. |
| `runtime.state*` | Durable local state settings. |
| `runtime.state.kind*` | `sqlite` in 1.0. |
| `runtime.state.path*` | SQLite path. |
| `runtime.state.keep_history_for*` | Duration; must cover every belief outcome delay. |
| `runtime.on_error*` | Safe failure policy. |
| `runtime.on_error.attempts*` | Positive integer including the first attempt. |
| `runtime.on_error.backoff*` | Duration between attempts. |
| `runtime.on_error.then*` | Only `stop_without_action` in 1.0. |
| `connections?` | Map of integration definitions. |
| `participants*` | Map of people, agents, groups, or organizations. |
| `observations*` | Map of arriving data. |
| `metrics*` | Map of calculated quantities. |
| `beliefs*` | Map; may be `{}`. |
| `actions*` | Map of executable choices. |
| `hard_rules*` | Map; may be `{}`, which produces a linter warning. |
| `messages*` | Map; use `{}` for a one-loop file. |
| `loops*` | Map of one or more loops. |
| `known_gaps*` | Map of deliberate omissions. |

### Connections

Every `connections.<id>` has exactly one `kind`:

| Path | Meaning |
|---|---|
| `.kind*` | `sql`, `http`, or `llm`. |
| SQL `.driver*` | `postgres`, `mysql`, or `sqlite`. |
| SQL `.dsn_from_env*` | Environment variable containing the DSN. |
| HTTP `.base_url?` / `.base_url_from_env?` | Exactly one literal or environment-provided base URL. |
| HTTP `.auth*` | Authentication map. |
| HTTP `.auth.kind*` | `none`, `bearer`, or `header`. |
| HTTP `.auth.token_from_env?` | Required for `bearer` and `header`. |
| HTTP `.auth.name?` | Header name; required for `header`. |
| HTTP `.default_headers?` | String-to-string map. |
| LLM `.base_url?` / `.base_url_from_env?` | Exactly one OpenAI-compatible base URL. |
| LLM `.api_key_from_env*` | API-key environment variable. |
| LLM `.model?` / `.model_from_env?` | Exactly one model name source. |
| LLM `.temperature?` | Number from 0 through 2; default 0. |

`console` and `shared_state` are built-in delivery labels, not connections. In `participants.receives`, another plain label may describe an external surface such as a live pricing page; naming an HTTP connection instead makes delivery executable and requires a `request`.

### Participants

| Path | Meaning |
|---|---|
| `participants.<id>.kind*` | `human`, `agent`, `group`, or `organization`. |
| `.role*` | Plain description of responsibility. |
| `.loses_if_wrong*` | Non-empty list of concrete harms or lost authority. |
| `.receives*` | List of delivery records; may be `[]` only if isolation is intentional and explained by `x-isolation-reason`. |
| `.receives[].what*` | List of typed references or built-ins: `approval_packet`, `hand_off_packet`, `run_error`, `action_result`. |
| `.receives[].when*` | Schedule or plain event condition. |
| `.receives[].via*` | Plain delivery channel or connection ID. |
| `.receives[].request?` | HTTP request when `via` names an HTTP connection. |

### Observations

| Path | Meaning |
|---|---|
| `observations.<id>.description*` | What one arrival means. |
| `.value*` | Value schema. |
| `.arrives*` | Arrival expectation. |
| `.arrives.every*` | Duration. |
| `.arrives.at?` | Local time or readable weekday plus time. |
| `.arrives.lag*` | Delay between the real-world event and availability. |
| `.arrives.max_age*` | Age after which the value is stale. |
| `.cost*` | Acquisition cost. |
| `.cost.money*` | Amount and ISO currency, including zero. |
| `.cost.staff_time*` | Duration, including zero. |
| `.cost.per*` | `arrival`, `row`, or `request`. |
| `.origin*` | Whether the data exists independently of this system. |
| `.origin.kind*` | `outside` or `loop-produced`. |
| `.origin.source?` | Required plain source for `outside`. |
| `.origin.produced_by?` | Required non-empty action-ID list for `loop-produced`. |
| `.obtained_as*` | Epistemic acquisition method. |
| `.obtained_as.kind*` | `measured`, `reported`, or `calculated`. |
| `.obtained_as.by*` | Participant ID or plain source. |
| `.obtained_as.method?` | Required for `measured`; description of the measurement. |
| `.obtained_as.reporter_stake?` | Required for `reported`; how the reporter may benefit or lose. |
| `.obtained_as.based_on?` | Required for `calculated`; non-empty list of underlying records. |
| `.informs*` | Belief-ID list, explicitly `[]` when it informs none. |
| `.read*` | SQL or HTTP acquisition call. |
| `.read.connection*` | Connection ID. |
| `.read.query?` | SQL text; required for a SQL connection. |
| `.read.request?` | HTTP request; required for an HTTP connection. |
| `.read.take*` | CEL selecting the value from `row`, `rows`, or `response`. |

The value-schema keys are `type*` (`number`, `integer`, `string`, `boolean`, `object`, or `array`), `unit?`, `format?` (`date` or `date-time`), `minimum?`, `maximum?`, `minimum_length?`, `maximum_length?`, `enum?`, `fields?` (required for objects), and `items?` (required for arrays). No other JSON-Schema vocabulary is part of 1.0.

An HTTP `request` has `method*`, `path*`, `query?`, `headers?`, and `body?`. Each of the latter three is a JSON-shaped value that may contain `${CEL expression}`.

### Metrics and goals

| Path | Meaning |
|---|---|
| `metrics.<id>.description*` | What the number means. |
| `.unit*` | Human-readable unit. |
| `.calculate*` | CEL over observations and other metrics. Cycles are forbidden. |
| `.valid_when*` | CEL stating sample-size and availability requirements. |
| `loops.<id>.goal*` | The one quantity this loop is steering. |
| `.goal.metric*` | Metric ID. |
| `.goal.target*` | Exactly one of `at_most`, `at_least`, `equals`, or `between: [low, high]`, in the metric's unit. |

### Beliefs and reality checks

| Path | Meaning |
|---|---|
| `beliefs.<id>.statement*` | The unobservable claim. |
| `.output*` | Map containing `confidence` plus optional named fields. |
| `.output.confidence*` | Number schema with unit `probability`, minimum 0, maximum 1. |
| `.form*` | How the belief is produced. |
| `.form.every*` | Update duration. |
| `.form.uses*` | Non-empty observation-ID list. |
| `.form.connection*` | LLM connection ID. |
| `.form.prompt*` | Full instructions; the runtime supplies named values, prior belief, and past-accuracy record as JSON. |
| `.reality_check*` | A check object or `{none: true, reason: string}`. Omitting it is an error; choosing `none` is a warning. |
| `.reality_check.forecast*` | Forecast recorded with a belief snapshot. |
| `.forecast.key*` | CEL producing the outcome-matching key. |
| `.forecast.when*` | CEL deciding when to create one forecast per key. |
| `.forecast.event*` | Boolean CEL evaluated later with `outcome`. |
| `.forecast.probability*` | CEL, normally `belief.confidence`. |
| `.reality_check.outcome*` | Later evidence. |
| `.outcome.observation*` | Observation ID. |
| `.outcome.match*` | CEL joining outcome to forecast. |
| `.outcome.due_after*` | Maximum expected resolution delay. |
| `.reality_check.score*` | Accuracy aggregation. |
| `.score.method*` | `brier` or `log_loss`. |
| `.score.over*` | `last N resolved forecasts` or a duration. |
| `.score.acceptable*` | CEL over local `value`. |

The runtime stores the event expression and probability when the forecast is made; it never re-evaluates the old probability using a newer belief.

### Actions and approvals

| Path | Meaning |
|---|---|
| `actions.<id>.description*` | Concrete act, including scope. |
| `.parameters*` | Map of value schemas; use `{}` for none. |
| `.effects*` | Non-empty list of expected effects. |
| `.effects[].changes*` | Observation or metric ID. |
| `.effects[].expected*` | Plain, falsifiable direction or state change; uncertainty must be stated. |
| `.effects[].estimate?` | Expected magnitude or explicit `unknown`. |
| `.effects[].visible_after*` | Duration or range after which the effect could be observed. |
| `.reversible*` | Undo description. |
| `.reversible.kind*` | `"yes"`, `partly`, or `"no"` (quotes avoid YAML 1.1 boolean coercion). |
| `.reversible.by?` | Required for `yes`/`partly`. |
| `.reversible.within?` | Required for `yes`/`partly`; duration or `any time`. |
| `.reversible.cannot_restore?` | Required for `partly`. |
| `.reversible.reason?` | Required for `no`. |
| `.approval*` | Human gate. |
| `.approval.required*` | Boolean. |
| `.approval.by?` | Required human participant ID when true. |
| `.approval.via?` | Required delivery label or connection when true. |
| `.approval.show?` | Required non-empty evidence list when true. |
| `.approval.expires_after?` | Required duration when true. |
| `.approval.if_no_answer?` | Must be `do_not_run` in 1.0. |
| `.run*` | Integration call. |
| `.run.connection*` | SQL or HTTP connection ID. |
| `.run.query?` / `.run.request?` | One call matching the connection kind. |
| `.run.idempotency_key*` | Template; normally `${run.id}`. |
| `.run.success_when*` | CEL over `response` for HTTP or `row`/`rows` for SQL. |

An action with `reversible.kind: no` and no human approval is a lint error. `partly` without approval is a warning. Approval packets always include the action ID, parameters, decision reason, approver identity, creation and expiry times, declared effects, reversibility, the requested `show` values, and all hard-rule results; `show` cannot hide those built-ins.

### Hard rules

| Path | Meaning |
|---|---|
| `hard_rules.<id>.description*` | Human statement of the invariant. |
| `.must*` | Boolean CEL; true permits the proposed action. |
| `.applies_before*` | `every_action` or a non-empty action-ID list. |
| `.on_failure*` | Failure response. |
| `.on_failure.stop*` | Must be true in 1.0. |
| `.on_failure.tell*` | Human participant ID. |
| `.on_failure.show*` | Non-empty evidence list. |

Hard rules cannot call an LLM or use prose as their `must` value. This is what makes “regardless of the objective” executable rather than aspirational.

### Messages

| Path | Meaning |
|---|---|
| `messages.<id>.description*` | Meaning of the message. |
| `.from*` | Sender loop ID. |
| `.to*` | Non-empty recipient loop-ID list. |
| `.when*` | Named lifecycle event or CEL. |
| `.include*` | Non-empty list of references or `proposed action`. |
| `.delivery*` | Delivery settings. |
| `.delivery.via*` | `shared_state` or connection ID. |
| `.delivery.request?` | Required HTTP request for an HTTP connection. |
| `.triggers_run*` | Boolean. |

### Loops and decisions

| Path | Meaning |
|---|---|
| `loops.<id>.description*` | One-sentence responsibility. |
| `.run_by*` | Participant ID whose kind is `agent`. |
| `.runs*` | Schedule. |
| `.runs.every*` | Duration. |
| `.runs.at?` | Optional local time. |
| `.read*` | Non-empty observation-ID list refreshed when due. |
| `.update_beliefs*` | Belief-ID list; may be `[]`. |
| `.goal*` | Goal described above. |
| `.may_choose*` | Action-ID list; may be `[]` for an observe-only loop. |
| `.hand_off_when*` | Non-empty ordered list. |
| `.hand_off_when[].when*` | Boolean CEL. |
| `.hand_off_when[].to*` | Human participant ID. |
| `.hand_off_when[].ask*` | Concrete question or decision request. |
| `.hand_off_when[].show*` | Non-empty evidence list. |
| `.hand_off_when[].resume_when*` | Observable resumption condition. |
| `.decide*` | Action-selection rule. |
| `.decide.method*` | `ordered_rules` in 1.0. |
| `.decide.rules*` | Ordered list; may be empty. |
| `.decide.rules[].when*` | Boolean CEL. |
| `.decide.rules[].choose*` | An action listed in `may_choose`. |
| `.decide.rules[].with*` | Parameter map of literals or CEL strings. |
| `.decide.rules[].reason*` | Human rationale. |
| `.decide.otherwise*` | Required fallback, either an ordinary rule body or `{wait, reason}`. |
| `.decide.otherwise.wait?` | Duration. |
| `.decide.otherwise.reason*` | Rationale. |

The hand-off list is evaluated before the decision list. A hand-off pauses only that loop; other loops continue unless their own rules or messages say otherwise.

### Known gaps

| Path | Meaning |
|---|---|
| `known_gaps.<id>.not_modelled*` | Deliberately omitted phenomenon. |
| `.risk*` | How the omission could make the loop wrong. |
| `.revisit_when*` | Observable reason to reconsider it. |

## What a linter can find

At minimum, a conforming linter reports:

- An error when a goal metric is not transitively calculable from arriving observations, or its calculation has a cycle.
- An error when a loop-produced observation lacks `produced_by`, or names an action whose effects do not include it.
- An error when a reported observation lacks both a participant reporter and `reporter_stake`.
- An error when a belief uses no arriving evidence, lacks a reality-check choice, or has an outcome delay longer than retained history. `reality_check: none` is an explicit warning, not silent success.
- An error when an observation says it `informs` a belief but that belief does not list it in `form.uses`, or vice versa.
- An error when an action has no effect, no time-to-visible-effect, invalid parameters, or an effect on a quantity that can never be observed or calculated.
- An error for an irreversible ungated action, a non-human approver, an approval with insufficient evidence, or an execution without an idempotency key.
- An error when a loop can choose an undeclared action, has no hand-off condition, lacks an `otherwise`, or refers to stale/invalid data without testing validity or being protected by a hard rule.
- An error for an unenforceable hard rule, missing referenced participant, invalid message endpoint, or unresolvable reference.
- A warning when a participant receives no information, a known-gaps map is empty, an action claims a direction but no later observation can test it, two loops share an action but do not read all quantities used by its hard rules, or an accuracy score is calculated but never reaches a decision or hand-off.

These checks operate on the same reference graph used for a diagram. Nodes are the top-level named objects. Edges come from fields such as `calculate`, `uses`, `informs`, `produced_by`, `effects.changes`, `goal.metric`, `may_choose`, approvals, participant deliveries, and messages. There is deliberately no `diagram`, `position`, `lane`, `color`, or other layout key.

## The three hardest design decisions

### 1. Make action choice ordered and executable

**Chosen:** `decide` contains ordered CEL rules, a named action, typed parameters, and a mandatory fallback.

**Rejected:** A free-form “policy” prompt that lets an LLM choose any allowed action.

**Why:** A prompt is attractive for LLM-written files but hides reachability, priority, and edge cases from both a thirty-second reader and a linter. It also makes LangGraph and Goose implementations behave differently. LLM judgment still has a legitimate place in forming an uncertain belief; the authority to act remains inspectable. A future version could add an LLM choice method, but only with a mechanically enforced rule envelope.

### 2. Check beliefs through dated forecasts, not a field called “ground truth”

**Chosen:** An unobservable belief emits a probability for a later observable event, keeps the original snapshot, and scores resolved forecasts with Brier score or log loss.

**Rejected:** `validated_by: retention_90d` or a generic confidence number updated whenever new evidence arrives.

**Why:** Product-market fit never turns into a directly visible truth value. A proxy can test whether confidence was useful, but it cannot magically measure PMF. A dated forecast makes the proxy, delay, matching rule, and scoring method explicit, and it detects confident systems that are consistently wrong. The rejected form looks simpler while allowing “confidence” to mean nothing testable.

### 3. Split “where it came from” from “how we know it”

**Chosen:** Every observation independently declares `origin.kind` and `obtained_as.kind`.

**Rejected:** One enum such as `source: measured | reported | internal | external`.

**Why:** Those labels are not mutually exclusive. Ad-platform spend is measured, yet the loop caused it by setting a budget. A customer survey comes from outside, yet it is a report by someone with interests. A single enum forces one fact to erase the other—the exact mistake that makes self-created evidence and interested reports look objective.

## Where this design is weakest

The weakest point is action effects. `effects` makes claims falsifiable and forces a visible delay, but it does not establish that an action caused the later change. Confounding, concurrent actions, seasonality, auction dynamics, and strategic reactions remain possible. A linter can prove that an effect is measurable; it cannot prove the declared direction or magnitude. A later version should add optional experiment assignment and causal comparison without making the common file harder to scan.

There are three other practical limits:

- CEL, SQL, and HTTP are portable enough for code generation, but external schemas, pagination, OAuth refresh, and provider-specific behavior can still make a generated program need adapter work.
- The participant loss fields expose stakes but do not mathematically reconcile them. Multi-agent action locking prevents races; it does not solve political or strategic disagreement.
- One goal per loop is intentionally restrictive. It keeps the steering quantity obvious, but users with genuine competing objectives must express the others as hard rules, separate loops, or a precomputed metric. That is clearer, but sometimes less faithful than a multi-objective decision.
