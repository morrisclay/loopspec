# The loop spec format

**Design constraints, in priority order:**

1. A person unfamiliar with cybernetics can read one and know what the loop does.
2. A linter can check structural closure, epistemic grounding, resources, and authority while
   stating clearly where control-theoretic proof would require a richer model.
3. **Any competent LLM can compile it** — to Flue, LangGraph, CrewAI, Goose, or plain code —
   given only the spec file and a target name. No compiler binary, no schema document.
4. It projects to a diagram without additional layout information.

Constraint 3 is the strict one. If compiling requires reading a separate specification, the
format has failed — every key must be self-evident from its name and its position.

---

## The format

```yaml
loop: customer_acquisition
runs: weekly                        # cadence — the loop's clock

boundary:
  drawn_by: founder
  purpose: regulate acquisition without exhausting company viability
  inside: [growth policy, acquisition channel, company budget]
  outside: [prospective customers, advertising market]

# WHAT THIS LOOP IS TRYING TO CONTROL
goal:
  cac:
    keep: "below 400"
    from: [ad_spend, new_customers]

# WHAT IT BELIEVES THAT IT CANNOT SEE DIRECTLY
beliefs:
  product_market_fit:
    how: bayesian
    checked_by: quarterly_cohort_review        # omit and the linter says so
    explains: cac                              # explicit process model
  willingness_to_pay:
    how: judgement
    settled_by: "a buyer pays list price without a pilot discount"

# WHAT IT ACTUALLY OBSERVES
observes:
  billing_events: { informs: cac, every: daily, origin: outside, how: measured, source: Stripe }
  customer_interviews:
    { informs: [product_market_fit, willingness_to_pay], every: weekly, cost: high,
      origin: outside, how: reported }

# THE WORLD/SYSTEM PATH THROUGH WHICH ACTION BECOMES LATER OBSERVATION
processes:
  acquisition_channel:
    location: interface
    observed_as: [billing_events]
    description: market response that turns spend decisions into customers and cost

# WHAT IT CAN DO ABOUT IT
actions:
  increase_budget: { moves: cac, through: acquisition_channel, effect: unknown,
                     can_undo: "yes", effect_after: 2w }
  change_pricing:  { moves: willingness_to_pay, can_undo: costly, effect_after: 4w,
                     needs_approval: founder }
  stop_market:     { moves: cac, can_undo: "no", needs_approval: founder }

# WHEN IT DOES WHAT
when:
  - if: "cac > 400 and product_market_fit.confidence > 0.6"
    reads: [cac, product_market_fit]
    against: [cac]
    do: increase_budget

asks_human_when:
  - "product_market_fit confidence falls below 0.4"
asks_human: founder

# WHO IS INVOLVED AND WHAT IT COSTS THEM
people:
  founder: { human: true, loses_if_wrong: "the company", sees: [cac, product_market_fit] }
  growth_agent: { agent: true, loses_if_wrong: nothing }

# WHAT MUST NEVER HAPPEN
never:
  - "spend exceeds committed runway"

# WHAT WE KNOW WE ARE NOT MODELLING
not_modelling:
  - competitor_response
  - seasonality
```

Every key is a plain English word doing one job. `goal`, `beliefs`, `observes`, `actions`,
`when`, `people`, `never`, `not_modelling`. Nothing is named after a primitive.

## The specification

This document is the **rationale and the tour**. The normative parts are elsewhere, and are
generated rather than written, so they cannot drift from the parser:

| artifact | what it is |
|---|---|
| `schema/loop.keys.yaml` | **the grammar** — the single place a key is defined |
| `schema/semantic-map.yaml` | every accepted key's declared IR, validation, or annotation meaning |
| `REFERENCE.md` | every key, type, enum and referential rule — *generated* |
| `schema/loop.schema.json` | JSON Schema for editors and CI — *generated* |
| `NOTATION.md` | the diagram language: bands, shapes, arrows, how a defect is drawn |
| `tools/loopspec.py doctor` | fails on stale artifacts, uncovered semantics, or behavioral regressions |

**Unknown keys are errors and enums are checked.** A spec misspelling `reversibility` on an
act named `wipe_production` previously parsed clean and produced no finding — in a format
written mostly by LLMs, silent key loss is the defining failure mode, and it is the same
failure the compile study found one layer down. Errors carry a did-you-mean.

**Names resolve across the file, not the document.** A group whose loops cannot reference each
other's acts and signals is not a group. This rule was forced by the validator rejecting the
project's own group example, which is the right way to settle a scoping question.

## How it maps to the checked model

The reader never needs this table; the linter and the compiler do.

