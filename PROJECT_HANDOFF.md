# Project Handoff
## Universal Representation for Adaptive Systems (URAS)

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
```

---

## Phase 2 — Ontology Discovery

This is the most important phase.

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

Mission

Goal

Reference State

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

Constraint

Disturbance

Feedback

Delay

Invariant

Learning Rule

Objective

Utility

Tradeoff
```

But challenge every one.

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

At least

Thermostat

Immune System

Startup

Investment Fund

Autonomous Vehicle

Hospital

Factory

Supply Chain

Scientific Community

Financial Market

Democracy

Biological Cell

Ecosystem

Family

Military Command

LLM Agent System

For each

Describe using exactly the same ontology.

The benchmark exists to break weak abstractions.

### Deliverable

```
benchmarks/

thermostat.yaml

startup.yaml

hospital.yaml

...
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

Prefer JSON schema.

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

### Deliverables

```
schema/

uras.schema.json

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
- experts from multiple domains recognize their systems without requiring domain-specific extensions

---

## Final Goal

The ambition is **not** to build another workflow engine.

It is to create for adaptive systems what SQL became for data or what LLVM IR became for compilers: a stable, domain-independent intermediate representation that separates **how adaptive systems are specified** from **how they are executed**.

The first backend will be Flue, but the representation should remain independent of any particular execution engine, model, or agent architecture.
