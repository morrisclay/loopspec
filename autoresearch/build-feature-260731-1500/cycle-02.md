# Cycle 2 — cybernetic semantic closure and distributable release candidate

## Accepted change

- The authoring language is v1.1 and generated canonical IR is v2.1.
- Observer-relative boundaries, controlled processes, intended effect direction, explicit
  reference use, ordered per-rule policies, escalation recipients, observation cadence,
  calibration cadence, and attention-review cadence now survive expansion as typed semantics.
- `loses_if_wrong: nothing` is preserved as explicit non-exposure rather than discarded;
  missing consequence information remains distinguishable and reviewable.
- Every one of the 79 accepted authoring fields is accounted for by
  `schema/semantic-map.yaml`; unknown keys and ambiguous aliases fail closed.
- The control projection draws comparators and process paths only when their canonical edges
  exist. Missing structure is rendered as a gap rather than filled by convention.
- The ruleset contains 50 documented checks. The theorem-adjacent checks now state only
  structural or qualitative-proxy conclusions supported by the representation; the former
  requisite-variety headcount check is withdrawn.
- A complete v1.1 example validates, expands, renders, and produces zero design findings.
- The `uras-loop` wheel includes its grammar, ontology, check catalog, and base rates. Its
  `uras` command was installed into an isolated environment and exercised outside the source
  checkout for check, diagram, and doctor operations.
- The external-author study is preregistered with executable eligibility gates and frozen
  artifact hashes. No external usefulness result has been claimed.

## Verification

- 35 semantic-pipeline tests pass.
- Nine product specs are invariant to reversal of every authored mapping, including findings.
- Eight legacy held-out IR encodings remain readable without v2 invention.
- Mutation fixtures reject misspelled safety fields, broken references, incompatible types,
  ambiguous aliases, and colliding graph identifiers.
- Generated grammar/reference and generated check/base-rate artifacts are current under
  `PYTHONHASHSEED=1` and `PYTHONHASHSEED=777`.
- Machine-readable analysis output is byte-identical under both hash seeds.
- `git diff --check` reports no whitespace errors.
- External-study records are rejected unless their frozen spec hash and recomputed
  pattern/assurance/presentation-bucket multiset match exactly.

## Result

Local release-candidate predicate passed. The remaining product claim is empirical: recruit
independent authors, run the frozen study, and let `tools/external_eval.py` decide whether the
pre-registered usefulness thresholds pass. That work requires external coordination and is
not substituted with internal examples.
