# Phase 7 — URAS → Flue Primitive Mapping

Written against the real Flue documentation (97 pages, `npx flue docs`), not the marketing
page. Supersedes the six open questions in `research/flue_notes.md`, which the public site
could not answer.

**This is a mapping, not an implementation.** Per the charter, Phase 7 asks how each
primitive compiles, not how it runs.

---

## 0. The mapping is kept in two columns, deliberately

The top-of-repository directive requires preferring concepts that survive the replacement of
today's LLMs. Flue is 2026 technology. Every row below separates **what URAS means** from
**how Flue happens to execute it**, and nothing from the right column is permitted to flow
back into the ontology.

---

## 1. The termination question is resolved, and the answer is Agent

`research/flue_notes.md` recorded a structural mismatch: a URAS system is a non-terminating
regulator while a Flue `Workflow` appeared to terminate. The real documentation confirms the
mismatch and supplies the resolution.

> **Workflow** — "a bounded job that runs once and returns a result."
> **Agent** — "a continuing assistant or event-driven agent with an identity and sessions
> that can accept interactions over time." Agents are "continuing, stateful contexts."

So:

| URAS | Flue | Why |
|---|---|---|
| **`Loop`** | **`Agent`** (`defineAgent`) | Non-terminating, has identity, accumulates state, accepts input over time. This is a homeostat. |
| A one-shot analysis | `Workflow` (`defineWorkflow`) | Bounded, returns a result. Not a regulator. |
| A single `Intervention` | `Action` (`defineAction`) | "Reusable finite behavior", schema-validated input and output. |

The earlier worry — that mapping a regulator onto a terminating workflow would push the loop
outside the representation — does not arise. **`Agent` is the correct target and it is
natively non-terminating.**

## 2. The Durable Object finding is confirmed and refined

Earlier analysis of Cloudflare DOs concluded that one alarm per object makes `Loop` the unit
that maps to a DO. The Flue docs confirm the shape and remove the manual work:

> "Generated Cloudflare agents use one Durable Object per agent instance. Durable Object
> SQLite stores the canonical stream, attachment bytes, and accepted submissions."

**One Agent instance = one Durable Object.** Since `Loop` maps to `Agent`, `Loop` maps to a
DO — as predicted — but Flue owns the alarm multiplexing, so the "one alarm per DO" constraint
that drove the original analysis is Flue's problem rather than URAS's.

Consequence for the ontology, unchanged: a `System` is a **grouping over Loops**, not itself
the execution unit. That remains the non-obvious result.

## 3. At-least-once is confirmed in the documentation, in these words

The idempotency requirement on `Estimator` was derived from Cloudflare alarm semantics and
was, until now, an inference. The Flue docs state it directly:

> "When no output was durably persisted before the interruption, recovery may re-dispatch the
> provider once — **consistent with at-least-once execution**."
>
> "Use **application-owned idempotency keys** where repeated effects would be harmful."

`Estimator.idempotency_basis` is required by `tools/validate.py` and errors when absent. That
validator rule now has a documented platform justification rather than an inferred one, and
"application-owned idempotency keys" is precisely what the field holds.

**A Bayesian update applied twice double-counts its evidence into a well-formed but wrong
posterior.** This is the single most important correctness constraint in the mapping.

## 4. Full primitive mapping

| URAS primitive | Flue construct | Notes / gaps |
|---|---|---|
| `System` | project + agent grouping | A grouping over Loops. No single Flue object corresponds; it is organisational. |
| `Boundary` | agent/tool capability config | What the agent can reach. Not first-class in Flue. |
| `Loop` | **`Agent`** via `defineAgent` | The core mapping. Continuing, stateful, identity-bearing. |
| `Party` | **agent instance** (`agents/:name/:id`) | Per-instance canonical stream = per-party belief store. Distinct parties are distinct instances. |
| `Signal` | `defineTool` (read-only) / channel ingress | Flue has Discord, Slack, GitHub, Linear, Notion, Shopify, Resend channels — real sensor ingress. |
| `Intervention` (target: world) | **`Action`** via `defineAction` | Schema-validated finite behavior. Exactly the right shape. |
| `Intervention` (target: own-structure) | agent reconfiguration / redeploy | **No native support.** See gaps. |
| `Estimator` | `Action` or agent operation | `idempotency_basis` → application-owned idempotency key. |
| `Estimate` | canonical conversation stream + `ConversationStreamStore` | Durable, append-only, per-instance. |
| `Evidence` (retired) | canonical stream records | Retired from the ontology as a runtime instance rather than a specification structure — and Flue confirms this by making it a *stream record*, not a declared type. |
| `Policy` | agent instructions + Action selection | The `guard` becomes a condition in agent logic. |
| `Delay` | scheduled wake / DO alarm | Flue-managed. |
| `TimeScale` | dispatch cadence / scheduled invocation | |
| `Constraint` | Valibot input schema + tool gating | Non-tradeable constraints become validation that rejects. Good fit. |
| `Consequence` | — | **No mapping.** See gaps. |
| `DesiredCondition` | — | **No mapping.** Currently prose in instructions. |
| `PreferenceOrdering` | — | **No mapping**, and must not be scalarized. |
| `Resource` | — | **No mapping.** See gaps. |
| `Calibration` | `EventStreamStore` + application logic | Records exist to compare prediction against outcome; the comparison is application-side. |
| `Revision` | redeploy / profile change | Schema change, not parameter change. Flue has no first-class notion. |
| Recursive `System` | **subagent** via `task(...)` | Shares the parent's durability envelope; recovery resumes in-process. Genuine recursion. |

