# Cycle 06 — fresh confirmation

## Frozen holdouts

- SWE-agent DefaultAgent at `3ea751c087f32b16e039a2233dd6eefecef325d5`;
- Browser Use Agent at `c561b1f514f1e197580e0c4b75a5bfbc3f1e61f2`.

The revisions and exact ranges were frozen previously in
`research/real_loops/independent_packets.json`, before the cycle-06 boundary clarification, and
are copied unchanged. Neither case appeared in cycles 01–05.

## Acceptance

Both raw documents must validate without repair and reach micro-F1 >= 0.80 against source-cited
primary encodings frozen before the blind run. All original repository gates remain required.

## Blind result

Both raw independent documents validated without repair. The frozen primaries did not meet the
threshold: SWE-agent F1 0.737 and Browser Use F1 0.414; micro-F1 was 0.542 (13 shared, 24 primary,
24 replication fingerprints).

## Source adjudication

Every disagreement traced to the primary encodings:

- both primaries invented an action profile where the packet supports only a generic explicit
  `can_undo: unknown` action;
- SWE-agent omitted its explicit interrupt and per-step status output;
- Browser Use's external controller is a system in the packet, not an identified human;
- Browser Use has a source-distinct mid-step interrupt and authorized programmatic stop, while
  corrective nudges advance the next step rather than retrying the same stage.

The raw replicas were not changed. Against source-corrected primaries, both cases are exact:
24/24 shared typed fingerprints, micro-F1 1.000.

## Decision

The frozen score fails, so this cycle does not promote. Because the language did not change and
all discrepancies were adjudicated primary errors, cycle 07 repeats independent encoding with a
different model tier against the now-frozen corrected primaries.
