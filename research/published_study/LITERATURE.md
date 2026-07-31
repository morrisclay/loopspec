# What the 2026 loop-engineering literature says — and does not

Gathered from the AI Engineer World's Fair 2026 material and the canonical posts. Read
*before* linting the code corpus, and recorded separately, because it is evidence of a
different kind: not what practitioners build, but what the field has words for.

## The field converged on taxonomy, not quality

Three independent canonical statements, all mid-2026, all describing loops as **nested
levels**:

| source | the levels |
|---|---|
| swyx, *Loopcraft: The Art of Stacking Loops* (AIEWF keynote) | token → chat → agent turn → goal → automation → software factory |
| LangChain, *The Art of Loop Engineering* | agent loop → verification loop → event-driven loop → hill-climbing loop |
| O'Reilly Radar, *What the Hell Is a Loop, Anyway?* | execution → task → product → system |

They agree substantially, which is a real convergence and worth respecting. **They also share
an omission.**

## What none of them has

O'Reilly's piece, asked directly, does not discuss how to know whether a loop is
well-designed or badly designed, nor calibration, confidence tracking, irreversible-action
safeguards, approval gates, or **what quantity the loop is regulating**.

LangChain's has a verification loop — a rubric grader that fails a run and sends it back —
and human touchpoints before sensitive tool calls. It has **no discussion of confidence
calibration or whether agent confidence aligns with actual correctness.**

That distinction is the whole wedge, and it is worth stating precisely because the two are
easily conflated:

> **Verification** asks *is this output good?* — grade the artifact in front of you.
> **Calibration** asks *has this agent's confidence historically tracked reality?* — score
> past predictions against what happened.
>
> The field has built the first thoroughly. The second has no name in it.

An agent that is verified but uncalibrated passes every rubric and still cannot tell you how
much to trust it *next* time. That is exactly the failure three independent real systems
showed, and it is now visible in the reference literature rather than only in my corpus.

## Where the literature is ahead of this project

Not a one-way critique. The conference material carries things this project has underweighted:

- **Budgets, step ceilings, stall detection, quotas, rate limits.** `Resource` exists in the
  catalog and no check uses it. A loop with no step ceiling is a real defect and the linter is
  silent on it.
- **"The log-is-the-agent principle"** — per-step traces as the primary artifact. Relevant to
  the open Flue question about whether evidence chains can be *reconstructed* from durable
  records or only replayed.
- **Mike Krieger on delegation** — agents with "standing ownership, feedback channels, and
  proactive task license." `authority` and `Party` are the right primitives for that and have
  never been tested against it.

## The honest threat to the thesis

The field's answer to loop quality is **evals and traces**: measure outcomes in production,
feed them back. That is outcome measurement, and it is genuinely powerful.

This project's answer is **structural**: read the spec, find defects before it runs.

The threat is that evals subsume the need. If you can measure outcomes well enough, why check
structure? The honest answer, and it needs testing rather than asserting:

1. Evals tell you *that* it is failing, not *why*, and *"the belief nothing scores"* is the
   kind of cause a trace does not name.
2. Evals require the loop to have run and failed. A structural check runs before deployment,
   which is where an irreversible ungated act is cheap to catch.
3. **An eval is itself an estimator, and nothing calibrates it.** LLM-as-judge scoring is a
   belief formed by judgement and typically never scored against outcomes — so the field's
   quality mechanism trips this project's most-cited check.

Point 3 is the strongest and it is testable: encode a published eval harness and lint it.

## One line worth keeping

O'Reilly's piece, on the failure it names but does not resolve:

> *"a loop without its signal doesn't converge. It just runs until something external stops
> it."*

That is `no_loop_closed` and `orphan_signal`, arrived at independently by a practitioner, in
prose, with no way to check for it.

## Sources

- https://www.truefoundry.com/blog/aiewf-2026-loops-harness-engineering
- https://www.langchain.com/blog/the-art-of-loop-engineering
- https://www.oreilly.com/radar/what-the-hell-is-a-loop-anyway/
- https://www.latent.space/p/aiewf26trends
- https://www.ai.engineer/
