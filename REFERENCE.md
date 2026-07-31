# Loop format reference

**Generated from `schema/loop.keys.yaml` by `tools/gen_spec.py`. Do not edit.**
Edit the grammar; the reference, the JSON Schema and the parser all follow from it.

Format version **0**.

Unknown keys are **errors**, not warnings, and enum values are checked. A spec that misspells
`reversibility` on an act named `wipe_production` used to parse clean and produce no finding —
the most dangerous declaration in the format is the easiest to lose.

## Top level

One document per loop. `---` separates loops in a group; **names resolve across the whole file**, so loops may reference each other's acts and signals.

| key | type | required | meaning |
|---|---|---|---|
| `loop` *(alias: `name`)* | str | **yes** | The loop's name. One document per loop; `---` separates loops in a group. |
| `every` | str |  | The loop's clock — how often it runs. Free text (`weekly`, `per_question`, `5m`) because cadence is domain-specific; the linter checks presence, not units. |
| `regulates` | map of entries |  | What the loop steers toward a target. |
| `estimates` | map of entries |  | What it believes but cannot see directly. |
| `observes` | map of entries |  | What actually arrives from the world. |
| `acts` | map of entries |  | The levers it may pull. |
| `when` | list of entries |  | The rule selecting among acts. |
| `parties` | map of entries |  | Who is involved and what it costs them. |
| `never` | list[str] |  | Guardrails that hold regardless of the objective. |
| `ignoring` | list[str] |  | Declared out of scope. Not decoration — this is the revision frontier, the list you revisit when the loop misbehaves for reasons it cannot see. |

## `regulates.<name>`

What the loop steers toward a target.

| key | type | required | meaning |
|---|---|---|---|
| `target` | str |  | The setpoint, as a readable comparison — `< 400`, `>= 3 sources`, prose is fine. |
| `computed_from` | list[str] |  | Inputs this quantity is derived from. |
| `confidence` | number |  | How firmly the target itself is held, 0–1. Uncertainty about what you WANT, distinct from uncertainty about the world. A target held at 0.7 and one held at 0.99 warrant different revision policies. Candidate finding, per Briefing §7 — accepted here as an OPTIONAL field only, and it does not enter the primitive catalog on this evidence. |

## `estimates.<name>`

What it believes but cannot see.

| key | type | required | meaning |
|---|---|---|---|
| `from` | list[str] |  | Signals feeding this belief. Each must appear in `observes`. |
| `method` | str |  | How the belief is formed: bayesian, judgement, frequency, model… |
| `calibrated_by` | str |  | What scores this estimator's PAST predictions against what happened. Its absence is the single most common defect found in real loops — three independent authors, none careless. |
| `window` | str |  | Over what period calibration scores. |
| `explains` | str |  | The quantity this belief is a MODEL OF. Conant & Ashby 1970: every good regulator of a system must be a model of that system. Without this the loop is a reflex. |
| `settled_by` | str |  | The observable that would finally decide this — what makes the belief refutable. |
| `idempotency_basis` | str |  | What makes a repeated update safe. Execution is at-least-once on every durable runtime, and a Bayesian update applied twice double-counts into a well-formed but WRONG posterior. |

## `observes.<name>`

What actually arrives.

| key | type | required | meaning |
|---|---|---|---|
| `measures` | str |  | The estimand this signal informs. Omit and it is an orphan. |
| `every` | str |  | Sampling period. |
| `cost` | `low` \| `medium` \| `high` |  | What it costs to obtain. |
| `asserted_by` | str |  | A party who REPORTS this rather than a mechanism that measures it. A reported number is a claim by someone with interests, not an observation. |
| `produced_by` | str |  | An act inside this system that manufactures this signal. Load-bearing for groups: a loop whose every input is produced_by something inside it cannot be corrected from outside. |

## `acts.<name>`

The levers.

| key | type | required | meaning |
|---|---|---|---|
| `moves` | str |  | The estimand this act drives. Absence means the target is a wish. |
| `delay` | str |  | Lag between acting and seeing the effect. |
| `damping` | str |  | Deadband |
| `reversibility` | `reversible` \| `costly` \| `irreversible` |  | THE LOAD-BEARING FIELD. Approval demanded everywhere is ignored; approval demanded where the act cannot be undone is a rule people follow. `costly` means undoable at real cost. |
| `approval` | str |  | Party whose approval gates this act. Must name a party in `parties`. |
| `consumes` | list[str] |  | Finite resources this act draws down. |

## `when[]`

The rule selecting among acts. Evaluated in order.

| key | type | required | meaning |
|---|---|---|---|
| `if` | str |  | The condition |
| `do` | str|list |  | Act(s) to take. Must name entries in `acts`. |
| `escalate` | str |  | Party the loop stops and asks. Must name a party in `parties`. |

## `parties.<name>`

Who is exposed.

| key | type | required | meaning |
|---|---|---|---|
| `human` | bool |  | A person. Mutually exclusive with `agent`. |
| `agent` | bool |  | An automated actor. Mutually exclusive with `human`. |
| `kind` | `human` \| `agent` \| `system` |  | Explicit alternative to the above. |
| `bears` | str |  | What this party loses when the loop is wrong. `nothing` is a legitimate and revealing answer — an agent that bears nothing and a human who bears everything is the asymmetry that explains overrides looking irrational against the agent's objective. |
| `sees` | list[str] |  | Estimands whose value reaches this party. A party that bears a consequence and sees nothing is accountable and blind — human oversight as compliance theatre. |
| `authority` | str |  | What this party may decide. |
| `asymmetry` | str |  | How this party's exposure differs from others'. |

## Referential rules

Checked at parse time, because a name pointing at nothing is a silent hole:

- `acts.*.approval` must name a party in `parties`
- `when[].do` must name an act in `acts`
- `when[].escalate` must name a party in `parties`
- `estimates.*.from` must name a signal in `observes`
- `parties.*.sees` must name an estimand in `regulates` or `estimates`
- `observes.*.produced_by` must name an act in `acts`

Errors carry a did-you-mean suggestion, so the message names the fix rather than only the fault.
