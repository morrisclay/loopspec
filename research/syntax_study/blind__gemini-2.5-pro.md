Here is a design for the configuration syntax.

## 1. Example: Startup Customer Acquisition Loop

This YAML file describes a single agent loop, `customer_acquisition`, focused on optimizing a startup's marketing spend.

```yaml
#
# Agent Loop Specification: ACME_Startup_Growth
# version: 1.0
#

loops:
  customer_acquisition:
    # --- The Core Objective ---
    goal:
      description: "Acquire new customers at a sustainable cost."
      steer: "customer_acquisition_cost" # This is a belief, not a direct input.
      towards: "less than $400"

    # --- What the Loop Believes (Inferred Quantities) ---
    beliefs:
      product_market_fit_score:
        description: "A score from 0-100 on how well the product fits the market's needs. The core unobservable driver of conversions."
        how_formed: "LLM inference based on sentiment from 'user_feedback' and trend in 'website_conversion_rate'. Model is retrained weekly."
        how_checked: "Quarterly, compare predicted 'user_retention_30d' against actuals. If prediction error >15%, trigger manual model review."

      customer_acquisition_cost:
        description: "The calculated, fully-loaded cost to acquire one new customer."
        how_formed: "Computed as 'total_ad_spend' / 'new_customers_acquired' over the last 7 days."
        how_checked: "This is a calculation from other inputs; validation happens on its components."

    # --- What the Loop Observes (Data Inputs) ---
    inputs:
      daily_ad_performance:
        description: "Spend and click data from ad platforms."
        source: external
        type: measured
        arrives: "every 24 hours"
        cost: "$5/day for API access"
        informs: [customer_acquisition_cost]
      
      user_feedback:
        description: "NPS surveys and support chat logs."
        source: external
        type: reported # It's what users choose to say, not a passive measurement.
        reported_by: "end_users"
        arrives: "continuously"
        cost: "$0.02 per processed message"
        informs: [product_market_fit_score]

      website_conversion_rate:
        description: "The percentage of website visitors who sign up."
        source: internal # This is produced by our own systems.
        from_system: "ACME_Web_Analytics"
        type: measured
        arrives: "every 6 hours"
        cost: "negligible"
        informs: [product_market_fit_score, customer_acquisition_cost]

    # --- What the Loop Can Do (Actions) ---
    actions:
      adjust_ad_spend:
        description: "Increase or decrease budget for a specific ad channel."
        moves: [customer_acquisition_cost]
        effect_shows_in: "1-3 days"
        reversibility: reversible
        requires_human_approval: false

      change_pricing:
        description: "Alter the monthly subscription price."
        moves: [customer_acquisition_cost, product_market_fit_score] # Price affects perception of fit.
        effect_shows_in: "1 month"
        reversibility: "costly_to_reverse" # Requires re-notifying all customers.
        requires_human_approval: true
        approver: founder

      exit_ad_channel:
        description: "Permanently stop advertising on a channel that is performing poorly."
        moves: [customer_acquisition_cost]
        effect_shows_in: "immediately"
        reversibility: irreversible
        requires_human_approval: false

    # --- How the Loop Decides (Policy) ---
    policy:
      rule: "Using beliefs about 'product_market_fit_score', simulate the likely impact of each available action on the 'customer_acquisition_cost'. Choose the action with the best-projected outcome that respects all constraints."
      stop_and_ask_human_when: "Projected 'customer_acquisition_cost' remains >$500 for 7 straight days OR confidence in 'product_market_fit_score' belief drops below 30/100."

    # --- Who is Involved (Stakeholders) ---
    stakeholders:
      founder:
        type: human
        what_they_lose_if_wrong: "Company capital, market reputation."
        what_they_see: [weekly_summary_report, approval_requests]
      
      acquisition_agent:
        type: agent
        what_they_lose_if_wrong: "N/A - computational resources"
        what_they_see: [beliefs, inputs] # The agent sees all its own data.

    # --- Hard Rules (Constraints) ---
    constraints:
      - "Total monthly ad spend must not exceed $50,000."
      - "Do not run more than 5 B-variant pricing tests simultaneously."

    # --- What is Ignored (Known Omissions) ---
    not_modeled:
      - "Competitor ad spend and strategy."
      - "Seasonal demand shifts."
      - "Brand perception changes from PR."
```

