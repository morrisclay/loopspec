# Agent Loop Spec

## 1. Full example — startup customer acquisition

```yaml
# customer-acquisition.loop.yaml
# Steer cost-per-customer under $400 while building a checked belief about PMF.

loops:
  acquisition:
    purpose: >
      Acquire customers cheaply enough to survive, and notice early if the
      product itself is the real bottleneck.

    steers:
      cost_per_customer:
        keep: below 400
        unit: USD
        currently: 520          # optional starting snapshot

    believes:
      product_market_fit:
        means: "New customers stick 90 days and refer others without paid nudge"
        formed_how: >
          Weight week-4 retention 50%, trial-to-paid rate 30%,
          unsolicited referrals 20%. Ignore survey scores unless
          retention also moves.
        scored_as: 0.0–1.0
        checked_by:
          - after: 90 days
            compare: what we predicted retention would be
            against: actual_90_day_retention
            consequence: >
              If off by more than 0.15, freeze ad-spend raises until a human
              re-baselines the belief rule.

    observes:
      ad_spend_and_signups:
        every: 1 day
        costs: 0
        comes_from: ourselves      # we produced the spend; platform reports signups
        informs: [cost_per_customer]

      trial_to_paid_rate:
        every: 1 day
        costs: 0
        comes_from: ourselves
        informs: [product_market_fit, cost_per_customer]

      week4_retention:
        every: 1 week
        costs: 0
        comes_from: ourselves
        informs: [product_market_fit]

      nps_survey:
        every: 2 weeks
        costs: 2 USD per response
        comes_from: reported       # interested party, not a measurement
        reported_by: customers
        informs: [product_market_fit]
        caution: "Customers who answer are happier than those who churn silently"

      competitor_cpc_benchmark:
        every: 1 week
        costs: 0
        comes_from: outside
        informs: [cost_per_customer]

    actions:
      raise_ad_spend:
        moves: ad_spend
        by: up to +20% of current daily
        effect_shows_after: 3 days
        can_undo: yes
        needs_approval: no

      lower_ad_spend:
        moves: ad_spend
        by: down to -50% of current daily
        effect_shows_after: 3 days
        can_undo: yes
        needs_approval: no

      change_price:
        moves: price
        by: any amount in $5 steps
        effect_shows_after: 14 days
        can_undo: yes
        needs_approval: founder

      exit_channel:
        moves: channel_active
        to: false
        effect_shows_after: 0
        can_undo: no               # irreversible
        needs_approval: founder

    chooses_actions: >
      While cost_per_customer is above target, prefer lower_ad_spend unless
      product_market_fit is above 0.6 and competitor_cpc_benchmark says we
      are under-bidding — then raise_ad_spend. Propose change_price only
      when PMF has been stable 30 days and CPC is flat. Never propose
      exit_channel unless cost_per_customer > 800 for 14 days straight.

    asks_human_when:
      - cost_per_customer > 600 for 7 days
      - product_market_fit check fails (prediction off > 0.15)
      - any action with can_undo: no is the chosen move
      - belief rule itself looks wrong two checks in a row

    people:
      founder:
        loses_if_wrong: cash runway, 18-month survival odds
        sees: [weekly summary, every approval request, check failures]
      growth_agent:
        loses_if_wrong: nothing material (no wallet, no reputation surface)
        sees: [all observes, all beliefs, action outcomes]
      customers:
        loses_if_wrong: money if price rises; time if product is bad
        sees: [price, the product itself]   # not our internal beliefs

    constraints:
      - ad_spend per day must stay under 5000 USD
      - price must stay above 0
      - do not contact a customer more than twice in 7 days
      - never charge a card without an explicit checkout event

    not_modelling:
      - competitor reactions to our price changes
      - seasonal demand (Black Friday, summer lull)
      - brand/reputation effects of heavy ads
      - support-cost load from bad-fit customers
```

---

## 2. Short multi-agent example

