# LoopSpec 1

LoopSpec is a YAML format for describing an agent loop as an inspectable contract. The
first screen says what the loop wants, what it sees, what it can do, and when it gives up.
The remaining sections define those names precisely enough to lint, draw, and implement.

The format has one deliberate rule: important facts are never implied by prose. Every
arrival says whether it was measured, reported, or generated; every action says when its
effects can be seen, whether it can be undone, and who approves it.

## 1. Complete example: paid-social customer acquisition

```yaml
loop_spec: 1
name: Paid-social customer acquisition
summary: Keep the rolling paid-social cost per new customer below $400 without buying growth that retention does not support.

runtime:
  timezone: America/Los_Angeles
  state:
    kind: sqlite
    location: ./state/acquisition.db
  approvals:
    public_url: "${env.PUBLIC_URL}/approvals"
  on_error:
    do: stop_and_ask
    who: founder

loops:
  acquisition:
    agent: growth_agent
    run:
      every: 1d
      max_actions: 1

    aims:
      - quantity: paid_cac_30d
        target:
          at_most: 400
        over: 30d

    sees:
      arrivals:
        - ad_cost
        - new_paid_customers
        - trial_to_paid_rate
        - cohort_retention_90d
        - sales_fit_rating
        - landing_page_fit_score
        - current_daily_ad_budget
        - current_intro_price
        - current_gross_margin
        - channel_status
      quantities:
        - paid_cac_30d
        - paid_cac_42d
        - new_customers_30d
        - daily_ad_spend
        - daily_ad_budget
        - intro_annual_price
        - gross_margin
        - channel_active
      beliefs:
        - product_market_fit
      handoffs: []

    can_do:
      - set_daily_ad_spend
      - set_intro_annual_price
      - exit_paid_social

    # Checked before the rules below. No action is proposed when one is true.
    stop_and_ask:
      who: founder
      question: The acquisition evidence is too weak or contradictory. What should the loop do?
      when_any:
        - "quantity.new_customers_30d < 30"
        - "belief.product_market_fit.check.mean_last_8 > 0.24"
        - "quantity.paid_cac_30d > 400 and belief.product_market_fit.value >= 0.40 and belief.product_market_fit.value <= 0.60"
      send:
        - quantity.paid_cac_30d
        - quantity.new_customers_30d
        - belief.product_market_fit
        - belief.product_market_fit.check
        - decision.recent_actions

    decide:
      mode: first_match
      rules:
        - name: leave_a_failed_channel
          when: "quantity.channel_active and quantity.paid_cac_42d > 600 and belief.product_market_fit.value < 0.35"
          do: exit_paid_social
          because: Six weeks of very high acquisition cost plus weak product-market-fit evidence makes further learning too expensive.

        - name: test_a_lower_entry_price
          when: "quantity.paid_cac_30d > 400 and belief.product_market_fit.value < 0.40 and quantity.intro_annual_price > 600"
          do: set_intro_annual_price
          with:
            annual_price_usd: "${max(600, round(quantity.intro_annual_price * 0.90))}"
          because: A lower entry price may distinguish price resistance from lack of demand.

        - name: cut_expensive_marginal_spend
          when: "quantity.paid_cac_30d > 400 and belief.product_market_fit.value > 0.60"
          do: set_daily_ad_spend
          with:
            daily_budget_usd: "${max(500, round(quantity.daily_ad_budget * 0.85))}"
          because: Demand looks real, but the current marginal ad inventory is too expensive.

        - name: scale_a_working_channel
          when: "quantity.paid_cac_30d < 320 and belief.product_market_fit.value > 0.70 and quantity.gross_margin >= 0.75"
          do: set_daily_ad_spend
          with:
            daily_budget_usd: "${min(5000, round(quantity.daily_ad_budget * 1.10))}"
          because: Cost, product-market-fit evidence, and margin all leave room to scale.

      otherwise: wait

quantities:
  paid_cac_30d:
    description: Ad cost divided by new paying customers over the last 30 days.
    type: number
    unit: USD/customer
    calculate: "sum(arrival.ad_cost, 30d) / max(sum(arrival.new_paid_customers, 30d), 1)"

  paid_cac_42d:
    description: The same acquisition cost over the longer window used for a channel-exit decision.
    type: number
    unit: USD/customer
    calculate: "sum(arrival.ad_cost, 42d) / max(sum(arrival.new_paid_customers, 42d), 1)"

  new_customers_30d:
    description: New paying customers attributed to paid social in the last 30 days.
    type: number
    unit: customer
    calculate: "sum(arrival.new_paid_customers, 30d)"

  daily_ad_spend:
    description: Paid-social spend over the last 24 hours.
    type: number
    unit: USD/day
    calculate: "sum(arrival.ad_cost, 1d)"

  daily_ad_budget:
    description: Configured maximum paid-social spend per day.
    type: number
    unit: USD/day
    calculate: "arrival.current_daily_ad_budget.latest"

  intro_annual_price:
    description: Current first-year list price offered to new US customers.
    type: number
    unit: USD/year
    calculate: "arrival.current_intro_price.latest"

  gross_margin:
    description: Current company gross margin as a fraction.
    type: number
    unit: ratio
    calculate: "arrival.current_gross_margin.latest"

  channel_active:
    description: Whether paid-social campaigns are permitted to run.
    type: boolean
    calculate: "arrival.channel_status.latest"

beliefs:
  product_market_fit:
    description: Probability that the product solves a recurring, important problem for the current target segment.
    value:
      type: probability
    starts_at: 0.50

    # The runner supplies the agent with the history of every arrival whose
    # `informs` list contains `product_market_fit`.
    formed:
      every: 7d
      agent: growth_agent
      prompt: |
        Estimate the probability that the current target segment has product-market fit.
        Return JSON with `probability` and `reason`. Treat retention and trial conversion
        as stronger evidence than opinions. The sales rating is reported by a quota-bearing
        person. The landing-page score is generated by this system and is not independent
        evidence. Do not infer missing data.
      returns:
        value: "$.probability"
        reason: "$.reason"

    # Each weekly belief is a forecast for that week's cohort. Ninety days later,
    # the matching retention record settles it and contributes a Brier score.
    check:
      against: cohort_retention_90d
      after: 90d
      match:
        forecast: "start_of_week(now)"
        actual: "arrival.value.cohort_started_at"
      correct_when: "arrival.value.retention >= 0.35"
      score: brier
      alert:
        mean_over: 8
        above: 0.24
        who: founder

arrivals:
  ad_cost:
    description: Booked paid-social media cost for the preceding day.
    value:
      type: number
      unit: USD
      min: 0
    kind: measured
    source:
      origin: outside
      name: Meta Ads via the warehouse
    every: 1d
    available_after: 6h
    cost:
      money: "0 USD"
      human_time: 0m
    read:
      sql:
        connection: "${env.WAREHOUSE_URL}"
        query: |
          SELECT COALESCE(SUM(cost_usd), 0) AS value
          FROM paid_social_daily
          WHERE spend_date = CURRENT_DATE - INTERVAL '1 day'
        take: "$.rows[0].value"
    informs: []

  new_paid_customers:
    description: New paying customers whose locked first-touch attribution is paid social.
    value:
      type: number
      unit: customer
      min: 0
    kind: measured
    source:
      origin: outside
      name: Stripe and the attribution warehouse
    every: 1d
    available_after: 6h
    cost:
      money: "0 USD"
      human_time: 0m
    read:
      sql:
        connection: "${env.WAREHOUSE_URL}"
        query: |
          SELECT COUNT(*) AS value
          FROM customer_acquisitions
          WHERE acquired_on = CURRENT_DATE - INTERVAL '1 day'
            AND first_touch_channel = 'paid_social'
            AND became_paying = TRUE
        take: "$.rows[0].value"
    informs:
      - product_market_fit

  trial_to_paid_rate:
    description: Fraction of paid-social trials from the prior week that became paying customers.
    value:
      type: number
      unit: ratio
      min: 0
      max: 1
    kind: measured
    source:
      origin: outside
      name: Stripe and the product warehouse
    every: 7d
    available_after: 1d
    cost:
      money: "0 USD"
      human_time: 0m
    read:
      sql:
        connection: "${env.WAREHOUSE_URL}"
        query: |
          SELECT converted_trials::float / NULLIF(all_trials, 0) AS value
          FROM weekly_paid_social_conversion
          ORDER BY week_started DESC
          LIMIT 1
        take: "$.rows[0].value"
    informs:
      - product_market_fit

  cohort_retention_90d:
    description: Ninety-day retention for a weekly paid-social customer cohort.
    value:
      type: object
      fields:
        cohort_started_at:
          type: date
        retention:
          type: number
          unit: ratio
          min: 0
          max: 1
    kind: measured
    source:
      origin: outside
      name: Product event warehouse
    every: 7d
    available_after: 90d
    cost:
      money: "0 USD"
      human_time: 0m
    read:
      sql:
        connection: "${env.WAREHOUSE_URL}"
        query: |
          SELECT cohort_started_at, retained_90d::float / NULLIF(cohort_size, 0) AS retention
          FROM paid_social_retention
          WHERE cohort_started_at <= CURRENT_DATE - INTERVAL '90 days'
          ORDER BY cohort_started_at DESC
          LIMIT 1
        take: "$.rows[0]"
    informs:
      - product_market_fit

  sales_fit_rating:
    description: Sales lead's weekly 0–10 rating of how strongly prospects say the product solves an urgent problem.
    value:
      type: number
      unit: score
      min: 0
      max: 10
    kind: reported
    source:
      origin: outside
      participant: sales_lead
    every: 7d
    available_after: 1d
    cost:
      money: "0 USD"
      human_time: 20m
    read:
      sql:
        connection: "${env.CRM_DATABASE_URL}"
        query: |
          SELECT fit_rating AS value
          FROM weekly_sales_assessment
          ORDER BY submitted_at DESC
          LIMIT 1
        take: "$.rows[0].value"
    informs:
      - product_market_fit

  landing_page_fit_score:
    description: This system's own weekly model score for how well the landing page matches recent customer language.
    value:
      type: number
      unit: score
      min: 0
      max: 1
    kind: generated
    source:
      origin: this_system
      participant: growth_agent
    every: 7d
    available_after: 5m
    cost:
      money: "0.05 USD"
      human_time: 0m
    read:
      http:
        method: GET
        url: "${env.GROWTH_OPS_URL}/agent-scores/landing-page-fit"
        headers:
          Authorization: "Bearer ${env.GROWTH_OPS_TOKEN}"
        take: "$.score"
    informs:
      - product_market_fit

  current_daily_ad_budget:
    description: Configured paid-social daily budget.
    value:
      type: number
      unit: USD/day
      min: 0
    kind: measured
    source:
      origin: this_system
      action: set_daily_ad_spend
    every: 1d
    available_after: 5m
    cost:
      money: "0 USD"
      human_time: 0m
    read:
      http:
        method: GET
        url: "${env.GROWTH_OPS_URL}/budgets/paid-social"
        headers:
          Authorization: "Bearer ${env.GROWTH_OPS_TOKEN}"
        take: "$.daily_budget_usd"
    informs: []

  current_intro_price:
    description: Active first-year annual price for new US customers.
    value:
      type: number
      unit: USD/year
      min: 0
    kind: measured
    source:
      origin: this_system
      action: set_intro_annual_price
    every: 1d
    available_after: 5m
    cost:
      money: "0 USD"
      human_time: 0m
    read:
      http:
        method: GET
        url: "${env.GROWTH_OPS_URL}/pricing/us-intro"
        headers:
          Authorization: "Bearer ${env.GROWTH_OPS_TOKEN}"
        take: "$.annual_price_usd"
    informs: []

  current_gross_margin:
    description: Company gross margin for the latest closed week.
    value:
      type: number
      unit: ratio
      min: 0
      max: 1
    kind: measured
    source:
      origin: outside
      name: Finance warehouse
    every: 7d
    available_after: 2d
    cost:
      money: "0 USD"
      human_time: 0m
    read:
      sql:
        connection: "${env.WAREHOUSE_URL}"
        query: |
          SELECT gross_margin AS value
          FROM weekly_company_metrics
          ORDER BY week_started DESC
          LIMIT 1
        take: "$.rows[0].value"
    informs: []

  channel_status:
    description: Whether paid social is enabled in growth operations.
    value:
      type: boolean
    kind: generated
    source:
      origin: this_system
      action: exit_paid_social
    every: 1d
    available_after: 5m
    cost:
      money: "0 USD"
      human_time: 0m
    read:
      http:
        method: GET
        url: "${env.GROWTH_OPS_URL}/channels/paid-social"
        headers:
          Authorization: "Bearer ${env.GROWTH_OPS_TOKEN}"
        take: "$.active"
    informs: []

actions:
  set_daily_ad_spend:
    description: Set tomorrow's total paid-social budget.
    scope: paid_social
    available_to:
      - acquisition
    inputs:
      daily_budget_usd:
        type: number
        unit: USD/day
        min: 500
        max: 5000
        required: true
    effects:
      - quantity: daily_ad_budget
        change: set_to
        to: "${input.daily_budget_usd}"
        shows_after: 15m
      - quantity: daily_ad_spend
        change: unknown
        shows_after: 1d
      - quantity: paid_cac_30d
        change: unknown
        shows_after: 7d
        note: Auction prices and conversion mix determine the direction.
    undo:
      possible: true
      by: set_daily_ad_spend
      with:
        daily_budget_usd: "${before.quantity.daily_ad_budget}"
      within: 1d
      leaves_behind: Spend already entered into auctions cannot be recovered.
    approval:
      required: false
    call:
      http:
        method: POST
        url: "${env.GROWTH_OPS_URL}/budgets/paid-social"
        headers:
          Authorization: "Bearer ${env.GROWTH_OPS_TOKEN}"
          Idempotency-Key: "${run.id}:${action.name}"
        body:
          daily_budget_usd: "${input.daily_budget_usd}"
        success_when: "response.status >= 200 and response.status < 300"

  set_intro_annual_price:
    description: Set the first-year annual price shown to new US customers; existing contracts are untouched.
    scope: new_customers_only
    available_to:
      - acquisition
    inputs:
      annual_price_usd:
        type: number
        unit: USD/year
        min: 600
        max: 1200
        required: true
    effects:
      - quantity: intro_annual_price
        change: set_to
        to: "${input.annual_price_usd}"
        shows_after: 15m
      - quantity: paid_cac_30d
        change: down
        shows_after: 14d
        note: Expected through improved checkout conversion; the direction is not guaranteed.
      - quantity: gross_margin
        change: down
        shows_after: 30d
    undo:
      possible: true
      by: set_intro_annual_price
      with:
        annual_price_usd: "${before.quantity.intro_annual_price}"
      within: 30d
      leaves_behind: Customers acquired during the test retain the price they accepted.
    approval:
      required: true
      by: founder
      expires_after: 2d
      send:
        - action.name
        - action.inputs
        - action.effects
        - quantity.paid_cac_30d
        - belief.product_market_fit
    call:
      http:
        method: POST
        url: "${env.GROWTH_OPS_URL}/pricing/us-intro"
        headers:
          Authorization: "Bearer ${env.GROWTH_OPS_TOKEN}"
          Idempotency-Key: "${run.id}:${action.name}"
        body:
          annual_price_usd: "${input.annual_price_usd}"
        success_when: "response.status >= 200 and response.status < 300"

  exit_paid_social:
    description: Permanently close the paid-social account and discard its learned audiences and campaign history.
    scope: paid_social
    available_to:
      - acquisition
    inputs: {}
    effects:
      - quantity: channel_active
        change: set_to
        to: false
        shows_after: 15m
      - quantity: daily_ad_budget
        change: set_to
        to: 0
        shows_after: 15m
      - quantity: daily_ad_spend
        change: down
        shows_after: 1d
      - quantity: paid_cac_30d
        change: unknown
        shows_after: 30d
    undo:
      possible: false
      reason: The vendor does not restore deleted optimization history or learned audiences.
    approval:
      required: true
      by: founder
      expires_after: 2d
      send:
        - action.name
        - action.effects
        - action.undo
        - quantity.paid_cac_42d
        - belief.product_market_fit
    call:
      http:
        method: DELETE
        url: "${env.GROWTH_OPS_URL}/channels/paid-social"
        headers:
          Authorization: "Bearer ${env.GROWTH_OPS_TOKEN}"
          Idempotency-Key: "${run.id}:${action.name}"
        success_when: "response.status == 204"
    after_success:
      stop_loops:
        - acquisition

participants:
  growth_agent:
    kind: agent
    description: Forms the product-market-fit belief and runs the acquisition rules.
    model:
      provider: openai
      name: "${env.GROWTH_MODEL}"
      credential: "${env.OPENAI_API_KEY}"
    loses_if_wrong:
      - Its future recommendations are down-weighted or disabled.
      - It spends its weekly experiment and model budget.
    receives:
      - what:
          - loop.acquisition.sees
        when: each_run
        via: loop_state

  founder:
    kind: human
    description: Owns cash runway, pricing, and channel-exit decisions.
    contact:
      webhook:
        url: "${env.FOUNDER_NOTIFICATION_WEBHOOK}"
    loses_if_wrong:
      - Cash runway, ownership value, and customer trust.
    receives:
      - what:
          - approval.request
          - stop_and_ask.request
          - constraint.failure
        when: immediately
        via: contact
      - what:
          - quantity.paid_cac_30d
          - quantity.new_customers_30d
          - belief.product_market_fit
          - belief.product_market_fit.check
          - decision.recent_actions
        when: 7d
        via: contact

  sales_lead:
    kind: human
    description: Supplies the reported fit rating and carries a new-revenue quota.
    contact:
      webhook:
        url: "${env.SALES_NOTIFICATION_WEBHOOK}"
    loses_if_wrong:
      - Quota attainment and commission if a good channel is cut.
      - Credibility if optimistic reports cause waste.
    receives:
      - what:
          - quantity.paid_cac_30d
          - belief.product_market_fit
          - decision.recent_actions
        when: 30d
        via: contact

must_always:
  - name: monthly_spend_cap
    require: "proposed.quantity.daily_ad_budget * 30 <= 150000"
    on_failure:
      do: block_and_ask
      who: founder

  - name: price_floor
    require: "proposed.action != 'set_intro_annual_price' or proposed.input.annual_price_usd >= 600"
    on_failure:
      do: block_and_ask
      who: founder

  - name: existing_contracts_do_not_change
    require: "proposed.action != 'set_intro_annual_price' or proposed.scope == 'new_customers_only'"
    on_failure:
      do: block

not_modelled:
  - what: Competitor launches and competitor price changes.
    why: There is no reliable, timely feed.
    risk: The loop may attribute a market-wide demand change to its own actions.

  - what: Long-term brand damage from discounting or aggressive ads.
    why: The company has no agreed brand-health measure.
    risk: A locally cheaper customer may be globally expensive.

  - what: Cross-device and view-through attribution error.
    why: Identity resolution is incomplete.
    risk: Paid-social acquisition cost may be biased in either direction.

handoffs: {}
```

