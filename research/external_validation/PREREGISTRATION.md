# Preregistration — does LoopSpec improve real loop designs?

**Status:** protocol specified; no participants recruited and no outcomes observed. The
artifact manifest is not frozen until `--freeze` succeeds on a committed release candidate.
Do not edit thresholds after the first system is encoded. Later amendments must be appended
with date and reason.

## Question

After correcting encoding errors, does a LoopSpec review give external loop authors accurate,
actionable findings that change a specification, decision, or implementation?

This study evaluates LoopSpec as a **structural loop specification and review tool**. It does not
test dynamic stability, theorem compliance, runtime correctness, or whether LoopSpec findings
predict production incidents.

## Frozen artifact

Before recruitment, commit the release candidate and generate the manifest:

```bash
python3 tools/external_eval.py --freeze > study.yaml
```

The command refuses uncommitted semantic artifacts or a failing `loopspec doctor` gate. It records:

- the git commit containing authoring format v1.1, canonical IR v2.1, and check metadata;
- the SHA-256 hashes of the package/dependency constraints, authoring grammar and semantic map,
  graph schema and ontology, check catalog and base rates, expansion/validation/analysis/CLI
  code, protocol, and evaluator listed exactly in `study.template.yaml`;
- the exact Python implementation/version and PyYAML version used to produce analyzer output;
- `python3 tools/loopspec.py doctor` output;
- the exact active check list and assurance levels.

No grammar, semantic, ranking, or message change is allowed after the first system is encoded.
A crash fix may be made only by ending the run and beginning a separately labelled replication.

## Sample

- At least 12 loop authors who did not contribute to LoopSpec.
- At least three domains; no domain contributes more than half the sample.
- At least six systems already operating and at least four still in design.
- One loop per author in the primary analysis.
- Exclude single-pass workflows after author confirmation that no repeated feedback cycle is
  intended. Record exclusions; do not replace them silently.

Recruitment may be convenience-based, but the report must state channels and conflicts. No
participant is told which findings are common in the existing corpus.

## Procedure

1. Collect the artifact the author currently uses: code, diagram, prompt, runbook, or prose.
2. A researcher encodes a draft without seeing linter output.
3. The author corrects the draft until it matches intended design. Track every correction as
   an encoding error; the corrected spec, not the first draft, is the evaluation object.
4. De-identify and freeze the corrected spec, record its SHA-256 hash, and run
   `python3 tools/loopspec.py check <spec> --json`.
5. Present findings in ranked order without theorem embellishment. Show evidence paths and
   assurance labels.
6. For each finding, the author assigns exactly one initial verdict:
   - wrong;
   - encoding error that survived correction;
   - correct, already known, no action;
   - changes understanding;
   - changes the spec or decision;
   - changes implementation.
7. A second reviewer resolves disputed `wrong` versus `correct` labels using only the frozen
   spec and source artifact. Preserve both original labels and adjudication.
8. Recontact acted-on cases after 30–90 days. Record whether the planned change happened and
   any observed outcome. No causal claim follows from this uncontrolled follow-up.

## Primary measures

High-priority is computed, not hand-labelled: a finding shown under `SPECIFIC`, or one whose
pattern is in the frozen set `irreversible_without_approval`, `reversibility_unspecified`,
`incomplete_loop`, `open_loop`, `target_without_actuator`,
`unmeasured_estimand`, `process_path_not_declared`, `reference_not_used`,
`incomplete_calibration_contract`, or `incomplete_attention_contract`. The executable list in
`tools/external_eval.py` must match this paragraph at freeze.

- **Precision:** adjudicated correct findings / adjudicated findings.
- **Encoding-induced rate:** findings caused by an author correction missed before lint / all
  findings.
- **Author action rate:** authors with at least one `changes spec/decision/implementation`
  verdict / authors receiving at least one finding.
- **Finding action rate:** findings labelled as changing spec, decision, or implementation /
  correct findings.
- **Time burden:** minutes from source handoff to author-approved encoding, reported median and
  range.

Report all findings and high-priority findings separately. Do not pool multiple findings for
one author as independent systems when calculating uncertainty.

## Success thresholds

The release claim may advance from “structural notation and review prototype” to “useful design
review tool” only if all hold:

- at least 70% precision on high-priority findings;
- fewer than 20% of all surfaced findings are encoding-induced after author correction;
- at least 50% of authors receiving a finding change a spec, decision, or implementation;
- no safety-relevant false negative is discovered in the mutation set for approval,
  reversibility, resource limits, or calibration joins;
- results do not depend on one domain or one encoder.

“Do not depend” means all three primary rate thresholds still pass after removing each domain
in turn and after removing each encoder in turn. At least three domains and two encoders are
required. This leave-one-group-out rule is deliberately strict and frozen before data.

The study does **not** justify “prevents incidents,” “proves cybernetic adequacy,” or “improves
outcomes.” Those require prospective controlled evidence.

## Kill and narrow conditions

- If high-priority precision is below 60% after 12 systems, stop calling the analyzer a design
  critic; retain the specification/review language.
- If encoding-induced findings exceed 25%, make authoring primary and code/prose extraction
  explicitly experimental.
- If fewer than 25% of authors change anything, describe LoopSpec as a comparison and reasoning
  notation unless qualitative evidence identifies a narrower valuable workflow.
- If a finding needs an unrepresented premise to survive adjudication, withdraw or weaken it;
  do not add the premise retroactively during this run.

## Data record

Store one de-identified YAML record per system with:

```yaml
system_id:
author_id:
domain:
stage: operating | design
source_kind: code | diagram | prompt | runbook | prose | mixed
encoder_id:
loopspec_contributor: false
spec_path:
spec_sha256:
encoding_minutes:
author_corrections: []
findings:
  - pattern:
    assurance:
    presentation_bucket: specific | common | universal | considered
    initial_verdict:
    adjudicated_correct: true | false
    action_promised:
    action_observed_at_followup:
    notes:
```

Raw source artifacts remain private unless the author explicitly licenses publication. Publish
the de-identified corrected LoopSpec specs, records, analysis script, exclusions, amendments, and
all failed thresholds. The evaluator re-runs every frozen spec and rejects a record whose
pattern, assurance, or presentation-bucket multiset does not match analyzer output.

## Executable gate

Generate `study.yaml` with `--freeze`, copy `record.template.yaml` once per author, then run:

```bash
python3 tools/external_eval.py study.yaml records/*.yaml --json
```

Exit 0 means the data is valid and every frozen runtime, sample, rate, safety, and
leave-one-group-out gate passes. Exit 1 means the dataset or frozen artifact record is invalid.
Exit 2 means the
study is valid but does not justify the “useful design review tool” claim. The script verifies
artifact hashes and the exact pattern→assurance map before scoring, derives high-priority
status from the frozen rule above, and reports failed thresholds rather than optimizing them.
`protocol.yaml` is the machine-readable source for the sample minima, thresholds, and frozen
high-priority pattern set; this document explains their meaning.
