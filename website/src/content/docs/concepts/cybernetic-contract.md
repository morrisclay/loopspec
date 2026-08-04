---
title: "Cybernetic contract"
description: "What LoopSpec can establish structurally, where theorem claims stop, and what stronger analysis would require."
---

> This page is generated from `CYBERNETICS.md` during every site build. Edit the canonical source, not this copy.

LoopSpec is a **cybernetically informed specification and structural analysis tool for agent
loops**. It is not yet a control-systems solver, and it does not turn a qualitative agent
description into a proof of stability, observability, controllability, or requisite variety.

That boundary is part of the design. A useful formal tool says both what follows from its
representation and what additional structure would be required to say more.

## The object LoopSpec represents

The authoring language records a loop's declared control purpose and operating envelope:

| Cybernetic role | LoopSpec v1 surface | Canonical IR |
|---|---|---|
| observer-relative boundary | `boundary.drawn_by`, `purpose`, `inside`, `outside` | `Party →frames→ Boundary →bounds→ System` |
| regulated quantity | `goal:` / `beliefs:` | `Estimand` |
| reference condition | `goal.<q>.keep` | `DesiredCondition →targets→ Estimand` |
| observation | `observes:` | `Signal →measures→ Estimand` |
| estimation | `beliefs.<q>.how` | `Estimator →estimates→ Estimand` |
| calibration contract | `checked_against`, `scoring_rule`, `window`, `adjusts` | `Calibration →compares→ Signal`, `Calibration →revises→ Estimator` |
| comparison/reference use | `when[].against` | `Policy →uses_reference→ DesiredCondition` |
| selection rule | ordered `when:` entries | one priority-indexed `Policy` per rule, with `reads` and `authorizes` edges |
| actuation | `actions.<a>.moves` | `Intervention →targets→ Estimand` |
| world/process path | `actions.<a>.through`, `processes.*.observed_as` | `Intervention →causes→ System →produces→ Signal` |
| intended effect direction | `actions.<a>.effect` | `Intervention.effect_direction`, including explicit `unknown` |
| cadence and lag | `runs`, `every`, `effect_after` | `TimeScale`, `Delay` |
| hard boundary | `never:` | `Constraint` |
| resource boundary | `spends:` | `Resource` and `consumes` |
| authority and exposure | `people:`, `needs_approval` | `Party.consequence_status`, `Party →bears→ Consequence` |
| epistemic provenance | `origin`, `how`, `reported_by` | fields plus `produces`/`asserts` |
| model boundary | `not_modelling:` | `excluded_variables` |
| attention contract | `observes.*.value_metric`, `review_window`, `review_every`, `adjusts` | `Calibration →revises→ Signal`, `Calibration →reviews_at→ TimeScale` |

A canonical loop record contains its complete sets of signals and interventions. No signal or
action becomes privileged because it appeared first in YAML.

This is enough to ask structural questions such as:

- Is a target connected to any declared actuator?
- Does an observation inform a quantity used by a policy?
- Can an irreversible act occur without a named approval gate?
- Does a belief have a declared outcome-scoring process?
- Is all feedback produced inside the system itself?
- Is the action-to-observation process path explicit?
- Is the observer and purpose behind the boundary declared?

It is not enough to calculate dynamic behaviour.

## Assurance levels

Every finding carries an assurance label in machine output and generated documentation.

| Level | What LoopSpec may say | What it may not imply |
|---|---|---|
| `structural` | a fact follows directly from declared nodes, fields, and edges | that the declaration matches runtime reality |
| `qualitative-proxy` | a represented pattern warrants domain review | a theorem's quantitative conditions hold |
| `quantitative` | a result follows from explicit numeric dynamics and assumptions | empirical performance outside those assumptions |
| `empirical` | observed outcomes support a claim over a stated cohort/window | universal validity |

The current linter emits structural findings and one qualitative proxy. It emits no
quantitative or empirical control claims. Corpus prevalence is tracked separately as evidence
about how often checks fire; prevalence does not raise a finding's assurance level.

## The theorem boundary

Several earlier LoopSpec check names borrowed more authority from cybernetics than the encoded
structure justified. They are now narrowed.

| Earlier claim | Current check | What is actually established |
|---|---|---|
| `regulator_without_model` violated Conant & Ashby | `no_explicit_process_model` | no explicit `explains` relation is encoded; an implicit policy model may exist |
| `unmeasured_estimand` was Kalman observability | `unmeasured_estimand` | no declared signal informs the quantity |
| `uncontrollable_target` was Kalman controllability | `target_without_actuator` | no declared action says it moves the quantity |
| self-produced feedback was reinforcing and divergent | `endogenous_feedback_without_crosscheck` | no independent observation of the same quantity is encoded |
| cadence inversion proved a cascade would hunt | `cascade_cadence_inversion` | the inner update cadence is not faster; dynamics need review |
| exclusions outnumbering actions violated requisite variety | withdrawn | exclusions are not disturbances, and headcounts are not state variety |

