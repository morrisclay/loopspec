---
set: adversarial
domain: organization
encoded_by: claude-opus-5
encoded_from: general knowledge of the Toyota Production System
vantage: plant management, with explicit line-worker counterpoint
axes: [discrete, multi-timescale, many-actors, observable-by-design, non-stationary, engineered, nested-goals, designed]
attacks: [loci-hypothesis, authority-relation, revision-regime, comprehensibility-ceiling]
demands:
  - System
  - Boundary
  - Party
  - Estimand
  - Signal
  - Estimate
  - Estimator
  - DesiredCondition
  - PreferenceOrdering
  - Intervention
  - Policy
  - Loop
  - Delay
  - TimeScale
  - Resource
  - Constraint
  - Revision
---

# Toyota Production System

**Written in domain language deliberately. No URAS vocabulary appears below.**

The most thoroughly documented adaptive organization in existence, and it exists to attack
four open questions rather than to add coverage. Toyota deliberately engineered solutions to
several things the hospital seed shows going wrong naturally — which makes the pair far more
informative than either alone.

## What happens

A car moves down a line at a fixed pace. Each station has a defined time to complete
defined work. Parts arrive not on a schedule but on request: when a station consumes a bin
of parts, a card travels back upstream authorising replacement of exactly that quantity.
Nothing is built until something downstream has consumed something.

Any worker who sees a problem pulls a cord. The line stops.

## The four things it does deliberately

**Any worker can stop the entire line.** The andon cord gives the person with the most
direct observation — a station worker, minutes into a shift — the authority to halt output
for the whole plant. This is expensive by design. Toyota's reasoning is that a defect
passed downstream costs more than the stoppage, and more importantly that a defect passed
downstream *destroys the information* about where it came from.

Compare the hospital directly. There, the party with the most continuous observation — the
nurse — has the least formal authority, and can only block by documenting a concern.
Toyota inverted exactly that relation on purpose.

**Goals are set at the top and negotiated back upward.** Annual objectives are decomposed
down through the organisation, but each level is expected to push back on what it has been
handed — arguing that a target is wrong, or that achieving it requires something not
provided. This back-and-forth is a named part of the process, not a failure of it. What
arrives at a department is not an instruction; it is an opening position.

**Improvement is routine, not episodic.** There is a documented current best method for
every task. Workers are expected to propose changes to it continuously, in small
increments, and a changed method becomes the new documented standard. The standard exists
*in order to be improved* — Toyota's position is that improvement is impossible without a
written current baseline, because otherwise there is nothing to improve against and no way
to tell whether a change helped.

**Reported information is assumed to have drifted from reality.** Managers are required to
go to the physical place and look at the physical thing rather than work from reports.
Doctrine, not preference. The written assumption is that the report and the reality come
apart, continuously, and that no amount of reporting discipline fixes it.

## The one-page constraint

A problem is written up on a single sheet of A3 paper. Background, current condition, target,
analysis, proposed countermeasures, plan, follow-up. One sheet, for anything from a jammed
fixture to a plant-level quality failure.

The size limit is the point. It forces the problem to be understood well enough to fit,
and it makes the artifact readable by someone who was not involved. Sixty years of
evidence that a bounded representation beats an unbounded one.

## Timescales

Seconds for station cycle time. Minutes for a line stoppage. Days for a proposal to become
standard. Months for model-level quality data. Years for platform decisions. A change
optimal at station level can be bad at platform level, and the negotiation described above
is partly how that conflict is surfaced rather than suppressed.

## What is unwritten

Which supervisors treat a pulled cord as information and which treat it as a complaint.
Whether this month's numbers make a stoppage politically expensive. Which suppliers will
absorb a schedule change quietly. The system depends on workers actually pulling the cord,
and whether they do depends on things no procedure records.

## What this settles

**The loci hypothesis gets direct evidence FOR it, contradicting the seed derivation.**
`research/prior_art_gate.md` predicted that plural, endogenous, nested goal formation is
one capability at three scales. Deriving primitives from the four seeds produced three
separate demands instead, which I recorded as evidence against.

Toyota resolves it. Goal decomposition-with-pushback is *simultaneously* nested
(across levels), plural (each level forms a position), and endogenous (positions change
through negotiation, not through learning what the true target was). One mechanism, all
three faces, engineered on purpose and running for decades.

The seed derivation missed this because none of the four seeds contained an organisation
that does goal formation *well*. The hospital has plural goals and handles them badly;
the startup revises goals episodically under duress. Toyota does it as routine practice,
and only then is it visible that they are the same thing.

**The authority relation is confirmed and shown to be configurable.** Hospital and Toyota
have the same structure — authority over intervention, held separately from who observes —
in opposite configurations. One is pathology, one is design. That the same relation
expresses both is the strongest available evidence it belongs in the representation, and it
still costs no budget.

**`Policy` + `Revision` cover documented-standard-plus-improvement.** I checked whether
standardized work needs its own primitive. It does not: the documented current method is a
`Policy`, and kaizen is `Revision` acting on it. Useful confirmation that both earn their
place, and a reminder that Toyota's insight — you cannot improve without a written
baseline — is an argument for the representation existing at all.

**Two revision regimes, not one.** Toyota revises continuously in small increments against
a documented baseline. The startup revised once, discontinuously, under a clock, with the
old goal abandoned rather than refuted. Same primitive, and the difference between routine
and episodic revision may need to be an attribute rather than left implicit.

**`genchi genbutsu` is the Signal/Estimand split as management doctrine.** Toyota
institutionalised the thermostat's lesson: what is reported diverges from what is true,
permanently, and the response is structural rather than better reporting. Independent
confirmation from a completely different direction that the split is load-bearing.

## What this should break

- **Any assumption that authority follows observation** — in either direction. Both
  configurations are real and the representation must not prefer one.
- **Any single goal per organisation.** Every level holds a position, and the positions
  conflict as a designed feature.
- **Any treatment of a documented method as fixed.** The standard is the thing being
  revised, continuously.
- **Any assumption that reports track reality.** Toyota assumes the opposite as doctrine.
- **Unbounded encodings.** A3 is a working, battle-tested size ceiling. If a URAS encoding
  of a plant problem cannot fit comparable bounds, it is worse than the thing it replaces —
  and Toyota has sixty years of evidence on that specific point.