The `landing_page_fit_score` and `channel_status` entries are intentionally explicit
examples of arrivals produced by this system. They do not masquerade as independent facts.
The `sales_fit_rating` is explicitly reported, and the reporter's incentives are visible
under `participants`.

## 2. Short multi-agent example

This file has two loops, one shared quantity, one shared action, and an explicit handoff.
The shared action also states how simultaneous choices are resolved.

```yaml
loop_spec: 1
name: Incident response
summary: Reliability contains failures while support keeps customers informed.

runtime:
  timezone: UTC
  state:
    kind: sqlite
    location: ./state/incidents.db
  approvals:
    public_url: "${env.PUBLIC_URL}/approvals"
  on_error:
    do: stop_and_ask
    who: on_call

loops:
  reliability:
    agent: sre_agent
    run: { every: 1m, max_actions: 1 }
    aims:
      - quantity: error_rate
        target: { at_most: 0.01 }
        over: 5m
    sees:
      arrivals: [http_errors, repeated_ticket_rate]
      quantities: [error_rate, customer_confusion]
      beliefs: []
      handoffs: []
    can_do: [publish_incident_banner]
    stop_and_ask:
      who: on_call
      question: Error rate is severe; should traffic be shed?
      when_any: ["quantity.error_rate > 0.10"]
      send: [quantity.error_rate, decision.recent_actions]
    decide:
      mode: first_match
      rules:
        - name: explain_visible_incident
          when: "quantity.error_rate > 0.01 and quantity.customer_confusion > 0.20"
          do: publish_incident_banner
          with:
            message: "We are investigating elevated request failures."
      otherwise: wait

  support:
    agent: support_agent
    run: { every: 5m, max_actions: 1 }
    aims:
      - quantity: customer_confusion
        target: { at_most: 0.20 }
        over: 30m
    sees:
      arrivals: [repeated_ticket_rate]
      quantities: [customer_confusion, error_rate]
      beliefs: []
      handoffs: [incident_to_support]
    can_do: [publish_incident_banner]
    stop_and_ask:
      who: on_call
      question: Customers are confused but telemetry does not show an incident. Investigate manually?
      when_any: ["quantity.customer_confusion > 0.50 and quantity.error_rate <= 0.01"]
      send: [quantity.customer_confusion, quantity.error_rate]
    decide:
      mode: first_match
      rules:
        - name: explain_confirmed_incident
          when: "handoff.incident_to_support.received and quantity.customer_confusion > 0.20"
          do: publish_incident_banner
          with:
            message: "We are investigating elevated request failures."
      otherwise: wait

quantities:
  error_rate:
    description: Fraction of HTTP requests returning 5xx in the last five minutes.
    type: number
    unit: ratio
    calculate: "arrival.http_errors.latest"
  customer_confusion:
    description: Fraction of new tickets that duplicate an already-open incident question.
    type: number
    unit: ratio
    calculate: "arrival.repeated_ticket_rate.latest"

beliefs: {}

arrivals:
  http_errors:
    description: Five-minute 5xx request rate.
    value: { type: number, unit: ratio, min: 0, max: 1 }
    kind: measured
    source: { origin: outside, name: production telemetry }
    every: 1m
    available_after: 1m
    cost: { money: "0.01 USD", human_time: 0m }
    read:
      tool:
        name: telemetry.error_rate
        arguments: { window: 5m }
        take: "$.value"
    informs: []

  repeated_ticket_rate:
    description: Share of new support tickets duplicating the current incident topic.
    value: { type: number, unit: ratio, min: 0, max: 1 }
    kind: measured
    source: { origin: outside, name: support system }
    every: 5m
    available_after: 1m
    cost: { money: "0 USD", human_time: 0m }
    read:
      tool:
        name: support.repeated_ticket_rate
        arguments: { window: 30m }
        take: "$.value"
    informs: []

actions:
  publish_incident_banner:
    description: Publish the fixed incident notice to the status page and help center.
    scope: public_status_surfaces
    available_to: [reliability, support]
    inputs:
      message: { type: string, required: true }
    effects:
      - quantity: customer_confusion
        change: down
        shows_after: 10m
    undo:
      possible: true
      by: publish_incident_banner
      with:
        message: ""
      leaves_behind: Customers may retain screenshots or notifications.
    approval: { required: false }
    call:
      tool:
        name: status.publish_banner
        arguments:
          message: "${input.message}"
    if_many_choose:
      mode: priority
      priority: [reliability, support]

participants:
  sre_agent:
    kind: agent
    description: Runs the reliability loop.
    model: { provider: openai, name: "${env.SRE_MODEL}", credential: "${env.OPENAI_API_KEY}" }
    loses_if_wrong: [Its release authority and incident budget.]
    receives:
      - { what: [loop.reliability.sees], when: each_run, via: loop_state }
  support_agent:
    kind: agent
    description: Runs the support loop.
    model: { provider: openai, name: "${env.SUPPORT_MODEL}", credential: "${env.OPENAI_API_KEY}" }
    loses_if_wrong: [Its publishing authority and customer trust score.]
    receives:
      - { what: [loop.support.sees], when: each_run, via: loop_state }
  on_call:
    kind: human
    description: Makes decisions outside either loop's authority.
    contact:
      webhook: { url: "${env.ON_CALL_WEBHOOK}" }
    loses_if_wrong: [Sleep, incident budget, and service-level performance.]
    receives:
      - { what: [stop_and_ask.request, constraint.failure], when: immediately, via: contact }

must_always:
  - name: no_unverified_cause_in_banner
    require: "proposed.action != 'publish_incident_banner' or not contains(lower(proposed.input.message), 'caused by')"
    on_failure: { do: block_and_ask, who: on_call }

not_modelled:
  - what: Customer sentiment outside support tickets.
    why: Social feeds are not connected.
    risk: Customer confusion may be understated.

handoffs:
  incident_to_support:
    from: reliability
    to: [support]
    when: "quantity.error_rate > 0.01"
    sends: [quantity.error_rate, decision.recent_actions]
    wake_receiver: true
```

