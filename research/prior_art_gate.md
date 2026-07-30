# Phase 1 — The Prior Art Gate

> **Why is URAS not a Dec-POMDP with better ergonomics?**

This document exists to answer that or concede it. It is written as prosecution first,
because the failure mode is a defence that was never tested.

**Verdict in advance:** the project survives, but on a substantially narrower and
sharper claim than the charter originally implied. Of seven proposed residue
capabilities, **three are genuine expressivity gaps, three are representational
benefits only, and one does not survive at all.** The three survivors appear to be one
capability seen at three scales, which — if it holds — is a much stronger result than
seven loose items.

---

## The prosecution case

Most of the candidate primitive list already has names, and they are older than they look.

| URAS candidate | Existing name | Age |
|---|---|---|
| `State Estimate` / `Belief` | belief state `b(s)` | ~60y |
| `Latent State` | hidden state | ~60y |
| `Sensor` / `Observation` | observation function `Ω` | ~60y |
| `Model` / `Prediction` | transition function `T` | ~60y |
| `Estimator` | Bayes filter | ~60y |
| `Policy` | `π` | ~60y |
| `Intervention` / `Actuator` | action set `A` | ~60y |
| `Preference Ordering` | reward function `R` | ~60y |
| `Constraint` / `Invariant` | constrained MDP | ~30y |
| `Learning Rule` | model-based RL | ~35y |
| `Delay` | k-step observation lag | ~40y |
| `Disturbance` | stochastic transition | ~60y |
| `System` nesting | options / hierarchical RL | ~25y |
| Factored state | dynamic Bayesian network | ~30y |
| Multiple actors | Dec-POMDP | ~25y |
| Actors modelling actors | I-POMDP | ~20y |
| `Calibration` | proper scoring rules, reliability diagrams | ~70y |
| `Resource` | budgeted / constrained MDP | ~30y |

That is the large majority of the list, with execution semantics and composition rules
already worked out. The prosecution's summary: URAS is a Dec-POMDP with a YAML syntax
and a nicer vocabulary.

**This case is strong and must be answered item by item, not in aggregate.**

---

## Capability-by-capability adjudication

### 1. Goal revision — SURVIVES

**Prosecution.** Reward uncertainty is well-studied: Bayesian IRL, CIRL, preference-based
RL, reward-learning POMDPs. Make the reward parameters part of the latent state and
infer them. Formally routine.

**Defence.** All of that machinery infers a reward that is *unknown but fixed*. There is
a ground truth being approached. That is estimation, not revision.

What cannot be expressed is a goal that changes **because the system chose to change
it** — endogenous, non-truth-tracking. A startup pivoting is not discovering the
objective it always had; it is adopting a new one, and the old one was not wrong. To
formalize this the reward would have to be an *action*, which breaks the framework's
constitutive separation of reward from action.

**Survives, narrowly.** The distinction is *exogenous-unknown-fixed* vs.
*endogenous-chosen-new*, and it must be stated that precisely. Stated loosely — "goals
can change" — it collapses immediately into Bayesian IRL.

### 2. State-space revision — SURVIVES ON REPRESENTATIONAL GROUNDS ONLY

**Prosecution.** Nonparametric Bayes handles growing state spaces: infinite HMMs,
Dirichlet processes, the Indian Buffet Process. And formally, any "new" variable can be
pre-included with negligible prior mass. `S` is already effectively unbounded.

**Defence.** Nonparametric methods grow *within a specified hypothesis class*; they
cannot represent discovering a variable nobody had conceived of, because the class had to
be written down. The pre-include-everything move is a formal trick that fails in
practice — you cannot enumerate the unconceived.

But this is honestly a weaker defence than it first appears. The real gap is not
expressivity: it is that no formalism has anywhere to **record** that the state space
changed, when, why, and on whose recognition.

**Survives as a representation need, not an expressivity gap.** Distinction preserved
deliberately — see the honesty note below.

### 3. Observer plurality — SURVIVES, WEAKENED

**Prosecution.** The strongest counter in the document. **I-POMDPs** model agents'
beliefs about other agents' beliefs, nested to arbitrary depth. POSGs, plus the whole
epistemic game theory apparatus, cover interactive knowledge thoroughly.

**Defence.** I-POMDPs are irreducibly *subjective* — every model is indexed to one
agent's viewpoint. They express *my belief about your belief*. They have no vantage in
which "the ward and the administration disagree about readmission risk" is a
**representable fact** rather than two separate unreconciled models.

That vantage is the one that matters in practice, because the party who needs it is
typically a third one: an auditor, a board, a regulator, a historian. Secondarily,
I-POMDP nesting is computationally brutal and near-unused outside the literature.

**Survives, but the claim must be stated as "disagreement as inspectable fact," not
"agents hold different beliefs."** The latter is solved and has been for twenty years.

### 4. Negotiable boundary — DOES NOT SURVIVE

**Prosecution.** Boundary membership is a modelling choice. Put membership variables in
the factored state. Nothing prevents it.

**Defence.** None available. This is a representational convenience, not a limit of any
formalism.

**Does not survive as an expressivity claim.** Consistent with the charter's decision to
defer boundary-as-relation until a benchmark actually forces it — that deferral now has
a second, independent justification.

### 5. Evidence provenance — SURVIVES ON REPRESENTATIONAL GROUNDS ONLY

