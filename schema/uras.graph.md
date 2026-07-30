# URAS Canonical Graph — the IR definition

**This document is the definition.** JSON Schema and YAML are serializations of it.

It exists because round-1 measurement revealed that the ontology specified *primitives* and
not *shape*. Four independent encoders produced four incompatible document structures:

| Encoder | Section naming |
|---|---|
| claude-opus-5 | `parties`, `estimands`, `signals` — lowercase plural |
| gpt-5-codex (r1) | `Party`, `Estimand`, `Signal` — PascalCase primitive names |
| gpt-5-codex (r2) | everything nested under a single `System` key |
| gemini-2.5-pro / deepseek-v3.2 | further variants |

`D` was measurable only because the encoding task happened to pin the top-level keys
(`uses`, `estimands`, `loops`). Everything below that was unconstrained, which meant the
Semantic Validator could not locate sections to check referential integrity or loop closure
across encoders. Fixing shape is therefore a precondition for both `D` and validation.

---

## 1. The IR is a typed graph, not a tree

A URAS document is a set of **nodes** with unique ids and **edges** expressed as id
references. It is *not* a nesting of objects.

This is a deliberate reversal of the round-1 encoding style. Nesting caused the two worst
`C` results — depth 5 to 6 against a target of 4 — and made the same information reachable
by different paths in different encodings, which is precisely what destroys determinacy.

**Flat wins twice: it is more comparable and more readable.** Toyota's A3 constraint is the
precedent — one sheet, readable by someone not involved.

## 2. Canonical document shape

Exactly these top-level keys. Unknown keys are an error. Order is not significant.

```yaml
uras_version: 0
encodes: <system-slug>              # required
set: seed | adversarial | held_out | negative
domain: <slug>
encoded_by: <model-or-person>
encoder_role: author-intent | independent

nodes:                              # ALL nodes, flat, one list
  - id: <slug>                      # unique within the document
    kind: System | Boundary | Party | Estimand | Signal | Estimate | Evidence |
          Estimator | DesiredCondition | PreferenceOrdering | Consequence |
          Intervention | Policy | Loop | Delay | TimeScale | Resource |
          Constraint | Revision
    # kind-specific fields, max 2 levels below this point
edges:
  - from: <id>
    to: <id>
    rel: measures | estimates | holds | targets | closes | delays | constrains |
         authorizes | consumes | revises | contains | bears |
         asserts | replenishes | produces
  ...
loops:                              # derived view, but declared explicitly
  - id: <slug>
    timescale: <id of a TimeScale node>
    signal: <id of a Signal node>
    intervention: <id of an Intervention node>
excluded_variables: [...]
breaks_declared: [...]
breaks_handled: [...]
surfaced: [...]
reduces_to: <formalism-name> | null
```

### Why `edges` is separate from `nodes`

Relationships in round-1 encodings were expressed inline as ad-hoc fields (`measures:`,
`held_by:`, `from:`, `to:`), and every encoder chose different field names. Naming the
relation set closes that: `rel` is a **closed vocabulary**, so two encoders describing the
same relationship must use the same token or fail validation.

### Relations added by the held-out set

Three relations were added after the held-out benchmarks were opened. All three were demanded
by independent encoders, and all three are relations rather than primitives — the node
vocabulary held, the edge vocabulary did not.

| rel | from → to | Why it was needed |
|---|---|---|
| `asserts` | Party → Signal | A **reported** quantity is not a measured one. Reported fish landings are assertions by parties under economic pressure and may knowingly differ from the catch. Without this, the graph cannot say who authored a datum or that incentives shape its content. |
| `replenishes` | Intervention or Signal → Resource | `consumes` was the only resource relation, so stocks could only deplete. Payday replenishes money, rest replenishes attention, a kanban card replenishes parts. |
| `produces` | System or Intervention → Signal | Distinguishes a **produced** artifact from an **observed** one. Tool directives, retrieved passages and synthesized plans are passed between components and can lose meaning without becoming invalid. |

`asserts` is the most consequential of the three, and it is not confined to the system that
demanded it. The same structure recurs throughout the existing corpus: how arrival time gets
recorded against a four-hour target, why *genchi genbutsu* exists as doctrine at all, a
founder's pipeline number, a competitor's selectively published result. The representation
previously had no way to distinguish a measurement from a claim, which for institutional
systems is close to the central fact.

## 3. Hard rules

1. **Depth ceiling 4.** Measured from document root. Enforced as an error, not a warning.
2. **No reserved-word keys.** `on`, `off`, `yes`, `no`, `true`, `false`, `y`, `n`, `null`
   are banned as keys. YAML 1.1 parses them as booleans, which silently produces non-string
   keys — a defect that occurred in real encoder output from two different encoders. Use
   `applies_to` instead of `on`.
3. **Canonical serialization is JSON**, or YAML restricted to the JSON-compatible subset.
   YAML's convenience is not worth its ambiguity for an artifact intended to last.
4. **Every id referenced must exist.** Dangling references are errors.
5. **Every `Loop` must close** — it must name a timescale, a signal and an intervention.
6. **Loop identity:** one loop per distinct (timescale, closing intervention). Two loops
   sharing both are one loop.
7. **Every `Estimator` declares `idempotency_basis`.** Not stylistic: alarm delivery is
   at-least-once, so a Bayesian update applied twice double-counts into a well-formed but
   wrong posterior.
8. **Every `Party` bears a `Consequence`** (edge `rel: bears`). An authority-holding
   mechanism that bears no consequence is a component, not a Party.
9. **`PreferenceOrdering` may not be scalarized.** Scalarizing is a policy-layer decision.
10. **`Intervention` with `target: own-structure` must state a `motive`.**
11. **No estimator may read and write the same estimand** without an intervening `Delay`.

## 4. What this does not fix

**Shape agreement is not meaning agreement.** Pinning section names will raise `D` because
it removes a source of divergence that was never conceptual. That rise is a **measurement
artifact and must be reported as such**, exactly as the coverage-measurement fix was.

The conceptual divergences round 1 found are untouched by this document:

- estimand individuation on the hospital (0.43–0.67 across pairs) — whether five parties
  assessing discharge readiness constitutes five estimands or one contested aggregate
- primitive selection (0.65–0.87) — whether `Estimator` is needed when a party already
  holds an estimate

Those are real ambiguities in the primitives. This document makes them *visible* by removing
the noise that was masking them; it does not resolve them.

## 5. Migration

Round-1 encodings predate this shape and are retained unmigrated as the evidentiary record
for the divergence that motivated it. They are marked `uras_version: 0-prenormal`. Round 2
onward uses this shape.
