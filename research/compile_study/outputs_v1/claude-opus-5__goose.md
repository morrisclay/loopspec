<!-- model: anthropic/claude-opus-5  tier: strong  target: goose  finish: stop -->

Below is a runnable Goose recipe. Goose recipes are a *single-shot agent contract* (instructions + parameters + extensions + structured output), so the loop's declarative parts are re-expressed as (a) hard structure where Goose has a slot for it, and (b) an explicit operating procedure where it doesn't. Everything that lost enforcement is listed at the end.

```yaml
# customer_acquisition.goose.yaml
#
# Goose recipe implementation of the customer_acquisition loop (v1 spec).
# Goose executes ONE pass. "runs: weekly" is not in this file; see the schedule
# line in `instructions` and `## did not survive`.
#
#   goose run --recipe customer_acquisition.goose.yaml \
#     --params committed_runway_usd=850000 --params run_date=2025-06-09
#
#   # cadence, since the recipe cannot hold it:
#   goose schedule add --id customer_acquisition_weekly \
#     --cron "0 9 * * MON" --recipe customer_acquisition.goose.yaml

version: 1.0.0
title: Customer Acquisition Loop (one weekly pass)
description: >-
  One pass of the customer_acquisition decision loop. Reads this week's
  observations, updates two beliefs, evaluates two goals against thresholds,
  proposes at most the actions the rules allow, and escalates to the founder
  whenever an escalation trigger fires or an irreversible move is chosen.
  Emits a machine-readable run record and appends to the loop journal.

parameters:
  - key: state_dir
    input_type: string
    requirement: optional
    default: ".loop/customer_acquisition"
    description: >-
      Loop memory root. Expected layout:
      observations/ (stripe.json, ad_platform.json, customer_interviews.md,
      board_sentiment.md), beliefs.json, journal.md, last_run.json.

  - key: run_date
    input_type: string
    requirement: optional
    default: "today"
    description: ISO date for this pass (the loop is nominally weekly).

  - key: committed_runway_usd
    input_type: number
    requirement: required
    description: >-
      Committed runway in USD. Hard ceiling for the `never` invariant:
      proposed spend must never exceed this.

  - key: cost_per_customer_limit
    input_type: number
    requirement: optional
    default: 400
    description: goal.cost_per_customer.keep = below this (USD).

  - key: payback_months_limit
    input_type: number
    requirement: optional
    default: 12
    description: goal.payback_months.keep = below this (months).

  - key: pmf_escalation_floor
    input_type: number
    requirement: optional
    default: 0.4
    description: Escalate to founder if product_market_fit falls below this.

  - key: cpc_alarm_level
    input_type: number
    requirement: optional
    default: 600
    description: Escalate if cost_per_customer stays above this for 14 days.

  - key: dry_run
    input_type: boolean
    requirement: optional
    default: true
    description: >-
      true = propose only, write no external change. Goose has no approval
      gate; dry_run is the stand-in for needs_approval: founder.

extensions:
  - type: builtin
    name: developer
    display_name: Developer
    timeout: 300
    bundled: true

activities:
  - Read this week's observations and flag stale or missing feeds
  - Update product_market_fit and channel_saturation
  - Check cost_per_customer and payback_months against their limits
  - Evaluate the two decision rules
  - Check the never-invariant against committed runway
  - Report escalations and open gaps to the founder

settings:
  temperature: 0.1