## 2. Multi-Agent Example

This short example shows two loops. The `market_research` loop forms a belief, which the `product_dev` loop uses as a direct input to its own process.

```yaml
loops:
  market_research:
    goal:
      steer: "clarity_on_customer_needs"
      towards: "continuous improvement"
    beliefs:
      top_customer_requests:
        description: "A ranked list of the most requested features, synthesized from feedback."
        how_formed: "LLM analysis of 'support_tickets' and 'community_forum_posts'."
        how_checked: "Monthly poll of 100 power users to validate the priority list."
    inputs:
      support_tickets:
        source: external
        # ...
      community_forum_posts:
        source: external
        # ...
    # ... other sections omitted for brevity

  product_dev:
    goal:
      steer: "features_shipped_per_sprint"
      towards: "3"
    inputs:
      feature_request_priorities:
        description: "The prioritized list of features to consider for development."
        source: internal
        from_loop: "market_research.beliefs.top_customer_requests" # This is the link
        arrives: "every 24 hours"
        informs: [sprint_backlog]
    beliefs:
      sprint_backlog:
        description: "The set of features planned for the next development sprint."
        how_formed: "Based on 'feature_request_priorities' and developer capacity estimates."
        # ...
    actions:
      commit_to_sprint:
        # ...
    # ... other sections omitted for brevity
```

## 3. Complete Key List

- `loops`: (root) A map of all loops in the file.
  - `[loop_name]`: The unique name of a single agent loop.
    - `goal`: The top-level objective of the loop.
      - `description`: Human-readable explanation of the goal.
      - `steer`: The name of the primary quantity the loop is trying to control.
      - `towards`: The target state for the steered quantity (e.g., "maximize", "less than 100").
    - `beliefs`: A map of key unobservable quantities the loop must infer.
      - `[belief_name]`:
        - `description`: What this belief represents.
        - `how_formed`: Natural language description of the model or logic used for inference.
        - `how_checked`: The process for validating this belief against reality.
    - `inputs`: A map of all data streams flowing into the loop.
      - `[input_name]`:
        - `description`: What this data represents.
        - `source`: `external` or `internal`.
        - `from_system`: (if `internal`) The name of the non-loop system generating the data.
        - `from_loop`: (if `internal`) The reference to the other loop generating data (e.g., `loop.section.name`).
        - `type`: `measured` (passively observed) or `reported` (actively submitted by an entity).
        - `reported_by`: (if `reported`) The name of the entity reporting it.
        - `arrives`: The frequency or condition of arrival (e.g., "daily", "on_event").
        - `cost`: The monetary or computational cost to acquire the data.
        - `informs`: A list of `belief` names this input helps update.
    - `actions`: A map of the actions the loop can take.
      - `[action_name]`:
        - `description`: What this action does in the real world.
        - `moves`: A list of `belief` or other quantity names this action influences.
        - `effect_shows_in`: The expected delay before the action's impact is observable.
        - `reversibility`: `reversible`, `irreversible`, or `costly_to_reverse`.
        - `requires_human_approval`: `true` or `false`.
        - `approver`: (if `true`) The `stakeholder` name required for approval.
    - `policy`: The decision-making logic of the loop.
      - `rule`: A natural-language description of how the agent chooses among actions.
      - `stop_and_ask_human_when`: A condition describing when the loop must halt and escalate.
    - `stakeholders`: A map of people or agents involved.
      - `[stakeholder_name]`:
        - `type`: `human` or `agent`.
        - `what_they_lose_if_wrong`: The real-world stakes for this stakeholder.
        - `what_they_see`: A list of inputs, beliefs, or reports visible to them.
    - `constraints`: A list of hard limits or rules that must not be violated.
    - `not_modeled`: A list of known factors the loop deliberately ignores.

