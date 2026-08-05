# Loop format reference

**Generated from `schema/loop.keys.yaml` by `tools/gen_spec.py`. Do not edit.**
Edit the grammar; the reference, the JSON Schema and the parser all follow from it.

Format version **1.2**.

Unknown keys are **errors**, not warnings, and enum values are checked. A spec that misspells
`reversibility` on an act named `wipe_production` used to parse clean and produce no finding —
the most dangerous declaration in the format is the easiest to lose.

## Top level

One document per loop. `---` separates loops in a group; **names resolve across the whole file**, so loops may reference each other's actions and observations.

| key | type | required | meaning |
|---|---|---|---|
| `loop` *(alias: `name`)* | str | **yes** | The loop's name. One document per loop; `---` separates loops in a group. |
| `runs` *(alias: `every`)* | str |  | How often the loop runs — `weekly`, `every 6 hours`, `per_question`. Free text, since cadence is domain-specific; the linter checks that one exists, not its units. This is also the execution boundary used by `outputs.*.terminates`: if a public API returns after one step and expects a later call to continue, write `per_step` and model that return as a non-terminal output plus `pause`; if one API call internally drives all steps, write `per_run_invocation`. A terminal output at this represented boundary uses `terminates: run` even when the domain calls that invocation a turn. Do not mix both altitudes in one document. |
| `boundary` | map of entries |  | The observer-relative system boundary: who drew it, for what purpose, and what is treated as inside or outside. Cybernetic claims are meaningless without a declared system/environment distinction; this block makes that modelling choice reviewable. |
| `goal` *(alias: `regulates`)* | map of entries |  | What the loop is steering, and toward what. |
| `beliefs` *(alias: `estimates`)* | map of entries |  | What it holds a view on but cannot read off directly. |
| `observes` | map of entries |  | What data actually arrives. |
| `actions` *(alias: `acts`)* | map of entries |  | The levers it may pull on the represented world or controlled process. Classify by semantic effect, not implementation dispatch: a `final_answer`, `done`, `complete`, or `terminate` sentinel whose only effect is ending controller execution is a `stop` operation even when the runtime routes it through tool or action code. A sentinel that also changes an outside domain process may be both, but those effects must be represented separately. |
| `action_profiles` | map of entries |  | Conditional, late-bound variants of generic actions. A runtime-level action such as `execute_tool` may have different reversibility and approval properties for different deployments or concrete requests. Profiles preserve that variation without pretending the whole action family is safe or always gated. Make one profile per distinct (binding stage, reversibility, approver) tuple and include one explicit default. Conditions with the same typed properties are one profile with a disjunctive selector, not several named cases. Do not create a lone default profile: put those non-varying properties on the action. Across several profiles, reversibility or approver must actually vary; binding stage alone is not a safety distinction. Do not profile controller-only sentinels; they are operations. |
| `operations` | map of entries |  | Changes to execution of the controller itself — pause, resume, interrupt, retry, compact, hand off, or stop. These are not interventions on the controlled process and therefore do not inherit world-action reversibility or effect-path checks. Merge branches into one operation when kind, authority, and emitted outputs are the same; write their trigger as a disjunction. Split them only when one of those typed consequences differs. The language enforces one operation per `(kind, authorized_by, emitted output-role set)` tuple. |
| `outputs` | map of entries |  | Values emitted out of the represented loop boundary, including final responses, submissions, approval requests, status records, and failures. An output says what leaves; `terminates:` says whether it closes a turn, a run, or neither. Model returned values and operation-relevant emissions, not every log line or persisted trace; termination is always relative to the boundary and cadence declared by this spec. Output identity is its typed role, not a branch label: declare at most one output for each `(kind, terminates)` pair and describe all producing branches together. Publicly yielded stream events are `status` with `terminates: none`; internal logs and persisted traces are not outputs. |
| `processes` | map of entries |  | Parts of the world or system through which actions become later observations. A process closes the represented effect path `action -> process -> observation`; it is not a transfer function or a claim about stability. |
| `when` | list of entries |  | The rule choosing among actions, evaluated in order. Structured rather than prose: prose reads better and cannot be checked, and the checking is the point. |
| `asks_human_when` | list[str] |  | The conditions under which the loop stops and asks a person. Top-level and on its own, because burying escalation inside the decision rule is how it goes missing — this is the list a reader scans first to find out whether the thing can run away. |
| `asks_human` | str |  | The person who receives the escalation described by `asks_human_when`. Must name an entry in `people`. Conditions without a recipient remain accepted as a partial design and produce `escalation_target_unspecified`. Local references may be bare (`operator`) or section-qualified (`people.operator`); normalization removes only a valid, known prefix before strict reference checking. |
| `people` *(alias: `parties`)* | map of entries |  | Who is involved — human or agent — and what each stands to lose. |
| `spends` | map of entries |  | What the loop burns as it runs — iterations, tokens, money, someone's attention — and what stops it. Harness engineering treats budgets, step ceilings and stall detection as standard, and this format could not express any of them: ceilings were prose inside `never`, where nothing could check them. |
| `consider` | map of entries |  | Findings you have read and decided about, keyed by check name — optionally `check/subject` to decide about one instance. This does NOT suppress anything: the finding moves to a `considered` section with your reason attached, so a reviewer sees the decision rather than a silence. A finding you have read and rejected is a different artifact from one you never saw, and that difference is most of what this notation is for. The linter warns when a `consider:` entry no longer matches any finding, because a stale justification is worse than none. |
| `never` | list[str] |  | Hard limits that hold regardless of the goal. |
| `not_modelling` *(alias: `ignoring`)* | list[str] |  | Knowingly out of scope. Not decoration: this is the first list to revisit when the loop misbehaves for reasons it cannot see. |