## 3. Execution semantics

A runner executes one loop transaction in this order:

1. Read arrivals that are due and append timestamped values to state. A failed or malformed
   read invokes `runtime.on_error`; stale data is never silently reused.
2. Recalculate quantities. Update beliefs that are due, snapshot their value, reason,
   source values, formation time, and check key, and settle any due past checks.
3. Evaluate `stop_and_ask.when_any`. If any expression is true, create a pending human
   request and end the run without choosing an action.
4. In file order, select the first true decision rule. `wait` records a no-action result.
5. Resolve simultaneous selections of a shared action, validate its inputs, and construct
   `proposed`, including direct `set_to` effects.
6. Evaluate every `must_always` rule. Failure always blocks the action.
7. If approval is required, persist the exact proposal and evidence, notify the named human,
   and wait. Approval applies only to that immutable proposal and expires as declared.
8. If an action was selected and approved, call it once with its saved idempotency key,
   record the result, schedule follow-up effect checks, and run `after_success`. At the end
   of every completed run, including `wait`, evaluate and emit any handoffs.

An approval or escalation response is stored in the same state database. The generated
implementation exposes approval endpoints below `runtime.approvals.public_url`; a
participant's contact webhook receives the link and the declared `send` data. Rejection
ends the proposal. Approval never bypasses `must_always`.

