---
set: seed
domain: institution
encoded_by: claude-opus-5
encoded_from: general knowledge of hospital operations
vantage: DELIBERATELY AMBIGUOUS — see note
axes: [discrete, multi-timescale, many-actors, latent, non-stationary, institutional, incommensurable-goals, designed]
demands:
  - System
  - Boundary
  - Party
  - Estimand
  - Signal
  - Estimate
  - Evidence
  - Estimator
  - DesiredCondition
  - PreferenceOrdering
  - Consequence
  - Intervention
  - Policy
  - Loop
  - Delay
  - TimeScale
  - Resource
  - Constraint
---

# Hospital — Patient Flow and Discharge

**Written in domain language deliberately. No URAS vocabulary appears below.**

Scoped to one loop — discharge decisions and bed availability — because the whole
institution is too large for a seed description and this loop contains the hard parts.

## What happens

A hospital has a fixed number of beds. Admissions arrive partly predictably (scheduled
surgery) and partly not (emergency). If no bed is free, patients wait in the emergency
department on trolleys, which is both dangerous and reportable. So beds must be freed,
which means discharging patients, which means deciding a patient is ready to leave.

That decision runs roughly like this. A consultant sees the patient on a ward round,
typically once a day. Nursing staff, present continuously, know things the consultant does
not — whether the patient actually walked to the bathroom, whether they ate, whether they
are frightened. A discharge coordinator knows whether a place is available in a care home,
whether the family can collect them, whether the pharmacy has dispensed. Any of these can
block a discharge that is clinically fine.

Meanwhile the bed manager holds a live picture of the whole hospital and is under pressure
from the emergency department, which is under pressure from a national four-hour waiting
target with financial consequences attached.

## The part that matters

**The same patient is a different fact to each party.**

Consider "is this patient ready to go home?"

- The **consultant** estimates clinical stability from observations made once a day, and
  bears the consequence of a readmission — which reflects on them individually and is
  measured.
- The **nurse** estimates functional capacity from continuous presence, and bears the
  consequence of an unsafe discharge more immediately but less formally.
- The **discharge coordinator** estimates logistical readiness, and bears the consequence
  of a patient stuck in a bed with nowhere to go.
- The **bed manager** estimates the marginal value of this bed against the queue, and
  bears the consequence of a four-hour breach.
- The **patient** may want to go home badly, or be terrified of going home, and has the
  least ability to make that estimate count.

These are not noisy readings of one underlying truth. They are different questions, asked
against different evidence, by parties bearing different costs of being wrong. Averaging
them would be meaningless. Reconciling them is what a ward round *is*.

**And they have different authority.** Only the consultant can discharge. The nurse can
effectively block by documenting a concern. The bed manager can apply pressure but cannot
decide. The coordinator can delay indefinitely by not arranging transport. Authority is
distributed differently from information — the party with the most continuous observation
has the least formal power, and everybody in the building knows it.

## Timescales that do not line up

Bed pressure moves hourly. Ward rounds are daily. Staffing rotas are weekly. Budgets are
quarterly. Accreditation is on a multi-year cycle. A decision optimal on the hourly clock
is often bad on the quarterly one: discharging early relieves pressure today and produces
a readmission in a fortnight, which costs more and is measured separately.

## Things everybody knows and nothing records

Which consultants can be called at night and which cannot. Which care homes will accept a
patient on a Friday. That the four-hour target is partly managed by how arrival time gets
recorded. That a particular nurse's concern is worth more than the notes suggest.

None of this is written anywhere. All of it determines what actually happens.

## Note on vantage

This description is written from no single position, which is itself a choice, and a
slightly dishonest one — the phrasing above is closer to a clinician's account than to an
administrator's. An administrator's version would foreground throughput, breach rates and
length-of-stay variance, and would treat the disagreements above as coordination overhead
rather than as substance.

**Both versions should be encodable, and the difference between them should be visible in
the encoding.** If it is not, the representation is flattening the thing that matters
most.

## What this should break

- **Any single estimate per quantity.** Five parties, five estimates of "ready for
  discharge," none of them noise. If the representation permits only one belief per
  quantity, it cannot describe a hospital — and by extension cannot describe any
  institution.
- **Any assumption that authority follows information.** It inverts here, structurally and
  consequentially. Authority must be representable separately from who knows what.
- **Any single objective.** Throughput, safety, cost, staff sustainability and patient
  preference are not commensurable, and the hospital does not have exchange rates between
  them. Weighting them would be inventing information that does not exist.
- **Any assumption that costs of error are shared.** Each party bears a different
  consequence for being wrong, which is *why* their estimates differ. Model the estimates
  without the asymmetric costs and the disagreement looks like irrationality.
- **Anything requiring complete specification.** The unwritten knowledge above is
  load-bearing. A representation that omits it will be confidently wrong about what the
  hospital will do.