## `boundary`

Who drew the system/environment distinction, for what purpose, and where it lies.

| key | type | required | meaning |
|---|---|---|---|
| `drawn_by` | str | **yes** | The person or agent whose distinctions define inside and outside. Must name `people`. |
| `purpose` | str | **yes** | Why this boundary and these variables were chosen. This records the observer's purpose; it does not imply a stronger second-order analysis of how that purpose was formed. |
| `inside` | list[str] |  | Components treated as part of the regulated system for this purpose. |
| `outside` | list[str] |  | Environmental components treated as outside the system for this purpose. |

## `goal.<name>`

What the loop is steering, and toward what.

| key | type | required | meaning |
|---|---|---|---|
| `keep` *(alias: `target`)* | str |  | The target, read as a sentence: `keep: below 400`, `keep: above 3 sources`. |
| `from` *(alias: `computed_from`)* | list[str] |  | What this quantity is computed from. |
| `unit` | str |  | USD, days, percent — whatever makes the number meaningful. |
| `set_by` | str |  | `<loop>.<quantity>` — the outer loop's quantity that IS this setpoint. Cascade control, the standard shape of every real control hierarchy: a slow outer loop decides what the fast inner loop should aim at. Naming the QUANTITY and not just the loop is what makes the link structural — otherwise "set by the strategy loop" is a comment, and nothing can check whether that loop is able to move the number it is nominally responsible for. Naming it is what stops an outer loop's target from quietly becoming an inner loop's unexamined constant, which is how layered agent systems actually fail. Conventional cascade design requires the inner loop's DYNAMICS to be substantially faster than the loop setting its target. This format records update cadence, not bandwidth or settling time, so the linter uses a non-faster inner cadence only as a review signal. It does not prove oscillation. |
| `confidence` | number |  | How firmly the goal ITSELF is held, 0–1 — uncertainty about what you want, as distinct from uncertainty about the world. Optional, and deliberately not a primitive: it enters on one book sketch and that is not enough evidence. |

## `beliefs.<name>`

What it holds a view on but cannot read off directly.