**Prosecution.** Not a POMDP concern in either direction. Nothing forbids logging.

**Defence.** Correct — and that is the point. The formalism *permits* provenance and
does not *have* it. The claim is not that provenance is inexpressible; it is that making
it structural and mechanically checkable is worth doing, and no existing formalism does.

**Survives as representation.** Also the item with the clearest practical value and the
best execution fit — see `flue_notes.md` on durable streams.

### 6. Recursive viability — SURVIVES

**Prosecution.** Hierarchical RL, the options framework, MAXQ, feudal RL. Each level
carries its own value function. Beer's VSM levels are nested POMDPs.

**Defence.** HRL sub-policies are **subordinate**: they optimize a decomposition of the
parent's objective. Beer's recursion means each level is a *complete viable system* with
its own goals, which may conflict with the parent's, its own model of its own
environment, and genuine autonomy.

A hospital department has goals nobody assigned it and the executive does not share. HRL
cannot express **principled subordinate defection** — a sub-unit correctly pursuing an
objective the parent would veto. In HRL that is simply misspecification.

**Survives.**

### 7. Legitimacy — DOES NOT SURVIVE

**Prosecution.** Action masking: feasible action sets `A(s)` conditioned on state.
Constrained MDPs. Entirely routine.

**Defence.** Formally, legitimacy *is* an action mask. The residue is that **who** holds
the authority and **why** is not representable — only *that* the action is unavailable.
For hospitals, military command and democracies, the who and why are the substance.

**Does not survive as expressivity, and is weaker than #5 even as representation.**
Retain as an open modelling question, not a differentiator.

---

## The likely unification

Items 1, 3 and 6 look like one capability observed at three scales:

| Scale | Manifestation |
|---|---|
| Over time (1) | goals change endogenously rather than being estimated |
| Across parties (3) | multiple parties form goals and beliefs independently |
| Across levels (6) | nested units form goals autonomously, possibly against the parent |

The common structure: **the system contains multiple independent loci of goal
formation.** POMDPs — every variant, including Dec- and I-POMDP — assume a single
exogenous objective supplied from outside the model. That assumption is the axiom URAS
breaks.

If this unification holds, the thesis becomes considerably more defensible than seven
loose items:

> **URAS represents adaptive systems containing multiple independent loci of goal
> formation — whose goals change endogenously, whose disagreement is an inspectable
> fact, and whose nested units retain genuine autonomy — over a substrate that remains
> POMDP-reducible when those loci collapse to one.**

That last clause is the reduction floor, and it now has a precise meaning: **collapse
the goal-forming loci to one and URAS should reduce to a POMDP exactly.** A thermostat
has one locus. A hospital has dozens.

**This unification is a hypothesis, not a finding.** It should be attacked in the first
turns of the 2–4 loop. If it holds, the primitive budget gets much easier, because
`Observer`, `Revision` and recursive `System` become three faces of one construct.

---

## Honesty note: expressivity vs. representation

Three survivors are representational rather than expressivity claims. That distinction
must not be blurred, because blurring it is how this project would become
indefensible — but it is also **not a weakness**, provided the right thing is claimed.

LLVM IR is not more expressive than assembly. SQL is not more expressive than C.
Relational algebra added no computational power to anything. Their value was separation
and checkability, and both are cited in this project's own README as the models to
follow.

So the pitch is *not* "we can express what POMDPs cannot." It is:

1. **One genuine expressivity gap** — endogenous, plural, recursive goal formation.
2. **Three structural benefits** — state-space revision recorded, provenance made
   first-class, encodings mechanically checkable.
3. **Reduction to known formalisms** when the extra structure is unused.

Claiming (1) alone overreaches. Claiming (2) alone is a schema project, not a research
project. The combination is defensible, and it is what the gate permits.

---

## What this changes upstream

- **`Observer`, `Revision`, and recursive `System` may be one primitive**, not three.
  Test early — it would be the single largest simplification available.
- **`Legitimacy` is not a differentiator.** Do not add a primitive for it. Revisit only
  if the military-command or democracy benchmark cannot be encoded without one.
- **`Boundary` stays a simple property.** Second independent reason to defer.
- **The reduction floor is now testable, not rhetorical:** collapse to one goal-forming
  locus, and the encoding must reduce to a POMDP.
- **The README's claim needs narrowing.** "No common representation exists" is false as
  written — Dec-POMDPs are one, and they are older than most of this project's
  intellectual furniture. The true claim is that no representation makes plural
  endogenous goal formation first-class while remaining reducible.

---

## Reading order for `comparison.md`

Not the charter's list order. POMDPs are the competitor, not an item.

1. **POMDP / Dec-POMDP / I-POMDP** — read first, read hardest
2. **Hierarchical RL, options, MAXQ, feudal RL** — the counter to recursive viability
3. **Bayesian IRL, CIRL, preference-based RL** — the counter to goal revision
4. **Nonparametric Bayes** — the counter to state-space revision
5. **Beer's VSM** — the strongest source for what HRL is missing
6. **Ashby** — requisite variety, bearing directly on the core/extension ratio
7. Statecharts, Petri nets, System Dynamics, BPMN — notation lessons, weak competitors
8. Everything else in the charter's list

Items 1–4 are the adversaries. Everything after 5 is furniture.
