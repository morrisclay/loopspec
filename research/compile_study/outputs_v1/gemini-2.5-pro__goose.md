<!-- model: google/gemini-2.5-pro  tier: strong  target: goose  finish: stop -->

This is a Goose recipe implementation of the provided loop specification.

```yaml
name: customer_acquisition
cadence: weekly
description: A recipe for managing the trade-offs in customer acquisition between cost, long-term value, and channel viability.

metrics:
  # === GOALS ===
  - name: cost_per_customer
    description: "The fully-loaded cost to acquire one new customer."
    unit: USD
    objective: "keep below 400"
    influenced_by: [ad_spend, new_customers, product_market_fit]

  - name: payback_months
    description: "The number of months it takes for a customer's revenue to pay back their acquisition cost."
    objective: "keep below 12"
    # This metric's dependencies are implicitly defined by its inputs, like cost_per_customer.

  # === BELIEFS ===
  - name: product_market_fit
    description: "If we keep buying customers like this month's, will they stay?"
    type: belief
    calculation_method: bayesian
    influenced_by: [customer_interviews, stripe]
    influences: [cost_per_customer] # 'explains' is modelled as a causal influence
    validation_condition: "A cohort retains above 80% at month 6"
    notes:
      - "Known Bias: Reads high when volume is low — interviews only reach people who reply."

  - name: channel_saturation
    description: "Can this channel absorb more money before cost climbs?"
    type: belief
    calculation_method: expert_judgement
    influenced_by: [ad_platform]
    controls:
      - name: monthly_spend_vs_cost_review
        description: "Monthly review of ad spend versus acquisition cost to check for saturation effects."
        frequency: monthly

  # === SUPPORTING METRICS (implied by other parts of the spec) ===
  - name: runway
    description: "The financial runway of the company, consumed by actions like ad spend."
    # Unit could be USD or months; assumed to be a resource that can be compared against spend.
  
  - name: ad_spend
    description: "Total spend on advertising platforms, derived from data sources."
    unit: USD
    
  - name: new_customers
    description: "Number of new customers acquired, derived from data sources."

data_sources:
  - name: stripe
    description: "Customer and revenue data from Stripe, which informs PMF and cost calculations."
    update_frequency: daily
    measurement_type: measured
    notes:
      - "Origin: outside (customer behavior)"

  - name: ad_platform
    description: "Spend and performance data from ad platforms which informs channel saturation and cost."
    update_frequency: daily
    measurement_type: measured
    notes:
      - "Origin: ourselves (we caused this spend to exist)"

  - name: customer_interviews
    description: "Qualitative feedback from customer interviews, informing our belief in PMF."
    update_frequency: weekly
    measurement_type: reported
    reported_by: customers
    notes:
      - "Cost: high"
      - "Origin: outside (customer sentiment)"

  - name: board_sentiment
    description: "Sentiment reported by investors/board members."
    update_frequency: monthly
    measurement_type: reported
    reported_by: investor
    notes:
      - "Origin: outside"
      - "This data is collected but does not directly inform a specific metric in this model."

actions:
  - name: increase_budget
    description: "Increase the advertising budget."
    influences: [cost_per_customer]
    reversibility: reversible # from 'can_undo: yes'
    time_lag: "2 weeks"
    costs:
      - resource: runway
        amount: variable

  - name: change_pricing
    description: "Change the product's pricing structure or level."
    influences: [payback_months]
    reversibility: costly
    time_lag: "4 weeks"
    requires_approval_from: [founder]

  - name: exit_channel
    description: "Stop advertising and pull out of an acquisition channel."
    influences: [cost_per_customer]
    reversibility: irreversible # from 'can_undo: no'
    # Approval for irreversible actions is governed by the Founder's decision rights.
    requires_approval_from: [founder]

stakeholders:
  - name: founder
    type: human
    stakes: "The company — runway, and 18-month survival odds"
    visibility: [cost_per_customer, product_market_fit]
    decision_rights:
      - description: "Must approve pricing changes."
        applies_to_actions: [change_pricing]
      - description: "Must approve any irreversible action."
        applies_to_property: { reversibility: irreversible }

  - name: growth_agent
    type: agent
    stakes: "none"
    visibility: [cost_per_customer, product_market_fit, channel_saturation]

  - name: investor
    type: human
    stakes: "A position in the fund"
    visibility: [] # Accountable but blind in the context of this loop's metrics

rules:
  - name: scale_spend_on_pmf
    if: "metrics.cost_per_customer.value < 400 and metrics.product_market_fit.value > 0.6"
    then:
      recommend_action: increase_budget
      rationale: "Both CAC is within target and PMF belief is strong, indicating an opportunity to scale acquisition."

  - name: fix_payback_period
    if: "metrics.payback_months.value > 12"
    then:
      recommend_action: change_pricing
      rationale: "Payback period is too long; pricing may need to be adjusted to improve unit economics."

alerts:
  - name: pfm_falling
    trigger: "metrics.product_market_fit.value < 0.4"
    description: "Product/Market Fit belief has fallen below the critical threshold of 0.4."
    notify: [founder, growth_agent]

  - name: cac_sustained_high
    trigger: "metrics.cost_per_customer.value > 600 for 14 days"
    description: "Cost Per Customer has remained above $600 for 2 weeks."
    notify: [founder, growth_agent]
  
  - name: irreversible_action_proposed
    trigger: "rules.recommended_action.reversibility == 'irreversible'"
    description: "The recommended action cannot be undone. Requires human review and approval."
    notify: [founder]

guardrails:
  - name: runway_constraint
    description: "Spend must not exceed committed runway."
    condition: "metrics.ad_spend.value <= metrics.runway.value"

out_of_scope:
  - "Competitor response to our marketing or pricing changes."
  - "Seasonality effects on customer acquisition cost or volume."
```

---

## did not survive

The following parts of the specification could not be expressed as first-class, structured concepts in the target Goose YAML format and were instead preserved as unstructured `notes`.

*   **`origin` of an observation**: The distinction between data `origin: ourselves` vs. `origin: outside` is an important piece of metadata for interpreting the data source. It was placed in the `notes` field of each data source as it lacks a dedicated structured field.
*   **`cost` of an observation**: The `cost: high` metadata for `customer_interviews` was also moved to the `notes` field. While Goose models the `costs` of `actions`, it does not appear to have a structured way to model the cost of observation or data gathering.
*   **Interpretation of "needs approval"**: The original spec includes a comment that `exit_channel` has no `needs_approval`. However, the `people` section gives the `founder` decision rights over "anything that cannot be undone." I prioritized the stakeholder's explicit decision rights over the comment, assuming the `people` section is the source of truth for authorization rules. This represents an interpretation of conflicting spec details rather than a feature that couldn't be expressed.