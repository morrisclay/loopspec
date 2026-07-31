<!-- model: anthropic/claude-opus-5  tier: strong  target: goose  finish: stop -->

```yaml
# Goose recipe — implementation of loop `customer_acquisition`
#
# Fidelity note: a Goose recipe is a one-shot agent invocation with a prompt,
# tools, an optional output schema, and an optional post-run shell check.
# It has no scheduler field, no typed graph, no estimator, no resource ledger,
# no approval gate, and no party/ACL model. Everything in the loop spec that is
# not "text the model reads" or "a shell command that runs after" is degraded
# below. See `## did not survive` at the bottom.
#
# Cadence (`every: weekly`) is not part of this file. Install it with:
#   goose schedule add --id customer-acquisition-weekly \
#     --cron "0 9 * * 1" --recipe recipes/customer_acquisition.yaml

version: 1.0.0
title: Customer Acquisition Loop (weekly tick)
description: >-
  One tick of the customer_acquisition regulation loop: read the observation
  sources, re-estimate product_market_fit and channel_saturation, evaluate the
  regulated variables cac and payback_months against target, and emit gated
  action proposals + escalations. Proposes; never executes an approval-gated or
  irreversible act.

author:
  contact: growth_agent (see `parties` in instructions)

settings:
  temperature: 0.1

parameters:
  # --- regulated variables: targets ---
  - key: cac_target
    input_type: number
    requirement: optional
    default: 400
    description: "regulates.cac.target — CAC must stay < this (USD)."
  - key: payback_target_months
    input_type: number
    requirement: optional
    default: 12
    description: "regulates.payback_months.target — payback must stay < this."

  # --- gate thresholds from `when` ---
  - key: pmf_go_threshold
    input_type: number
    requirement: optional
    default: 0.6
    description: "product_market_fit above this + cac in band => propose increase_budget."
  - key: pmf_escalate_threshold
    input_type: number
    requirement: optional
    default: 0.4
    description: "product_market_fit below this => escalate to founder."

  # --- never clause input (no resource ledger exists; must be supplied) ---
  - key: committed_runway_usd
    input_type: number
    requirement: required
    description: >-
      never: "spend exceeds committed runway". Total spend still committed and
      available. Any proposal whose incremental spend exceeds this is forbidden.

  # --- observation sources: paths/commands, since `observes` has no runtime ---
  - key: stripe_source
    input_type: string
    requirement: optional
    default: "data/stripe/latest.csv"
    description: "observes.stripe (measures cac; spec cadence daily) — file or shell command."
  - key: ad_platform_source
    input_type: string
    requirement: optional
    default: "data/ads/latest.csv"
    description: "observes.ad_platform (measures channel_saturation; spec cadence daily)."
  - key: interviews_source
    input_type: string
    requirement: optional
    default: "data/interviews/"
    description: "observes.customer_interviews (measures product_market_fit; weekly; cost: high)."
  - key: board_sentiment_source
    input_type: string
    requirement: optional
    default: "data/board/latest.md"
    description: "observes.board_sentiment (monthly; asserted_by investor; measures nothing)."

  # --- weak stand-in for `approval: founder` ---
  - key: founder_approval_token
    input_type: string
    requirement: optional
    default: "none"
    description: >-
      Pre-authorisation for acts marked `approval: founder`. Must literally be
      "approved:change_pricing" (etc.) to allow execution. Default "none" means
      the recipe may only PROPOSE. This is a pre-run flag, not a real gate.

  - key: allow_execution
    input_type: string
    requirement: optional
    default: "false"
    description: "If not \"true\", the run is analysis-only for every act."

  - key: state_dir
    input_type: string
    requirement: optional
    default: ".loop/customer_acquisition"
    description: "Where this tick writes latest.json / history, so the next tick can read it."

extensions:
  - type: builtin
    name: developer
    display_name: Developer
    timeout: 900
    bundled: true

activities:
  - "Run this week's customer_acquisition tick"
  - "Show CAC and payback vs target"
  - "Why was increase_budget not proposed?"
  - "Lint the loop: which estimates are uncalibrated?"

