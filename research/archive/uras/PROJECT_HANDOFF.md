# Project Handoff
## Universal Representation for Adaptive Systems (URAS)

> [!CAUTION]
> **Historical charter, superseded by LoopSpec.** The universal-representation ambition in this
> document was rejected by the later evidence and narrowed to agentic feedback loops. It remains
> here so that the change of scope is auditable. See the archived [`FORK.md`](FORK.md), current
> [`convergence record`](../../CONVERGENCE.md), and product [`README`](../../../README.md).

> **Assume we are designing something that should still make sense in 30 years. Prefer timeless cybernetic concepts over current AI terminology. If a primitive would become obsolete when today's LLMs are replaced, it does not belong in the core representation.**

---

## Vision

The objective of this project is **not** to invent another workflow language or agent framework.

The objective is to develop a **universal representation for adaptive systems**.

Cybernetics gave us the theory of adaptive systems.

Programming languages gave us abstractions for computation.

We believe there is still no common representation whose first-class primitives are:

- goals
- state estimates
- uncertainty
- observations
- evidence
- learning
- interventions
- feedback loops

The long-term goal is a representation that can describe:

- companies
- startups
- investment funds
- governments
- hospitals
- supply chains
- autonomous robots
- ecosystems
- biological systems

using exactly the same conceptual building blocks.

The representation should eventually compile into executable systems.

The first execution backend will be **Flue**.

---

## Philosophy

Do **not** begin by designing syntax.

Do **not** begin by writing parsers.

Do **not** begin by implementing execution.

Language design comes last.

Representation comes first.

The textual DSL, diagrams and execution engine are merely different projections of the same underlying model.

---

## Overall Architecture

```
Adaptive System
        │
        ▼
Universal Representation (URAS)
        │
 ┌──────┼──────────┐
 ▼      ▼          ▼
Diagram DSL     JSON/YAML IR
        │
        ▼
Semantic Validator
        │
        ▼
Compiler
        │
        ▼
Flue Runtime
        │
        ▼
Agents
LLMs
Tools
Memory
Events
Evaluators
```

The IR is the canonical truth.

Everything else is a projection.

---

## Guiding Principles

The representation should be:

- composable
- recursive
- hierarchical
- explainable
- executable
- domain independent
- machine readable
- human readable
- graph native
- uncertainty aware
- temporal
- inspectable
- versionable

---

## Phase 1 — Research

Survey adjacent work.

Do not copy it.

Instead identify missing concepts.

Research:

**Cybernetics**

- Wiener
- Ashby
- Beer
- Pask
- Maturana
- Varela

**Systems Theory**

- Bertalanffy
- Meadows
- Forrester

**Control Theory**

**Decision Theory**

**Bayesian Networks**

**Probabilistic Programming**

**POMDPs**

**Statecharts**

**Petri Nets**

**System Dynamics**

**BPMN**

**Agent Frameworks**

**Knowledge Graphs**

**Ontology Engineering**

**Programming Language Theory**

**Reactive Programming**

**Constraint Programming**

**Digital Twins**

**Model-Based Systems Engineering**

Represent findings as comparison tables.

### The prior-art gate

Phase 1 is a **gate**, not a survey. It exists to answer one question, and the project
does not proceed until it has an answer that survives adversarial reading:

> **Why is URAS not a Dec-POMDP with better ergonomics?**

Take this seriously, because most of the candidate primitive list already has names.
`State Estimate`/`Belief` is a belief state. `Sensor`/`Observation` is an observation
function. `Model` is a transition function. `Estimator` is a Bayes filter. `Policy` and
`Intervention` are π and A. `Preference Ordering` is a reward function. `Constraint` is
a constrained MDP. `Learning Rule` is model-based RL. System nesting is hierarchical RL
with options. Factored state is a dynamic Bayesian network. Multiple actors is a
Dec-POMDP.

That accounts for the large majority of the list using formalisms between thirty and
sixty years old, all of which already have execution semantics and composition rules.
POMDPs are listed above as one item among nineteen. They are in fact the primary
competitor and should be read first.

The defensible residue — the current best answer, to be attacked rather than assumed:

