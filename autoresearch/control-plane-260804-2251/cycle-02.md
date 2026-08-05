# Cycle 02 — prose did not canonicalize identity

## Frozen holdouts

- Hugging Face smolagents at `e3a5b8994b301983b91c0325546e9dc82eab8cf0`;
- Skyvern at `6442cdc49dbe031c7d9462c140d9035fd2d6f0cd`.

The revisions and exact source ranges were added to
`research/control_plane/source_packets.json` before either independent encoding was run.
Primary encodings and the typed mechanism expectations were also frozen first.

## Blind result

| case | precision | recall | F1 |
|---|---:|---:|---:|
| smolagents | 0.467 | 0.778 | 0.583 |
| Skyvern | 0.147 | 0.417 | 0.217 |
| **micro** | **0.245** | **0.571** | **0.343** |

The micro row is computed from 12 shared fingerprints, 21 primary fingerprints, and 49
replication fingerprints. The preregistered 0.80 threshold failed. No normative promotion is
allowed from this cycle.

## Adjudication

The independent documents are valid v1.2 documents, so grammar mechanics were not the failure.
Four semantic identity ambiguities remained:

1. Branches with the same typed outcome were still named as separate operations and outputs.
   Skyvern, for example, emitted separate failed, terminated, canceled, timed-out, and
   budget-exhausted records rather than canonical output roles.
2. `authorized_by` was read as the controller that executes a branch rather than an external
   party granted authority to invoke it.
3. Runtime sentinel values named `final_answer`, `CompleteAction`, and `TerminateAction` were
   encoded as world interventions because the implementation routes them through its tool or
   action dispatcher, even though their semantic purpose is to stop the controller.
4. Public streaming and step-boundary returns made the chosen run boundary inconsistent.

The raw outputs and run metadata are retained under
`research/control_plane/independent_encodings/`; neither required a syntax repair.

## Decision

Reject promotion again. Prose guidance alone is too weak. Cycle 03 will freeze fresh holdouts,
then make canonical identity machine-checkable: one output per `(kind, termination)` role; one
operation per `(kind, authority, emitted-role set)`; invocation authority distinct from the
executing controller; terminal sentinels classified by semantic effect rather than dispatcher
class; and explicit boundary rules for public streams and resumable per-step returns.