Durations are integer values ending in `s`, `m`, `h`, or `d`. Times are UTC internally and
displayed in `runtime.timezone`. Money is a quoted number plus ISO currency code. Ratios are
between 0 and 1.

Expressions are a small, side-effect-free language:

- Namespaces are `arrival`, `quantity`, `belief`, `handoff`, `input`, `before`,
  `proposed`, `response`, `run`, `action`, `decision`, and `now`.
- Operators are arithmetic, comparison, `and`, `or`, and `not`.
- Built-ins are `min`, `max`, `round`, `abs`, `sum(series, duration)`,
  `mean(series, duration)`, `count(series, duration)`, `lower`, `contains`,
  `start_of_week`, and `age`.
- `arrival.x.latest` is the latest valid value. A bare `arrival.x` is its timestamped
  series. `belief.x.value` is its latest value.
- `belief.x.check.mean_last_N` means the mean of its last `N` settled scores. It is null
  until `N` scores exist; a null used in a comparison makes that comparison false.
- In a hard rule, `proposed.input` contains action arguments and `proposed.quantity`
  contains current quantities with direct `set_to` effects applied. `proposed.scope` is
  copied from the selected action's required `scope`.
- `before.quantity` is the immutable quantity snapshot saved with an executed action and
  is available when rendering that action's `undo.with` arguments.
