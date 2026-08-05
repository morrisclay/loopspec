# Fork — a representation language for cybernetic loop engineering

> [!NOTE]
> **Archived scope-decision record.** This explains the move from the original URAS programme
> to LoopSpec. It is provenance, not onboarding or a current language specification. See the
> product [`README`](../../../README.md) for the current system.

**Scope: agent control loops. First compile target: Flue.**

This supersedes the URAS charter. Everything before it is retained as the research programme
that produced this narrowing, and as the evidence for it.

---

## What changed

The original charter's success criterion was:

> a hospital and a venture can be represented using the same ontology

**The corpus answered no**, and the answer is quantified:

```
                 determinacy   estimand agreement
simple loop         0.881            1.00
agentic loop        0.878            1.00
organisation        0.692            0.46      (37 pairs)
```

Two separate individuation rules were written to fix estimand agreement on organisations.
Both failed — `0.122 → 0.111`, then `0.111 → 0.000`. The problem was never rule-shaped. Loops
converge and organisations do not.

**The execution boundary falls in the same place.** Of twenty primitives, four have no Flue
mapping: `Consequence`, `DesiredCondition`, `PreferenceOrdering`, `Resource`. I recorded that
as a Phase 7 gap. It is a boundary marker — what fails to compile is the multi-party
machinery, and what compiles is the loop.

**And the only human-validated result was an agent loop.** One encoding of `/complicate`,
63 lines: **2 of 4 claims genuine, both rated "changes a decision"** — against 11 hand-asserted
claims across the whole prior corpus that produced zero.

## What this is for

Agent frameworks let you **build** loops. None of them let you **reason about** loops as
control systems.

Flue gives you `Agent`, `Action`, `Tool`, sessions, durable streams. Nothing in it — or in any
comparable framework — will tell you:

- your estimator has **no calibration**, so its trust is unearned
- your loop's signal is **produced by its own intervention**, so it can converge on confidence
  from evidence it chose to seek
- your policy reads three quantities and **only one is measured**
- your invariant references something **nothing observes**, so its violation is undetectable
- your estimator **reads and writes the same estimand** with no delay — an algebraic loop

Every one of those is already implemented and checkable. The first two landed with a human on
a real system this week. They are invisible in code and obvious in the graph.

**That is the wedge: a design language and linter for agent control loops.** Not a universal
representation. Not an ontology of everything.

## Core — 18 primitives

Re-derived for this scope from the 20 that survived the general programme.

**The loop (11)** — nothing works without these
`Loop` · `Signal` · `Estimand` · `Estimator` · `Estimate` · `DesiredCondition` · `Policy` ·
`Intervention` · `Delay` · `TimeScale` · `Constraint`

**Third order (3)** — what makes it more than a thermostat
`Explanation` · `Calibration` · `Revision`

An agent loop that only regulates is a thermostat with a language model in it. These three are
the difference: a **mechanism** that can be refuted, a **score** on the estimator's past
predictions, and a way to change the schema when the categories turn out wrong.

**Agent context (4)**
`System` · `Boundary` · `Party` · `Resource`

`Boundary` is what the agent can reach — tools, data, sandbox. `Resource` is tokens, time and
compute, which Flue does not track and every real agent is bound by.

**Demoted to extension (2)**
`PreferenceOrdering` · `Consequence` — multi-party incommensurable objectives and asymmetric
stakes. Real, and out of scope. They are what made organisations hard.

## What carries over

| carries over | why |
|---|---|
| the canonical flat graph | comparable and checkable; 63 lines fits a screen |
| `tools/validate.py` | 15 invariants; caught real defects in third-party output three times |
| `tools/derive.py` | went **1-for-1** on the human test — the only tool with a validated hit |
| the Flue mapping | `Loop → Agent`, `Intervention → Action`, idempotency from Flue's own docs |
| loop identity rule | one loop per (timescale, closing intervention) |
| estimand individuation | the settling-observation test |
| `Estimator.idempotency_basis` | required — Flue documents at-least-once execution |

## What is dropped

- The universality claim, and the SQL/LLVM analogy with it.
- Multi-party organisational modelling. Hospitals, Toyota, institutions.
- The metis problem — unwritten knowledge that runs a place. Agent loops have none; they are
  code.
- `D` as a headline metric. Loops already sit at 0.88 with perfect estimand agreement, so it
  has little left to measure here.

## What replaces the score

The five-term geometric mean was built for an ontology programme. For a language the measure
is simpler and harder:

**Does a loop encoding find something in a real agent loop that its author did not know, and
would act on?**

Current record: **2 of 4, n=1 system, one operator.** That establishes the rate is not zero,
which after 20 prior attempts was the thing in doubt. It establishes nothing else.

## Open questions

1. **Surface syntax.** Two candidate forms exist, both authored by the operator and both mapping
   cleanly onto the IR: loop-centric YAML, and a `loop { goal / observe / estimate / policy /
   invariant }` DSL. The DSL reads better. The IR stays flat and canonical; the DSL is a
   projection.
2. **Does the linter hold up across loops?** One system, four claims. The next test is three
   more real agent loops, from someone other than their author.
3. **Round-trip.** Can a Flue agent be *read back* into a loop encoding, so the linter runs on
   code that already exists rather than only on hand-written specs? That is the difference
   between a design tool and an adoption path.
4. **Name.** Working title `governor`, after Watt's — the founding cybernetic device and
   literally a loop that regulates. Provisional.

## The honest risk

The fork rests on **one human-validated data point.** Two of four claims, on a system its
adjudicator built, judged by that adjudicator.

The general programme died of exactly this: findings that looked solid at n=1 and dissolved at
n=19. The correct next move is therefore not to build the language. It is **three more agent
loops, authored by other people**, and to hold the fork lightly until they land.