instructions: |
  You are the `growth_agent` role in the `customer_acquisition` loop.
  You are an agent, not a human. You lose nothing if you are wrong; the founder
  loses the company. Act accordingly: propose, escalate, never quietly commit.

  Cadence: this loop is meant to run WEEKLY. This recipe is one pass. If the
  journal at {{ state_dir }}/journal.md shows the last pass was more than 10
  days ago, say so in `notes` — the loop has been skipped, and belief freshness
  is suspect.

  Run date: {{ run_date }}. Dry run: {{ dry_run }}.

  ## 1. Goals (both are "keep below")

  | goal              | keep below                    | unit   | derived from                |
  |-------------------|-------------------------------|--------|-----------------------------|
  | cost_per_customer | {{ cost_per_customer_limit }} | USD    | ad_spend / new_customers    |
  | payback_months    | {{ payback_months_limit }}    | months | (stated in inputs)          |

  Compute cost_per_customer as ad_spend / new_customers for the trailing period
  in {{ state_dir }}/observations/stripe.json plus ad platform spend. If either
  input is missing, DO NOT invent a number: mark the goal reading
  `status: unknown` and treat every rule that depends on it as not firing.

  ## 2. Beliefs

  ### product_market_fit
  - question: "If we keep buying customers like this month's, will they stay?"
  - fed by: customer_interviews, stripe
  - method: bayesian. Maintain a prior in {{ state_dir }}/beliefs.json as
    {mean, interval_low, interval_high, n_observations, last_updated}. Update by
    moving the mean toward this week's evidence in proportion to evidence
    strength (interview count and cohort size), and WIDEN the interval when
    evidence is thin. You have no inference engine; show your arithmetic in
    `reasoning` so a human can audit or overrule it. Never report a point
    estimate without the interval.
  - explains: cost_per_customer. When cost_per_customer moves, this belief is
    the first candidate explanation.
  - settled_by: "a cohort retains above 80% at month 6". If stripe data shows a
    cohort at month 6 with retention above 80%, mark this belief `settled: true`
    and stop updating it from interviews.
  - known_bias: reads HIGH when volume is low, because interviews only reach
    people who reply. If interview count this week is low (<10) or reply rate is
    unknown, apply a downward adjustment to the mean and say by how much.
  - checked_by: NOTHING. This belief has no independent check. It steers the
    largest goal in the loop and nothing outside the loop can falsify it. Emit
    this as an open gap on EVERY run; do not let it go quiet.

  ### channel_saturation
  - question: "Can this channel absorb more money before cost climbs?"
  - fed by: ad_platform
  - method: judgement. It is a judgement call, not a measurement. State it as
    a stance with a confidence word, not a number pretending to be data.
  - checked_by: monthly_spend_vs_cost_review. If the journal shows no
    spend-vs-cost review in the last 35 days, the check is overdue: report it in
    `overdue_checks` and lower your confidence in this belief.

  ## 3. Observations

  | source              | informs            | every   | origin    | how      | reported_by | cost |
  |---------------------|--------------------|---------|-----------|----------|-------------|------|
  | stripe              | cost_per_customer  | daily   | outside   | measured | -           | -    |
  | ad_platform         | channel_saturation | daily   | ourselves | measured | -           | -    |
  | customer_interviews | product_market_fit | weekly  | outside   | reported | customers   | high |
  | board_sentiment     | (nothing)          | monthly | outside   | reported | investor    | -    |

  Read each from {{ state_dir }}/observations/. Rules that follow from the
  columns, and that you must actually apply:

  - origin: ourselves (ad_platform) — this data exists because WE caused the
    spend. Do not treat rising spend capacity as independent evidence that the
    channel is healthy; it is partly our own footprint.
  - how: reported + reported_by: customers (customer_interviews) — customers
    CHOOSE what to tell us. This is testimony, not measurement. Never average it
    with stripe numbers as if it were the same kind of fact.
  - cost: high (customer_interviews) — do not propose collecting more interviews
    casually. If you want more, say what decision the extra interviews would
    change.
  - board_sentiment informs NOTHING. It is collected monthly at the investor's
    word and wired to no belief and no goal. Report it in `open_gaps` every run:
    either connect it to a belief or stop collecting it. Do NOT let it leak into
    your reasoning about pmf or saturation through the back door.
  - Staleness: if a daily feed is more than 3 days old, or the weekly interview
    file is more than 10 days old, mark it stale and downgrade every belief that
    depends on it.

  ## 4. Actions

  | action          | moves             | can_undo | effect_after | consumes | needs_approval |
  |-----------------|-------------------|----------|--------------|----------|----------------|
  | increase_budget | cost_per_customer | yes      | 2w           | runway   | -              |
  | change_pricing  | payback_months    | costly   | 4w           | -        | founder        |
  | exit_channel    | cost_per_customer | no       | -            | -        | NONE DECLARED  |

  - effect_after is a LAG, not a delay before acting. If the journal shows
    increase_budget within the last 2 weeks, or change_pricing within the last
    4 weeks, the effect has not landed yet: do not re-fire the same action and
    do not read the unchanged metric as failure. Say "effect pending, fired
    <date>".
  - increase_budget consumes runway. Every proposal must state the USD delta and
    the resulting total committed spend.
  - change_pricing can_undo: costly — reversing it costs real trust and revenue.
    It requires founder approval. You may only PROPOSE it.
  - exit_channel can_undo: no, and NO approval is declared for it. That is a
    hole in the spec. Treat it as founder-approval-required anyway, escalate it,
    and report the missing needs_approval in `open_gaps` on every run.

  ## 5. Decision rules (evaluate in order, on this pass's readings)

  1. IF cost_per_customer below {{ cost_per_customer_limit }}
     AND product_market_fit above 0.6  -> increase_budget
  2. IF payback_months above {{ payback_months_limit }} -> change_pricing

  A rule with an `unknown` input does not fire. Record each rule's evaluation
  (fired / not fired / blocked-unknown) with the numbers used.

  ## 6. Escalate to the human (stop, do not act)

  Raise an escalation and set `awaiting_human: true` if ANY of these hold:
  - product_market_fit falls below {{ pmf_escalation_floor }}
  - cost_per_customer stays above {{ cpc_alarm_level }} for 14 days
    (check the journal history, not just today's reading)
  - any action whose can_undo is `no` becomes the chosen move
    (today that means exit_channel)
  Also escalate whenever a proposal needs_approval: founder (change_pricing).

  When awaiting_human is true you take NO external action this pass, regardless
  of dry_run. Write the run record and stop.

  ## 7. Never (hard invariant)

  "spend exceeds committed runway." Committed runway is
  {{ committed_runway_usd }} USD. Before emitting any proposal, sum existing
  committed spend plus the proposed delta. If the total would exceed
  {{ committed_runway_usd }}, DROP the proposal, set
  `invariant_never_spend_exceeds_committed_runway` to "would_breach", and
  escalate. There is no override, no approval that unlocks it, and no partial
  version of it.

  ## 8. Not modelling

  competitor_response and seasonality are explicitly OUT of this loop. Do not
  explain movements with either one. If you believe one of them is actually the
  dominant driver this week, do not model it — put it in `out_of_scope_pressure`
  so a human can decide whether the loop's scope was wrong.

  ## 9. People

  - founder — human. Loses if wrong: the company (runway, and 18-month survival
    odds). Sees: cost_per_customer, product_market_fit. May decide: pricing, and
    anything that cannot be undone.
  - growth_agent — you. Agent. Loses nothing. Sees: cost_per_customer,
    product_market_fit, channel_saturation.
  - investor — human. Loses if wrong: a position in the fund. Sees NOTHING.
    Accountable and blind. Report this in `open_gaps` every run: the investor
    supplies board_sentiment monthly and is shown no goal and no belief in
    return.

  Goose cannot enforce per-person visibility. Honour it in the OUTPUT: put
  founder-visible material in `founder_briefing` and limit it to
  cost_per_customer and product_market_fit. channel_saturation stays in the
  agent-only section.

  ## 10. Write-back

  Always, even when escalating:
  - overwrite {{ state_dir }}/beliefs.json with updated belief state
  - overwrite {{ state_dir }}/last_run.json with the structured response
  - append a dated entry to {{ state_dir }}/journal.md: readings, rule
    evaluations, actions proposed/taken, escalations, open gaps
  Create {{ state_dir }} and subdirectories if absent. If an observation file is
  missing, note it — do not create a placeholder with fabricated numbers.

prompt: |
  Run one pass of the customer_acquisition loop for {{ run_date }}.

  1. Read {{ state_dir }}/beliefs.json and the tail of
     {{ state_dir }}/journal.md for history (last actions, cost_per_customer
     streak, last spend-vs-cost review).
  2. Read every file in {{ state_dir }}/observations/ and record freshness.
  3. Update product_market_fit (bayesian, with interval, with the low-volume
     downward adjustment) and channel_saturation (judgement).
  4. Compute cost_per_customer and read payback_months; compare to limits.
  5. Evaluate the two rules and the escalation triggers.
  6. Check the never-invariant against {{ committed_runway_usd }} USD.
  7. Write beliefs.json, last_run.json, and the journal entry.
  8. Return the structured run record. List every open gap: pmf has no
     checked_by, exit_channel has no needs_approval, board_sentiment informs
     nothing, the investor sees nothing.

response:
  json_schema:
    type: object
    additionalProperties: false
    required:
      - run_date
      - goals
      - beliefs
      - observations
      - rule_evaluations
      - proposals
      - escalations
      - awaiting_human
      - invariant_never_spend_exceeds_committed_runway
      - open_gaps
      - overdue_checks
      - out_of_scope_pressure
      - founder_briefing
    properties:
      run_date:
        type: string
      goals:
        type: array
        items:
          type: object
          additionalProperties: false
          required: [name, value, unit, limit, direction, status]
          properties:
            name:
              type: string
              enum: [cost_per_customer, payback_months]
            value: { type: ["number", "null"] }
            unit: { type: string }
            limit: { type: number }
            direction: { type: string, enum: [keep_below] }
            status: { type: string, enum: [within, breached, unknown] }
            inputs_used: { type: string }
      beliefs:
        type: array
        items:
          type: object
          additionalProperties: false
          required: [name, method, stance, checked_by, reasoning]
          properties:
            name: { type: string, enum: [product_market_fit, channel_saturation] }
            method: { type: string, enum: [bayesian, judgement] }
            stance: { type: string }
            mean: { type: ["number", "null"] }
            interval_low: { type: ["number", "null"] }
            interval_high: { type: ["number", "null"] }
            bias_adjustment_applied: { type: ["string", "null"] }
            settled: { type: boolean }
            settled_by_met: { type: boolean }
            checked_by: { type: ["string", "null"] }
            unchecked: { type: boolean }
            evidence_quality: { type: string, enum: [measured, reported, mixed, stale, absent] }
            reasoning: { type: string }
      observations:
        type: array
        items:
          type: object
          additionalProperties: false
          required: [source, informs, origin, how, freshness]
          properties:
            source: { type: string }
            informs: { type: ["string", "null"] }
            origin: { type: string, enum: [outside, ourselves] }
            how: { type: string, enum: [measured, reported] }
            reported_by: { type: ["string", "null"] }
            cost: { type: ["string", "null"] }
            freshness: { type: string, enum: [fresh, stale, missing] }
            note: { type: ["string", "null"] }
      rule_evaluations:
        type: array
        items:
          type: object
          additionalProperties: false
          required: [rule, outcome, numbers_used]
          properties:
            rule: { type: string }
            outcome: { type: string, enum: [fired, not_fired, blocked_unknown, effect_pending] }
            numbers_used: { type: string }
      proposals:
        type: array
        items:
          type: object
          additionalProperties: false
          required: [action, moves, can_undo, needs_approval, status, rationale]
          properties:
            action: { type: string, enum: [increase_budget, change_pricing, exit_channel] }
            moves: { type: string }
            can_undo: { type: string, enum: ["yes", "costly", "no"] }
            effect_after: { type: ["string", "null"] }
            consumes: { type: ["string", "null"] }
            needs_approval: { type: ["string", "null"] }
            spend_delta_usd: { type: ["number", "null"] }
            resulting_total_committed_usd: { type: ["number", "null"] }
            status: { type: string, enum: [proposed, awaiting_founder_approval, dropped_invariant, taken, withheld_dry_run] }
            rationale: { type: string }
      escalations:
        type: array
        items:
          type: object
          additionalProperties: false
          required: [trigger, detail]
          properties:
            trigger: { type: string }
            detail: { type: string }
      awaiting_human: { type: boolean }
      invariant_never_spend_exceeds_committed_runway:
        type: string
        enum: [held, would_breach, uncheckable]
      open_gaps:
        type: array
        items: { type: string }
      overdue_checks:
        type: array
        items: { type: string }
      out_of_scope_pressure:
        type: array
        items: { type: string }
      founder_briefing:
        type: object
        additionalProperties: false
        required: [cost_per_customer, product_market_fit, decision_needed]
        properties:
          cost_per_customer: { type: string }
          product_market_fit: { type: string }
          decision_needed: { type: string }
      notes:
        type: array
        items: { type: string }

retry:
  max_retries: 2
  timeout_seconds: 900
  checks:
    - type: shell
      command: >-
        test -f "{{ state_dir }}/last_run.json" &&
        grep -q "invariant_never_spend_exceeds_committed_runway"
        "{{ state_dir }}/last_run.json"
    - type: shell
      command: >-
        ! grep -q '"invariant_never_spend_exceeds_committed_runway": *"would_breach"'
        "{{ state_dir }}/last_run.json" ||
        grep -q '"awaiting_human": *true' "{{ state_dir }}/last_run.json"
  on_failure: >-
    echo "customer_acquisition pass incomplete or invariant breach not escalated;
    re-run must write {{ state_dir }}/last_run.json with an explicit invariant
    status and, if would_breach, awaiting_human=true"
```

## did not survive

Each item is something the spec states and the Goose recipe format cannot hold as structure. Where I could preserve intent as prose or output shape, I say so — prose is not enforcement.

1. **`runs: weekly`** — no cadence field exists in a recipe. A recipe is one invocation. Cadence moved to a comment showing `goose schedule add --cron "0 9 * * MON"`, plus an instruction to notice from the journal if a pass was skipped. If nobody registers the schedule, the loop simply never runs and the recipe cannot tell.

2. **Loop identity and state across runs** — there is no `loop:` construct and no persistent memory between invocations. Emulated with files under `state_dir` written by the `developer` extension. A missing, hand-edited, or partially written `beliefs.json`/`journal.md` degrades silently; the format offers no schema check on the loop's own state.

3. **`how: bayesian`** — Goose has no inference engine. Reduced to an instruction to keep `{mean, interval, n}` in JSON and update it by hand-waved proportional reasoning, with the arithmetic shown for audit. Nothing enforces that the posterior is actually Bayesian, monotone in evidence, or even numerically consistent between runs.

4. **`checked_by: monthly_spend_vs_cost_review`** — not resolvable to anything executable. There is no registry of checks and no way to name a sibling procedure. Represented as "if the journal shows no such review in 35 days, report it overdue". The review itself is unimplemented; a real version would be a separate recipe plus a schedule.

5. **`settled_by: "a cohort retains above 80% at month 6"`** — no terminal-condition construct. A belief cannot be permanently closed in Goose. Implemented as a `settled` boolean the agent is told to set and told to respect on later passes; nothing prevents a later pass from re-opening it.

6. **`known_bias`** — no first-class slot. Kept as an instruction to apply a downward adjustment when interview volume is low, and a `bias_adjustment_applied` field in the output. The size of the correction is at the model's discretion; the spec's bias is documented, not corrected.

7. **`needs_approval: founder`** — Goose has no approval gate, no second-actor confirmation, and no way to block a tool call pending a human. Approximated three ways, all soft: `dry_run: true` by default, `status: awaiting_founder_approval` in the output, and an instruction to take no external action when `awaiting_human` is true. A model that ignores the instruction is not stopped by the runtime.

8. **`can_undo` semantics (`yes` / `costly` / `no`)** — carried as an enum in the response schema and as prose, but reversibility has no operational meaning to Goose: there is no compensating-action mechanism and no rollback. `costly` in particular is pure annotation.

9. **`effect_after: 2w` / `4w`** — no timers, no cooldowns, no per-action rate limits. Turned into "read the journal, and if the action fired inside the window, mark the effect pending and don't re-fire". This depends entirely on the journal being intact and read correctly.

10. **`exit_channel` missing `needs_approval`** — the spec's deliberate hole. Goose has no linter, so I hard-coded the finding: treat it as founder-approval-required, escalate it, and re-report the gap every run. The compensating rule lives in prose and will drift from the spec if the spec changes.

11. **The linter itself** — the spec's comments ("the linter says so, and that is the point") describe a static check over the loop file. Nothing in Goose reads a loop spec. All three intended findings — `product_market_fit` has no `checked_by`, `exit_channel` has no `needs_approval`, `board_sentiment` informs nothing — plus the investor-sees-nothing observation are re-encoded as literal strings the agent must emit in `open_gaps`. They are now duplicated text, not derived facts.

12. **`observes.*` typing (`origin`, `how`, `reported_by`, `cost`, `every`)** — no observation schema exists. Preserved as a table in `instructions` and as enums in the response schema, with the behavioural consequences spelled out (self-caused data isn't independent evidence; customer testimony isn't measurement; high-cost collection needs a justifying decision). None of that is checked; the model can conflate a reported source with a measured one and the run still succeeds.

13. **`board_sentiment` with no `informs`** — the format has no way to represent a dangling edge, so it survives only as an instruction to keep reporting it as a gap and to keep it out of the reasoning. There is no mechanism that actually prevents an unwired observation from influencing a belief.

14. **`people.*.sees`** — Goose has no identities, no per-actor views, and no access control. One session sees everything. Reduced to an output convention: a `founder_briefing` object restricted to `cost_per_customer` and `product_market_fit`, with `channel_saturation` kept outside it. Whoever runs the recipe sees the whole transcript regardless.

15. **`loses_if_wrong`** — no representation at all. Kept as text in `instructions` ("you lose nothing; the founder loses the company") to shape caution. Asymmetric stakes are not something the runtime can weigh.

16. **`may_decide: pricing, and anything that cannot be undone`** — no decision-rights model. Prose only, and it is prose in a natural-language clause the format cannot parse into a permission check.

17. **`investor` role** — appears nowhere executable. The investor supplies `board_sentiment` (a file someone drops in) and sees nothing. The accountable-and-blind condition survives only as a recurring `open_gaps` string.

18. **`never: spend exceeds committed runway`** — no hard invariant construct, no pre-tool-call guard. Implemented as (a) a required `committed_runway_usd` parameter, (b) an instruction to sum before proposing and drop the proposal on breach, (c) a `retry.checks` shell assertion that a `would_breach` status is accompanied by `awaiting_human: true`. All post-hoc: the check fires after the pass, not before spend.

19. **Rule ordering and "at most one action"** — `when:` is an ordered list; Goose has no rule engine. Order is prose. The spec never says whether both rules may fire in one pass, so I let both produce proposals and escalate individually; that is my choice, not the spec's.

20. **`asks_human_when` as a runtime interrupt** — Goose cannot pause mid-run and wait for a human. The triggers become escalation records plus `awaiting_human: true` plus an instruction to stop acting. "Stops and asks" degrades to "finishes, and says it should have asked".

21. **`cost_per_customer stays above 600 for 14 days`** — requires a time series. There is no window or streak primitive; it depends on the agent correctly reading a 14-day history out of a Markdown journal it wrote itself. Fragile.

22. **`goal.*.from: [ad_spend, new_customers]`** — no dependency graph, so no automatic invalidation when an input is stale or missing. Substituted by an instruction to emit `status: unknown` and block dependent rules. `payback_months` has no `from:` in the spec at all, so its value has no declared provenance and here arrives as an ungrounded input.

23. **`beliefs.product_market_fit.explains: cost_per_customer`** — no causal link type. Reduced to "when cost_per_customer moves, consider this belief first".

24. **Real data sources** — `stripe` and `ad_platform` are named as feeds. Goose has no builtin extension for either, and I will not ship stdio MCP entries pointing at servers that may not exist. Substituted with file drops in `state_dir/observations/`. Wiring genuine Stripe / ad-platform MCP servers is left undone; until then every "measured" observation is really a file someone placed there.

25. **`not_modelling: [competitor_response, seasonality]`** — no scope-exclusion construct. Prose instruction not to explain movements with either, plus an `out_of_scope_pressure` field so the agent can flag when the exclusion looks wrong. Nothing prevents the exclusion being violated in reasoning.

26. **Units** — `unit: USD` and months survive as strings in the schema. No dimensional checking; a months value could be compared against a USD limit and nothing would object.