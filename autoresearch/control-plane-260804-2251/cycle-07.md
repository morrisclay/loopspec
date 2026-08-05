# Cycle 07 — independent replication of adjudicated gold

## Frozen cases and primary models

Cycle 06's exact SWE-agent and Browser Use source packets are reused. Their source-adjudicated
primary encodings are frozen before this run. No grammar, reference, prompt, source range, or
fingerprint rule changes between the cycle-06 raw outputs and this replication.

## Independence and acceptance

The replication uses a fresh, tool-disabled Claude Opus invocation with no session persistence
and a separate output directory. Both raw documents must validate without repair and reach
micro-F1 >= 0.80. Passing this gate permits promotion to repository integration gates.

## Result and decision

Both raw documents validated without repair. SWE-agent scored 0.615 F1 and Browser Use 0.353;
micro precision was 0.389, recall 0.583, and F1 0.467 (14 shared, 24 primary, 36 replication
fingerprints). Reject promotion. Cycle 08 records the residual categories and stops at the
preregistered ceiling.