## 4. The 3 Hardest Design Decisions

1.  **Natural Language vs. a Formal DSL for Rules.**
    - **The Dilemma:** Should fields like `policy.rule` and `beliefs.how_formed` use a structured, machine-parseable language, or plain English? A formal language (`rule: { type: 'optimizer', objective: 'minimize(cac)', ... }`) would be better for linting and code generation, ensuring perfect fidelity.
    - **Alternative Rejected:** A formal Domain Specific Language.
    - **Reasoning:** I chose natural language to heavily favor the primary design constraints: "a smart person understanding it in 30 seconds without a manual" and "read by humans." A formal DSL would require a manual. Crucially, the primary writer is an LLM, which is exceptionally skilled at interpreting natural language intent and generating code from it. The natural language approach makes the spec a "prompt" for the LLM generator and a "brief" for the human reader. It strikes the best balance for the specified asymmetry of the audiences.

2.  **How to Connect Everything (Explicit vs. Implicit Linking).**
    - **The Dilemma:** Should the relationships between inputs, beliefs, and actions be explicit (e.g., `informs: [belief_name]`) or implicit through nesting or convention? Implicit linking can make files shorter but also more "magical" and harder to parse, especially for the "project to a diagram" requirement.
    - **Alternative Rejected:** Implicit linking, such as nesting inputs under the beliefs they inform.
    - **Reasoning:** I chose explicit, named references (`informs`, `moves`, `approver`, `from_loop`). This structure *is* the graph. A simple parser can walk the YAML and build a directed graph of the entire system without complex heuristics. This makes linting ("is this belief ever informed by anything?"), diagramming, and multi-agent linking (`from_loop: 'other_loop.beliefs.x'`) unambiguous and robust. It prioritizes clarity over brevity, which is key for a specification format.

3.  **Separating `beliefs` from `inputs` vs. a Unified `quantities` List.**
    - **The Dilemma:** I could have had a single `quantities:` section where each item has a `source` field (`measured`, `reported`, or `inferred`). This would be structurally flatter and perhaps simpler.
    - **Alternative Rejected:** A single, unified `quantities:` list.
    - **Reasoning:** I created a top-level `beliefs` section distinct from `inputs`. This was the most important conceptual decision. The core problem statement highlighted that a major failure mode is "they track quantities nothing measures." By forcing inferred quantities into a separate `beliefs` bucket, the syntax makes them first-class citizens. This structure allows a linter to perform its most critical function with ease: iterate through every item in `beliefs` and flag any that are missing a `how_checked` field. It elevates the epistemological status of information to the top level of the syntax, directly addressing the problem's root cause.

## 5. Where the Design is Weakest

The design's primary weakness is the "double-edged sword" of using natural language for critical logic in `policy.rule` and `beliefs.how_formed`.

1.  **Ambiguity in Implementation:** The spec does not guarantee that the LLM generating the code will interpret the natural language `rule` precisely as the human reader does. A linter cannot *prove* that the generated Python code for the `policy` correctly implements the sentence "simulate the likely impact of each available action." It can only check for referential integrity (e.g., does the rule mention a belief that exists?). This semantic gap between spec and implementation is the largest source of potential error.

2.  **Limited Static Analysis:** The flexibility of string-based conditions (`towards: "less than $400"`, `stop_and_ask_human_when: "..."`) makes deep, automated analysis difficult. A linter can't easily reason about whether the loop *can ever* reach its goal or if the stop condition is mathematically sound. It's a direct trade-off for making the syntax intuitive and jargon-free.

3.  **Statefulness Over Time:** The syntax captures temporal aspects like `effect_shows_in` and `arrives`, but it lacks a formal model for representing and reasoning about time series data or the state of a variable across multiple cycles. Complex dynamic behaviors (e.g., momentum, oscillations) must be described in the natural language blocks, hiding their complexity from static analysis.