| Capability | Why classical formalisms cannot express it |
|---|---|
| **Goal revision** | Reward is exogenous and fixed. Adaptive systems change what they want. |
| **State-space revision** | `S` is fixed at specification time. Real systems discover variables they did not know existed. |
| **Observer plurality** | Dec-POMDPs give actors separate beliefs but have no object representing *disagreement itself*. |
| **Negotiable boundary** | The agent/environment split is stipulated by fiat and cannot move. |
| **Evidence provenance** | Records that a belief moved, never why, from what, or on whose authority. |
| **Recursive viability** | Each level is a sub-policy, not a full regulator in Beer's sense. |
| **Legitimacy** | No representation of who is *permitted* to intervene. |

If that residue collapses under scrutiny — if each item turns out to be expressible
with known machinery plus notation — **the correct outcome is to stop**, and to write
the ergonomics layer over an existing formalism instead. That is a real possible
result, and a cheap one to reach at this stage rather than at Phase 7.

### The reduction floor

The complement of the gate. URAS must **degrade cleanly**: the thermostat encoding has
to reduce mechanically to a classical control loop, and a single-actor benchmark has to
reduce to a POMDP.

This is a two-sided test and both sides matter. Failing to reduce means the
representation has drifted into abstraction that buys nothing. Reducing *completely*,
with no residue, means it is a POMDP with extra words.

### Deliverable 1

Create

```
research/
```

containing

```
comparison.md

missing_capabilities.md

design_principles.md

prior_art_gate.md        <- the POMDP question, answered or conceded
```

---

## Phase 2 — Ontology Discovery

This is the most important phase.

### Phases 2 through 4 are one loop

A charter about feedback should not itself be an open-loop pipeline. Phases 2, 3 and 4
do not run once in sequence — they cycle:

```
        ┌──────────────────────────────────────────┐
        │                                          │
        ▼                                          │
   2. Ontology  ──▶  3. Encode benchmark  ──▶  4. Contradiction
                                                   │
                                          revise ──┘
```

Each turn of the loop: encode the next adversarial benchmark using the current
ontology, record every point where it does not fit, then revise. Revision means adding,
merging, splitting, or **deleting** primitives.

**Convergence criterion:** three consecutive adversarial benchmarks encode with no new
primitive required and no unresolved contradiction. Until that holds, the ontology is
not a candidate for Phase 5.

Log every turn. The sequence of revisions is itself a finding — a primitive that is
added, removed, and re-added is telling you something the catalog is not.

### The primitive budget

**Twenty core primitives. Hard ceiling.**

Exceeding it is not a warning, it is a stop condition: merge or delete something before
continuing. The charter already says "prefer deleting concepts over adding them," but
exhortation does not delete anything. A budget does, because it forces the comparison —
*which existing primitive is worth less than this new one?*

Anything beyond twenty lives in an extension namespace, explicitly marked, and the
core/extension ratio is tracked as a project metric. LLVM IR and SQL both achieved
reach with a small core plus target-specific constructs; neither achieved it by being
extension-free.

Every core primitive must appear in **at least three** benchmark encodings from
**at least two** different domains. This is checked mechanically, not by judgement —
see the coverage matrix below.

### Machine-readable from the start

The primitive catalog carries YAML front-matter per primitive, so the coverage matrix
is generated rather than maintained by hand, and orphan primitives — those appearing in
too few benchmarks — fail the check automatically.

Phases 2 through 4 otherwise produce only prose, which means four phases with no
mechanical signal. This is the cheapest available fix.

Derive candidate primitives.

Each primitive should contain

```
Name

Definition

Purpose

Inputs

Outputs

Relationships

Temporal behavior

Uncertainty behavior

Examples

Counterexamples

Composition rules
```

Do not assume the first list is correct.

Generate.

Merge.

Split.

Refine.

Potential candidate primitives

```
System

Boundary

Observer

Desired Condition        (collapses Mission, Goal, Reference State)

Preference Ordering      (collapses Objective, Utility, Tradeoff)

Observed State

Latent State

State Estimate

Sensor

Observation

Evidence

Estimator

Belief

Model

Prediction

Policy

Intervention

Actuator

Resource

Constraint

Disturbance

Feedback

Delay

Time Scale

Invariant

Learning Rule

Calibration

Revision                 (of goals, of state space, of boundary)
```

But challenge every one.

### Notes on the current list

The synonym collapses above are provisional but deliberate. `Mission`, `Goal`, and
`Reference State` were three names for *desired condition*; `Objective`, `Utility`,
and `Tradeoff` were three names for *a ranking over conditions*. Five names became
two. Apply the same pressure to everything that remains.

