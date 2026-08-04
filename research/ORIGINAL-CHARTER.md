# Original URAS charter

This is the original universal-adaptive-systems charter, moved intact from the primary README
when authoring v1.1 / IR v2.1 converged on the narrower agent-loop scope. It is retained as a
research artifact, not as the current product claim. See [`../FORK.md`](../FORK.md) for the
scope decision and [`../CONVERGENCE.md`](../CONVERGENCE.md) for the release path.

---

## Rethinking how we specify intelligent systems

---

## The Premise

Software engineering has produced remarkable abstractions for computation.

We have languages for algorithms, databases, distributed systems, user interfaces, infrastructure, machine learning, and hardware.

What we still lack is a universal way to describe **adaptive systems**.

Today, every organization, autonomous system, startup, government, robot, investment fund, supply chain, or scientific institution ultimately exists to maintain, improve, or transform some part of the world under uncertainty. They all observe, infer, decide, intervene, learn, and adapt.

Yet we have no common representation for these behaviors.

Every domain reinvents its own concepts, diagrams, tooling, and execution models.

This project explores whether a common representation is possible.

---

## Why Now?

Cybernetics has existed for more than seventy years.

The mathematics of feedback, control, adaptation and regulation are well understood.

The missing ingredient was never the theory.

It was instrumentation.

Historically, most adaptive systems could only observe structured signals.

Temperature.

Pressure.

Velocity.

Voltage.

Today's intelligent systems can observe something fundamentally different.

Documents.

Meetings.

Code.

Scientific literature.

Emails.

Contracts.

Conversations.

Research papers.

Customer interviews.

Software repositories.

Natural language has become machine-readable.

Large language models transformed text from passive information into active sensor input.

At the same time, modern software agents can increasingly act upon digital environments through APIs, workflows, browsers, and software systems.

For the first time, we can construct feedback loops around knowledge work itself.

This dramatically expands the space of systems that can be represented and eventually executed.

---

## The Gap

Today's software describes **how computation happens**.

It does not describe **how adaptive behavior emerges.**

Programming languages express:

- functions
- objects
- data structures
- state
- messages
- concurrency

Workflow systems express:

- sequences
- dependencies
- triggers
- retries

Machine learning frameworks express:

- optimization
- inference
- prediction

None of these make the following concepts first-class:

- goals
- uncertainty
- evidence
- beliefs
- interventions
- regulation
- feedback
- adaptation
- learning from operational experience

Instead these concepts remain scattered across documents, dashboards, meetings, spreadsheets, prompts, and human intuition.

Organizations are adaptive systems, but we do not specify them as such.

---

## The Opportunity

We believe adaptive behavior deserves its own abstraction layer.

Instead of programming *computations*, we should be able to specify *adaptive systems*.

Imagine describing:

- what the system is trying to regulate,
- what it believes,
- what it cannot observe directly,
- how evidence updates those beliefs,
- what interventions are available,
- how uncertainty propagates,
- how learning changes future behavior,

without committing to any particular implementation.

That representation should be independent of:

- programming language
- workflow engine
- LLM provider
- orchestration framework
- database
- execution runtime

Just as SQL separates data specification from storage engines, a representation for adaptive systems should separate adaptive intent from execution.

---

## Our Hypothesis

There exists a relatively small set of universal primitives capable of describing adaptive systems across domains.

These primitives should be expressive enough to represent:

- biological systems
- organizations
- autonomous robots
- venture capital firms
- governments
- supply chains
- hospitals
- scientific institutions
- ecosystems

without requiring fundamentally different conceptual models.

This is a hypothesis and may be false. A representation that fits every domain
equally well risks fitting none of them usefully — a small core plus a disciplined
extension mechanism is the more likely shape of a real answer, as it was for LLVM IR
and for SQL, neither of which achieved reach without dialects and target-specific
constructs. The measure to watch is the ratio of core to extension, not the absence
of extension.

If such a representation exists, diagrams, textual specifications, simulations, execution engines, and explanations become different projections of the same underlying model.

---

## Design Principles

The representation should be:

- domain independent
- composable
- recursive
- graph-native
- uncertainty-aware
- explainable
- machine-readable
- human-readable
- executable
- versionable
- inspectable
- extensible

The core should remain intentionally small.

New domains should emerge from composition rather than special cases.

---

## Representation Before Syntax

This project is **not** primarily about inventing a programming language.

Syntax is an implementation detail.

The central artifact is a canonical representation.

Potential projections include:

- graphical notation
- textual DSL
- JSON schema
- YAML
- visual editor
- simulation engine
- execution runtime
- documentation
- audit trails

All should remain consistent because they describe the same underlying structure.

---

## Relationship to Cybernetics

Cybernetics provides the intellectual foundation.

It introduced many of the concepts this work builds upon:

- regulation
- feedback
- control
- adaptation
- homeostasis
- variety
- recursive organization

Our objective is not to replace cybernetics.

Our objective is to provide an operational representation suitable for modern software systems.

Cybernetics explained adaptive systems.

We aim to make them specifiable, executable, inspectable, and evolvable.

---

## Relationship to Artificial Intelligence

Artificial intelligence is not the subject of this project.

Artificial intelligence is an enabling technology.

Large language models become one possible implementation of:

- sensors
- estimators
- reasoning components
- evidence extraction
- policy evaluation

Future execution engines may use entirely different technologies.

The representation should remain stable regardless of implementation.

---

## Relationship to Flue

Flue is the first execution backend.

URAS should describe *what* adaptive behavior exists.

Flue determines *how* that behavior is executed.

The relationship is analogous to:

- SQL → PostgreSQL
- LLVM IR → machine code
- React → React Runtime

URAS should remain independent from Flue while being able to compile into it.

---

## Research Questions

Among the questions this project seeks to answer:

- What are the universal primitives of adaptive systems?
- How should uncertainty be represented?
- How should latent state differ from observable state?
- How should evidence modify beliefs?
- How should competing goals interact?
- How should nested feedback loops compose?
- Can organizations, biological systems, and autonomous software share the same representation?
- Can adaptive behavior become executable without losing interpretability?

---

## Non-Goals

This project is not:

- another workflow engine
- another agent framework
- another orchestration platform
- another BPMN replacement
- another prompt language
- another automation tool

Execution engines will evolve.

The representation should outlive them.

---

## Long-Term Vision

If successful, this project could provide a common language for describing adaptive systems across science, engineering, organizations, and artificial intelligence.

Rather than treating adaptation as an emergent property hidden inside software, adaptive behavior itself becomes an explicit design artifact.

Goals become inspectable.

Beliefs become observable.

Evidence becomes traceable.

Learning becomes versioned.

Feedback loops become first-class citizens.

Each of these is a form of legibility, and legibility is never symmetric — it makes
some parties visible to others. A representation of a hospital is written by someone,
from somewhere, and the beliefs it records will be the beliefs of whoever held the
pen. This is why beliefs in URAS are observer-indexed rather than free-floating, and
why encodings record their own provenance: not as an ethical gesture, but because a
representation that hides its vantage point is one that cannot be checked.

The ambition is not merely better automation.

The ambition is to establish a durable representation for adaptive systems analogous to the role that relational algebra played for databases or intermediate representations played for modern compilers.

Whether this ultimately becomes a language, a standard, a compiler, a visual notation, or something entirely different is intentionally left open.

The representation comes first.

Everything else follows.