- `${...}` evaluates an expression inside an otherwise literal YAML value. `${env.NAME}`
  reads an environment variable. Missing environment variables are startup errors.
- `take` uses only root JSON paths such as `$.score`, `$.rows[0].value`, and `$.rows[0]`.

The runner stores the exact evidence used for every belief and decision. LLM output must
match the declared type and range; invalid output is a runtime error, not a value to clamp.

## 4. Complete key list

No keys outside this list are valid in version 1. Extension keys must begin with `x-`.
Mappings keyed by an ID use lower-case `snake_case` IDs. Every reference is checked.

### File and runtime

| Key | Required | Meaning |
|---|---:|---|
| `loop_spec` | yes | Format version; exactly `1`. |
| `name` | yes | Human title. |
| `summary` | yes | One-sentence purpose and principal trade-off. |
| `runtime` | yes | Execution settings. |
| `runtime.timezone` | yes | IANA timezone or `UTC`. |
| `runtime.state` | yes | Durable state store. |
| `runtime.state.kind` | yes | `sqlite` in v1. |
| `runtime.state.location` | yes | SQLite path. |
| `runtime.approvals` | yes | Human approval service settings. |
| `runtime.approvals.public_url` | yes | Public base URL for generated approve/reject links. |
| `runtime.on_error` | yes | Response to read, model, validation, or call errors. |
| `runtime.on_error.do` | yes | `stop_and_ask` or `stop`. |
| `runtime.on_error.who` | if asking | Human participant to notify. |
| `loops` | yes | Map of loop IDs to loop definitions. |
| `quantities` | yes | Map of quantity IDs. |
| `beliefs` | yes | Map of hidden-belief IDs; may be empty. |
| `arrivals` | yes | Map of arriving-data IDs. |
| `actions` | yes | Map of action IDs. |
| `participants` | yes | Map of human and agent IDs. |
| `must_always` | yes | List of objective-independent hard rules; may be empty. |
| `not_modelled` | yes | Explicit omissions; may be empty. |
| `handoffs` | yes | Messages between loops; may be empty. |