instructions: |
  You are the `growth_agent` party of the loop `customer_acquisition`.
  You bear NOTHING. The founder bears the company; the investor bears a position
  in the fund. Because you bear nothing, you may not commit spend, may not take
  an irreversible act, and may not decide on the founder's behalf. You produce
  measurements, estimates, gate evaluations, and proposals.

  ## Regulated variables (what the loop is holding steady)
  - cac            — target: < {{ cac_target }}. Computed from ad_spend and new_customers.
                     Compute it yourself as ad_spend / new_customers over the window;
                     do not accept a pre-computed CAC from a dashboard without
                     recomputing, and report both if they disagree.
  - payback_months — target: < {{ payback_target_months }}.

  ## Estimates (latent; never observed directly)
  - product_market_fit
      from: customer_interviews, stripe
      method: bayesian — you have no inference engine. Do this explicitly and
        transparently instead: state the prior you are carrying (read
        {{ state_dir }}/latest.json for last tick's posterior; if absent use
        Beta-ish 0.5 ± 0.2), state each piece of evidence and the direction and
        rough strength of the update, then state the posterior as a point
        estimate in [0,1] plus an interval. Show the arithmetic. Do not
        pretend to precision you did not derive.
      explains: cac — if cac moves, product_market_fit is the first candidate
        explanation. Say whether this tick's cac movement is consistent with
        your posterior.
      settled_by: "a cohort retains above 80% at month 6". Check every cohort
        old enough to have a month-6 number. If one clears 80%, mark this
        estimate settled in the output and say which cohort settled it.
      calibrated_by: MISSING. This estimate has never been scored against
        outcomes. Every time you report it, report it as UNCALIBRATED and
        include the lint warning in the output. Do not let an uncalibrated
        estimate carry a gate on its own without saying so out loud.
  - channel_saturation
      from: ad_platform
      method: judgement — this is a judgement call, not a computation. Say what
        you looked at (frequency, CPM drift, reach curve flattening, incremental
        CAC by spend decile) and give a qualitative level plus confidence.
        Never dress it up as a measurement.

  ## Observation sources
  Read each source at the path/command given in parameters. The loop spec asks
  for different cadences per source; this runtime has one cadence, so instead
  check FRESHNESS and report it:
    - stripe ({{ stripe_source }})            expected daily   — measures cac
    - ad_platform ({{ ad_platform_source }})  expected daily   — measures channel_saturation
    - customer_interviews ({{ interviews_source }}) expected weekly, COST: HIGH.
        Because it is expensive, do not request more interviews unless the
        posterior on product_market_fit is genuinely gate-relevant this tick;
        justify any request.
    - board_sentiment ({{ board_sentiment_source }}) expected monthly, asserted
        by the investor, and measures nothing in this loop. Read it, record it,
        and let it inform nothing. If it conflicts with the numbers, say so and
        follow the numbers.
  If a source is missing or stale, say so explicitly and mark every downstream
  number as degraded. Do not fabricate an observation. A missing source is a
  finding, not an obstacle.

  ## Acts (all of these are PROPOSALS unless explicitly cleared below)
  - increase_budget  moves: cac            reversibility: reversible
                     delay: 2w (effect on cac will not be visible for ~2 weeks —
                     do not re-propose or reverse it before then; check
                     {{ state_dir }}/history for an in-flight increase_budget and
                     report it as pending instead of stacking another)
                     consumes: runway (there is no ledger here — you must state
                     the incremental spend and check it against
                     committed_runway_usd = {{ committed_runway_usd }})
  - change_pricing   moves: payback_months  reversibility: COSTLY
                     delay: 4w   approval: FOUNDER (required)
  - exit_channel     reversibility: IRREVERSIBLE, and it is bound to no regulated
                     variable in the spec — there is no stated thing it moves and
                     no `when` clause fires it. You may never execute it. You may
                     only surface it as an option for the founder, with the
                     unboundness named.

  ## Gates (`when`) — evaluate all three, every tick, and report each
  1. if cac < {{ cac_target }} AND product_market_fit above {{ pmf_go_threshold }}
       -> propose increase_budget
  2. if payback_months > {{ payback_target_months }}
       -> propose change_pricing (founder approval required)
  3. if product_market_fit below {{ pmf_escalate_threshold }}
       -> escalate to founder
  Gates 1 and 3 can both be false; gates 1 and 2 can both fire. Report the
  operands and the boolean for each, even when it does not fire.

  ## never (hard constraint)
  "spend exceeds committed runway". No proposal, and certainly no execution, may
  put committed spend above {{ committed_runway_usd }}. If a gate fires but the
  act would breach this, the gate outcome becomes BLOCKED_BY_NEVER, not a
  proposal. Report the arithmetic. This is checked again after the run.

  ## ignoring (declared out of scope — name them, do not model them)
  - competitor_response
  - seasonality
  If either looks like it is actually driving this tick's numbers, do not start
  modelling it. Say "the loop declares this ignored and it appears to be
  binding" and hand that to the founder as a loop-design defect.

  ## Execution discipline
  allow_execution = {{ allow_execution }}; founder_approval_token = {{ founder_approval_token }}.
  - Execute nothing unless allow_execution is exactly "true".
  - Even then: change_pricing requires founder_approval_token to be exactly
    "approved:change_pricing". exit_channel is never executable.
  - Anything you cannot execute, emit as a proposal with a clear owner.

  ## Visibility (`sees`)
  The founder's view is cac and product_market_fit. Put those first and make
  them legible without reading the rest. This is a formatting duty only — this
  runtime cannot actually restrict who sees what, so assume everyone sees
  everything and write accordingly.

  ## Persistence
  Write the full structured result to {{ state_dir }}/latest.json and append a
  timestamped copy to {{ state_dir }}/history/. The next tick reads these for
  its prior and for in-flight acts. Create the directories if needed.

