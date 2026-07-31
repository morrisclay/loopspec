# Sealed set v2 — agent loop domain

## Why a new seal

`llm_agent_system` was in the v1 sealed set and was **spent on 2026-07-31**, several hours
before the agent-loop pivot was proposed. It was opened as part of the general programme's
generalisation gate, when it was one of four sealed systems and agent loops were not the
domain. Nothing improper happened — the pivot changed what that expenditure cost, after the
fact.

**Consequence: the pivot has no held-out generalisation signal in its native domain.** That is
a real hole and it cannot be undone. This file opens a new one.

## Sealed — do not read, encode, or design against

Chosen for structural spread across the agent-loop space, not for convenience:

| system | where | why it is here |
|---|---|---|
| `cartographer_meeseeks` | `t-minus spec/CARTOGRAPHER-MEESEEKS.md` | a mapping/exploration loop rather than a converging one — different shape from steward and sourcing |
| `ein_concierge` | `t-minus spec/EIN-CONCIERGE-SPEC.md` | human-facing, conversational, interruptible — the human-in-the-loop case |
| `mission_lifecycle` | `t-minus features/mission/mission-lifecycle.feature` | long-lived with explicit lifecycle states |
| `langgraph_reference` | a LangGraph published reference example, to be chosen by someone else | a foreign framework, so the IR is not tested only on this house's conventions |

**I have not read any of these.** `CARTOGRAPHER-MEESEEKS.md` and `EIN-CONCIERGE-SPEC.md`
appeared in a directory listing and their filenames were visible; neither was opened.
`mission-lifecycle.feature` was listed but not read. That is the extent of the exposure and it
is recorded so the seal's integrity can be judged rather than assumed.

## The rule

From `ontology/score.md`, unchanged:

> Encoding held-out systems to raise `E` destroys the only generalization signal available,
> permanently and irrecoverably.

Opened only when the agent-loop catalog is frozen — meaning three consecutive agent benchmarks
requiring no new primitive and no new relation. Not before, and not to settle an argument.

The v1 lesson stands: it took three harvest attempts and a spent sealed system to learn that
the expensive mistakes here are the ones that look cheap at the time.