## 5. What Flue gives free, and it is more than expected

**Evidence provenance.** The canonical conversation stream records "model-visible messages,
assistant output, tool calls and results, compaction, topology, and recovery facts",
append-only, per instance, readable from a durable offset. URAS wants traceable evidence;
Flue has an append-only audit substrate as its core abstraction. This is the strongest point
of fit and it was predicted before the docs were read.

**Per-party belief isolation.** One agent instance owns one canonical stream. Distinct
parties holding distinct estimates map onto distinct instances with no extra machinery — the
`Party` primitive, which is URAS's likeliest differentiator from classical formalisms, has a
native execution target.

**Recursive viability.** `task(...)` subagents write their own durable records and recover
independently, which is closer to Beer's recursion than hierarchical RL's subordinate
sub-policies.

**Real sensor ingress.** Eleven channel integrations mean `Signal` has concrete
implementations rather than a hand-wave.

**Abort as a distinct terminal outcome.** "Abort is a distinct terminal outcome, not a
failure." That is exactly the `stop_market` exit-branch intervention — abandoning the goal
rather than failing to meet it — and it needs no encoding.

## 6. Gaps — must be built over Flue, not mapped onto it

**Uncertainty. Still the largest gap.** Nothing in Flue represents a distribution, a
confidence, or a posterior. `ConversationStreamStore` and `EventStreamStore` are typed
persistence contracts, so a URAS uncertainty layer can be stored, but the semantics are
entirely URAS-side. First-class uncertainty is a stated design principle and a success
criterion; Flue does not supply it.

**`Consequence` and `PreferenceOrdering`.** No platform concept. These are the primitives
that carry asymmetric stakes and incommensurable objectives — the things that make an
institution more than a pipeline — and they must be pure URAS state.

**`Resource`.** No budget or cost accounting surfaced in the API. Cloudflare billing is a
proxy at the platform layer but is not addressable from the representation.

**Structural interventions.** An `Intervention` with `target: own-structure` changes what the
system can subsequently observe — the andon cord, the tethered rig, vertical integration.
Flue has no notion of an agent modifying its own configuration at runtime; this compiles to
redeploy, which puts the intervention outside the running system. **The sharpest remaining
mismatch**, and it matters because structural interventions were identified as the highest-
leverage move available to a real organisation.

**`DesiredCondition` is prose.** It compiles into agent `instructions`, which is a string.
Everything URAS gained by making goals inspectable is lost at the execution boundary. This is
the clearest case where the IR is strictly more expressive than the backend.

## 7. Where this leaves the engine-independence claim

Four of nineteen primitives have no Flue mapping at all, and one more (structural
intervention) maps only by leaving the running system. That is **evidence for
engine-independence rather than against it**: the IR is not a description of Flue, because
Flue cannot express a fifth of it.

The paper-only second backend from the charter remains worth doing for the opposite reason —
a discrete-event simulator would handle `Resource`, `Delay` and non-termination natively while
handling `Party` and evidence provenance far worse. Two backends failing in *opposite*
directions is the strongest available evidence that the IR is neither.

## 8. Next, concretely

1. **A thin URAS runtime over Flue** carrying uncertainty, `Consequence`, `PreferenceOrdering`
   and `Resource` — the four unmapped primitives — as typed state through a
   `PersistenceAdapter`.
2. **Compile the `venture_acme` encoding** to one `defineAgent` per Loop, one `defineAction`
   per Intervention, and check the result against the source encoding.
3. **Resolve structural interventions.** Either accept redeploy and record the limitation, or
   model self-modification as a Revision the runtime applies to its own configuration.

Documentation is available offline and version-matched via `npx flue docs search <query>` and
`npx flue docs read <path>`, which is the correct source for all follow-up rather than the
website.
