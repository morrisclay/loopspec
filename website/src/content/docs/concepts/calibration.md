---
title: "Calibration"
description: "How a loop joins prior beliefs to later outcomes and changes what it trusts."
---

> This page is generated from `CALIBRATION.md` during every site build. Edit the canonical source, not this copy.

`ATTENTION.md` is about what a loop looks at. This is about whether what it believes turns out
to be true. They are the two halves of the same thing and neither works alone.

---

## What it is, and what it is not

> **Verification** asks *is this output good?* — grade the artifact in front of you.
> **Calibration** asks *has this thing's confidence historically tracked reality?* — score past
> predictions against what actually happened.

Agent frameworks commonly foreground the first. The measured reference corpus does not make
the second a first-class loop contract. LangChain's *Art of Loop Engineering* has a
verification loop with rubric grading and human touchpoints, and **no discussion of confidence
calibration or whether agent confidence aligns with correctness.**

An agent that is verified but uncalibrated **passes every rubric and still cannot tell you how
much to trust it next time.** That sentence is the whole gap.

The distinction is not academic. A verified system knows its last answer was good. A calibrated
system knows that when it says 0.8 it is right about 80% of the time — which is the only thing
that lets you decide *how much to depend on it*, and the only thing that lets a human allocate
attention rationally across a fleet of agents.

## The evidence

| corpus | n | result |
|---|---|---|
| published reference examples | 10 | **10/10** form a belief nothing scores |
| eval harnesses — the layer built to catch this | 4 | **4/4** ship a judge nothing scores |
| real systems, three independent authors | 3 | **3/3** — different purposes, one a widely-copied public technique |

The 10/10 and the 4/4 both **survived independent encoding** by a model that had never seen
this project. `belief_never_checked` is one of only two checks here that did.

**The regress, and why it matters:** the eval layer is the field's answer to loop quality. It
is also an estimator, and nothing calibrates it. So the mechanism built to check agents has the
defect it exists to catch — the regress is moved one level up, not closed.

**And the partial refutation, kept because it is the honest version:** G-Eval's *method* was
validated against human judgments in its originating paper. But `criteria` is arbitrary free
text and the validator checks only that one of `criteria`/`evaluation_steps` is *present*.

> A judge validated for one rubric, deployed with another, is not a validated judge. The
> paper's correlation does not travel with the class.

## Why it is genuinely hard, not merely neglected

Worth stating, because "nobody calibrates" reads as an accusation and it should not.

1. **It requires an immutable record of what was believed *before* the outcome arrived.** Not a
   log of what happened — a record of the prediction, timestamped, un-revisable. Most agent
   infrastructure stores traces for debugging, which is a different thing: a trace tells you
   what the agent did, not what it expected.
2. **The outcome often arrives much later than the belief**, or never. A deal that never closed
   is not a refuted prediction; it may be an abandoned one.
3. **It needs a resolution criterion agreed in advance.** `settled_by:` exists in the format for
   exactly this — *what observation would finally decide this?* — and it is the field almost
   nobody fills in.
4. **Outcomes are often unobserved by construction.** The counterfactual — what would have
   happened had the agent chosen otherwise — is not available. Calibration on the taken branch
   only is still worth having, and is not the same as knowing you chose well.

This is why the open Flue question is on the critical path rather than a curiosity:

> **Can evidence chains be *reconstructed* from durable stream records, or only replayed?**

If records are replay-only, calibration cannot be built on them, and that is a finding about
the representation and not just the runtime.

## What the format says today

```yaml
beliefs:
  product_market_fit:
    question: "If we keep buying customers like this month's, will they stay?"
    how: bayesian
    checked_by: quarterly_cohort_review     # ← what scores it
    checked_against: six_month_retention    # ← the later outcome observation
    scoring_rule: Brier score               # ← how prediction and outcome are compared
    window: 200 cohorts                     # ← the cohort over which loss is interpreted
    adjusts: trust                          # ← what changes when performance is poor
    every: quarterly                        # ← how often the review runs
    settled_by: "a cohort retains above 80% at month 6"   # ← what would decide it
    known_bias: "reads high when volume is low"           # ← which way it is wrong
```

- **`checked_by`** — the check. Its absence trips `belief_never_checked`.
- **`checked_against`, `scoring_rule`, `window`, and `adjusts`** — the structural contract
  joining past calls to later outcomes and closing a revision path. Missing parts trip
  `incomplete_calibration_contract`.
- **`settled_by`** — what makes the belief refutable at all. A belief with no settling
  condition cannot be calibrated even in principle.
- **`known_bias`** — the direction it is expected to be wrong in. Cheap to write, and it is the
  thing a reader most wants and most rarely gets.
- **`observes.*.checked_by`, `value_metric`, `review_window`, `review_every`, and `adjusts`** — the attention
  counterpart: what reviews whether *looking here* earned its cost, over what cohort, and what
  changes when it did not. Missing parts trip `incomplete_attention_contract`.

## The result boundary

**The design format says how a belief will be checked. It does not store what a runtime check
found.**

`checked_by: quarterly_cohort_review` records that a check exists. There is nowhere to record
that the review found the estimator overconfident by 0.2, or that it has been right 6 of the
last 8 quarters, or that its Brier score is drifting. Calibration is a *result*, and this
notation currently only carries the *intent*.

That separation is intentional in v1.1. A design spec is versioned intent; calibration results
are time-indexed operational evidence. Putting the latest score into the spec would turn a
stable design contract into a mutable monitoring record and make semantic diffs mix design
changes with new observations. A future evidence artifact may reference the spec, frozen
predictions, outcomes, and scoring results, but it belongs beside the language rather than as
another authoring key. It should be admitted only with executable scoring semantics and real
cases that require it.

## Why attention and calibration are the same project

They are duals, and each is unusable alone:

| | attention | calibration |
|---|---|---|
| side of the loop | the input — what enters | the output — what came out |
| the question | *am I looking at the right things?* | *is what I concluded true?* |
| what it scores | a **signal** | an **estimator** |
| failure when absent | paying for information that changes nothing | confidently wrong forever |

**Calibration is how you find out whether your attention was well spent.** A source that never
moved a belief that turned out to matter was not worth watching — and you cannot know that
without scoring the beliefs. Conversely, **attention determines what you can calibrate
against**: a belief about something you never observe has no outcome to be scored on. That is
`unmeasured_estimand`, and it is why a declared observation path is a prerequisite rather than
a nicety. This is structural sensing, not a Kalman observability result.

Both are **meta-control**. The operating loop observes, believes, decides, and acts. Attention
and calibration are loops *about parts of that loop* — regulating the observing and the
believing rather than directly regulating the world.

> **The operating loop is what agent frameworks foreground. Attention and calibration loops
> are omitted by most examples in the measured corpus, and this notation makes them
> discussable.**

This is cybernetically useful without exhausting second-order cybernetics. LoopSpec now records
who draws the system boundary, for what purpose, and what they place inside and outside. A
fuller second-order account must also represent how observing changes the system and how the
observer's distinctions, purpose, and boundary are themselves revised.
