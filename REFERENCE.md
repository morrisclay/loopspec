# Loop format reference

**Generated from `schema/loop.keys.yaml` by `tools/gen_spec.py`. Do not edit.**
Edit the grammar; the reference, the JSON Schema and the parser all follow from it.

Format version **1**.

Unknown keys are **errors**, not warnings, and enum values are checked. A spec that misspells
`reversibility` on an act named `wipe_production` used to parse clean and produce no finding —
the most dangerous declaration in the format is the easiest to lose.

## Top level

One document per loop. `---` separates loops in a group; **names resolve across the whole file**, so loops may reference each other's actions and observations.

| key | type | required | meaning |
|---|---|---|---|
| `loop` *(alias: `name`)* | str | **yes** | The loop's name. One document per loop; `---` separates loops in a group. |
| `runs` *(alias: `every`)* | str |  | How often the loop runs — `weekly`, `every 6 hours`, `per_question`. Free text, since cadence is domain-specific; the linter checks that one exists, not its units. |
| `goal` *(alias: `regulates`)* | map of entries |  | What the loop is steering, and toward what. |
| `beliefs` *(alias: `estimates`)* | map of entries |  | What it holds a view on but cannot read off directly. |
| `observes` | map of entries |  | What data actually arrives. |
| `actions` *(alias: `acts`)* | map of entries |  | The levers it may pull. |
| `when` | list of entries |  | The rule choosing among actions, evaluated in order. Structured rather than prose: prose reads better and cannot be checked, and the checking is the point. |
| `asks_human_when` | list[str] |  | The conditions under which the loop stops and asks a person. Top-level and on its own, because burying escalation inside the decision rule is how it goes missing — this is the list a reader scans first to find out whether the thing can run away. |
| `people` *(alias: `parties`)* | map of entries |  | Who is involved — human or agent — and what each stands to lose. |
| `spends` | map of entries |  | What the loop burns as it runs — iterations, tokens, money, someone's attention — and what stops it. Harness engineering treats budgets, step ceilings and stall detection as standard, and this format could not express any of them: ceilings were prose inside `never`, where nothing could check them. |
| `consider` | map of entries |  | Findings you have read and decided about, keyed by check name — optionally `check/subject` to decide about one instance. This does NOT suppress anything: the finding moves to a `considered` section with your reason attached, so a reviewer sees the decision rather than a silence. A finding you have read and rejected is a different artifact from one you never saw, and that difference is most of what this notation is for. The linter warns when a `consider:` entry no longer matches any finding, because a stale justification is worse than none. |
| `never` | list[str] |  | Hard limits that hold regardless of the goal. |
| `not_modelling` *(alias: `ignoring`)* | list[str] |  | Knowingly out of scope. Not decoration: this is the first list to revisit when the loop misbehaves for reasons it cannot see. |

## `goal.<name>`

What the loop is steering, and toward what.

| key | type | required | meaning |
|---|---|---|---|
| `keep` *(alias: `target`)* | str |  | The target, read as a sentence: `keep: below 400`, `keep: above 3 sources`. |
| `from` *(alias: `computed_from`)* | list[str] |  | What this quantity is computed from. |
| `unit` | str |  | USD, days, percent — whatever makes the number meaningful. |
| `set_by` | str |  | `<loop>.<quantity>` — the outer loop's quantity that IS this setpoint. Cascade control, the standard shape of every real control hierarchy: a slow outer loop decides what the fast inner loop should aim at. Naming the QUANTITY and not just the loop is what makes the link structural — otherwise "set by the strategy loop" is a comment, and nothing can check whether that loop is able to move the number it is nominally responsible for. Naming it is what stops an outer loop's target from quietly becoming an inner loop's unexamined constant, which is how layered agent systems actually fail. CASCADE HAS A HARD REQUIREMENT: the inner loop must run FASTER than the loop setting its target. If it does not, the outer loop's corrections arrive before the inner one has settled, and both oscillate. That is checkable and is checked. |
| `confidence` | number |  | How firmly the goal ITSELF is held, 0–1 — uncertainty about what you want, as distinct from uncertainty about the world. Optional, and deliberately not a primitive: it enters on one book sketch and that is not enough evidence. |

