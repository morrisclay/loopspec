---
set: seed
domain: engineering
encoded_by: claude-opus-5
encoded_from: general engineering knowledge
vantage: external designer
axes: [continuous, fast-loop, single-actor, observable, stationary, engineered, single-goal, designed]
demands:
  - System
  - Boundary
  - Party
  - Estimand
  - Signal
  - Estimate
  - Estimator
  - DesiredCondition
  - Intervention
  - Policy
  - Loop
  - Delay
  - TimeScale
  - Constraint
---

# Thermostat

**Written in domain language deliberately. No URAS vocabulary appears below.
Primitives are derived from this description, not imposed on it.**

## What it does

A householder sets a dial to 20°C. A sensor in the hallway reports the air temperature
every few seconds. When the reported temperature falls more than half a degree below the
dial setting, the controller closes a relay and the boiler fires. When it rises half a
degree above, the relay opens and the boiler stops.

The half-degree band exists because without it the relay would chatter — switching on and
off many times a minute as the reading jitters around the setting, destroying the relay
and the boiler both.

## What makes it non-trivial

**The sensor does not measure what the householder cares about.** It measures hallway air
temperature at one point, roughly 1.5m up a wall. The householder cares whether the
*rooms* are comfortable. These diverge: sun on the hallway wall, a draught under the front
door, a closed door to the room actually being used. The controller is regulating a proxy
and cannot tell when the proxy has come apart from the thing itself.

**The boiler does not act instantly.** Heat takes fifteen to forty minutes to move from a
radiator into room air, and continues arriving after the boiler stops. A controller that
responded only to the current reading would overshoot every time. Cheap thermostats
overshoot; better ones anticipate.

**Nobody inside the system knows what the house is for.** The dial is set from outside.
The controller has no way to represent "the householder is on holiday" or "the baby's room
matters more." Those are handled by the householder changing the dial, which is to say:
outside the loop.

## What it cannot do

It cannot decide that 20°C was the wrong target. It cannot notice that the sensor has
drifted three degrees over four years. It cannot learn that this house takes longer to
heat in an east wind. It cannot come to want anything.

It has one job, given from outside, and it will pursue that job with a broken sensor
forever without complaint.

## Why this is in the seed set

This is the **floor**. Every concept the representation needs in order to describe a
thermostat is a concept it genuinely cannot do without.

If a thermostat is hard to describe, the representation is broken. If describing it
requires more than a handful of parts, the representation is too heavy. And the parts it
does *not* need — anything to do with disagreement, revised goals, or nested authority —
are exactly the parts that should be optional rather than structural.

## What this should break

- **Anything that makes goal-holding mandatory.** The thermostat holds no goal. The
  householder does, and the householder is outside the boundary. If the representation
  forces a goal-holder inside every system, it will lie about this one.
- **Anything that makes a target a number.** The target is a number *plus* a deadband,
  and the deadband is not a tolerance on measurement — it is a structural feature that
  exists to prevent oscillation. Modelling it as measurement error gets it wrong.
- **Anything requiring the measured quantity to be the quantity of interest.** Hallway
  air is not room comfort. This gap is the single most important fact about the system
  and the easiest to omit.