prompt: |
  Run one tick of the customer_acquisition loop now.

  1. Read the four observation sources; record freshness and any that are missing.
  2. Compute cac (from ad_spend and new_customers) and payback_months.
  3. Update product_market_fit from last tick's posterior in {{ state_dir }}/latest.json,
     using customer_interviews and stripe; show the update. Flag it UNCALIBRATED.
     Check the settled_by condition against month-6 cohort retention.
  4. Form a judgement on channel_saturation from ad_platform.
  5. Evaluate all three `when` gates and report operands + boolean for each.
  6. For any firing gate, check the `never` clause against
     committed_runway_usd={{ committed_runway_usd }} before proposing.
  7. Check {{ state_dir }}/history for in-flight acts still inside their delay
     window (increase_budget 2w, change_pricing 4w) and report them as pending
     rather than re-proposing.
  8. Emit the structured result, write it to {{ state_dir }}/latest.json and
     history, and finish with the founder-facing two-line summary (cac,
     product_market_fit) plus anything needing founder approval or escalation.

response:
  json_schema:
    type: object
    required: [tick, regulated, estimates, gates, proposals, escalations, never_check, lint, ignored, observation_health]
    additionalProperties: false
    properties:
      tick:
        type: object
        required: [loop, timestamp, declared_cadence, degraded]
        additionalProperties: false
        properties:
          loop: { type: string, const: customer_acquisition }
          timestamp: { type: string }
          declared_cadence: { type: string, const: weekly }
          degraded:
            type: boolean
            description: true if any source was missing/stale
      regulated:
        type: array
        items:
          type: object
          required: [name, value, target, in_band, computed_from, method]
          additionalProperties: false
          properties:
            name: { type: string, enum: [cac, payback_months] }
            value: { type: [number, "null"] }
            unit: { type: string }
            target: { type: string }
            in_band: { type: [boolean, "null"] }
            computed_from: { type: array, items: { type: string } }
            method: { type: string, description: "how value was derived, incl. arithmetic" }
      estimates:
        type: array
        items:
          type: object
          required: [name, method, from, value, interval, calibration_status, settled, notes]
          additionalProperties: false
          properties:
            name: { type: string, enum: [product_market_fit, channel_saturation] }
            method: { type: string, enum: [bayesian, judgement] }
            from: { type: array, items: { type: string } }
            prior: { type: [string, "null"] }
            value: { type: [number, string, "null"] }
            interval: { type: [string, "null"] }
            update_trace: { type: string }
            explains: { type: array, items: { type: string } }
            calibration_status: { type: string, enum: [calibrated, UNCALIBRATED] }
            settled: { type: boolean }
            settled_by_condition: { type: string }
            settled_evidence: { type: [string, "null"] }
            notes: { type: string }
      gates:
        type: array
        items:
          type: object
          required: [condition, operands, fired, outcome]
          additionalProperties: false
          properties:
            condition: { type: string }
            operands: { type: string }
            fired: { type: boolean }
            outcome:
              type: string
              enum: [no_action, proposed, escalated, BLOCKED_BY_NEVER, pending_delay_window, blocked_missing_observation]
            outcome_detail: { type: string }
      proposals:
        type: array
        items:
          type: object
          required: [act, moves, reversibility, delay, approval_required, approval_state, consumes, incremental_spend_usd, status, rationale, owner]
          additionalProperties: false
          properties:
            act: { type: string, enum: [increase_budget, change_pricing, exit_channel] }
            moves: { type: [string, "null"] }
            reversibility: { type: string, enum: [reversible, costly, irreversible] }
            delay: { type: string }
            approval_required: { type: boolean }
            approval_state: { type: string, enum: [not_required, requested, pre_authorised, absent] }
            consumes: { type: array, items: { type: string } }
            incremental_spend_usd: { type: [number, "null"] }
            status: { type: string, enum: [proposed, executed, withheld, forbidden, pending_delay_window] }
            rationale: { type: string }
            owner: { type: string, enum: [founder, growth_agent, investor] }
      escalations:
        type: array
        items:
          type: object
          required: [to, trigger, message]
          additionalProperties: false
          properties:
            to: { type: string, enum: [founder, investor] }
            trigger: { type: string }
            message: { type: string }
            delivered:
              type: boolean
              description: "always false — this runtime has no delivery channel"
      never_check:
        type: object
        required: [clause, spend_exceeds_committed_runway, arithmetic]
        additionalProperties: false
        properties:
          clause: { type: string, const: "spend exceeds committed runway" }
          spend_exceeds_committed_runway: { type: boolean }
          arithmetic: { type: string }
      lint:
        type: array
        description: "loop-hygiene warnings, e.g. estimates with no calibrated_by"
        items:
          type: object
          required: [severity, subject, message]
          additionalProperties: false
          properties:
            severity: { type: string, enum: [warn, error] }
            subject: { type: string }
            message: { type: string }
      ignored:
        type: array
        items:
          type: object
          required: [factor, appears_binding]
          additionalProperties: false
          properties:
            factor: { type: string, enum: [competitor_response, seasonality] }
            appears_binding: { type: boolean }
            note: { type: string }
      observation_health:
        type: array
        items:
          type: object
          required: [source, measures, expected_cadence, last_seen, stale, cost]
          additionalProperties: false
          properties:
            source: { type: string, enum: [stripe, ad_platform, customer_interviews, board_sentiment] }
            measures: { type: [string, "null"] }
            expected_cadence: { type: string, enum: [daily, weekly, monthly] }
            last_seen: { type: [string, "null"] }
            stale: { type: boolean }
            cost: { type: string, enum: [low, high, unspecified] }
            asserted_by: { type: [string, "null"] }
      founder_summary:
        type: string
        description: "two lines: cac, product_market_fit — the founder's `sees` set"