Four additions, each justified by absence rather than theory:

- **`Observer`** — a belief with no holder cannot represent disagreement. Hospitals,
  funds, markets, democracies, scientific communities and military command all turn
  on parties holding different estimates of the same quantity. Without this primitive
  more than half the benchmark corpus flattens into a single averaged posterior that
  describes nobody.

- **`Resource`** — interventions are not free. Every real adaptive system is bound by
  capital, attention, headcount, or energy. Nothing in the original list represented
  scarcity.

- **`Calibration`** — the loop that closes on the *estimator* rather than on the
  world. It appeared only in Phase 8; it is arguably the most important loop in any
  system that must learn whether its own beliefs track reality.

- **`Revision`** — change to the *schema* of the system rather than to its parameters:
  goals rewritten, state variables discovered, boundaries renegotiated. This is
  distinct from `Learning Rule`, which improves performance within a fixed identity.
  A startup pivot, an institution captured by its opponents, and a cell differentiating
  are all revision, not learning. This is also the sharpest candidate for what
  classical formalisms cannot express (see the prior-art gate in Phase 1).

### Representational commitments

Four constraints on the representation, adopted for engineering reasons and to be
overturned only by benchmark evidence:

1. **Beliefs and desired conditions are observer-indexed.** There is no unowned
   belief. Where a system appears to hold a single belief, that is a modelling
   choice to be stated, not a default.

2. **Competing desired conditions are never scalarized in the representation.**
   A weighted sum is a *decision*, and decisions belong to the policy layer.
   The representation holds the conflict; a policy may resolve it. Collapsing
   early permanently destroys the ability to express contested tradeoffs.

3. **Every system declares its excluded-variable frontier.** State variables known
   to exist and deliberately left out of the state space are recorded, not merely
   absent. This is not documentation — it is the candidate set for `Revision` when
   the system underperforms, and the first place to look when an encoding fails.
   May be empty; emptiness is reported as a coverage metric, not an error.

4. **Unspecified values are typed.** `unknown` and `deliberately-unspecified` are
   distinct, because they have different execution semantics: an estimator should
   spend evidence-gathering budget reducing the former and must not spend it on
   the latter.

### Deliverable

```
ontology/

primitive_catalog.md

relationships.md

composition_rules.md
```

---

## Phase 3 — Benchmark Corpus

Represent many different systems.

### Three sets, not one

The corpus does two different jobs — grounding the ontology and falsifying it — and a
single undifferentiated set does neither well. Worse, encoding all sixteen while
designing guarantees overfitting to all sixteen with no way to detect it.

**Seed set — 4 systems, encoded BEFORE the ontology exists.**

Informal prose descriptions, written first. Primitives are then derived from what these
descriptions actually needed. You cannot derive an ontology from a literature survey
alone; that is the classic failure of ontology engineering, and it produces primitives
that fit the theory and not the data.

```
Thermostat            (minimal, continuous, single-actor)
Immune System         (no designer, no explicit goal, evolved)
Hospital              (multi-actor, conflicting estimates, institutional)
Startup               (revises its own goals and state space)
```

**Adversarial set — 8 systems, encoded DURING the 2–4 loop.**

Chosen to attack specific weaknesses, not for variety's sake.

```
Financial Market      (reflexive — observation changes the observed)
Military Command      (legitimacy and authority are structural)
Supply Chain          (boundary genuinely ambiguous)
Scientific Community  (metis-dominated; should hurt)
Biological Cell       (recursive viability, autopoietic boundary)
Democracy             (incommensurable goals, no scalarization possible)
Autonomous Vehicle    (hard real-time, safety invariants)
Market Maker vs Traders  (adversarial — systems modelling each other)
```

**Held-out set — 4 systems, SEALED.**

Not opened, not read, not discussed until the ontology is frozen at the end of the
2–4 loop. First-encounter encoding cost on these is the only honest measure of
generalization available. Everything else measures how well the ontology fits what it
was built against.

```
Ecosystem
Family
Factory
LLM Agent System
```

### Coverage axes

The original list had near-duplicates on the axes that matter — Factory and Supply
Chain, Startup and Investment Fund — and gaps on several. The corpus should span:

```
continuous  ⟷  discrete
fast loop   ⟷  slow loop
single actor ⟷ many actors
cooperative ⟷  adversarial
observable  ⟷  deeply latent
stationary  ⟷  non-stationary
engineered  ⟷  evolved
single goal ⟷  incommensurable goals
designed    ⟷  no designer
```

Three additions above close real gaps: **Market Maker vs Traders** (two systems
modelling each other — genuinely adversarial), **Financial Market** (reflexivity), and
**Immune System** (no designer, no stated goal).

`Investment Fund` is deliberately *not* in the corpus. It appears in Phase 8 as the
demonstrator, and having it in both would let venture-shaped assumptions enter the
ontology through the front door.

### Negative control

**A sorting algorithm.** URAS must *fail* to represent it in any useful way — it
computes, it does not adapt: no goal it could fail to meet, no state it estimates, no
evidence, no learning.

A representation that fits everything describes nothing. Without at least one system
the ontology explicitly cannot express, "domain independent" is unfalsifiable. If a
sorting algorithm encodes cleanly, the primitives have become so general they have
stopped meaning anything.

For each

Describe using exactly the same ontology.

The benchmark exists to break weak abstractions.

### Encoding metadata

Every benchmark encoding carries document-level provenance: who encoded it, from
what source material, and from whose vantage point within the system. This is not
bookkeeping — inter-encoder agreement is the strongest objective measure available
for whether the ontology is determinate or merely suggestive, and it cannot be
computed without knowing who produced which encoding.

Document level only. Per-node provenance is not worth its weight.

### Questions the corpus should settle

- Whose account gets encoded when a system contains parties that disagree? Encode
  a hospital from the administration's vantage and from the ward's, and compare.
  If the ontology cannot make the difference visible, `Observer` is not doing its job.
- Is belief *visibility* structural? In a hospital, who may see which estimate is
  not incidental — patient data and performance assessment are both restricted.
  Determine whether this needs representation or belongs to the execution layer.

### Deliverable

```
benchmarks/

  seed/                     <- prose (.md) by design: written BEFORE primitives exist,
    thermostat.md              so there is nothing to encode them in yet
    immune_system.md
    hospital.md
    startup.md

  adversarial/
    financial_market.yaml
    military_command.yaml
    supply_chain.yaml
    scientific_community.yaml
    biological_cell.yaml
    democracy.yaml
    autonomous_vehicle.yaml
    market_maker.yaml

  held_out/            <- SEALED until the ontology is frozen
    ecosystem.yaml
    family.yaml
    factory.yaml
    llm_agent_system.yaml

  negative/
    sorting_algorithm.md    <- a record of why this cannot be encoded

  coverage_matrix.md        <- generated, never hand-maintained
```

---

## Phase 4 — Contradiction Discovery

Find where the ontology fails.

Questions include

Can multiple goals exist?

Can goals conflict?

Can estimators estimate estimators?

Can systems regulate themselves?

How are nested loops represented?

Can interventions create observations?

Can loops regulate other loops?

How is uncertainty propagated?

How are competing controllers represented?

Every contradiction becomes an issue.

### Deliverable

```
ontology_failures.md
```

---

## Phase 5 — Intermediate Representation

Design the canonical IR.

### The IR is a typed graph; JSON Schema is one serialization of it

"Prefer JSON Schema" is a premature commitment, and following it directly will hit a
wall. JSON Schema validates *shape* — it cannot express the constraints that actually
matter here:

- every feedback loop must close
- every referenced observer, sensor and estimand must exist
- probability mass must be well-formed
- recursion must terminate
- no estimator may depend on its own output without a `Delay`
- every core primitive must be reachable from some `System`

So: define the IR abstractly first, as a typed graph with named node and edge kinds.
JSON Schema then becomes *a* serialization — the wire format — rather than the
definition. YAML is a second serialization of the identical graph.

Getting this order wrong means graph-level invariants get encoded as informal prose in
the schema description fields, where nothing enforces them.

### The Semantic Validator is a Phase 5 deliverable

It appears in the architecture diagram and, until now, in no phase's deliverables.
That was a hole: the diagram promised a component nobody owned.

It is the enforcement point for every constraint above, and it is what makes Phases 2–4
mechanically checkable rather than a matter of taste. Structural invariants belong in
executable form, checked on every encoding — not in a document describing what a valid
encoding would look like.

Must support

hierarchies

loops

graphs

recursion

uncertainty