### `loops.<id>`

| Key | Required | Meaning |
|---|---:|---|
| `agent` | yes | Agent participant running the loop. |
| `run` | yes | Schedule and per-run limit. |
| `run.every` | yes | Duration between scheduled runs. |
| `run.max_actions` | yes | Maximum executed actions per run. |
| `aims` | yes | Non-empty list of steered quantities. |
| `aims[].quantity` | yes | Quantity reference. |
| `aims[].target` | yes | Target mapping. |
| `aims[].target.at_most` | one target | Inclusive upper bound. |
| `aims[].target.at_least` | one target | Inclusive lower bound. |
| `aims[].target.equals` | one target | Required value. |
| `aims[].target.between` | one target | Two-element inclusive range. |
| `aims[].over` | yes | Window on which the target is judged. |
| `sees` | yes | Exact information exposed to this loop. |
| `sees.arrivals` | yes | Arrival references; may be empty. |
| `sees.quantities` | yes | Quantity references; may be empty. |
| `sees.beliefs` | yes | Belief references; may be empty. |
| `sees.handoffs` | yes | Handoff references; may be empty. |
| `can_do` | yes | Action references available to the loop. |
| `stop_and_ask` | yes | Conditions that pre-empt decision-making. |
| `stop_and_ask.who` | yes | Human participant asked. |
| `stop_and_ask.question` | yes | Question presented to that human. |
| `stop_and_ask.when_any` | yes | Non-empty list of Boolean expressions. |
| `stop_and_ask.send` | yes | Evidence references included in the request. |
| `decide` | yes | Ordered action-selection rule. |
| `decide.mode` | yes | `first_match` in v1. |
| `decide.rules` | yes | Ordered list; may be empty. |
| `decide.rules[].name` | yes | Unique rule ID within the loop. |
| `decide.rules[].when` | yes | Boolean expression. |
| `decide.rules[].do` | yes | An action in `can_do`. |
| `decide.rules[].with` | if inputs exist | Action argument mapping. |
| `decide.rules[].because` | no | Short human rationale; stored with the decision. |
| `decide.otherwise` | yes | `wait` in v1. |

### `quantities.<id>`

| Key | Required | Meaning |
|---|---:|---|
| `description` | yes | Plain-language definition. |
| `type` | yes | `number` or `boolean`. |
| `unit` | for numbers | Unit string; use `ratio` for a 0–1 fraction. |
| `calculate` | yes | Expression using arrivals and/or other quantities. |

Quantities are calculated facts, not writable variables. An action's direct effects create
a temporary `proposed.quantity` for constraint checking; observed state changes only when
new data arrives.

### `beliefs.<id>`

| Key | Required | Meaning |
|---|---:|---|
| `description` | yes | What cannot be directly seen. |
| `value` | yes | Declared result schema. |
| `value.type` | yes | `probability`, `number`, `boolean`, `string`, or `object`. |
| `value.unit`, `value.min`, `value.max`, `value.fields` | as applicable | Same schema fields as arrival values. |
| `starts_at` | yes | Initial value before first formation. |
| `formed` | yes | How and when the belief is formed. |
| `formed.every` | yes | Update interval. |
| `formed.agent` | one method | Agent participant that forms it. |
| `formed.prompt` | with agent | Complete formation instructions. |
| `formed.calculate` | one method | Expression alternative to `agent` plus `prompt`. |
| `formed.returns` | with agent | JSON extraction from agent output. |
| `formed.returns.value` | with agent | JSON path to the typed belief value. |
| `formed.returns.reason` | no | JSON path to a human-readable reason. |
| `check` | yes | Outcome check mapping, or the literal `none`. |
| `check.against` | with check | Arrival that eventually reveals the outcome. |
| `check.after` | with check | Minimum delay before settlement. |
| `check.match` | no | Forecast/actual key mapping for cohort or entity alignment. |
| `check.match.forecast` | with match | Key expression saved when forming the belief. |
| `check.match.actual` | with match | Key expression evaluated on candidate actuals. |
| `check.correct_when` | with check | Boolean expression over `arrival.value`. |
| `check.score` | with check | `brier` for probabilities or `absolute_error` for numbers. |
| `check.alert` | no | Poor-check-score alert. |
| `check.alert.mean_over` | with alert | Number of settled scores in the rolling mean. |
| `check.alert.above` | with alert | Alert threshold. |
| `check.alert.who` | with alert | Human participant notified. |

An arrival informs a belief only through `arrivals.<id>.informs`; that is the single source
of truth for the evidence graph. The runner supplies all matching histories to `formed`.
`check: none` is legal but produces a linter warning, making the omission deliberate rather
than invisible.

### `arrivals.<id>`