## `beliefs.<name>`

What it holds a view on but cannot read off directly.

| key | type | required | meaning |
|---|---|---|---|
| `question` *(alias: `means`, `description`)* | str |  | The belief in plain language, as the question it answers — "will the customers we buy this month stay?". Optional and worth writing: it is the line a reader understands first, and the one that exposes a belief nobody can actually state. |
| `from` *(alias: `formed_from`)* | list[str] |  | DEPRECATED — declare the edge once, on the observation, with `informs:`. This said the same thing from the other end and the two could disagree silently: one spec had `beliefs.product_market_fit.from: [stripe]` and `observes.stripe.informs: cost_per_customer`, and BOTH edges were created. Still accepted so old specs parse; it is now an error for the two to contradict each other. |
| `how` *(alias: `method`, `how_formed`)* | str |  | How the view is formed: bayesian, judgement, a formula, an LLM call. |
| `checked_by` *(alias: `calibrated_by`, `how_checked`)* | str |  | What scores this belief's PAST calls against what actually happened. Its absence is the most common defect in real loops — found in three independent systems by three careful authors. A belief nothing checks cannot be shown to track anything. |
| `every` | str |  | How often the check runs. |
| `explains` | str |  | The quantity this belief is a model OF. A loop steering something it has no model of is a reflex against a setpoint — it can correct but never anticipate. |
| `settled_by` | str |  | The observation that would finally decide this — what makes the belief refutable. |
| `known_bias` | str |  | The direction this belief is expected to be wrong in, and why. |
| `safe_to_repeat` *(alias: `idempotency_basis`)* | str |  | What makes re-running the update safe. Execution is at-least-once on every durable runtime, and an update applied twice double-counts into a confident wrong answer. |

## `observes.<name>`

What data actually arrives.

| key | type | required | meaning |
|---|---|---|---|
| `informs` *(alias: `measures`)* | str|list |  | Which belief or goal this tells you about. Omit and it is data nobody uses. |
| `every` | str |  | How often it arrives. |
| `cost` | `low` \| `medium` \| `high` |  | What it costs to obtain. |
| `origin` | `outside` \| `ourselves` |  | Did something OUTSIDE this system cause this data to exist, or did we? Half of provenance, and the half that decides whether the loop can be surprised. A loop whose every input has `origin: ourselves` is sealed — it can only agree with itself. |
| `how` *(alias: `obtained_as`)* | `measured` \| `reported` \| `calculated` |  | The other half, and orthogonal to `origin` — measured by a mechanism, reported by someone with interests, or derived from other numbers. The two axes must stay separate: `origin: ourselves` + `how: reported` is an agent's own self-assessment, which is a claim and not a measurement, and collapsing provenance to one axis cannot say it. |
| `reported_by` *(alias: `asserted_by`)* | str |  | Who reports it, when `how: reported`. A reported number is a claim by someone. |
| `produced_by` | str |  | Which of our own actions creates this, when `origin: ourselves`. |
| `source` | str |  | Where it physically comes from — Stripe, Attio, a webhook, a cron. OPTIONAL, and it belongs here rather than in the name. NAME AN OBSERVATION FOR WHAT IT TELLS YOU, NOT WHERE YOU GET IT: `billing_events`, not `stripe`. Vendors churn and the loop does not; a spec named after today's tools has to be rewritten when they change, and two companies observing the same thing through different vendors cannot be compared at all. |
| `checked_by` | str |  | What reviews whether this observation is worth what it costs — whether looking here earned the attention. Distinct from calibrating a belief. Every Calibration in this project scored an ESTIMATOR: was my conclusion right. Nothing scored a SIGNAL: was my LOOKING right. A loop that keeps paying for a source that never changed a decision is not wrong about anything; it is spending attention it will not get back. |

## `actions.<name>`