### Good Regulator theorem

Conant and Ashby's theorem concerns an optimal regulator under stated assumptions and a
mapping between regulator and system states. A prose `Explanation` node is neither necessary
nor sufficient for that mapping. LoopSpec can reveal the absence of an **explicit process model**;
it cannot certify or refute the theorem's conditions.

### Observability and controllability

Kalman observability and controllability are properties of a specified state-space model. A
missing sensor edge or actuator edge is a useful structural defect and only a precondition.
LoopSpec v1 has no state-transition or observation matrices, so it does not run Kalman tests.

### Loop polarity and stability

Polarity needs signed causal links around the complete cycle. LoopSpec records the intended sign
of an intervention's effect, including explicit `unknown`, but does not assign signs to all
process and observation transformations. Stability additionally needs dynamics: gain, delay,
operating point, and usually a plant model. LoopSpec v1 records qualitative delay and damping
descriptions but cannot infer polarity or stability. Self-produced feedback without an
outside cross-check is an epistemic grounding problem, not proof of positive feedback.

### Requisite variety

Ashby's variety is over distinguishable states and responses. `not_modelling:` declares a
boundary; it is not a disturbance list. A variable can be excluded without perturbing the
system, and a modelled variable can be a disturbance. A future variety analysis needs explicit
disturbance modes, response partitions, and the channel connecting them.

### Cascade control

Conventional cascade design requires inner-loop dynamics or bandwidth to be substantially
faster than the outer loop. Update cadence is only a proxy for that relationship. LoopSpec flags
a non-faster inner cadence for review and remains silent when free-text periods cannot be
ranked. It does not claim the loops will oscillate.

## The control projection

`tools/control.py` renders each target as a familiar feedback ring:

```text
reference ─┐
           ▼
       (difference) ─▶ policy ─▶ action ─▶ process
           ▲                                  │
           └──── estimate ◀── observation ◀───┘
```

The comparator path is drawn only from `uses_reference`; its displayed error value remains a
**projection convention** rather than an executable calculation. The process box and its connections are now
drawn only from canonical `causes` and `produces` edges; when those are absent, the renderer
shows an unrepresented process rather than inventing “the world.” Neither path nor comparator
proves that a runtime implements the architecture or that it is stable. Exclusions are shown
as detached model-boundary notes, never fabricated as disturbances.

## Meta-control and second-order cybernetics

LoopSpec represents two useful loops about a loop:

- **calibration** joins past beliefs to later outcomes, scores them over a window, and names
  what poor performance adjusts;
- **attention review** names a decision-value measure, review window, and what changes in
  sampling, source, routing, or retirement when an observation does not earn its cost.

These are meta-control mechanisms. Calling them second-order cybernetics without qualification
would still be too broad. LoopSpec now makes the observer, purpose, and boundary explicit. A
stronger second-order representation must additionally show how observing changes the system
and how the observer's distinctions, purpose, and boundary can themselves be revised.

## The contribution, stated narrowly

LoopSpec's credible contribution is the integration of:

1. a human-readable authoring language for agent-loop intent;
2. a deterministic, typed, order-independent graph IR;
3. fail-closed structural diagnostics with explicit assurance boundaries;
4. governance, reversibility, resource, provenance, attention, and calibration concerns in
   the same analysable artifact;
5. an empirical workflow that preserves preregistration, independent encodings, adjudication,
   negative results, and historical invalid artifacts.

The contribution is not a new theorem. It is an executable specification discipline that
makes consequential omissions visible before implementation, while refusing to describe
structural proxies as control-theoretic proofs.

## What would justify stronger analysis

Stronger future IR revisions should add structure only with an executable analysis attached:

- explicit process state and typed environment transitions beyond the current structural path;
- executable error functions and typed comparison operators beyond structural reference use;
- signed influence around the full cycle beyond the current intervention-effect direction;
- gain, units, delay distributions, and saturation/deadband;
- disturbance modes and response partitions for variety analysis;
- stored prediction/outcome records and executable scoring over declared calibration contracts;
- distinction and boundary revision for stronger second-order claims.

Until those exist, LoopSpec should remain strong at structural design analysis and quiet about
dynamic guarantees.
