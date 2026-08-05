# Cycle 05 — nonredundant comparator references

## Frozen holdouts

- OpenAI Codex turn loop at `2a16af823456712e3dbb030ecf29fb727c2cde66`;
- Goose agent turn loop at `7f62ce53e70c49e634ed9ba16a1ef8e02a2d239c`.

These revisions and exact source ranges were already frozen in
`research/real_loops/independent_packets.json` before the cycle-05 refinement and are copied into
the control-plane manifest unchanged. Neither system appeared in cycles 01–04.

## Preregistered refinement and acceptance

`against:` now implies that the policy reads the named goal quantity. When an explicit `reads:`
list exists, normalization adds a missing comparator quantity deterministically. Unknown names
still fail strict reference checking.

Promotion requires both raw independent documents to validate, micro-F1 >= 0.80, and every
original acceptance condition. No repair may contribute to the promotion score.

## Blind result

Both raw documents validated without repair, but the frozen-primary agreement failed:

| case | precision | recall | F1 |
|---|---:|---:|---:|
| Codex | 0.412 | 0.333 | 0.368 |
| Goose | 0.500 | 0.524 | 0.512 |

## Source adjudication

The disagreement exposed two language ambiguities and two primary-encoding errors:

1. Both loops represent a whole user-turn invocation. The primaries used `terminates: turn`,
   while independent encoders used `run`. `run` now unambiguously means the represented
   invocation; `turn` is reserved for a nested provider/model turn.
2. Both APIs await approval inside one still-running call. That is an action gate and
   non-terminal approval-request output, not a public resumable pause/resume boundary.
3. Codex's cited approval classifier binds from deployment policy and sandbox configuration,
   not the concrete command arguments represented in the packet.
4. Goose's stop-hook plugin actually authorizes one stop branch, while its cancellation token
   packet does not establish who is authorized to set it.

After source-correcting the primaries only—raw replicas remain untouched—the diagnostic scores
are Codex 0.971 and Goose 0.952, or 37 shared fingerprints from 38 primary and 39 replication
fingerprints: micro precision 0.949, recall 0.974, F1 0.961.

## Decision

Reject promotion because the same holdouts exposed the refinement. Carry the clarified boundary
rules into a fresh confirmation cycle.