The levers.

| key | type | required | meaning |
|---|---|---|---|
| `moves` | str|list |  | The quantity this drives. Nothing pointing at a goal makes that goal a wish. |
| `can_undo` *(alias: `reversibility`)* | `yes` \| `costly` \| `no` |  | THE LOAD-BEARING FIELD, phrased as the question anyone would actually ask. Approval demanded everywhere gets ignored; approval demanded where the answer is `no` is a rule people follow. `costly` means undoable at real expense. NOTE: YAML 1.1 reads bare yes/no as booleans, so `can_undo: no` arrives as False. That is accepted and normalised rather than rejected — the natural phrasing must not be a trap. It is the one place this format tolerates YAML's ambiguity, because the blind test showed people write exactly this. |
| `needs_approval` *(alias: `approval`)* | str |  | The person who must say yes first. Must name someone in `people`. |
| `effect_after` *(alias: `delay`, `effect_shows_after`, `effect_shows_in`)* | str |  | How long until the effect is visible. Lag with no damping is what makes loops thrash. |
| `damping` | str |  | Deadband |
| `consumes` | list[str] |  | Finite things this draws down. |

## `spends.<name>`

What the loop burns, and what stops it.

| key | type | required | meaning |
|---|---|---|---|
| `limit` | str |  | The ceiling — `25 iterations`, `100k tokens`, `5 hours a week`. A limit is a STOP, not a correction: it truncates the loop rather than regulating it. Declaring one is necessary and is not the same as being able to slow down before reaching it. |
| `replenished` | str |  | What refills this, if anything. Omit and it only ever depletes. |
| `spent_by` | str|list |  | Which actions draw it down. Each must name an entry in `actions`. |

## `consider.<check>`

A finding you have read and decided about. Does not suppress it.

| key | type | required | meaning |
|---|---|---|---|
| `because` | str |  | Why this is acceptable here. Write it for whoever reads the spec after you. |
| `revisit` | str |  | What would change your mind, or when to look again. Optional and worth writing. |

## `when[]`

The rule choosing among actions, in order.

| key | type | required | meaning |
|---|---|---|---|
| `if` | str |  | The condition. |
| `do` | str|list |  | Action(s) to take. Must name entries in `actions`. |
| `escalate` | str |  | DEPRECATED — use the top-level `asks_human_when:`. Escalation buried inside a decision rule is how it goes missing, and having both meant four different ways to say a human is involved. Still accepted. |

## `people.<name>`

Who is involved and what they stand to lose.

| key | type | required | meaning |
|---|---|---|---|
| `human` | bool |  | A person. Mutually exclusive with `agent`. |
| `agent` | bool |  | An automated actor. Mutually exclusive with `human`. |
| `kind` | `human` \| `agent` \| `group` \| `system` |  | Explicit alternative. |
| `loses_if_wrong` *(alias: `bears`)* | str|list |  | What this one actually loses when the loop is wrong. `nothing` is a legitimate and revealing answer — an agent that loses nothing beside a human who loses everything is the asymmetry that explains overrides looking irrational against the agent's objective. |
| `sees` | list[str] |  | What information actually reaches them. Someone who loses something and sees nothing is accountable and blind, which is oversight in name only. |
| `may_decide` | str |  | DEPRECATED — prose that nothing reads. What a person may decide is already stated, and checkably, by `needs_approval:` on the actions they gate. |

## Referential rules

Checked at parse time, because a name pointing at nothing is a silent hole:

- `actions.*.needs_approval` must name someone in `people`
- `actions.*.moves` must name something in `goal` or `beliefs`
- `when[].do` must name an action in `actions`
- `when[].escalate` must name someone in `people`
- `beliefs.*.from` must name an observation in `observes`
- `observes.*.informs` must name something in `goal` or `beliefs`
- `people.*.sees` must name something in `goal` or `beliefs`
- `observes.*.produced_by` must name an action in `actions`

Errors carry a did-you-mean suggestion, so the message names the fix rather than only the fault.