| Key | Required | Meaning |
|---|---:|---|
| `description` | yes | What arrives and for what period/entity. |
| `value` | yes | Result schema. |
| `value.type` | yes | `number`, `boolean`, `string`, `date`, or `object`. |
| `value.unit` | for numbers | Unit string. |
| `value.min`, `value.max` | no | Inclusive validation bounds. |
| `value.fields` | for objects | Map of field IDs to nested value schemas. |
| `kind` | yes | `measured`, `reported`, or `generated`. |
| `source` | yes | Who or what produced it. |
| `source.origin` | yes | `outside` or `this_system`. |
| `source.name` | one source | Named external or internal system. |
| `source.participant` | one source | Participant reference; required for `reported`. |
| `source.action` | one source | Action reference that produces the arrival. |
| `source.loop` | one source | Loop reference that produces the arrival. |
| `every` | yes | Expected arrival interval. |
| `available_after` | yes | Normal delay between the described event and availability. |
| `cost` | yes | Marginal cost of one read. |
| `cost.money` | yes | Quoted amount and ISO currency. |
| `cost.human_time` | yes | Human effort duration. |
| `read` | yes | Exactly one read adapter. |
| `informs` | yes | Belief references; may be empty. |

`measured` means an instrument or ledger observed an event. `reported` means an interested
person asserted it; the source must be a participant so their losses are visible.
`generated` means software or a model produced it. `kind` does not determine `origin`: a
generated vendor score can come from outside, and an internally measured queue depth can
come from this system.

### `actions.<id>`

| Key | Required | Meaning |
|---|---:|---|
| `description` | yes | Concrete operation and scope. |
| `scope` | yes | Stable machine-readable name for the people, accounts, or resources affected. |
| `available_to` | yes | Loops allowed to choose it. |
| `inputs` | yes | Map of argument IDs; may be empty. |
| `inputs.<id>.type` | yes | `number`, `boolean`, or `string`. |
| `inputs.<id>.unit` | for numbers | Unit string. |
| `inputs.<id>.min`, `.max`, `.enum` | no | Input bounds or allowed values. |
| `inputs.<id>.required` | yes | Whether callers must supply it. |
| `inputs.<id>.default` | no | Literal default for an optional input. |
| `effects` | yes | Non-empty list of quantities the action may move. |
| `effects[].quantity` | yes | Quantity reference. |
| `effects[].change` | yes | `set_to`, `up`, `down`, or `unknown`. |
| `effects[].to` | with `set_to` | Literal or `${...}` value. |
| `effects[].shows_after` | yes | Earliest credible observation delay. |
| `effects[].note` | no | Important uncertainty or mechanism. |
| `undo` | yes | Reversibility statement. |
| `undo.possible` | yes | Boolean. |
| `undo.by` | if possible | Action reference used to reverse it. |
| `undo.with` | if possible | Arguments for the reversing action; may reference `before.quantity`. |
| `undo.within` | no | Time limit on reversal. |
| `undo.leaves_behind` | no | Effects reversal cannot erase. |
| `undo.reason` | if impossible | Why it cannot be undone. |
| `approval` | yes | Human gate. |
| `approval.required` | yes | Boolean. |
| `approval.by` | if required | Human participant. |
| `approval.expires_after` | if required | Approval lifetime. |
| `approval.send` | if required | Evidence included in the approval request. |
| `call` | yes | Exactly one action adapter. |
| `if_many_choose` | if shared | Resolution when more than one loop chooses the action. |
| `if_many_choose.mode` | if shared | `priority` or `ask_human`. |
| `if_many_choose.priority` | with priority | Ordered loop references. |
| `if_many_choose.who` | with ask | Human participant. |
| `after_success` | no | Post-call runtime changes. |
| `after_success.stop_loops` | no | Loop references to disable after success. |

An action is shared when `available_to` has more than one loop. An action with
`undo.possible: false` and no human approval is a lint error, not a warning.

### `participants.<id>`

| Key | Required | Meaning |
|---|---:|---|
| `kind` | yes | `human` or `agent`. |
| `description` | yes | Role in this file. |
| `model` | for agents | Model connection. |
| `model.provider` | for agents | Provider ID. |
| `model.name` | for agents | Model name or environment template. |
| `model.credential` | for agents | Environment template for the credential. |
| `contact` | for contacted humans | Notification adapter. |
| `loses_if_wrong` | yes | Non-empty list of concrete stakes. |
| `receives` | yes | Actual information routes; may be empty. |
| `receives[].what` | yes | Data, request, or `loop.<id>.sees` references. |
| `receives[].when` | yes | `each_run`, `immediately`, or a duration. |
| `receives[].via` | yes | `loop_state` or `contact`. |

`contact` contains exactly one `webhook` or `tool` adapter. `approval.request`,
`stop_and_ask.request`, `constraint.failure`, and `decision.recent_actions` are built-in
event references.

### Hard rules, omissions, and handoffs

| Key | Required | Meaning |
|---|---:|---|
| `must_always[].name` | yes | Unique hard-rule ID. |
| `must_always[].require` | yes | Boolean expression; false always blocks. |
| `must_always[].on_failure` | yes | Failure handling. |
| `must_always[].on_failure.do` | yes | `block` or `block_and_ask`. |
| `must_always[].on_failure.who` | if asking | Human participant. |
| `not_modelled[].what` | yes | Deliberately omitted factor. |
| `not_modelled[].why` | yes | Why it is omitted. |
| `not_modelled[].risk` | yes | How the omission can mislead the loop. |
| `handoffs.<id>.from` | yes | Sending loop. |
| `handoffs.<id>.to` | yes | Non-empty receiving-loop list. |
| `handoffs.<id>.when` | yes | Boolean send condition. |
| `handoffs.<id>.sends` | yes | Data references copied into the immutable message. |
| `handoffs.<id>.wake_receiver` | yes | Whether receipt triggers an immediate run. |