| key | type | required | meaning |
|---|---|---|---|
| `question` *(alias: `means`, `description`)* | str |  | The belief in plain language, as the question it answers — "will the customers we buy this month stay?". Optional and worth writing: it is the line a reader understands first, and the one that exposes a belief nobody can actually state. |
| `from` *(alias: `formed_from`)* | list[str] |  | DEPRECATED — declare the edge once, on the observation, with `informs:`. This said the same thing from the other end and the two could disagree silently: one spec had `beliefs.product_market_fit.from: [stripe]` and `observes.stripe.informs: cost_per_customer`, and BOTH edges were created. Still accepted so old specs parse; it is now an error for the two to contradict each other. |
| `how` *(alias: `method`, `how_formed`)* | str |  | How the view is formed: bayesian, judgement, a formula, an LLM call. |
| `checked_by` *(alias: `calibrated_by`, `how_checked`)* | str |  | What scores this belief's PAST calls against what actually happened. Its absence is the most common defect in real loops — found in three independent systems by three careful authors. A belief nothing checks cannot be shown to track anything. |
| `checked_against` *(alias: `outcome`)* | str |  | The observation that later carries the outcome used to score this belief. Must name an entry in `observes`. Without a prediction→outcome join, `checked_by:` is only a review label and cannot establish calibration. |
| `scoring_rule` *(alias: `score`)* | str |  | How predictions are scored against outcomes — for example Brier score, log loss, calibration error, or a domain rubric. Free text because belief types differ; absence is reported as an incomplete calibration contract. |
| `window` *(alias: `calibration_window`)* | str |  | The cohort or time window over which the score is interpreted, such as 90 days or 200 predictions. Distinct from `every:`, which says how often the review runs. |
| `adjusts` | `trust` \| `method` \| `threshold` \| `source` \| `retirement` |  | What the check changes when performance is poor. Scoring without a revision target is evaluation, not a closed calibration loop. |
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
| `checked_by` | str |  | What reviews whether this observation is worth what it costs — whether looking here earned the attention. Distinct from calibrating a belief: belief calibration asks whether a conclusion was right, while this attention review asks whether looking at this signal was worthwhile. A loop that keeps paying for a source that never changed a decision is not wrong about anything; it is spending attention it will not get back. |
| `value_metric` | str |  | How the review judges this observation's decision value relative to its cost — for example decisions changed, information gain, or avoided review time. |
| `review_window` | str |  | The cohort or period over which the observation's value metric is assessed. |
| `review_every` | str |  | How often the attention review runs. Distinct from `review_window`, which says which observations are included in the assessment. |
| `adjusts` | `sampling` \| `source` \| `routing` \| `retirement` |  | What changes when this observation does not earn its cost. A review that cannot alter attention is evaluation, not a closed attention-control contract. |

## `actions.<name>`

The levers.

| key | type | required | meaning |
|---|---|---|---|
| `moves` | str|list |  | The quantity this drives. Nothing pointing at a goal makes that goal a wish. |
| `can_undo` *(alias: `reversibility`)* | `yes` \| `costly` \| `no` \| `unknown` |  | THE LOAD-BEARING FIELD, phrased as the question anyone would actually ask. Approval demanded everywhere gets ignored; approval demanded where the answer is `no` is a rule people follow. `costly` means undoable at real expense. `unknown` states that the design has not bound reversibility; it never counts as safe. NOTE: YAML 1.1 reads bare yes/no as booleans, so `can_undo: no` arrives as False. That is accepted and normalised rather than rejected — the natural phrasing must not be a trap. It is the one place this format tolerates YAML's ambiguity, because the blind test showed people write exactly this. |
| `needs_approval` *(alias: `approval`)* | str |  | The person who must say yes first. Must name someone in `people`. |
| `effect_after` *(alias: `delay`, `effect_shows_after`, `effect_shows_in`)* | str |  | How long until the effect is visible. Lag with no damping is what makes loops thrash. |
| `damping` | str |  | Deadband |
| `consumes` | list[str] |  | Finite things this draws down. |
| `through` | str|list |  | The declared process or processes through which this action's effect becomes observable. Must name entries in `processes`. Without it, `moves:` states intended influence but not a represented feedback path. |
| `effect` | `increase` \| `decrease` \| `unknown` |  | The believed direction of this action's effect on every quantity in `moves`. Write `unknown` when the sign is not known; omission and explicit uncertainty are different. Direction alone is insufficient for stability or gain analysis. |
| `effects` | map |  | Per-quantity effect directions when one action moves several quantities in different directions. Keys must exactly name quantities in `moves`. Use either `effect:` for one shared direction or `effects:`, never both. |

## `action_profiles.<name>`

Late-bound variants of generic actions.

| key | type | required | meaning |
|---|---|---|---|
| `action` | str | **yes** | The generic entry in `actions` whose request or deployment variant this describes. |
| `when` | str |  | The condition selecting this profile. Use `default: true` instead for the fallback profile; exactly one of `when:` and `default: true` is required. |
| `default` | bool |  | This profile covers requests not matched by another profile. At most one default is allowed per action. A default with `can_undo: unknown` is how a generic runtime remains honestly unbound rather than silently safe. |
| `resolved_at` | `design` \| `deployment` \| `request` | **yes** | The stage at which this profile becomes known. `deployment` distinguishes an available runtime capability from configured policy; `request` says concrete arguments determine it. |
| `can_undo` | `yes` \| `costly` \| `no` \| `unknown` | **yes** | Reversibility for this profile only. `unknown` is explicit and does not count as safe. |
| `needs_approval` | str |  | The person who must approve requests matching this profile. Because the profile has a selector, this gate is conditional rather than a claim about every instance of the action. |
| `description` | str |  | What source or deployment fact this profile represents. |

