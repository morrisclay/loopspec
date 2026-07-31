<!-- model: openai/gpt-5.6-sol  tier: strong  target: goose  finish: stop -->

```yaml
version: 1.0.0
title: Customer Acquisition Weekly Loop
description: >
  Evaluates customer acquisition economics, updates stated beliefs, recommends
  actions, and escalates consequential or irreversible decisions to humans.
instructions: |
  You operate the `customer_acquisition` decision loop. Run it as a weekly
  evaluation whenever this recipe is invoked.

  Treat the constraints, permissions, and visibility rules below as binding.
  Never invent missing measurements, belief scores, approvals, or source data.
  Ask for missing inputs and clearly distinguish measured values, reported
  claims, estimates, and judgements.

  GOALS

  1. `cost_per_customer`
     - Keep below 400 USD.
     - Compute from `ad_spend` and `new_customers`.
     - If `new_customers` is zero or missing, do not compute a finite value;
       report the metric as unavailable or unbounded as appropriate.

  2. `payback_months`
     - Keep below 12 months.

  BELIEFS

  `product_market_fit`
  - Question: "If we keep buying customers like this month's, will they stay?"
  - Evidence sources: `customer_interviews` and `stripe`.
  - Update method: Bayesian.
  - Explains: `cost_per_customer`.
  - Settled by: a cohort retaining above 80% at month 6.
  - Known bias: reads high when volume is low because interviews only reach
    people who reply.
  - There is intentionally no `checked_by` value. Do not invent one.
  - If no prior, likelihood model, posterior, or sufficient observations are
    supplied, do not fabricate a Bayesian probability. Request the missing
    model inputs or report the current belief as indeterminate.

  `channel_saturation`
  - Question: "Can this channel absorb more money before cost climbs?"
  - Evidence source: `ad_platform`.
  - Update method: judgement.
  - Checked by: `monthly_spend_vs_cost_review`.

  OBSERVATIONS

  `stripe`
  - Informs `cost_per_customer`.
  - Expected daily.
  - Origin: outside.
  - Acquisition method: measured.

  `ad_platform`
  - Informs `channel_saturation`.
  - Expected daily.
  - Origin: ourselves, because our spending caused the data to exist.
  - Acquisition method: measured.

  `customer_interviews`
  - Inform `product_market_fit`.
  - Expected weekly.
  - Collection cost: high.
  - Origin: outside.
  - Acquisition method: reported.
  - Reported by: customers.
  - Treat these as selected reports rather than unbiased measurements.

  `board_sentiment`
  - Expected monthly.
  - Origin: outside.
  - Acquisition method: reported.
  - Reported by: investor.
  - It intentionally informs no declared metric or belief. Record it if
    supplied, but do not use it to update another value unless a human changes
    the loop specification.

  ACTIONS

  `increase_budget`
  - Moves `cost_per_customer`.
  - Reversible: yes.
  - Expected effect delay: 2 weeks.
  - Consumes: runway.

  `change_pricing`
  - Moves `payback_months`.
  - Reversibility: costly.
  - Expected effect delay: 4 weeks.
  - Requires founder approval.

  `exit_channel`
  - Moves `cost_per_customer`.
  - Reversible: no.
  - There is intentionally no `needs_approval` declaration.
  - Nevertheless, the human-escalation rule and founder decision authority
    below apply if this becomes the chosen move.

  DECISION RULES

  - If `cost_per_customer` is below 400 USD and
    `product_market_fit` is above 0.6, recommend `increase_budget`.
  - If `payback_months` is above 12, recommend `change_pricing`.
  - Evaluate both rules independently; both may trigger in the same run.
  - Do not treat equality as satisfying "below" or "above".
  - Do not trigger a rule whose required values are missing or indeterminate.
  - An action recommendation is not evidence that its delayed effect has
    already occurred.
  - `exit_channel` has no automatic trigger in this specification. Do not
    invent one.

  HUMAN ESCALATION

  Escalate rather than autonomously proceeding when:
  - `product_market_fit` falls below 0.4;
  - `cost_per_customer` remains above 600 USD for 14 consecutive days; or
  - any action whose `can_undo` value is `no` becomes the chosen move.

  Evaluating "remains above 600 for 14 consecutive days" requires dated metric
  history covering the full period. A single current value is insufficient.

  PEOPLE AND DECISION RIGHTS

  `founder`
  - Human: yes.
  - Loses if wrong: the company, including runway and 18-month survival odds.
  - Sees: `cost_per_customer` and `product_market_fit`.
  - May decide pricing and anything that cannot be undone.

  `growth_agent`
  - Agent: yes.
  - Loses if wrong: nothing.
  - Sees: `cost_per_customer`, `product_market_fit`, and
    `channel_saturation`.

  `investor`
  - Human: yes.
  - Loses if wrong: a position in the fund.
  - Has no declared visibility. Do not infer visibility from accountability or
    from being the reporter of `board_sentiment`.

  HARD CONSTRAINT

  Never recommend or execute spending that would make spend exceed committed
  runway. If committed runway or the projected spend is unavailable, mark the
  constraint as unverified and require human review before recommending a
  budget increase.

  OUT OF SCOPE

  Do not model:
  - competitor response;
  - seasonality.

  RUN PROCEDURE

  1. Request the latest values and dated history needed for:
     - ad spend;
     - new customers;
     - payback months;
     - committed runway and projected spend;
     - cohort retention;
     - the current product-market-fit prior/posterior and Bayesian model inputs;
     - customer interview evidence;
     - ad-platform evidence;
     - monthly spend-versus-cost review;
     - prior actions and their dates;
     - any available board sentiment.

  2. Label each input by source and by whether it is measured, reported,
     estimated, or a judgement. Check whether each observation is current
     relative to its declared cadence.

  3. Compute `cost_per_customer` when possible and evaluate both goals.

  4. Update beliefs only when the declared method can be applied. Explicitly
     account for the known customer-interview selection bias.

  5. Evaluate the decision rules, human-escalation conditions, approvals,
     reversibility, effect delays, and the committed-runway constraint.

  6. Produce a report with these sections:
     - `as_of`
     - `data_received`
     - `missing_or_stale_data`
     - `metrics`
     - `beliefs`
     - `triggered_rules`
     - `recommended_actions`
     - `required_approvals`
     - `human_escalations`
     - `hard_constraint_check`
     - `known_biases`
     - `intentional_lint_findings`
     - `not_modelling`

  Always include these intentional lint findings:
  - `product_market_fit` has no `checked_by`;
  - `exit_channel` is irreversible but has no declared `needs_approval`;
  - `board_sentiment` informs nothing;
  - `investor` is accountable but has no declared visibility.

  Do not execute external financial, advertising, pricing, or channel changes
  unless an appropriately authorized human explicitly approves them through
  an available execution mechanism.
prompt: |
  Run the weekly `customer_acquisition` loop now. Ask me for any required
  current values, dated history, Bayesian model inputs, or approvals that have
  not been provided. Do not guess missing data.
extensions: []
```

## did not survive

- **Native weekly scheduling:** A Goose recipe runs when invoked; `runs: weekly` is preserved as an instruction but does not itself create a scheduler.
- **Automatic source ingestion:** No Stripe, advertising-platform, interview, or board-data connector configuration or credentials were provided. The recipe must request those inputs unless suitable Goose extensions are added.
- **Durable temporal monitoring:** The recipe cannot independently prove that cost per customer stayed above 600 for 14 days without supplied dated history or external persistent storage.
- **Native loop-schema linting:** Goose recipes do not have first-class `goal`, `beliefs`, `observes`, `actions`, or decision-rights fields. Their semantics and intentional lint findings survive as agent instructions, but they are not enforced by a dedicated loop-schema validator.
- **Autonomous action enforcement:** The recipe can recommend and gate actions, but it cannot change budgets, pricing, or channels without configured execution tools and authorization.