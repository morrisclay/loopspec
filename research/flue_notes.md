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