## `operations.<name>`

Transitions in execution of the controller itself.

| key | type | required | meaning |
|---|---|---|---|
| `kind` | `start` \| `pause` \| `resume` \| `interrupt` \| `retry` \| `compact` \| `handoff` \| `stop` | **yes** | The controller transition. `pause` is a resumable suspension exposed across the public invocation boundary; awaiting approval inside one still-running call is an action gate, not a pause/resume pair. `interrupt` cancels an active step asynchronously; a stop flag polled between steps is `stop`. Ordinary invocation is implicit, so use `start` only for a distinct out-of-band start transition. `retry` repeats the same stage; `handoff` changes the active controller; `stop` ends the declared turn or run. None acts on the controlled process. |
| `when` | str |  | The condition under which this controller operation occurs. |
| `authorized_by` | str |  | The external person or agent granted authority to invoke this operation. Must name an entry in `people`. Omit it when the controller merely executes its own branch; execution is not authorization. A generic API caller is not evidence of a human: use `kind: system` when the source identifies a calling component, and omit authority when it identifies neither. For asynchronous cancellation requested through an external flag, use `kind: interrupt` and name the party only when the source establishes who may set that flag. |
| `emits` | str|list |  | Output or outputs produced when this operation occurs. Must name entries in `outputs`. |
| `description` | str |  | What the operation changes in controller execution. |

## `outputs.<name>`

Values emitted out of the represented loop boundary.

| key | type | required | meaning |
|---|---|---|---|
| `kind` | `final` \| `submission` \| `approval_request` \| `status` \| `failure` | **yes** | The outward role of this emitted value. `final` is the successful deliverable; `failure` is an error result or exception; `status` is lifecycle/progress information; `approval_request` asks an external authority to decide; `submission` hands work to an external evaluator. Only model separately consumable interface values. Logs, internal callbacks, and fields nested inside a final result are not additional outputs unless the represented public contract exposes them independently. |
| `terminates` | `none` \| `turn` \| `run` | **yes** | The execution scope closed by this output. `run` always closes the represented invocation, even when that invocation is named a user turn. `turn` is reserved for an internal model/provider turn inside a longer represented run. `none` is outward but non-terminal. |
| `description` | str |  | What leaves the loop boundary. |

## `processes.<name>`

The world or system path through which action becomes later observation.

| key | type | required | meaning |
|---|---|---|---|
| `observed_as` | list[str] |  | Observations produced by this process. Each must name an entry in `observes`; together with an action's `through:` this closes the represented world path. |
| `location` | `inside` \| `outside` \| `interface` |  | Where this process lies relative to the declared boundary. |
| `description` | str |  | What transforms the action into a later observable consequence. |

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
| `reads` | list[str] |  | The goal, belief, or resource names this rule actually reads. This is the semantic input; `if:` is the human-readable expression. Older specs may omit it and the expander will infer likely inputs from `if:`, marking the result `inputs_inferred: true`. New specs should declare it so punctuation and prose wording cannot change the graph. |
| `against` | list[str] |  | Goal quantities whose declared `keep:` conditions this rule compares its inputs against. Each name must be a goal with a target. Naming it here implies that the rule reads that quantity; normalization adds it to an explicit `reads:` list when needed. This is the semantic comparator; `if:` remains the human-readable expression. |
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
- `action_profiles.*.action` must name an entry in `actions`
- `action_profiles.*.needs_approval` must name someone in `people`
- `operations.*.authorized_by` must name someone in `people`
- `operations.*.emits` must name an entry in `outputs`
- `actions.*.moves` must name something in `goal` or `beliefs`
- `actions.*.through` must name a process in `processes`
- `when[].do` must name an action in `actions`
- `when[].reads` must name something in `goal`, `beliefs`, or `spends`
- `when[].against` must name a targeted quantity in `goal`
- `when[].escalate` must name someone in `people`
- `asks_human` must name someone in `people`
- `beliefs.*.from` must name an observation in `observes`
- `beliefs.*.checked_against` must name an observation in `observes`
- `observes.*.informs` must name something in `goal` or `beliefs`
- `processes.*.observed_as` must name an observation in `observes`
- `boundary.drawn_by` must name someone in `people`
- `people.*.sees` must name something in `goal` or `beliefs`
- `observes.*.produced_by` must name an action in `actions`

Errors carry a did-you-mean suggestion, so the message names the fix rather than only the fault.