```yaml
# growth-system.loop.yaml
# Two loops share signups and a pause_ads action.

loops:
  acquisition:
    purpose: Keep cost_per_signup under 40 USD.
    steers:
      cost_per_signup: { keep: below 40, unit: USD }
    believes:
      channel_health:
        means: "This paid channel still has headroom"
        formed_how: "CPC trend + signup volume slope over 14 days"
        checked_by:
          - after: 21 days
            compare: predicted signup volume
            against: actual_signups
            consequence: "Mark channel_health stale; acquisition asks human."
    observes:
      daily_ads:
        every: 1 day
        costs: 0
        comes_from: ourselves
        informs: [cost_per_signup, channel_health]
    actions:
      tweak_bids:
        moves: bid
        by: ±15%
        effect_shows_after: 2 days
        can_undo: yes
        needs_approval: no
      pause_ads:
        moves: ads_active
        to: false
        effect_shows_after: 0
        can_undo: yes
        needs_approval: no
    chooses_actions: "Lower bids as cost_per_signup rises; pause_ads if > 80 for 5 days."
    asks_human_when: ["channel_health check fails"]
    people:
      growth_agent: { loses_if_wrong: nothing material, sees: [all] }
    constraints: ["ad_spend per day under 3000 USD"]
    not_modelling: ["creative quality fatigue"]
    shares:
      quantities: [signups]          # published for other loops
      actions: [pause_ads]           # other loops may call this

  retention:
    purpose: Keep month-1 retention above 35%.
    steers:
      month1_retention: { keep: above 0.35, unit: ratio }
    believes:
      onboarding_quality:
        means: "New users reach the aha moment inside 48 hours"
        formed_how: "activation_event rate among users aged 1–2 days"
        checked_by:
          - after: 30 days
            compare: predicted month1_retention
            against: actual month1_retention
            consequence: "Force onboarding rethink; request pause_ads from acquisition."
    observes:
      activation_events:
        every: 1 day
        costs: 0
        comes_from: ourselves
        informs: [onboarding_quality, month1_retention]
      signups:
        every: 1 day
        costs: 0
        comes_from: ourselves       # consumed from acquisition via shares
        informs: [month1_retention]
    actions:
      redesign_onboarding:
        moves: onboarding_variant
        by: next variant in queue
        effect_shows_after: 14 days
        can_undo: yes
        needs_approval: product_lead
      request_pause_ads:             # uses a shared action owned by acquisition
        moves: ads_active
        via: acquisition.pause_ads
        effect_shows_after: 0
        can_undo: yes
        needs_approval: no
    chooses_actions: >
      If onboarding_quality < 0.5 and signups are still high, call
      request_pause_ads before flooding more users through a bad funnel.
    asks_human_when: ["onboarding_quality check fails"]
    people:
      product_lead:
        loses_if_wrong: team road-map time, retention targets
        sees: [weekly summary, approval requests]
      retention_agent:
        loses_if_wrong: nothing material
        sees: [all]
    constraints: ["do not run more than one onboarding experiment at a time"]
    not_modelling: ["email deliverability", "long-term habit formation past day 90"]
    shares:
      quantities: [month1_retention]
      actions: []
```

---

## 3. Complete key list

Top-level
- `loops` — map of named loops in this file

Per loop
- `purpose` — one-sentence plain-language intent
- `steers` — quantities the loop pushes on
  - `<quantity>.keep` — `below N` | `above N` | `between A and B`
  - `<quantity>.unit` — unit label
  - `<quantity>.currently` — optional snapshot
- `believes` — latent quantities not directly observed
  - `<belief>.means` — plain-language definition
  - `<belief>.formed_how` — rule or short prose for how evidence is combined
  - `<belief>.scored_as` — optional range/units of the belief score
  - `<belief>.checked_by[]` — calibration hooks
    - `after` — delay before checking
    - `compare` — what past belief predicted
    - `against` — the later observation
    - `consequence` — what happens on miss
- `observes` — data that actually arrives
  - `<obs>.every` — cadence
  - `<obs>.costs` — cost to obtain (number + unit in the value, or 0)
  - `<obs>.comes_from` — `outside` | `ourselves` | `reported`
  - `<obs>.reported_by` — required when `comes_from: reported`
  - `<obs>.informs` — list of steers/believes this feeds
  - `<obs>.caution` — optional warning about bias
- `actions`
  - `<act>.moves` — quantity it affects
  - `<act>.by` *or* `<act>.to` — relative change or absolute target
  - `<act>.via` — optional `otherloop.action` when using a shared action
  - `<act>.effect_shows_after` — delay until observable effect
  - `<act>.can_undo` — `yes` | `no`
  - `<act>.needs_approval` — `no` | `<person name>`
