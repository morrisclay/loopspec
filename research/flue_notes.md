# Flue — Preliminary Notes

Source: flueframework.com, read 2026-07-30.

These are **research notes, not the Phase 7 deliverable.** Phase 7 cannot be written
until the ontology has converged; mapping primitives to a backend before the primitives
are settled is how backend assumptions get laundered into the representation. Recorded
here so the findings are not rediscovered later.

---

## What Flue is

A TypeScript framework for durable AI agents and workflows, built on **Pi** (an open
agent harness). Multi-LLM, multi-environment. Deploys to Cloudflare, AWS, Docker.

### Primitives

| Flue concept | Description |
|---|---|
| `Agent` | Primary abstraction. Defined via `defineAgent()`. Keeps context across conversations and events while working autonomously toward a goal. Exposed via routing. |
| `Workflow` | Structured automation where code guides agent reasoning "from a clear input to a finished result." Deterministic orchestration. |
| `Sandbox` | Secure execution environment — local, virtual, or remote container. Where agents access tools and modify files. |
| `Skill` | Packaged expertise. Reusable workflows and guidance loaded contextually, imported as markdown modules. |
| `Tool` | Typed agent action — APIs, data queries, controlled state changes. Supports MCP servers. |
| `Subagent` | Delegation to specialized expert child agents. |
| `Session` | Managed agent conversation with recovery. |

### Execution model

Durable execution via persistent session recording in durable streams. Interrupted work
resumes automatically; clients reconnect without restart. "Accepted work is never lost."

Supporting components: TypeScript runtime, database for persistent state, multi-platform
deployment.

---

## Affordances — where the fit is genuinely good

**Durable session recording ≈ evidence provenance.** An append-only durable stream and
"evidence becomes traceable" are close to the same requirement. This is the strongest
point of fit and it is not luck: both are audit structures, arrived at from different
directions. URAS evidence chains may map onto durable streams almost directly.

**`Agent` context ≈ `Observer`.** Each Flue agent carries its own context, which is
structurally per-observer belief. Given that `Observer` is the primitive most likely to
differentiate URAS from classical formalisms, having a natural execution target for it
is a significant piece of luck.

**`Tool` splits cleanly.** Read-only tools are `Sensor`; state-changing tools are
`Actuator`. Flue's typing of tool actions supports the distinction.

**`Subagent` ≈ recursive system nesting** — provisionally. Whether Flue's delegation is
recursive in Beer's sense (each level a full regulator) or merely hierarchical task
decomposition needs checking against the actual API.

---

## Gaps — must be built *over* Flue, not mapped onto it

**No uncertainty. Anywhere.** No belief-with-distribution, no probability, no confidence
interval, no posterior. Flue state is messages and database rows. Since first-class
uncertainty is a stated URAS design principle *and* a success criterion, every estimand
needs representation Flue does not supply. This is the largest gap and it means Phase 7
produces a thin URAS runtime layer over Flue, not a translation table.

**No `Resource`.** No budget, cost, token, or attention accounting surfaced in the
public material. Worth verifying against the API — it may exist unadvertised, since
durable execution systems usually need it internally.

**No `Learning Rule`, no `Calibration`.** Nothing closes a loop on the estimator itself.
Flue agents accumulate context; they do not update a model of how well their own
estimates track reality.

**No `Constraint` or `Invariant` as structure.** Expressible only as imperative workflow
code, which means they cannot be inspected, and "goals become inspectable" fails at the
execution layer.

---

## The structural mismatch

The most important finding, and the one to resolve before Phase 7 produces anything else:

> A Flue `Workflow` runs "from a clear input to a finished result." It **terminates**.
> A URAS system is a **non-terminating regulator**. A thermostat has no finished result.

Flue workflows are *transformations*; URAS loops are *homeostats*. Both are legitimate
shapes and they are not the same shape.

Mapping a continuous regulator onto a terminating workflow leaves two options:

1. An **outer scheduler** re-invokes the workflow on a tick. Cheap, but the loop lives
   outside the representation — the thing URAS most wants to make first-class becomes
   infrastructure Flue cannot see.
2. A **long-lived `Agent`** whose goal is the regulation. Keeps the loop inside, but the
   goal is prose in a prompt rather than a structured `Desired Condition`, so
   inspectability is lost exactly where it matters most.

Neither is natural. The choice will leak into the representation if made implicitly, and
the leak will be invisible because there is no second backend to contrast against.

This is precisely what the paper-only second-backend sketch is for: a discrete-event
simulator has no difficulty with non-termination whatsoever. If URAS ends up unable to
express a thermostat cleanly, it will be because Flue's termination assumption was
absorbed silently.