timestamps

events

versioning

references

metadata

Example

```yaml
system:

  mission:

  goals:

  loops:

  estimands:

  observations:

  estimators:

  interventions:

  learning_rules:

  policies:

  constraints:
```

The exact schema should evolve.

### Schema evolution policy

The charter requires encodings to be versionable. That covers instances. It says nothing
about the *ontology itself* changing — and since "prefer deleting concepts" is a standing
rule, deletion will happen repeatedly, breaking existing encodings each time.

For something intended to remain coherent over thirty years this is core, not clerical:

- every primitive gets a stability tier — `core`, `provisional`, or `extension`
- deletions and renames ship with a mechanical migration for existing encodings
- `provisional` carries no compatibility promise; `core` does
- the coverage matrix records which benchmarks a revision invalidated

### Deliverables

```
schema/

uras.graph.md            <- the typed graph: node kinds, edge kinds, invariants
                            (the definition)

uras.schema.json         <- wire serialization (a projection, not the definition)

validator/               <- executable invariant checks

migrations/              <- one per breaking ontology revision

examples/
```

---

## Phase 6 — Visual Grammar

Do not implement.

Specify.

Every visual element must map directly onto the IR.

Need

symbols

nesting

loop notation

edge semantics

uncertainty notation

time

confidence

learning

interventions

delays

recursive systems

Produce a handoff suitable for Claude Design.

### Deliverable

```
design/

visual_language.md

interaction_model.md
```

---

## Phase 7 — Flue Compilation

This is **not** execution.

It is mapping.

How does each primitive compile into Flue?

Example

```
Observation
↓

Extractor Agent

↓

Evidence

↓

Estimator

↓

State Update

↓

Policy Evaluation

↓

Intervention Selection
```

Map every primitive.

### One backend cannot validate engine independence

Engine independence is a stated success criterion, and mapping to Flue alone cannot
establish it — it can only produce a representation shaped like Flue while everyone
believes otherwise. Overfitting to a single target is invisible from inside that target.

So sketch a **second backend on paper only**, deliberately unlike Flue. A discrete-event
simulator is the best candidate: no LLMs, no agents, no sessions, synchronous, and
strong on exactly the continuous-time regulation Flue is weak on.

It is never implemented. The mapping exercise alone is what pays, because every place
the second mapping is awkward marks a Flue assumption that leaked into the
representation.

### Firewall URAS semantics from Flue accidents

Flue is 2026 technology and the top-of-repository directive says to prefer concepts that
survive the replacement of today's LLMs. `Skills`-as-markdown-modules and `Subagents`
are current-generation framing. They may not exist in ten years; `Estimator` and
`Feedback` will.

The mapping document keeps two columns separate throughout: what URAS *means*, and how
Flue happens to *execute* it today. Nothing from the right column is permitted to flow
back into the ontology.

### What is already known about the fit

Flue (flueframework.com) is a TypeScript framework for durable AI agents built on the
Pi harness. Its primitives are `Agents` (via `defineAgent()`), `Workflows`, `Sandboxes`,
`Skills`, `Tools`, `Subagents`, and `Sessions`, with durable execution via persistent
session recording in durable streams.

Three genuine affordances:

- **Durable session recording maps almost exactly onto evidence provenance.** "Evidence
  becomes traceable" and an append-only durable stream are close to the same
  requirement. This is the strongest single point of fit, and it is not a coincidence —
  both are audit structures.
- **A Flue `Agent` holds its own context, which is a natural `Observer`.** Per-agent
  context is per-observer belief. The mapping is nearly direct.
- **`Tools` split cleanly into `Sensor` (read) and `Actuator` (write).**

Four gaps that must be built *over* Flue rather than mapped onto it:

- **No uncertainty anywhere.** Flue has no belief-with-distribution, no probability, no
  confidence. Every URAS estimand needs a representation Flue does not supply. This is
  the largest gap.
- **No `Resource`.** No budget, cost, or attention accounting visible.
- **No `Learning Rule` or `Calibration`.** Nothing closes a loop on the estimator.
- **No `Constraint` or `Invariant` as structure** — expressible only as workflow code.

And one structural mismatch, which is the most important finding and should be resolved
before Phase 7 produces anything else:

> A Flue `Workflow` runs "from a clear input to a finished result." It **terminates**.
> A URAS system is a **non-terminating regulator** — a thermostat has no finished
> result.