| spec key | primitive | what the linter does with it |
|---|---|---|
| `loop`, `runs` | `Loop`, `TimeScale` | structural closure, cadence present |
| `boundary` | `Boundary` + `frames`/`bounds` | missing → `boundary_not_declared`; records observer and purpose |
| `goal.*.keep` | `DesiredCondition` | `target_without_actuator` if no action moves it |
| `goal.*` | `Estimand` (computed) | |
| `beliefs.*` | `Estimand` (latent) + `Estimator` | `unmeasured_estimand` if no signal informs it |
| `beliefs.*.how` | `Estimator` | idempotency required under at-least-once |
| `beliefs.*.checked_by` | `Calibration` | absent → `belief_never_checked` |
| `beliefs.*.explains` | `Explanation` | absent → `no_explicit_process_model` |
| `observes.*` | `Signal` | `orphan_signal` if it measures nothing |
| `observes.*.every` | `TimeScale` | |
| `actions.*` | `Intervention` | |
| `actions.*.through`, `processes.*` | controlled-process `System` | missing world leg → `process_path_not_declared` |
| `actions.*.effect` | signed or explicitly unknown influence | omission → `effect_direction_unspecified`; no stability inference |
| `actions.*.effect_after` | `Delay` | recorded; no stability inference in v1 |
| `actions.*.can_undo` | attribute | `irreversible_without_approval` |
| `actions.*.needs_approval` | `requires_approval_from` | the human gate |
| `when` | `Policy` | `policy_on_unmeasured_inputs` |
| `asks_human_when` | `Policy.asks_human_when` | absent → `no_escalation_path` |
| `people.*.loses_if_wrong` | `Consequence` | |
| `people.*.sees` | `holds` edges | absent → `accountable_but_blind` |
| `never` | `Constraint` | `invariant_on_unmeasured` |
| `not_modelling` | `excluded_variables` | the revision frontier, not a disturbance claim |

## Naming observations

**Name an observation for what it tells you, not where you get it.** `billing_events`, not
`stripe`. The vendor goes in `source:`, which is optional and implementation-facing.

Three reasons, in increasing order of importance:

1. Vendors churn and the loop does not. A spec named after today's tools has to be rewritten
   when they change, and nothing about the regulation changed.
2. A diagram of `stripe → attio → slack` is a plumbing diagram. Nobody reasons about it.
3. **Two companies observing the same thing through different vendors cannot be compared at
   all** — which defeats the point of having a shared notation.

## Agentic groups

A group is several loops that share estimands, parties or acts. No new syntax:

```yaml
loop: research_agent
regulates: { evidence_sufficiency: { target: ">= 3 independent sources" } }
estimates:
  claim_truth: { from: [search], method: judgement }
parties: { orchestrator: { agent: true } }
---
loop: verifier_agent
estimates:
  claim_truth: { from: [adversarial_search], method: judgement }   # SAME estimand
parties: { orchestrator: { agent: true } }
```

Two loops estimating `claim_truth` by different methods is the *point* of a verifier. The group
checks ask whether that is deliberate:

- **`shared_estimand_no_arbiter`** — two loops estimate the same quantity and nothing reconciles
  them. Felt symptom: *"my agents disagree and whichever finishes last wins."*
- **`unowned_act`** — an act reachable by two loops with different approval rules.
- **`no_exogenous_grounding`** — every signal in the group is produced by some loop in the
  group. The encoded design has no independent observation that can contradict it. This is an
  epistemic grounding result, not a signed-polarity or stability claim.

## Compiling

The compile contract is one sentence:

> Here is a loop spec. Emit a working implementation for **&lt;target&gt;**.

Anything a target cannot express is reported, not dropped. Flue has no `Calibration`,
`Resource` or structured goal; LangGraph has no uncertainty; a target's gaps are information
about the target. A compiled artifact ships with the list of what did not survive.

## Why not TOML

TOML is better for flat configuration and worse for nested lists of objects, which `when` and
`observes` are. The YAML here uses only maps, lists and strings — the JSON-compatible subset,
per `schema/loopspec.graph.md` — so it converts to TOML or JSON mechanically if a target prefers.

---

## Status: tested

The "any LLM can compile it" requirement is measured, not asserted —
`research/llm_as_compiler.md`. 8 models across four capability tiers × 3 targets (LangGraph,
Goose, Flue), each given **only** the spec file and a target name.

Mean fidelity by tier: **0.898** (8B) → 0.981 → 0.981 → **0.993** (frontier). Nearly flat,
which is the result to want — a format that needs a frontier model is a format whose
determinacy is being supplied by the reader.

**Approval gate preserved 20/20**, across three frameworks that have no such concept.

**The warning:** the most-dropped element was `exit_channel`, the irreversible ungated act,
in 4 of 20 — and two of those drops went unreported. Compilation output therefore needs a
target adapter and preservation manifest before it can make a safety claim; text-scan
verification remains a labelled heuristic, not proof of preservation.