### Read, call, and contact adapters

Each adapter mapping contains exactly one of these keys:

| Adapter | Allowed nested keys |
|---|---|
| `sql` | `connection` and `query` required; `parameters` and `take` optional. Reads only. |
| `http` | `method` and `url` required; `headers`, `query`, `body`, `take`, and `success_when` optional. |
| `tool` | `name` required; `arguments` and `take` optional. The generated target must bind this named tool. |
| `state` | `path` required. Reads previously persisted LoopSpec state. |
| `webhook` | `url` required; `headers` optional. Used only for participant contact. |

SQL must be a single read-only statement. An HTTP read permits only `GET` or `HEAD`; action
calls permit any method. Environment interpolation is allowed in adapter values, but a
linter rejects strings that appear to contain literal credentials.

## 5. Minimum lint rules

A conforming linter reports:

- any quantity that is undefined, cyclic, unit-inconsistent, or has no dependency path to
  an arrival, and any aimed-at quantity with no path to a measured or reported arrival;
- arrivals that are never used by a quantity, belief, check, or handoff;
- missing schedules, delays, costs, source origin, schemas, or readers;
- a reported arrival not tied to a participant, or a participant with no stated loss;
- a generated arrival labelled as measured, as far as the declared source makes detectable;
- a belief with no informing arrival, an unchecked belief, a check whose result can never
  arrive, or a probability checked with a non-probabilistic score;
- a self-confirming cycle from loop or action to generated arrival to belief to decision;
  it is a warning if independent evidence also enters the belief and an error otherwise;
- an action with no affected quantity, no observation delay, unspecified reversibility,
  invalid inputs, or an unavailable implementation adapter;
- an irreversible action without approval, an approval assigned to an agent or unreachable
  human, or an approver who is not sent the action, effects, and undo facts;
- a decision that names an unavailable action, can exceed `max_actions`, or has no
  `stop_and_ask`;
- a hard rule that references unavailable state or cannot be evaluated before an action;
- a participant shown data not in `receives`, or a loop expression referencing data absent
  from `sees`;
- a shared action without a simultaneous-choice rule, a handoff with an invalid endpoint,
  or multiple loops writing the same state without an explicit shared action.

Warnings may be acknowledged with an `x-lint-ignore` extension containing a reason. Errors
cannot be suppressed.

## 6. Diagram projection

No layout keys are needed. The projection is mechanical:

- create one node for every loop, arrival, quantity, belief, action, participant, hard rule,
  and handoff;
- draw arrival-to-quantity edges from `calculate`, arrival-to-belief edges from `informs`,
  check-arrival-to-belief edges from `check.against`, and action-to-quantity edges from
  `effects`;
- draw participant-to-loop edges from `agent`, loop-to-action edges from `can_do`,
  human-to-action edges from `approval.by`, and information-to-participant edges from
  `receives`;
- draw loop-to-handoff-to-loop edges from `from` and `to`;
- draw dotted loop/action/participant-to-arrival edges from any `source` whose origin is
  `this_system`;
- attach aims to loop-to-quantity edges, and hard rules to every action they reference.

Cycles are retained, not hidden; they are often the most important feature of the diagram.
Layout is a renderer concern and therefore cannot appear in a LoopSpec file.

## 7. Three hardest design decisions

### 1. Registries plus references, instead of deeply nested loops

I chose top-level registries for quantities, beliefs, arrivals, actions, and participants.
A loop's first screen remains a readable index, while a single definition can be shared
and every edge in a diagram comes from a named reference.

I rejected nesting arrivals, beliefs, and actions inside each loop. It reads pleasantly for
one loop but duplicates shared facts in multi-agent files, makes ownership ambiguous, and
turns diagram projection into heuristic tree-walking.

### 2. Separate `kind` from `source.origin`

`kind` answers whether a value was measured, reported, or generated. `source.origin`
separately answers whether it came from outside or from this system. These are independent:
an internal queue depth can be measured, an external analyst score can be generated, and a
sales rating can be reported.

I rejected a single enum such as `external_measurement`, `human_report`, and
`agent_generated`. It looks shorter but conflates evidence quality, incentives, and causal
origin. It also grows combinatorially and makes self-confirming-cycle linting unreliable.

### 3. Ordered rules, instead of an open-ended “policy” prompt

Version 1 chooses the first matching rule, with a mandatory, earlier
`stop_and_ask`. Beliefs may use an LLM, but authority and action selection remain visible
and reproducible. A reader can predict the possible behavior without mentally executing a
prompt.

I rejected `policy: <natural-language prompt>` as the main decision mechanism. It is easy
for an LLM to write and expressive, but a linter cannot prove action reachability, enforce
coverage, explain precedence, or reliably determine when the agent should surrender
control. It also makes two generated implementations behaviorally different.

## 8. Where the design is weakest

The weakest part is the action-effect model. `up`, `down`, `set_to`, and `unknown` plus
`shows_after` are honest and readable, but they do not capture dose-response curves,
interactions, delayed distributions, or effects that reverse over time. Adding a richer
forecast model would quickly make the common file unreadable and would invite authors to
state precision they do not possess.

There are two related limits. First, `proposed.quantity` can enforce hard rules only for
direct `set_to` effects; constraints involving uncertain downstream effects need a
conservative action-specific rule. Second, a generic `tool` adapter still requires the
target runtime to have a tool with that exact name and argument shape. The file is
sufficient to generate orchestration and all SQL/HTTP wiring, but it cannot conjure an
undeclared vendor capability.

Finally, calibration matching is intentionally small. Weekly cohorts and entity-keyed
outcomes work, but censored outcomes, shifting labels, counterfactual evaluation, and
several competing definitions of “correct” need either precomputed arrivals or a future
version. That limitation is preferable to a `check` key that sounds rigorous while doing
nothing reproducible.
