# Versioning and compatibility

LoopSpec versions the human authoring language separately from the canonical graph.

The project was renamed from **URAS** to **LoopSpec** on 2026-08-03. The rename changes the
package and primary command, not the meaning of earlier artifacts. New graphs
emit `loopspec_version`; readers accept the legacy `uras_version` marker throughout LoopSpec
2.x. The `uras` command remains a deprecated alias and is scheduled for removal in LoopSpec 3.0.

| Artifact | Current producer | Compatibility promise |
|---|---:|---|
| authoring language | 1.2 experimental | v1.1 documents remain accepted without edits; v1.2 adds optional control-plane declarations, but its cross-encoder convergence gate has not passed |
| canonical graph IR | 2.2 experimental | 2.x readers accept earlier v2 graphs; IR 2.2 adds typed controller operations, outputs, and action profiles |
| check catalog | generated with the repository | check names and assurance may be narrowed or withdrawn; a stronger claim requires represented premises and new fixtures |

`source_format: loop-v1.2` and `ir_revision: "2.2"` are emitted mechanically. Authors do not
write either field.

The v1.2 implementation is internally verified but not yet a converged field claim. Its bounded
control-plane study stopped at the preregistered ceiling after a fresh independent replication
scored 0.467 micro-F1 against a 0.80 threshold. The complete negative-result ledger is retained
under `autoresearch/control-plane-260804-2251/`.

## Reading older artifacts

- Pre-normal research encodings remain evidence and are validated by the legacy path; they are
  not silently rewritten.
- IR v1 singular loop members remain readable. New output uses plural, order-independent sets.
- Authoring aliases are normalized before validation. Supplying an alias and its canonical key
  together is an error because precedence would be ambiguous.
- Rules without `reads:` remain readable, but inferred inputs are marked and reported.
- IR v2 graphs without boundary/process/review-contract additions remain readable. Generated
  authoring artifacts receive structural findings for the absent semantics.

## Change discipline

A syntax or IR change is accepted only when:

1. its meaning is deterministic and documented in the grammar or IR contract;
   `schema/semantic-map.yaml` must account for the field;
2. unknown keys, references, and incompatible shared meanings still fail closed;
3. product examples, mutation cases, map-order metamorphisms, legacy held-out graphs, and
   generated artifacts pass `python3 tools/loopspec.py doctor`;
4. a migration note says whether old artifacts remain readable and whether findings change;
5. theoretical claims remain at or below the assurance supported by represented data.

The compatibility promise covers readability and semantic preservation, not identical finding
counts: new optional declarations may make previously implicit structure reviewable. Such
changes require a minor version and regenerated corpus base rates.

## Executable conformance target

`tests/conformance.yaml` is the normative release-fixture manifest. For every shipped product
example it pins the authoring version, canonical IR revision, encoded system identity, normalized
semantic hash, complete finding-set hash, and finding count. `python3 tools/loopspec.py doctor`
recomputes the manifest as part of the test suite.

The semantic hash ignores YAML mapping order and unordered canonical collections. The findings
hash covers the complete normalized finding records, including claim, evidence, assurance, and
repair metadata. A deliberate semantic or diagnostic change therefore requires an explicit
manifest update and compatibility review.

This manifest gives another implementation an exact comparison target. Agreement with an
independently developed implementation remains an external evidence gate; the repository does
not claim it merely because the reference implementation is self-consistent.
