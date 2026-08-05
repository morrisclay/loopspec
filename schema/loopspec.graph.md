# LoopSpec Canonical Graph — the IR definition

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

A LoopSpec document is a set of **nodes** with unique ids and **edges** expressed as id
references. It is *not* a nesting of objects.

This is a deliberate reversal of the round-1 encoding style. Nesting caused the two worst
`C` results — depth 5 to 6 against a target of 4 — and made the same information reachable
by different paths in different encodings, which is precisely what destroys determinacy.

**Flat wins twice: it is more comparable and more readable.** Toyota's A3 constraint is the
precedent — one sheet, readable by someone not involved.

## 2. Canonical document shape

Order is not significant. Research encodings carry provenance (`domain`, `encoded_by`,
`encoder_role`); mechanically expanded design artifacts identify their source language with
`source_format` instead. The validator requires the appropriate provenance for each kind.

```yaml
loopspec_version: 2
ir_revision: "2.2"
encodes: <system-slug>              # required
set: seed | adversarial | held_out | negative | field
shape: canonical-graph
source_format: loop-v1.2            # generated design artifacts
domain: <slug>                      # research encodings
encoded_by: <model-or-person>       # research encodings
encoder_role: author-intent | independent  # research encodings

uses: [...]                         # OPTIONAL and derivable — the set of node kinds.
                                    # Both independent encoders omitted it on all four
                                    # held-out systems. In the flat shape it restates
                                    # what `nodes[].kind` already says; it was only
                                    # load-bearing in the pre-normal nested shape.
nodes:                              # ALL nodes, flat, one list
  - id: <slug>                      # unique within the document
    kind: System | Boundary | Party | Estimand | Signal | Estimate | Evidence |
          Estimator | DesiredCondition | PreferenceOrdering | Consequence |
          Intervention | Policy | Loop | Delay | TimeScale | Resource |
          Constraint | Revision | ActionProfile | ControlOperation | Output
    # kind-specific fields, max 2 levels below this point
edges:
  - from: <id>
    to: <id>
    rel: measures | estimates | holds | targets | closes | delays | constrains |
         authorizes | consumes | revises | contains | bears |
         asserts | replenishes | produces | reads | compares | causes | frames | bounds |
         samples_at | reviews_at | sets | uses_reference | profiles | emits
  ...
loops:                              # derived view, but declared explicitly
  - id: <slug>
    timescale: <id of a TimeScale node>
    signals: [<ids of Signal nodes>]
    interventions: [<ids of Intervention nodes>]
    estimands: [<ids of Estimand nodes>]
    desired_conditions: [<ids of DesiredCondition nodes>]
    policies: [<ids of Policy nodes>]
    processes: [<ids of System nodes with role: controlled_process>]
    action_profiles: [<ids of ActionProfile nodes>]
    operations: [<ids of ControlOperation nodes>]
    outputs: [<ids of Output nodes>]
    boundary: <id of a Boundary node> | null
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

### Relations added after the original core

The first three relations below were demanded when held-out benchmarks were opened. IR v2 then
added explicit policy inputs, calibration joins, effect paths, and observer-relative boundary
links. These are relations rather than new domain nouns: the node vocabulary held, while the
edge vocabulary had been too weak to express closure and provenance.

| rel | from → to | Why it was needed |
|---|---|---|
| `asserts` | Party → Signal | A **reported** quantity is not a measured one. Reported fish landings are assertions by parties under economic pressure and may knowingly differ from the catch. Without this, the graph cannot say who authored a datum or that incentives shape its content. |
| `replenishes` | Intervention or Signal → Resource | `consumes` was the only resource relation, so stocks could only deplete. Payday replenishes money, rest replenishes attention, a kanban card replenishes parts. |
| `produces` | System or Intervention → Signal | Distinguishes a **produced** artifact from an **observed** one. Tool directives, retrieved passages and synthesized plans are passed between components and can lose meaning without becoming invalid. |
| `reads` | Policy → Estimand or Resource | Makes policy inputs explicit. In IR v1 they were stored only as a tokenized field inferred from prose, so punctuation could change semantics. |
| `compares` | Calibration → Signal | Joins a frozen prediction contract to the later observation carrying its outcome. |
| `causes` | Intervention → System (`controlled_process`) | States the represented action-to-world path without pretending to know gain or dynamics. |
| `frames` | Party → Boundary | Records whose distinctions selected inside/outside for this account. |
| `bounds` | Boundary → System (`controller`) | Attaches that observer-relative boundary to the described controller. |
| `samples_at` | Signal → TimeScale | Makes an observation cadence a typed relation instead of an orphan scalar or unreferenced time node. |
| `reviews_at` | Calibration → TimeScale | Gives belief-calibration and attention-review loops an explicit cadence distinct from their scoring window. |
| `sets` | Estimand → DesiredCondition | Makes a cascade's outer quantity structurally set the inner reference instead of leaving `set_by` as an opaque string. |
| `uses_reference` | Policy → DesiredCondition | Records which ordered decision rule actually compares its input with a declared target; the comparator is no longer inferred from co-presence alone. |
| `profiles` | ActionProfile → Intervention | Attaches a late-bound safety/approval variant to a world action without turning controller transitions into interventions. |
| `emits` | ControlOperation → Output | Separates a controller transition from the value it exposes across the represented boundary. |

A **fully represented structural ring** for a controlled quantity is traversable as
`Policy →uses_reference→ DesiredCondition →targets→ Estimand ←measures← Signal ←produces←
controlled_process ←causes← Intervention ←authorizes← Policy`, while the same Policy
`→reads→ Estimand`. The arrows encode declared
roles and influence paths, not an algebraic comparator, transfer function, gain, or stability
result. Missing roles remain valid partial IR and become findings.

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
5. **Partial loops are valid IR.** A design tool must be able to represent and diagnose a
   missing cadence, signal, action, quantity, or policy. `incomplete_loop` reports the missing
   roles; the semantic validator checks types and references rather than rejecting the design
   before analysis.
6. **Loop identity is its explicit unique `id`.** Signals and interventions are sets. No member
   is privileged by serialization order, and two loops may share cadence or actuators while
   remaining distinct control purposes.
7. **Every `Estimator` declares `idempotency_basis`.** Not stylistic: alarm delivery is
   at-least-once, so a Bayesian update applied twice double-counts into a well-formed but
   wrong posterior.
8. **Every `Party` declares its exposure state.** A `bears` edge names an actual
   `Consequence`; `consequence_status: none` records an intentionally stake-free actor. An
   omitted declaration is advisory-invalid because absence and unknown are not equivalent.
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

Round-1 encodings predate this shape and are retained unmigrated as the evidentiary record for
the divergence that motivated it. They are marked `uras_version: 0-prenormal`, retaining the
name under which that evidence was created. LoopSpec 2.x readers accept the legacy
`uras_version` marker; new output emits `loopspec_version`.

IR v1 introduced plural `signals` and `interventions`. IR v2 adds complete loop membership and
explicit `Policy →reads→ input` edges. The validator remains able to read legacy singular loop
members, but new mechanical expansions always emit v2. Authoring specs without `when.reads`
remain accepted and are marked `inputs_inferred: true`; `policy_inputs_inferred` is the
migration finding. In a mixed policy, only rules omitting `reads` are inferred, and their
zero-based indexes are recorded in `inferred_rule_indexes`; each rule keeps its own inputs so
an explicit rule cannot erase or absorb a neighbouring inferred rule.

IR v2.1 emits one `Policy` node per ordered `when` rule, with zero-based `priority`. Its
`reads` and `authorizes` edges therefore belong to that condition rather than to an aggregate
bag of all conditions, inputs, and actions. Loop membership lists every rule-policy. Older
aggregate Policy nodes remain readable.

Each belief calibration contract is a distinct node even when several contracts share a human
review name. The original name is retained in `review`, while `calibration_kind: belief`
distinguishes prediction scoring from an observation's `calibration_kind: attention` source
review. Both use the `Calibration` primitive for meta-control, but only the former requires an
outcome, scoring rule, window, and revision target.

IR revision 2.1 is backward-compatible within major version 2. It adds optional boundary and
controlled-process membership, `frames`/`bounds`/`causes` edges, action effect direction, and
distinct belief/attention review contracts. Older v2 graphs remain readable; new authoring
expansions emit the richer fields and receive explicit findings when they are absent.

IR revision 2.2 adds optional `ActionProfile`, `ControlOperation`, and `Output` nodes plus
`profiles` and `emits` edges. Existing v1.1 authoring documents and earlier v2 graphs remain
readable. The additions are experimental and still being tested across systems and independent
authors; they are implemented and testable but not yet claimed as a settled cross-encoder
vocabulary. Protocols and results live under `research/`.