---

## Cloudflare Durable Objects largely resolve the termination mismatch

Flue deploys to Cloudflare, so the regulator can be a **Durable Object** rather than a
Workflow. Verified against the DO alarms API documentation.

A DO is a long-lived, addressable, single-instance stateful entity with SQLite storage
and an `alarm()` handler that can reschedule itself. That changes the picture materially:
the two options recorded above were an external scheduler (loop lives outside the
representation) or a long-lived agent with a prose goal (inspectability lost). A
self-rescheduling DO alarm is a **third option that removes the objection to the first** —
the tick period becomes part of the object's own persisted state rather than external
infrastructure, so the loop stays inside the representation.

Confirmed properties and their consequences:

| DO property | Consequence for URAS |
|---|---|
| Long-lived, addressable by `getByName()`, deterministic routing | DO identity is a natural `Observer` or `System` identity — stable, addressable, one instance |
| SQLite storage per object | Per-observer belief store, queryable |
| `alarm()` can reschedule itself | Non-terminating regulation without external infrastructure |
| **One alarm per DO** — `setAlarm()` replaces any existing alarm | See below: pushes the mapping toward one DO per *loop*, not per *system* |
| **At-least-once execution**, retried with exponential backoff, up to 6 attempts | See below: forces idempotent estimators |
| Only one `alarm()` instance runs at a time per object | Belief updates serialize — no lost-update race on a posterior. Genuinely useful. |
| DO-to-DO RPC | Inter-system and inter-observer communication |
| Billed on wall-clock and requests | A real `Resource` accounting hook, which Flue itself does not supply |

### Consequence 1: map loops to DOs, not systems

One alarm per object means a system with several loops running at different time scales
inside one boundary cannot be one DO with one alarm. Either one DO per loop, or a
schedule table in storage that the handler drains and reschedules from.

This is a Phase 7 architecture decision that should be made explicitly. The natural
reading is that a URAS **feedback loop** is the unit that maps to a DO, and `System` is a
grouping over DOs — which is not the obvious first guess.

### Consequence 2: at-least-once delivery forces idempotent estimators

The important finding, and it flows *upward* into the representation.

Alarms are guaranteed **at-least-once**, not exactly-once, and are retried automatically
when the handler throws. A Bayesian update applied twice double-counts the evidence. So
under retry, a naive `Estimator` silently corrupts its own posterior — and the corruption
is invisible, because the result is a well-formed distribution that is simply wrong.

Therefore:

- **`Evidence` requires stable identity.** Not a convenience — a correctness requirement.
- **`Estimator` application must be idempotent with respect to evidence identity.**
  Applying the same evidence twice must equal applying it once.
- The validator should be able to check that an estimator declares its idempotency basis.

This is exactly the class of finding Phase 7 exists to produce, and it argues for doing a
thin slice of Phase 7 early rather than strictly last: an execution constraint has
revealed a requirement on the representation that pure ontology work would not have
surfaced.

### What DOs do not solve

- **Still no uncertainty representation.** A DO gives durable *storage* for a posterior,
  not belief *semantics*. The uncertainty layer remains entirely URAS-side. This was the
  largest gap and it is untouched.
- **Fast loops remain out of scope.** Alarms are wall-clock scheduled with no documented
  minimum granularity, but the practical floor and the per-invocation cost make
  high-frequency regulation impractical. Slow institutional loops — a fund reassessing
  quarterly, a hospital daily — fit well. The `Autonomous Vehicle` benchmark at control
  frequency does not, and should be encoded knowing its execution target is elsewhere.
- **No learning or calibration primitives** appear at the platform layer either.

---

## Firewall

Flue is 2026 technology, and the top-of-repository directive requires preferring concepts
that survive the replacement of today's LLMs.

`Skills`-as-markdown-modules, `Subagents`, and MCP integration are all
current-generation framing. They may not exist in ten years. `Estimator`, `Feedback`, and
`Delay` will.

Phase 7 keeps two columns separate throughout — what URAS *means*, and how Flue happens
to *execute* it today — and nothing from the right column flows back into the ontology.

---

## Open questions for the actual API

The marketing page is not enough to finish this. Before Phase 7:

- Is `Subagent` recursion true recursion or one-level decomposition?
- Does any resource or budget accounting exist?
- Can a `Workflow` be genuinely non-terminating, or is termination structural?
- What is the actual shape of durable stream records? Can evidence chains be
  reconstructed from them, or only replayed?
- Does `Session` state support arbitrary typed structures, or is it conversation-shaped?
- Is Pi documented separately? It may be the more honest compilation target, since it
  sits below Flue's agent framing.
