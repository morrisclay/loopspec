---
set: adversarial
domain: frontier_materials
encoded_by: claude-opus-5
encoded_from: general knowledge of computational materials discovery ventures
vantage: founders and lead scientists
evidence_cost: low-per-unit-astronomical-in-aggregate
goal_locus: inside-boundary
attacks: [search-allocation, cheap-evidence-vast-space, model-experiment-gap,
          no-single-target, portfolio-not-loop]
---

# Computational Materials Discovery Venture

**Written in domain language deliberately. No URAS vocabulary appears below.**

Added because every system in the corpus so far is bottlenecked on the *cost* of evidence.
This one is not. Evidence here is cheap per unit and the space is astronomically large, so
the binding constraint is *where to look* rather than *what it costs to look*. Nothing else
in the corpus has that shape, and it is a common shape in frontier ventures.

## What happens

Forty people, roughly half computational and half experimental. The claim: machine-learned
interatomic potentials plus high-throughput synthesis can find useful materials — a better
battery cathode, a cheaper catalyst, a membrane — orders of magnitude faster than the
traditional cycle of hypothesis and slow wet-lab work.

The computational side screens candidate compositions and structures. Millions are
evaluated. Thousands are shortlisted. Tens are actually synthesised and measured. A handful
behave as predicted.

## What they are actually trying to judge

- **Is the model right in the region we care about?** Trained on known materials, and the
  useful candidates are by definition unlike known materials. Accuracy on a held-out set of
  the known says little about accuracy where the company intends to operate.
- **Is this candidate synthesisable at all?** Predicted stability and actual synthesis
  routes are different questions, and the second is the one that kills most candidates.
- **Are we searching the right region?** The space is effectively unbounded. Every choice of
  where to look is also a choice of what will never be seen.
- **Will the customer's specification hold?** The offtake partner wants a cathode meeting
  several targets at once. Which of those they would genuinely relax is not something they
  will say, and possibly not something they know.

## The part that matters

**The bottleneck is search allocation, not evidence cost.** Any individual computation is
nearly free and any individual synthesis is merely expensive. Neither is the constraint. The
constraint is that the space is large enough that the search policy determines the outcome
more than the measurement quality does. A company with worse models and a better search
strategy beats the reverse.

**The model and the experiment disagree constantly, and the disagreement is the product.**
Every synthesised candidate that fails is information about the model, not just about the
candidate. The company's real asset is the accumulated record of where its predictions broke —
which is precisely the information nobody publishes and which does not appear on any balance
sheet.

**There is no single target quantity.** A useful cathode must satisfy capacity, cycle life,
rate capability, cost, thermal stability and manufacturability simultaneously. These are not
weighted; they are thresholds, and a candidate that fails one is worthless however well it
does on the others. Optimising a weighted combination of them produces candidates that are
excellent on average and useless in fact.

**The organisation is a portfolio, not a loop.** Dozens of candidate families are in flight
at different stages. There is no single regulation cycle; there is an allocation of finite
synthesis capacity across a changing population of bets, most of which will die.

**Negative results have value the organisation is structurally bad at capturing.** A failed
synthesis tells you something durable. The incentive — for the individual scientist, for the
next investor update — is to move on to the next candidate rather than to characterise the
failure well.

## Who pays for being wrong

- **The computational team** — model credibility, which is the company's whole thesis.
- **The experimental team** — bears the schedule cost of chasing candidates that were never
  going to work, and is usually blamed for the delay rather than the prediction.
- **The offtake partner** — has committed a specification and internal roadmap to a material
  that may not arrive.
- **Investors** — funding a search whose progress is genuinely hard to distinguish from
  activity.

## What is unwritten

Which model predictions the experimentalists have privately stopped believing. Which
candidate families are still in the deck for narrative reasons. Which of the partner's stated
specifications are real and which are opening positions. How much of last quarter's
throughput was informative rather than merely busy.

## What this should break

- **Any assumption that a single loop describes the system.** This is an allocation across a
  population of bets at different stages, not one regulation cycle.
- **Any assumption that the binding constraint is evidence cost.** It is search policy.
  Everything in the corpus so far is bottlenecked on the cost of finding out; this one is
  bottlenecked on knowing where to point.
- **Any scalarization of a multi-threshold objective.** Six simultaneous thresholds are not a
  weighted sum, and averaging them produces confidently useless candidates.
- **Any assumption that model output and measurement are the same kind of thing.** The gap
  between them is the company's actual product.
- **Any representation with no place for durable negative results.** The record of where
  predictions failed is the accumulating asset and has no natural home.
- **Any assumption that the customer's stated target is their real one.** Which
  specifications would be relaxed is unstated and possibly unknown to the customer.