- `chooses_actions` — prose or short ruleset for action selection
- `asks_human_when` — list of stop-and-escalate conditions
- `people`
  - `<person>.loses_if_wrong` — real stakes
  - `<person>.sees` — what information actually reaches them
- `constraints` — hard rules, always on, overriding the objective
- `not_modelling` — deliberate omissions
- `shares` — multi-loop surface
  - `quantities` — names other loops may read
  - `actions` — names other loops may invoke via `via:`

That is the full vocabulary. Nothing else is reserved.

---

## 4. Three hardest design decisions

**Decision 1 — Prose rules for `chooses_actions` / `formed_how`, not a mini-language**

- *Rejected:* a structured expression DSL (`if`, `prefer`, weighted scores, operators).
- *Why:* the file is mostly written by LLMs and read by humans in 30 seconds. A DSL that both sides must nail is where specs rot and linters pretend to understand more than they do. Prose + hard structure around it (the typed fields on actions, observes, checks) gives the linter the defects it can actually catch — missing `checked_by`, irreversible action with `needs_approval: no`, `comes_from: reported` without `reported_by`, steer with no observe that `informs` it — without forcing a second language. Implementers (LangGraph, Goose, …) already have an LLM in the loop; they can compile prose into code. Catching *structural* defects is the linter’s job; catching *bad judgment in the prose* is the human’s.

**Decision 2 — `comes_from: outside | ourselves | reported` as one enum, not separate sections**

- *Rejected:* splitting into `sensors:`, `internal_metrics:`, `reports:` sections, or a free-text `source:` string.
- *Why:* the three-way distinction is load-bearing (requirements 3–5) and must be lintable. Separate sections tempt authors to mis-file things and make “which belief does this inform?” repetitive. A free string is unlintable. One field on every arrival keeps the observe list scannable as a single table and makes the reported-vs-measured distinction impossible to skip — `reported` requires `reported_by`, enforced by schema. `ourselves` vs `outside` is exactly the self-produced distinction, no jargon needed.

**Decision 3 — Multi-loop sharing via explicit `shares` + `via`, not implicit global names**

- *Rejected:* all quantities global by name across loops; or a separate top-level `bus:` of shared topics.
- *Why:* implicit globals make it impossible to see, in 30 seconds, what a loop owns vs. borrows, and they break diagram projection (every identically named node collapses). A central bus re-introduces middleware jargon and a second place to look. `shares` on the owning loop declares the surface; `via: acquisition.pause_ads` on the caller makes the edge explicit. Diagram rule writes itself: one node per loop quantity, edge labelled `shares`/`via` across loops, edge labelled `informs`/`moves` inside a loop. No layout hints required — ownership is local, coupling is declared.

---

## 5. Where this design is weakest

- **Action selection prose is unlintable for quality.** A linter can check that every action named in the prose exists, but not that the policy is coherent, safe, or stable. Two LLMs will write equally schema-valid, wildly different policies for the same loop.
- **No typed units or dimensional checks.** `costs: 2 USD per response` and `keep: below 400` are strings-with-convention. A linter cannot catch comparing dollars to ratios without a unit system — which I deliberately left out to keep the 30-second read.
- **Belief formation is not composable across loops.** `shares` moves quantities and actions, not belief rules. A retention loop cannot reuse acquisition’s PMF belief without copying it; there is no `believes_via`. That will hurt larger multi-agent files.
- **Time is underspecified.** `every: 1 day`, `effect_shows_after: 3 days`, `after: 90 days` are durations with no shared clock, timezone, or “business days vs elapsed” distinction. Real implementations will quietly disagree.
- **People and stakes are decorative to an executor.** `loses_if_wrong` is excellent for the human reader and for an auditor LLM; it does not bind the running system unless something external reads it. The spec cannot force a runtime to care who gets hurt.
- **Diagram projection of prose edges is incomplete.** Structural edges (`informs`, `moves`, `via`, `needs_approval`, `checked_by.against`) project cleanly. The policy relationships inside `chooses_actions` (“prefer X unless Y”) do not, so the diagram under-represents the real decision graph.

---

**Why this shape overall.** The asymmetry — LLMs write, humans read — means the file should look like a briefing memo with consistent headings, not like a program. Every required concept from the brief lands in exactly one place with a name you can guess without a manual. Defects the brief cares about (unmeasured steers, unchecked beliefs, irreversible actions with no gate, reported data treated as measured, missing stakes) are all schema-detectable gaps, not semantic judgements.