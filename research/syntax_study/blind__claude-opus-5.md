# Loop Spec v1

A single YAML file. Sections appear in a fixed order that mirrors the loop itself: **goal → beliefs → data → actions → deciding → stop_and_ask → who → never → not_modelled**. Nothing is nested more than three levels deep. Every cross-reference is a bare name declared elsewhere in the file, which is what makes the diagram fall out for free.

Two rules drive the whole design:

- **Silence is illegal.** Every key that a lazy author would omit is required. If the answer is "nothing", you write `nothing` *and a reason*. `checked_by: nothing` is legal; a missing `checked_by` is a lint error. This is the single most important accommodation for LLM authors.
- **Values are constrained prose.** Only a handful of fields are machine-parsed (`target`, `every`, `shows_up_after`, `undo`, `approval`, `kind`). Everything else is a sentence, because a human reading it for 30 seconds needs sentences.

---

## 1. Flagship example: a startup's customer acquisition loop

```yaml
spec: loop/v1
file: seedco-growth
one_liner: >
  Buy customers for under $400 without lying to ourselves about whether
  the customers we buy actually fit the product.

plumbing:
  beliefs_live_in: postgres table `agent_beliefs` (one row per belief per refresh, never updated in place)
  log: every observation, belief change, rule fired, and action taken → S3 + Slack #growth-agent-log
  humans_reached_via: Slack DM to @nadia @tom, escalating to SMS after 4h
  agent_may_not_edit: this file (git, PR requires a founder review)

loops:
  - loop: customer_acquisition
    runs: every 6 hours
    run_by: LLM agent with tool access (ads APIs read/write, warehouse read-only)
    in_one_line: >
      Watch acquisition cost per channel, guess whether these customers fit the
      product, move ad budget freely, and escalate anything that touches price
      or kills a channel.

    # ── 1. What we're steering ─────────────────────────────────────────
    goal:
      quantity: cost_per_new_customer
      plain: 28-day ad spend ÷ signups that reached activation, blended across channels
      target: "<= 400 USD"
      window: rolling 28 days
      measured_by: [ad_spend, activated_signups]
      not_at_the_cost_of:
        - "activated_signups stays >= 40 per week — do not buy the number down by shrinking spend"
        - "week4_retention does not fall below 55%"
      review_target_every: quarter, with founders

    # ── 2. What we believe but cannot see ──────────────────────────────
    beliefs:
      - belief: product_market_fit
        question: "If we keep buying customers like this month's, will they stay?"
        stated_as: score 0.0–1.0, plus confidence 0.0–1.0
        formed_from: [activated_signups, week4_retention, referral_rate, churn_interview_notes]
        how: >
          Weekly, the agent reads the four inputs plus last week's score and reasoning,
          and outputs {score, confidence, one paragraph, which input moved it}.
          It may not move the score more than 0.15 in a week without naming a cause.
          Confidence must drop if churn_interview_notes count < 3 that week.
        refreshed: every Monday 09:00
        checked_by:
          compare: the score recorded 90 days ago
          against: week12_retention of the cohort bought in that same week
          every: month
          passes_if: "high-score weeks retained better than low-score weeks, in 3 of the last 4 comparisons"
          on_fail: stop_and_ask, and freeze exit_channel until re-checked
        known_bias: "reads high when volume is low — churn interviews only reach people who answer the phone"

      - belief: channel_headroom
        question: "Can this channel absorb more money before cost per customer climbs?"
        stated_as: per channel — room | tight | saturated
        formed_from: [ad_spend, attributed_conversions, our_own_budget_changes]
        how: >
          Fit cost-per-customer against daily spend over the last 60 days per channel.
          Label saturated if the last 20% of spend cost >1.5x the first 20%.
        refreshed: daily
        checked_by:
          compare: last month's "room" labels
          against: what actually happened to cost per customer after we added budget there
          every: month
          passes_if: "channels labelled room did not degrade more than channels labelled tight"
          on_fail: stop_and_ask; treat all channels as tight until re-checked

    # ── 3./4./5. What actually arrives ─────────────────────────────────
    data:
      - data: ad_spend
        from: Google Ads + Meta APIs
        kind: measured
        every: hourly
        costs: free; ~2 min of agent time per run
        feeds: [cost_per_new_customer, channel_headroom]

      - data: activated_signups
        from: warehouse model `signup_activation`
        kind: measured
        every: hourly, lagging 24h
        costs: free
        feeds: [cost_per_new_customer, product_market_fit]
        watch_out: "activation definition changed 2024-11; cohorts before that are not comparable"

      - data: week4_retention
        from: warehouse model `cohort_retention`
        kind: measured
        every: weekly
        costs: free
        feeds: [product_market_fit]

      - data: referral_rate
        from: warehouse, invite events
        kind: measured
        every: weekly
        costs: free
        feeds: [product_market_fit]

      - data: churn_interview_notes
        from: account executives, after churn calls
        kind: reported
        reported_by: account executives
        they_gain_if_wrong: "AEs are paid on closed-won; framing churn as 'wrong fit' rather than 'wrong pitch' protects their pipeline"
        cross_check: "compare the stated reason against the account's actual product usage in its last 14 days"
        every: ad hoc, roughly 5 per week
        costs: 20 min of a human per interview, plus one LLM summarise call
        feeds: [product_market_fit]

      - data: attributed_conversions
        from: Meta and Google attribution
        kind: reported
        reported_by: the ad platforms we are deciding whether to keep paying
        they_gain_if_wrong: "over-claiming credit makes us raise their budget"
        cross_check: geo holdout test every 6 weeks; warehouse signups are the tiebreaker
        every: daily
        costs: free
        feeds: [channel_headroom]

      - data: our_own_budget_changes
        from: this loop's own shift_ad_budget actions
        kind: ours
        every: on every action
        costs: free
        feeds: [channel_headroom]
        watch_out: >
          Self-caused. The cost curve moves because we bid, not because the market
          moved. Never read this as outside-world evidence about demand.

      - data: current_price
        from: revenue_loop
        kind: ours
        every: on change
        costs: free
        feeds: [cost_per_new_customer, product_market_fit]

    # ── 6. Levers ──────────────────────────────────────────────────────
    actions:
      - action: shift_ad_budget
        does: move up to 20% of weekly budget between channels already running
        moves: cost_per_new_customer
        hoped_effect: down 3–10%
        shows_up_after: 3–7 days for direction, 28 days for the real number
        undo: yes
        undo_note: budgets revert instantly; money already spent does not come back
        approval: not needed
        costs: the spend itself
        tool: POST /ads/budget {channel, weekly_usd}

      - action: pause_channel
        does: set a channel's budget to zero, keep the account and creative
        moves: cost_per_new_customer
        hoped_effect: down, at the cost of volume
        shows_up_after: 1–3 days
        undo: yes
        undo_note: re-enabling costs ~3 days of relearning
        approval: not needed
        costs: lost signups from that channel
        tool: POST /ads/budget {channel, weekly_usd: 0}

      - action: change_price
        does: change list price for new customers
        moves: [cost_per_new_customer, product_market_fit]
        hoped_effect: lower price → more signups, worse fit; higher price → the reverse
        shows_up_after: 14–30 days
        undo: partly
        undo_note: list price can revert, but customers who signed at the old price keep it forever
        approval: founders — one of two, in Slack; request expires in 48h
        owned_by: revenue_loop        # this loop can only request it
        costs: free to execute, expensive to be wrong
        tool: revenue_loop.request(change_price, {new_price, reasoning})

      - action: exit_channel
        does: close the ad account, delete audiences and creative library
        moves: cost_per_new_customer
        hoped_effect: down 10–20% blended
        shows_up_after: 28 days
        undo: no
        undo_note: >
          Account history, learned audiences and creative library are gone.
          Re-entry takes ~6 weeks and starts at worse CPMs. This is the one
          action in this file that cannot be walked back.
        approval: both founders, plus a written memo naming the evidence
        costs: irreversible loss of a demand source
        tool: POST /ads/account/close {channel}  — gated behind a human token the agent does not hold

    # ── 7a. How it chooses ─────────────────────────────────────────────
    deciding:
      first_match_wins:
        - when: "product_market_fit.confidence < 0.5"
          do: stop_and_ask
          why: "cheap customers of unknown value is the failure we most fear"

        - when: "any checked_by is failing"
          do: stop_and_ask
          why: "our beliefs are not tracking reality; acting on them is guessing"

        - when: "cost_per_new_customer > 400 for 14 days AND activated_signups >= 40/week"
          do: shift_ad_budget away from the worst channel, max 20%
          why: "we have volume slack, so trim cost first"

        - when: "cost_per_new_customer > 400 for 14 days AND activated_signups < 40/week"
          do: stop_and_