These are different shapes: Flue workflows are transformations, URAS loops are
homeostats. Mapping a continuous regulator onto a terminating workflow requires either
an outer scheduler that re-invokes it, or a long-lived `Agent` whose prose goal is the
regulation. Neither is natural, and the choice will leak into the representation if it
is made implicitly.

This is exactly the class of problem the second-backend sketch exists to catch — a
discrete-event simulator has no trouble with non-termination at all.

### Deliverable

```
compiler/

primitive_mapping.md

execution_model.md
```

---

## Phase 8 — Venture Demonstrator

Represent a startup.

Represent a VC fund.

Represent a single investment decision.

Compile conceptually into Flue.

Show

documents

↓

observations

↓

evidence

↓

belief updates

↓

hinges

↓

interventions

↓

decision

↓

calibration

This becomes the reference implementation.

---

## Coding Rules

Do not optimize for implementation speed.

Optimize for conceptual correctness.

Prefer deleting concepts over adding them.

Every primitive should justify its existence.

Every primitive should appear in multiple benchmark systems.

Avoid venture-specific abstractions unless absolutely necessary.

---

## Success Criteria

The project succeeds if:

- a hospital and a venture can be represented using the same ontology
- the representation remains understandable by humans
- uncertainty is a first-class concept
- diagrams, YAML and execution are all projections of the same IR
- Flue can execute meaningful subsets without changing the representation
- the ontology is significantly simpler than the systems it describes
- experts from multiple domains recognize their systems

Note the deletion: the original criterion read "…recognize their systems *without
requiring domain-specific extensions*." That target was wrong. Ashby's Law — cited in
Phase 1 — holds that a regulator needs variety matching what it regulates, so an
extension-free universal representation is either vacuous or false. The charter's own
analogies agree: LLVM IR has target intrinsics and address spaces, SQL has dialects.
The goal is a small stable core plus a disciplined extension mechanism, measured by
ratio rather than by absence.

### Making these measurable

Every criterion above is currently unfalsifiable. "Significantly simpler" and
"understandable by humans" cannot be passed or failed as written, which means the
project cannot tell whether it is succeeding.

| Criterion | Measure | Target |
|---|---|---|
| Ontology is simple | Core primitive count | ≤ 20, hard ceiling |
| Primitives are earned | Coverage matrix: benchmarks per primitive | ≥ 3, across ≥ 2 domains |
| Representation is determinate | **Inter-encoder agreement** — two encoders, same source, independently | High structural overlap |
| It generalizes | Encoding cost on the sealed held-out set | No new core primitives |
| Domain independence | Core / extension ratio per domain | Core dominates everywhere |
| Not vacuous | Negative control stays unencodable | Sorting algorithm fails |
| Experts recognize it | Structured walkthrough, fixed rubric, ≥ 2 domains | Recognition without translation |
| Degrades cleanly | Thermostat reduces to a control loop | Mechanical reduction |
| Not a POMDP in disguise | Residue survives the Phase 1 gate | Named, defended capabilities |

**Inter-encoder agreement is the most important row.** Give two independent encoders the
same source material and compare results. If the ontology is determinate, they converge;
if it is merely suggestive, they diverge, and no amount of documentation will fix that —
divergence means the primitives do not have single meanings. This is standard
inter-rater reliability practice, and it is the only proposed measure that tests whether
the representation *means* anything as opposed to being expressive enough to say
anything.

### Kill criteria

Stated so they can be recognized rather than rationalized:

- the Phase 1 residue collapses — everything reduces to known formalisms plus notation
- the 2–4 loop cannot converge: primitive count keeps climbing past 20 with each new
  benchmark
- inter-encoder agreement stays low after two rounds of catalog clarification
- the held-out set requires new core primitives, meaning the ontology only ever fit
  what it was built against
- domain experts consistently need the encoding translated back to their own vocabulary

Any one of these is a result worth having. Reaching it in Phase 1 costs weeks; reaching
it at Phase 7 costs the project.

---

## Final Goal

The ambition is **not** to build another workflow engine.

It is to create for adaptive systems what SQL became for data or what LLVM IR became for compilers: a stable, domain-independent intermediate representation that separates **how adaptive systems are specified** from **how they are executed**.

The first backend will be Flue, but the representation should remain independent of any particular execution engine, model, or agent architecture.
