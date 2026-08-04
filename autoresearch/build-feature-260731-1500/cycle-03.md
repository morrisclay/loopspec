# Cycle 3 — semantic review workflow and reproducible evidence freeze

## Completion audit

The aggregate release predicate was green, but two promised product capabilities were not yet
proved by it:

- “two specs can be diffed” existed only as a coarse side-by-side table, not as a canonical
  semantic review operation;
- the external protocol required a researcher to copy hashes, active checks, commit metadata,
  and doctor output manually.

The rule catalog audit also found one authoring diagnostic (`policy_entirely_blind`) incorrectly
classified as compatibility-only even though it fired on four v1.1 corpus specs.

## Accepted change

- `uras diff BEFORE AFTER` compares validated canonical documents and finding sets. It reports
  document fields, node fields, edges, loop membership, and finding deltas; `--json` emits a
  stable contract and `--fail-on-change` returns status 3.
- Every diff side carries a SHA-256 semantic hash independent of YAML mapping and collection
  order.
- `tests/conformance.yaml` pins normalized semantic and complete finding-set hashes for all
  nine shipped product examples. The doctor gate recomputes it, making intentional semantic
  drift reviewable and giving independent implementations an exact comparison target.
- `tools/external_eval.py --freeze` now refuses dirty semantic artifacts or a failing source
  doctor gate, then emits the complete protocol manifest from the committed checkout.
- The frozen artifact boundary now includes the normative protocol, templates, language and
  ontology sources, analyzer, generator/gate scripts, mutation tests, packaging constraints,
  and exact Python/PyYAML runtime fingerprint.
- The catalog distinguishes 38 active authoring checks from 12 compatibility-only graph
  checks. Every authoring check has an executable positive fixture; the complete example is a
  shared zero-finding negative. Compatibility checks cannot enter an external author record.
- Calibration results are documented as time-indexed operational evidence rather than mutable
  fields in the stable design spec.
- The convergence plan now treats the already-open historical transport set as compatibility
  evidence and the preregistered external-author systems as the prospective transport test.

## Verification

- 38 tests pass.
- The same source doctor gate passes under Python 3.11, 3.12, 3.13, and 3.14 with PyYAML 6.0.3.
- Semantic diff is invariant to reversed YAML mappings and detects an effect-direction change,
  lost reference edge, and introduced finding.
- Check and diff JSON are byte-identical under hash seeds 1 and 777.
- The wheel installs outside the checkout and its check, diff, and doctor commands pass.
- Generated references/check rates are stable and all relative Markdown links resolve.
- The freeze path is tested for both a clean doctor-green manifest and dirty-tree refusal.
- The conformance target is included in the external-study freeze boundary.

## Result

The local release-candidate predicate remains satisfied with a stronger product and evidence
boundary. Independent implementation conformance and external-author usefulness remain
unevidenced; neither is replaced by internal tests.
