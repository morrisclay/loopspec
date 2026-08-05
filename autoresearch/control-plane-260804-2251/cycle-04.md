# Cycle 04 — first-pass validity plus canonical agreement

## Frozen holdouts

- PocketFlow and its DOM browser-agent cookbook at
  `f74d023f93607b8c3268133339a5e532a949898c`;
- Notte's browser agent at `10e0fd35316565cc84bdbe9905d2645972f8b77c`.

Exact source ranges are frozen in `research/control_plane/source_packets.json` before cycle-04
normalization or documentation changes.

## Acceptance

The original micro-F1 threshold remains 0.80 with counter-based typed fingerprints. Unlike the
labelled cycle-03 diagnostic, promotion also requires both raw independent documents to validate
without repair.

Cycle 04 accepts natural qualified local references such as `goal.task_completion` only by
deterministically normalizing the known section prefix to the same local identifier. It does not
relax unknown-reference or provenance validation. The independent prompt also makes explicit
that an action with profiles must omit base `can_undo`/`needs_approval`, and that a
`produced_by` signal must use `origin: ourselves`.

## Blind result

Notte validated on the first pass. PocketFlow failed one redundant-reference check: its rule
declared `against: [task_completion]` but did not repeat that quantity in `reads:`. Qualified
references themselves normalized correctly. Because raw validity was preregistered, the cycle is
rejected.

For diagnosis only, adding the already-declared comparator to `reads:` produced:

| case | precision | recall | F1 |
|---|---:|---:|---:|
| PocketFlow | 1.000 | 1.000 | 1.000 |
| Notte | 0.800 | 0.889 | 0.842 |
| **diagnostic micro** | **0.895** | **0.944** | **0.919** |

The micro row is 17 shared fingerprints, 18 primary fingerprints, and 19 replication
fingerprints. The control-plane semantics exceed the threshold; the remaining failure is
authoring redundancy.

## Decision

Reject promotion. In cycle 05, `against:` will imply the corresponding read. This keeps the
comparator explicit while eliminating a duplicate declaration that can only disagree.