retry:
  max_retries: 2
  timeout_seconds: 900
  checks:
    - type: shell
      command: |
        set -eu
        f="{{ state_dir }}/latest.json"
        test -f "$f"
        python3 - "$f" <<'PY'
        import json, sys
        d = json.load(open(sys.argv[1]))

        # never clause — post-hoc, the only enforcement this runtime offers
        nc = d["never_check"]
        if nc["spend_exceeds_committed_runway"] is not False:
            raise SystemExit("NEVER VIOLATED: spend exceeds committed runway")

        for p in d.get("proposals", []):
            if p["act"] == "exit_channel" and p["status"] == "executed":
                raise SystemExit("irreversible act exit_channel was executed")
            if p["approval_required"] and p["status"] == "executed" \
               and p["approval_state"] not in ("pre_authorised",):
                raise SystemExit("approval-gated act executed without approval: " + p["act"])

        # the linter the spec expects, reduced to a runtime assertion
        for e in d.get("estimates", []):
            if e["calibration_status"] != "calibrated":
                print("LINT warn: estimate %s has no calibrated_by" % e["name"])

        if not any(g["condition"] for g in d.get("gates", [])) or len(d["gates"]) != 3:
            raise SystemExit("all three `when` gates must be evaluated and reported")
        print("tick ok")
        PY
  on_failure: |
    echo "customer_acquisition tick failed its post-run check; no act should be considered taken" >&2
