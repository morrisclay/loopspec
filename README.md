# Universal Representation for Adaptive Systems (URAS)

**A simple YAML for describing and arguing about agent loops. Applied cybernetics, and two
things every framework is missing: attention and calibration.**

Every agent framework builds the **first-order** loop — observe, believe, decide, act. None
builds the two loops *about* that loop:

- **Attention** — *am I looking at the right things, at what cost?* The input side.
- **Calibration** — *does what I believe turn out to be true?* The output side.

They are duals. Calibration is how you find out whether your attention was well spent;
attention determines what you can calibrate against at all. **Neither exists in any agent
framework**, and a notation is how they become sayable — what a format has a field for is what
people look at, and what it has no field for is what they never think to check.

```yaml
loop: customer_acquisition
runs: weekly

goal:
  cost_per_customer: { keep: below 400 }

beliefs:
  product_market_fit:
    question: "If we keep buying customers like this month's, will they stay?"
    how: bayesian
    checked_by: quarterly_cohort_review      # ← leave this out and you can SEE the hole

observes:
  billing_events:      { informs: cost_per_customer, origin: outside, how: measured, source: Stripe }
  customer_interviews: { informs: product_market_fit, origin: outside, how: reported, cost: high }

actions:
  increase_budget: { moves: cost_per_customer, can_undo: yes }
  exit_channel:    { moves: cost_per_customer, can_undo: no, needs_approval: founder }

asks_human_when:
  - "product_market_fit falls below 0.4"

people:
  founder: { human: yes, loses_if_wrong: "the company", sees: [cost_per_customer] }
```

**[`ATTENTION.md`](ATTENTION.md)** works out the three levels attention operates at — the
author's (a field is a place you have to look), the loop's (what it observes, at what cost —
and the finding that *nothing had ever scored a signal*), and the humans' (who must look, and
who pays when it is wrong).

**[`CALIBRATION.md`](CALIBRATION.md)** is the other half: verification asks *is this output
good?*; calibration asks *has this thing's confidence historically tracked reality?* The field
has built the first thoroughly and **the second has no name in it**.

**What was found by looking:** across 10 reference examples written by framework authors to
demonstrate best practice, **10/10 form a belief nothing scores** and **10/10 steer toward a
condition with no model of what produces it** — both robust to independent encoding. The eval
harnesses built to catch this **trip the same check, 4 of 4.** Half the published loops have a
ceiling nothing reads.

**You cannot diff two blog posts. You can diff two specs** — `tools/compare.py` puts ten
published loops side by side, generated from their specs. Reflection and reflexion differ in
exactly one column, and that column is the whole argument between them.

### Where to start

| | |
|---|---|
| **[`docs/GETTING-STARTED.md`](docs/GETTING-STARTED.md)** | **write your first spec — ten minutes, no framework to install** |
| [`docs/COOKBOOK.md`](docs/COOKBOOK.md) | the common loop shapes — reflection, judge, RAG, tree search, verifier — and **what each one structurally costs** |
| [`docs/LINTING-EXISTING.md`](docs/LINTING-EXISTING.md) | the brownfield path: lint a system you did not spec, including the three times it gave me a wrong answer |
| [`docs/CHECKS.md`](docs/CHECKS.md) | every check: felt symptom, what it looked at, how to fix, with a real example |
| **[`SYNTHESIS.md`](SYNTHESIS.md)** | where the field is, what this contributes, **and what it cannot claim** |
| **[`ATTENTION.md`](ATTENTION.md)** | half one — a notation is an attention device |
| **[`CALIBRATION.md`](CALIBRATION.md)** | half two — and why it is hard rather than neglected |
| [`REFERENCE.md`](REFERENCE.md) | every key — generated from `schema/loop.keys.yaml` |
| [`NOTATION.md`](NOTATION.md) | the diagram language, independent of any renderer |
| [`REFERENCES.md`](REFERENCES.md) | every external source and the decision it shaped |
| [`RULESET.md`](RULESET.md) | the checks, and which follow from theorems |
| `examples/field/` | four real systems; `research/published_study/` two pre-registered studies |

### The toolset

Six tools, one notation. Nothing here is a framework — the spec is the artifact and everything
else reads it.

```bash
python3 tools/loop.py     spec.loop.yaml --lint   # expand + validate + the checks
python3 tools/diagram.py  spec.loop.yaml --md     # mermaid; defects are DRAWN, not appended
python3 tools/compare.py  specs/*.loop.yaml       # argue about loops side by side
python3 tools/verify.py   spec.loop.yaml build/   # did compilation drop the approval gate?
python3 tools/gen_spec.py --check                 # reference + JSON Schema, generated
```

**Compiling has no tool, deliberately.** Hand the spec and a target name to any LLM — fidelity
is flat from 8B to frontier (0.898 → 0.993). `tools/compile_flue.py` remains as a reference
implementation of the mapping, not as the mechanism. If the target is newer than the model,
send one page of its API alongside: Flue went from **18% → 100%** on that alone.

---

*Everything below is the original charter, kept as written. The project has since forked to
agent loops specifically — see [`FORK.md`](FORK.md) — on the argument that agent loops are the
first domain where cybernetic claims can actually be checked. Universality stops being a
premise and becomes a hypothesis to test afterwards.*

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
