---
set: seed
domain: organization
encoded_by: claude-opus-5
encoded_from: general knowledge of early-stage company operation
vantage: founder/CEO
axes: [discrete, multi-timescale, few-actors, deeply-latent, non-stationary, organization, revisable-goals, designed]
---

# Startup — Seed Stage, Pre-Product-Market-Fit

**Written in domain language deliberately. No URAS vocabulary appears below.**

## What happens

Two founders raise £1.5m against a claim: mid-sized logistics firms will pay for software
that predicts which deliveries will be late. Eighteen months of runway. Four engineers and
a designer hired over the first quarter.

The plan assumes several things nobody has verified. That late deliveries are expensive
enough to buy software about. That the buyer is the operations director rather than IT.
That prediction accuracy achievable from the available data is high enough to be
actionable. That firms this size buy software at all rather than absorbing the problem
with staff.

Each month reduces runway by a known amount and produces ambiguous information about all
four assumptions at once.

## What the founders actually watch

Not one number. A shifting handful of quantities, none directly observable:

- **Is anyone buying?** Observed through a pipeline that is mostly noise at low volume.
  Three closed deals could be a signal or three friendly intros.
- **Which assumption is wrong?** Rarely resolvable from the same evidence that raised the
  question. A stalled deal is consistent with wrong buyer, wrong price, wrong product, or
  wrong month.
- **How long do we have?** Known precisely in cash terms, unknown in practice — the real
  question is how long until the next raise becomes impossible, and that depends on a
  market nobody can see.
- **Is the team still working?** Observed through mood, disagreement quality, whether the
  good engineer has updated their LinkedIn.

## The part that matters

**They discover a variable nobody had conceived of.** Eight months in, a customer mentions
they do not care about predicting lateness — they care about *proving* lateness was the
carrier's fault, for rebate claims. Nobody had thought of this. It was not a low-probability
hypothesis waiting to be confirmed. It was not in the space of things being considered.

This is not the plan being wrong. It is the plan having been written in the wrong
vocabulary.

**Then they change what they want.** The rebate-claims problem is smaller, less defensible,
and much more immediately sellable. After six weeks of argument the founders pivot.

The old goal was not *refuted*. Nobody proved late-delivery prediction was a bad business —
that question remains open and always will. They chose a different objective, for reasons
including exhaustion, a nine-month clock, and one founder's stronger conviction. A
counterfactual company with the same evidence and more runway would reasonably not have
pivoted.

**The founders disagree, and the disagreement is not resolvable by evidence.** One reads
the same eight months as "the market is telling us no." The other reads it as "we have not
yet reached the right buyer." Both readings fit the evidence. What differs is prior belief
and appetite for risk, and there is no observation that would settle it. The company
behaves as one actor while containing two incompatible views.

**Raising money changes the thing being valued.** Announcing a round produces inbound
customer interest, credible hiring, and press. The valuation is not an estimate of an
independent quantity — the act of estimating moves it.

**The boundary is genuinely unclear.** Two contractors do most of the data work. An
advisor with 0.5% sets the technical direction more than either founder. The lead investor
holds a board seat and a veto on the next raise. Are these inside the company? For
predicting what happens, the advisor and investor are more inside than one of the
employees.

## Where a formal encoding would earn its keep — and where it would not

Recorded now, before any encoding exists, so the comparison is honest rather than
retrofitted.

**Plausibly earns its keep:**

- **Naming which assumptions the strategy rests on, and whether anyone is tracking them.**
  The four assumptions above are real, load-bearing, and in most companies written down
  nowhere. A representation that makes them explicit and asks "what would change your mind"
  is doing work a board deck does not.
- **Recording that founders disagree, and on what.** Currently this lives in tension and
  hallway conversation. Making it an object — *we hold different estimates of the same
  quantity, here is the evidence each of us weights* — is genuinely new.
- **Distinguishing the pivot from a learning update.** A board deck presents pivots as
  discoveries. This one was a choice under a clock. The distinction matters for whether
  anyone should trust the next such decision.
- **Keeping the excluded-variable list.** "Proving fault" was outside the vocabulary for
  eight months. A discipline that maintains a list of *things we have decided not to model*
  gives that discovery somewhere to land earlier.

**Plausibly does not:**

- **Forecasting.** A spreadsheet is better at runway. Do not compete with it.
- **Anything requiring numeric priors on the four assumptions.** Founders do not have
  calibrated probabilities and inventing them adds false precision. If the representation
  demands numbers here it will be filled in with theatre.
- **Replacing the board deck.** Different audience, different job.
- **Weekly maintenance.** If the encoding must be updated weekly to stay true, it will not
  be updated, and a stale encoding is worse than none. Update cadence must match the rate
  the *structure* changes, not the rate the numbers do.

**The honest bar:** the encoding must surface at least one thing the founders did not
already know, or force one question they were avoiding. If it only reorganises what a good
board deck already says, it is decoration.

## What this should break

- **Anything treating goal change as learning.** The pivot was not an update toward truth.
  It was adopting a new objective under a clock, with the old question left open. Modelled
  as Bayesian belief revision, it is misdescribed.
- **Anything requiring the possibility space to be enumerable in advance.** The
  rebate-claims insight was not in the hypothesis space. If the representation cannot record
  its own vocabulary changing, it cannot describe this company.
- **Anything requiring one belief per company.** Two founders, two incompatible readings,
  one acting entity. Same structural demand the hospital makes, at smaller scale — which is
  evidence the demand is general.
- **Anything assuming observation is passive.** Raising money moves the valuation. Talking
  to customers creates the pipeline it measures.
- **Anything requiring numeric probability everywhere.** Forcing it produces theatre, and
  theatre in an audit artifact is worse than an admitted gap.