```

## did not survive

Each item is something in the loop spec that a Goose recipe cannot represent as structure. Where I could only degrade it into prose the model reads, or into a post-hoc shell assertion, that is stated — degraded is not the same as expressed.

1. **`every: weekly` (loop cadence).** A recipe has no schedule field. Cadence lives outside the artifact, in `goose schedule add --cron`, so it is not versioned with the loop and can silently not exist. Noted in a comment; not implemented.
2. **Per-source cadences (`stripe: daily`, `ad_platform: daily`, `customer_interviews: weekly`, `board_sentiment: monthly`).** One recipe = one invocation = one cadence. Four different sampling rates collapsed into "expected_cadence + stale flag" that the model self-reports. The loop cannot actually sample stripe daily and interviews weekly.
3. **The loop being a loop.** A recipe is one-shot and stateless. Continuity (prior → posterior, in-flight acts, delay windows) is faked by having the agent read and write `.loop/customer_acquisition/latest.json`. Nothing in the runtime guarantees that file exists, is trusted, or is the previous tick's.
4. **`regulates.*.computed_from` as a dependency graph.** No graph object exists. `cac ← [ad_spend, new_customers]` survives only as an instruction to recompute and a `computed_from` string array in the output schema. No primitive checks that the arrow holds.
5. **`method: bayesian`.** There is no inference engine, no prior representation, no likelihood, no posterior. Replaced with "show your update in prose." The word "bayesian" is now a style guide, not a method.
6. **`explains: cac`.** No causal/structural link between an estimate and a regulated variable. Reduced to a field the model fills in and a sentence asking it to check consistency.
7. **`settled_by: "a cohort retains above 80% at month 6"`.** There is no hypothesis registry with a lifecycle, and no cross-run state a runtime owns, so "settled" cannot latch. The agent may report `settled: true` this tick and `false` next tick with nothing objecting.
8. **The missing `calibrated_by` and the linter that reports it.** Goose has no recipe linter and no notion of estimate calibration. I hardcoded the warning: the schema forces `calibration_status`, and the retry check prints a LINT line. This is a runtime assertion after the fact, not a lint before the run, and it cannot block the loop from shipping with an uncalibrated estimate carrying a gate.
9. **`cost: high` on `customer_interviews`.** No cost model, no budget, no accounting of observation expense. Degraded to "justify any request for more interviews."
10. **`board_sentiment` with no `measures`.** The spec's dangling observation stays dangling; there is no place to declare an observation that feeds nothing, so I encoded `measures: null` and instructed that it inform nothing. Nothing enforces that it informs nothing.
11. **`asserted_by: investor`.** No human-assertion channel. There is no way for a recipe to solicit an input from a named person mid-run. It became a file path plus a metadata string.
12. **`reversibility: reversible | costly | irreversible`.** Not a runtime concept. Goose's actual controls are global tool-permission modes (approve/chat/auto), which are per-tool, not per-act, and cannot distinguish "reversible budget change" from "irreversible channel exit". Enforced only by (a) asking the model nicely and (b) a post-hoc check that fails the run *after* `exit_channel` would already have been executed.
13. **`delay: 2w` / `delay: 4w`.** No time-lag semantics, no deferred effect measurement, no ability to schedule the follow-up read. The recipe cannot wait, and cannot know its own effect. Reduced to "look in history for an in-flight act and don't stack."
14. **`consumes: [runway]`.** No resource ledger. Runway had to become a required input parameter the human retypes each tick, which means the constraint is only as good as that number.
15. **`approval: founder`.** No human-approval gate exists in the recipe format. Goose can prompt for parameter values *at start*, which is the wrong time — approval is needed after the proposal is formed. Degraded to a pre-authorisation token (`approved:change_pricing`) plus a refusal-to-execute default. This is theatre compared to a real gate.
16. **`escalate: founder`.** No notification, routing, or delivery primitive. Escalations become an array in the output with `delivered: false` hardcoded, because nothing delivers them.
17. **`parties` entirely.** `human: true` / `agent: true`, `bears: "the company"` / `bears: nothing`, and `sees: [cac, product_market_fit]` have no representation. There is no identity model and no per-party output filtering, so `sees` became a formatting request and the accountability asymmetry (founder bears the company, growth_agent bears nothing) became a paragraph of instructions. Any run in auto-approve mode ignores it.
18. **`never: "spend exceeds committed runway"`.** Not expressible as a hard constraint. The retry check fails the run *after* the model has already had tool access, so a breach is detected, not prevented. A `never` that only reports is not a `never`.
19. **`ignoring: [competitor_response, seasonality]`.** No scope primitive. Kept as prose plus an `appears_binding` output field. Nothing stops the agent from quietly modelling them.
20. **`exit_channel`'s unboundness.** The spec gives it no `moves` and no `when` clause. The recipe has no way to declare an act that exists but is unreachable, so it survives as an enum value that instructions forbid executing.
21. **Expansion to the flat graph (`python3 tools/loop.py`).** There is no Goose equivalent — no compilation step, no primitives, nothing that could validate this recipe against the loop spec it claims to implement. The correspondence between the two files is maintained by hand and by this list.