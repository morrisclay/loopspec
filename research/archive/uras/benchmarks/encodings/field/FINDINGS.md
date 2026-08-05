# Cold run on three real agent loops

Loops taken from `t-minus`, all specified by someone other than me: the Deal Steward, the
Meeseeks sourcing agent, and the conviction-termination loop. Encoded from spec and feature
files, linted cold.

**14 findings. Roughly 4 look real. The other 10 are my own encoding errors.**

That split is the result, and it is not the one I wanted.

## What is real

**1. `expected_info_gain` is in the termination rule and nothing says how it is measured.**
`conviction-termination.feature` routes on *"low conviction and high expected information
gain"*, and neither that file nor the surrounding spec states how expected information gain is
computed. The stop rule reads two quantities and only one — conviction — has a formula
(`0.4*hypothesis_score + 0.35*min(1,avg_confidence) + 0.25*convergence`).

This is the `policy_on_unmeasured_inputs` pattern that also fired on the Customer Acquisition
spec. A decision rule reading a quantity nothing computes.

**2. `readiness_check` has no calibration.** The Deal Steward proposes a stage move when every
call is debriefed and no blocking unknown is open. Nothing ever asks whether deals proposed
under that rule actually advanced. Same finding as `/complicate`, in a different loop, found
independently.

**3. `named_risk_status` is asserted, not estimated.** Named Risks carry `open / de-risked /
red flag` maintained by hand. No estimator derives status from evidence — so risk state is a
human assertion wearing the same clothes as a computed field. Worth a question rather than a
claim.

**4. `attio_stage` is read but connected to nothing.** In the spec it is a *trigger* — the
steward ensures the Slack channel when Attio says Due Diligence. The encoding had no way to
say "this signal gates an action but measures no quantity", which may be a gap in the
representation rather than in their system.

## What is not real — and what it means

Ten findings trace to **missing edges in my encoding**, not gaps in the loops:

- `candidate_quality never estimated` — I declared `three_dim_scorer` and `candidate_score` and
  never drew the edge between the estimate and the estimand.
- `deal_readiness never estimated` — same omission.
- `channel_viability` / `mandate_status` unmeasured — both are computed from channel state; I
  did not encode the derivation.
- `hypothesis_outcome` unmeasured — RESOLVE records it; I omitted the estimator.

**Every one is a real defect in the encoding.** So the tool works — it just found the encoder
rather than the design.

## The honest split

| used as | hit rate | verdict |
|---|---|---|
| **design linter** on someone else's system | ~4/14 | weak, and unverifiable without the author |
| **encoding completeness checker** | 14/14 | reliable — every finding was a genuine omission |

This is a more useful distinction than a single number. The second use needs no domain
knowledge and no adjudication: if you claim an estimand is tracked, something must estimate it.
That is checkable, it caught me four times in one sitting, and it is the same class of defect
the validator caught three times with unquoted commas.

The first use — telling a *system's author* something they did not know — is what
`/complicate` demonstrated at 2 of 4. Three cold loops did not reproduce that rate, and I
cannot verify the four candidates without the person who wrote the specs.

## Against the fork's stated risk

`research/archive/uras/FORK.md` said the fork rested on one human-validated data point and that the correct next move
was three more loops from other authors, held lightly until they landed.

They have now been run. **The result is equivocal**: one clearly real finding of the type that
landed before (`policy_on_unmeasured_inputs`), one exact repeat of the `/complicate` finding
(uncalibrated estimator) in an unrelated loop, and a large majority of noise traceable to me.

The repeat is the most interesting single fact here: **two independent agent loops, written by
different people for different purposes, both have an estimator nothing scores.** If that
generalises it is a real and common defect in agent loop design, and it is the strongest
candidate for what this tool is actually for.

Verification requires the specs' author confirming or rejecting the four candidates.
