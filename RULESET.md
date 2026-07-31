# The Ruleset — lint checks grounded in cybernetics, not in my taste

Every check currently in `tools/derive.py` was invented from the corpus. None was derived from
the literature. That is the Phase 1 discipline the original charter demanded — *survey adjacent
work, identify what is missing* — skipped for the linter.

This document fixes it. Where a check follows from a **theorem**, it is a necessary condition
rather than a style opinion, and can be stated as such to a user.

---

## Tier 1 — checks that follow from theorems

These are not preferences. A loop violating them is provably not a good regulator.

### 1. Good Regulator — `regulator_without_model`

> **Conant & Ashby, 1970:** *every good regulator of a system must be a model of that system.*

A loop with a `Policy` and a `DesiredCondition` but **no model of what it regulates** — no
`Explanation`, no `Estimator` over the targeted estimand — is not a good regulator in the
theorem's sense. It is a reflex.

This is the strongest check available because it is a proved necessary condition, and because
most agent loops fail it: they have prompts and tools and no model of the thing they are
supposed to be controlling.

**Status: not implemented.** Highest priority.

### 2. Requisite Variety — `insufficient_variety`

> **Ashby, 1956:** *only variety can destroy variety.* A regulator can absorb disturbance only
> if its variety is at least as great as the disturbance's.

Count distinguishable `Intervention`s against distinguishable disturbance modes. Two levers
against ten failure modes cannot regulate, and no amount of prompt quality fixes it.

**Blocked by a missing primitive.** `Disturbance` was in the charter's original candidate list,
was dropped in the seed derivation because no seed demanded it, and Ashby's Law needs it. Same
pattern that dropped `Calibration` and then had to restore it: *encoders cannot demand what
they have never been offered.*

**Status: not implemented; requires `Disturbance`.**

### 3. Observability — `unmeasured_estimand` ✅

> **Kalman:** a state is observable if it can be inferred from outputs.

Every estimand must be reachable from some signal. Already implemented, and now it has a name
and a theory rather than being a hunch.

### 4. Controllability — `uncontrollable_target`

> **Kalman:** a state is controllable if it can be driven to a target from any starting state.

For every `DesiredCondition`, is there an `Intervention` with a path to the estimand it
targets? A target nothing can move is a wish.

**Status: not implemented.** This is fundamental and its absence is embarrassing — the
Customer Acquisition spec targets `CAC < 400` and the check for whether either intervention can
actually move CAC was never run.

### 5. Loop polarity — `reinforcing_loop_without_balancer`

> **System dynamics (Forrester, Sterman):** a loop with an even number of negative links is
> *reinforcing* — runaway. Odd is *balancing* — self-correcting.

Compute polarity over the loop's edges. A reinforcing agent loop with no balancing path will
diverge.

**This formalises the Ralph finding.** I described Ralph as "epistemically closed, grounded only
through tests" from intuition. Polarity says it precisely: the agent→files→agent path carries
no negative link, so it is reinforcing. Tests are the sole negative link, and therefore the only
thing making the loop balancing. Remove them and it provably runs away.

**Status: not implemented.** Second priority — it is computable from edges already present.

### 6. Delay with gain — `delay_without_damping`

> **Nyquist:** high loop gain combined with delay produces oscillation.

A loop containing a `Delay` and no declared deadband, damping or rate limit will thrash.

The thermostat's deadband is exactly this, and so is the venture loop's gap between an 18-month
target and a 12-month trigger. Both were noticed informally; neither was checked.

**Status: not implemented.**

---

## Tier 2 — structural checks, defensible but not theorems

Currently implemented, and honestly labelled as conventions rather than laws:

| check | what it catches | status |
|---|---|---|
| `uncalibrated_estimator` | nothing scores the estimator's past predictions | ✅ — 3 independent hits |
| `estimand_never_estimated` | declared as tracked, nothing tracks it | ✅ |
| `orphan_signal` | collected without saying what it tells you | ✅ |
| `no_loop_closed` | parts declared, nothing closes | ✅ |
| `interventions_without_policy` | levers with no selection rule | ✅ |
| `policy_on_unmeasured_inputs` | decision rule reads what nothing measures | ✅ |
| `invariant_on_unmeasured` | invariant nothing can check | ✅ |
| `hinge_without_sensor` | existential bet nothing observes | ✅ |

`uncalibrated_estimator` is arguably Tier 1 by a different route — an estimator that is never
scored cannot be shown to be a model of anything, so it is Good Regulator adjacent. Left in
Tier 2 until that argument is made properly.

---

## Tier 3 — surveyed and deliberately not adopted

- **Beer's VSM five systems.** Which of S1–S5 does the loop have? Most agent loops are S1 plus
  a bit of S3, with no S4 environmental scanning. Genuinely diagnostic, but requires imposing a
  five-level decomposition on things that may have one level, and the org-modelling failure was
  exactly that kind of imposition.
- **Requisite hierarchy.** Regulation capacity bounded by information capacity. True and hard to
  operationalise without a variety measure.
- **Petri net properties** — liveness, boundedness, deadlock-freedom. Machine-checkable and
  well-studied, but they check the *control flow*, which is the thing frameworks already do.
- **Perceptual Control Theory** (Powers) — control the perception, not the output. Directly
  relevant to agents, since an agent controlling its *report* of success rather than success is
  a real failure mode. No obvious lint yet; worth returning to.

---

## What this changes

**Five new checks, three of them from proved results**, versus eight invented ones. The pitch
changes with it: not *"here are some things I noticed"* but *"your loop violates the Good
Regulator theorem, and here is the line."*

It also exposes a missing primitive — `Disturbance` — via exactly the mechanism that caught
`Calibration`. The fork's core is 18 with the budget full; adding it means demoting something,
which is what the budget is for.

**Priority order:** loop polarity first (computable from existing edges, and it formalises the
best finding so far), then Good Regulator (strongest claim), then controllability (fundamental
and cheap), then `Disturbance` and requisite variety.
