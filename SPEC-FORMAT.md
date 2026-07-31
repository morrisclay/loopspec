# The loop spec format

**Design constraints, in priority order:**

1. A person unfamiliar with cybernetics can read one and know what the loop does.
2. A linter can check it against the Good Regulator theorem, requisite variety, observability,
   controllability and loop polarity.
3. **Any competent LLM can compile it** — to Flue, LangGraph, CrewAI, Goose, or plain code —
   given only the spec file and a target name. No compiler binary, no schema document.
4. It projects to a diagram without additional layout information.

Constraint 3 is the strict one. If compiling requires reading a separate specification, the
format has failed — every key must be self-evident from its name and its position.

---

## The format

```yaml
loop: customer_acquisition
every: weekly                       # cadence — the loop's clock

# WHAT THIS LOOP IS TRYING TO CONTROL
regulates:
  cac:
    target: "< 400"
    computed_from: [ad_spend, new_customers]

# WHAT IT BELIEVES THAT IT CANNOT SEE DIRECTLY
estimates:
  product_market_fit:
    from: [customer_interviews, stripe]
    method: bayesian
    calibrated_by: quarterly_cohort_review     # omit and the linter says so
    explains: cac                              # the MODEL — Conant & Ashby
  willingness_to_pay:
    from: [customer_interviews]
    method: judgement
    settled_by: "a buyer pays list price without a pilot discount"

# WHAT IT ACTUALLY OBSERVES
observes:
  stripe:              { measures: cac, every: daily }
  crm:                 { measures: pipeline_velocity, every: daily }
  customer_interviews: { measures: product_market_fit, every: weekly, cost: high }

# WHAT IT CAN DO ABOUT IT
acts:
  increase_budget: { reversibility: reversible, delay: 2w }
  change_pricing:  { reversibility: costly, delay: 4w, approval: founder }
  stop_market:     { reversibility: irreversible, approval: founder }

# WHEN IT DOES WHAT
when:
  - if: "cac > 400 and product_market_fit.confidence > 0.6"
    do: increase_budget
  - if: "product_market_fit.confidence < 0.4"
    escalate: founder                          # where the loop stops and asks

# WHO IS INVOLVED AND WHAT IT COSTS THEM
parties:
  founder: { human: true, bears: "the company", sees: [cac, product_market_fit] }
  growth_agent: { agent: true, bears: nothing }

# WHAT MUST NEVER HAPPEN
never:
  - "spend exceeds committed runway"

# WHAT WE KNOW WE ARE NOT MODELLING
ignoring:
  - competitor_response
  - seasonality
```

Every key is a plain English word doing one job. `regulates`, `estimates`, `observes`, `acts`,
`when`, `parties`, `never`, `ignoring`. Nothing is named after a primitive.

## The specification

This document is the **rationale and the tour**. The normative parts are elsewhere, and are
generated rather than written, so they cannot drift from the parser:

| artifact | what it is |
|---|---|
| `schema/loop.keys.yaml` | **the grammar** — the single place a key is defined |
| `REFERENCE.md` | every key, type, enum and referential rule — *generated* |
| `schema/loop.schema.json` | JSON Schema for editors and CI — *generated* |
| `NOTATION.md` | the diagram language: bands, shapes, arrows, how a defect is drawn |
| `tools/gen_spec.py --check` | fails when the generated artifacts go stale |

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
| `loop`, `every` | `Loop`, `TimeScale` | loop closure, cadence present |
| `regulates.*.target` | `DesiredCondition` | **controllability** — can any act move it? |
| `regulates.*` | `Estimand` (computed) | |
| `estimates.*` | `Estimand` (latent) + `Estimate` | **observability** — is it measured? |
| `estimates.*.method` | `Estimator` | idempotency required under at-least-once |
| `estimates.*.calibrated_by` | `Calibration` | absent → `uncalibrated_estimator` |
| `estimates.*.explains` | `Explanation` | absent → **Good Regulator** violation |
| `observes.*` | `Signal` | `orphan_signal` if it measures nothing |
| `observes.*.every` | `TimeScale` | |
| `acts.*` | `Intervention` | |
| `acts.*.delay` | `Delay` | delay without damping → oscillation |
| `acts.*.reversibility` | attribute | `irreversible_without_approval` |
| `acts.*.approval` | `requires_approval_from` | the human gate |
| `when` | `Policy` | `policy_on_unmeasured_inputs` |
| `when.*.escalate` | `Policy.escalates` | absent → `no_escalation_path` |
| `parties.*.bears` | `Consequence` | |
| `parties.*.sees` | `holds` edges | absent → `accountable_but_blind` |
| `never` | `Constraint` | `invariant_on_unmeasured` |
| `ignoring` | `excluded_variables` | the revision frontier |

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
- **`group_without_exogenous_signal`** — every signal in the group is produced by some loop in
  the group. Loop polarity at group scale: the group is reinforcing and cannot be corrected
  from outside. **This is the multi-agent version of the Ralph finding.**

## Compiling

The compile contract is one sentence:

> Here is a loop spec. Emit a working implementation for **&lt;target&gt;**.

Anything a target cannot express is reported, not dropped. Flue has no `Calibration`,
`Resource` or structured goal; LangGraph has no uncertainty; a target's gaps are information
about the target. A compiled artifact ships with the list of what did not survive.

## Why not TOML

TOML is better for flat configuration and worse for nested lists of objects, which `when` and
`observes` are. The YAML here uses only maps, lists and strings — the JSON-compatible subset,
per `schema/uras.graph.md` — so it converts to TOML or JSON mechanically if a target prefers.

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
in 4 of 20 — and two of those drops went unreported. Compilation output must be linted back
against the source spec. That check does not exist yet and is the top tool priority.
