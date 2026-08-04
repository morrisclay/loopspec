---
title: "Attention"
description: "How the notation directs author attention, represents signal attention, and allocates human attention."
---

> This page is generated from `ATTENTION.md` during every site build. Edit the canonical source, not this copy.

A late reframe, and the right one. The linter is a consumer of the format, not the point. The
point is **a simple YAML people can describe and argue about loops in** — and a notation is an
attention device. It works at three levels, and until they were named they were being confused.

---

## L1 — the notation directs the *author's* attention

The thesis has always been *"you do not check for a defect you have no word for."*

That is an **attention** claim, not a knowledge claim. Nobody building agent loops is ignorant
of the idea that a judge might be miscalibrated. They are not *looking* at it, because nothing
in their tooling points there. Three careful authors of three real systems each shipped an
estimator nothing scores; the framework authors' own reference examples do it 10 out of 10.
These are not people who lack the concept.

**A field is a place you have to look.** A format with `checked_by:` makes its absence visible
on the page. A format without it makes the question unaskable, and the absence invisible.

This is why the blind syntax test mattered more than it first appeared. Three models designed
the syntax without seeing this one and **3/3 rejected every jargon word** — `regulates`,
`estimates`, `calibrated_by`, `acts`. A notation nobody will read directs nobody's attention.
Legibility is not polish here; it is the mechanism.

And it is why compilation legibility matters: a notation that requires a bespoke compiler to
try will be harder to adopt, and one that does not survive contact with the frameworks people
already use is a private language. The exploratory compile study measured element preservation,
not executable correctness, and found target API documentation was the decisive missing input.

## L2 — the spec describes the *loop's* attention

`observes` is literally what the loop pays attention to. Each entry carries what it costs
(`cost`), where it came from (`origin: outside | ourselves`), and how it was obtained
(`how: measured | reported | calculated`).

Here is the historical asymmetry that was invisible until someone named it:

> **Before the attention contract, every `Calibration` scored an `Estimator`. Nothing scored
> a `Signal`.**
>
> The whole apparatus asks *was my conclusion right*. It never asks *was my looking right*.

Three independent instances were already in the corpus, from three authors, which is this
project's own bar for admitting a concept:

| system | what it does |
|---|---|
| `meeseeks_sourcing` | `viability_review` **retires a channel that finds nothing** — scores the source, not the candidate. Flagged in `examples/field/README.md` as "unusual" and "the shape to copy" long before it had a name |
| `conviction_termination` | the stop rule reads `expected_info_gain` — *is more looking worth it?* — and **nothing computes it** |
| `customer_acquisition` | `customer_interviews` is `cost: high` and nothing reviews whether it earns that |

The authoring language now makes that review a small structural contract rather than only a
label:

```yaml
observes:
  customer_interviews:
    cost: high
    checked_by: quarterly_source_review
    value_metric: decisions changed per interview-hour
    review_window: one quarter
    review_every: quarterly
    adjusts: retirement
```

Three checks follow, so the meeseeks pattern is first-class rather than accidental:

- **`expensive_signal_unreviewed`** — a costly source nothing ever asks was worth it.
- **`informs_no_decision`** — sharper than `orphan_signal`, which catches a signal informing
  *nothing*. This catches a signal that informs a belief **no rule reads**. The loop is not
  wrong about anything. It is spending attention it will not get back.
- **`incomplete_attention_contract`** — a review name with no value metric, review window,
  review cadence, or ability to alter sampling, source, routing, or retirement. A label alone
  is not closure.

`informs_no_decision` found a hole in this project's own flagship example on its first run:
`channel_saturation` is modelled from a daily feed and no decision depends on it.

**Honest rate, before this gets oversold:** across the 10 published examples the two attention
checks fire **once**. They fire more on this project's own specs, which declare signals in more
detail. That is the expected shape — tutorials observe one or two things and use both — and it
means these checks are *motivated* by three real instances and **not yet evidenced at rate**.
Low firing is at least evidence they do not fire spuriously; it is not evidence of a widespread
defect, and this document does not claim one.

**This is motivated by value-of-information, which decision theory has had for decades.** LoopSpec
does not calculate counterfactual information value; it checks whether a loop has declared how
signal value will be assessed and how attention can change. Calibrating the estimator tells
you how much to trust the answer. Reviewing the *signal* asks whether the question was worth
asking.

## L3 — the spec allocates *human* attention across loops

`people.*.sees` says what information reaches whom; `loses_if_wrong` says who pays. Together
they are an attention budget, and at group scale they are the thing that actually breaks.

O'Reilly's piece names this and does not resolve it: in its four-level taxonomy, the **human
oversight loop at the top has no exit condition**. swyx's Loopcraft stacks six levels with the
human at the top of all of them. Nobody says how much looking that costs, or what happens when
it exceeds what a person has.

Two existing checks are attention checks under this reading, which is why they felt important
out of proportion to their complexity:

- **`accountable_but_blind`** — bears a consequence, sees nothing. Attention is owed and not
  paid.
- **`no_human_at_all`** — 10/10 published examples. Attention assumed and never allocated.

## And the linter is automated attention

It looks in the places you would otherwise have to remember to look, every time, for every
loop. That is all it is, and it is enough — the value is not cleverness, it is *not forgetting*.

---

## Why this reframe changes the pitch

**Before:** *a linter that finds defects in agent loops.* Which invites the fair reply — my
evals already tell me when it fails.

**After:** *a notation for describing and arguing about loops, which happens to make some
defects visible by construction.*

The difference is what happens when the linter is wrong. A linter that is wrong is a bad
product. **A notation that is wrong is still useful, because you can now say precisely what
you disagree with** — and only two of this project's checks survived independent encoding,
which is exactly the situation a notation handles gracefully and a linter does not.

`tools/compare.py` is the demonstration. Ten published loops from three frameworks, side by
side, generated from their specs:

```
| loop                     | scored | exogenous input | ceiling  | humans   |
| langgraph_reflection     | 0/1 ✗  | none (1 own)    | messages | none ✗   |
| langgraph_reflexion      | 0/1 ✗  | 1 of 2          | none ✗   | none ✗   |
| langgraph_self_rag       | 0/3 ✗  | 1 of 2          | none ✗   | none ✗   |
| openai_llm_as_a_judge    | 0/1 ✗  | none (1 own)    | rounds   | none ✗   |
| crewai_self_evaluation   | 0/1 ✗  | none (1 own)    | retries  | none ✗   |
```

Nobody could previously put LangGraph's reflection tutorial next to CrewAI's self-evaluation
flow and say precisely what differs — not because it is hard, but because there was no shared
form to say it in. Reflection and reflexion differ in exactly one column, and that column is
the whole argument between them.

**You cannot diff two blog posts. You can diff two specs.** That is the contribution, and the
attention findings are what you notice once the diffing is possible.
