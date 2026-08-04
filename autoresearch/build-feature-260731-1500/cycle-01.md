# Cycle 1 — authoritative semantic path

## Baseline

The acceptance suite began with seven tests. Six failed:

- the canonical `runs` cadence disappeared during expansion;
- generated graphs failed their own canonical validator;
- loop membership depended on which signal and action appeared first in YAML;
- `not_modelling` fabricated uncatalogued `Disturbance` nodes;
- alias/canonical duplicates silently overwrote one another;
- distinct source names could silently collapse to one graph id.

The one passing baseline assertion confirmed that a missing cadence was rejected only at the
canonical boundary.

## Accepted change

- Generated design IR is now version 1 and identifies `source_format: loop-v1`.
- `runs` is the single cadence authority and resolves through a `TimeScale` node.
- Loop records carry complete `signals` and `interventions` sets; singular, order-dependent
  representatives are gone.
- The canonical validator accepts generated design provenance and validates plural closure.
- Alias collisions, graph-id collisions, incompatible shared-node meanings, and declared type
  errors fail explicitly.
- `not_modelling` remains `excluded_variables`; no disturbance is inferred.
- `--lint` validates the expanded graph before analysis, uses a unique temporary artifact, and
  propagates query failures as non-zero status.
- Product examples now exercise expansion, semantic validation, and every analysis query in
  the regression suite.

## Working result

Predicate passed: 10 tests green; generated reference and JSON Schema current.

An expanded audit over historical research encodings found pre-existing invalid artifacts.
Those records are evidence and were not rewritten to make the metric green. Product examples
all pass the end-to-end path. Independent/metamorphic verification remains pending.
