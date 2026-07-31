<!-- model: google/gemini-2.5-pro  tier: strong  target: goose  finish: stop -->

```yaml
# Goose recipe for a venture's customer acquisition loop.
# Generated from a loop spec.

name: customer_acquisition
rhythm: weekly

stakeholders:
  - id: founder
    name: Founder
    responsibility: "the company"
    tags: [human]
  - id: growth_agent
    name: Growth Agent
    responsibility: "bears nothing"
    tags: [agent]
  - id: investor
    name: Investor
    responsibility: "a position in the fund"
    tags: [human]

indicators:
  - id: cac
    name: Customer Acquisition Cost
    description: "Computed from ad_spend and new_customers."
    objective: "< 400"
    sources: [stripe]
  - id: payback_months
    name: Payback Months
    objective: "< 12"
  - id: product_market_fit
    name: Product Market Fit
    description: "A Bayesian estimate. Settled by the condition: a cohort retains above 80% at month 6."
    sources: [customer_interviews, stripe]
    influences: [cac]
  - id: channel_saturation
    name: Channel Saturation
    description: "A judgement-based estimate."
    sources: [ad_platform]
  - id: board_sentiment
    name: Board Sentiment
    sources: [investor_check_in]
  # Implicitly required by other definitions
  - id: runway
    name: Runway
    description: "The amount of time the company has until it runs out of money."

collections:
  - id: stripe
    name: Stripe Data
    description: "Measures metrics related to revenue and customers."
    cadence: daily
  - id: ad_platform
    name: Ad Platform Data
    description: "Measures metrics related to advertising channels."
    cadence: daily
  - id: customer_interviews
    name: Customer Interviews
    description: "Qualitative feedback from customers."
    cadence: weekly
    tags: [cost:high]
  - id: investor_check_in
    name: Investor Check-in
    description: "Assertion of sentiment from the investor."
    cadence: monthly
    owner: investor

actions:
  - id: increase_budget
    name: Increase Budget
    description: "Increase advertising spend."
    influences: [cac, runway]
    leadTime: 2w
    tags: [reversibility:reversible]
  - id: change_pricing
    name: Change Pricing
    description: "Adjust the product's pricing model or price points."
    influences: [payback_months]
    leadTime: 4w
    approver: founder
    tags: [reversibility:costly]
  - id: exit_channel
    name: Exit Channel
    description: "Stop advertising on a specific channel."
    tags: [reversibility:irreversible]
    # This action does not specify what indicators it moves.

triggers:
  - name: Scale Spending
    condition: "cac < 400 and product_market_fit > 0.6"
    actions: [increase_budget]
  - name: Address Payback Period
    condition: "payback_months > 12"
    actions: [change_pricing]
  - name: PMF Crisis Alert
    condition: "product_market_fit < 0.4"
    escalations:
      - to: founder
        reason: "Product-market fit is dangerously low and requires founder-level attention."

guardrails:
  - name: Prevent Overspending
    condition: "runway < 0" # Or a threshold like "runway < 3m"
    description: "Spend should not exceed committed runway."

outOfScope:
  - "competitor_response"
  - "seasonality"

```

---

## did not survive

Some concepts in the loop spec could not be fully represented in the Goose recipe format.

-   **`computed_from`**: The formal relationship that `cac` is `computed_from` `ad_spend` and `new_customers` is not a first-class property in Goose. This information was moved to the `description` of the `cac` indicator.
-   **`parties.*.sees`**: The `founder`'s explicit permission to `see` specific indicators (`cac`, `product_market_fit`) has no direct equivalent. In Goose, a stakeholder's visibility is implied by their roles (e.g., as an `approver` for an action or an `escalation` target), but there is no mechanism to define a read-only "view" or dashboard for a stakeholder.
-   **`method`**: Specific estimation methods (`bayesian`, `judgement`) are not structured fields. This qualitative information was captured in the `description` of the relevant indicators.
-   **`explains`**: The causal link where an estimate `explains` a regulated variable was mapped to Goose's `influences` property (e.g., `product_market_fit` influences `cac`). This captures the relationship structure but loses the specific "explains" semantic.
-   **`settled_by`**: The explicit condition for resolving an estimate's uncertainty is not a formal property. It has been included in the indicator's `description`.
-   **`consumes`**: The concept of an action `consumes` a resource was modeled as an `influence`. The `increase_budget` action now `influences` the `runway` indicator, implying a negative impact. This is a reasonable mapping but loses the specific "consumes" verb.
-   **`asserted_by`**: This was mapped by creating a `collection` and assigning the party as its `owner`. This is a functional and common pattern but is less direct than the original spec.