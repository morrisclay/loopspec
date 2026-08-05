# Cycle 01 — types worked; individuation did not

## Candidate

- `ControlOperation` for controller-internal execution transitions;
- `Output` for values crossing the loop boundary;
- `ActionProfile` for request/deployment-resolved reversibility and authority;
- explicit `can_undo: unknown` remains non-safe;
- a missing default action profile is a structural finding.

## Blind result

| case | precision | recall | F1 |
|---|---:|---:|---:|
| Aider | 0.265 | 0.643 | 0.375 |
| AgentLab | 0.214 | 0.429 | 0.286 |
| OpenAI Agents SDK | 0.778 | 0.778 | 0.778 |
| **micro** | **0.394** | **0.667** | **0.495** |

The preregistered 0.80 threshold failed. No normative promotion is allowed from this cycle.

## Adjudication

The encoders did not collapse controller behavior into world actions once the types were
available. Disagreement came primarily from individuation and boundary altitude:

- Aider replication encoded every source-visible retry/interrupt and many user-visible status
  records; the primary encoded only mechanisms in the frozen gold set.
- AgentLab replication merged three termination causes into one stop operation and encoded
  setup, parse retry, logs, tape output, and errors separately.
- OpenAI Agents SDK differed on `pause` versus `interrupt`, omitted explicit run-again/final
  operations, and correctly exposed a primary boundary error: an approval result terminates one
  `Runner.run()` invocation even though its state is resumable.

Two raw outputs failed the grammar. Both are retained. AgentLab described a repair in its own
comments but failed to apply it; its labelled comparison copy materializes that action. The
Agents SDK output contradicted causal `origin` and `produced_by`; its labelled copy changes only
that provenance value.

## Decision

Keep the three node distinctions as an experimental candidate. Add explicit individuation rules
for operation merging, pause versus interrupt, boundary-relative termination, and meaningful
outputs. Do not rerun the opened systems as holdouts. Freeze a fresh coding/runtime system and a
fresh browser system for cycle 02.
