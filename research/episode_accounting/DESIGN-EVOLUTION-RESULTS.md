# Results: logs to LoopSpec design evolution

**Run date:** 2026-08-13
**Corpus:** 80 series; 20 untouched holdout series
**Input to proposer:** blinded ordinary typed traces only

## Holdout counterfactual replay

| arm | mean score | normal power | removal-probe power | governance | design burden |
|---|---:|---:|---:|---:|---:|
| unchanged LoopSpec | 0.519 | 0.575 | 0.408 | 0.689 | 0.000 |
| log-informed revision | 0.549 | 0.608 | 0.462 | 0.719 | 0.137 |
| shuffled revision | 0.527 | 0.593 | 0.430 | 0.689 | 0.137 |
| all controls | 0.544 | 0.654 | 0.550 | 0.719 | 1.170 |
| synthetic oracle | 0.549 | 0.608 | 0.462 | 0.719 | 0.137 |

## Frozen gates

- **G1_score_over_unchanged: passed**
- **G2_score_over_shuffled: passed**
- **G3_oracle_regret: passed**
- **G4_burden_below_maximal: passed**
- **G5_no_material_regression: passed**
- **G7_bundle_selection: passed**
- **G6_all_specs_valid: passed**

Exact holdout bundle selection was **100.0%**. The no-material-regression rate was **100.0%**.
 All 40 materialized alternatives had zero active LoopSpec design findings.

## Interpretation

The proposer did not edit the public LoopSpec grammar. It converted typed log evidence into a small candidate design diff, materialized that diff as a valid LoopSpec, and tested it against paired future episodes. An unchanged recommendation is a legitimate result when the trace shows repetition without retention; a matched-case hold is an evidence revision rather than a claim that extra control improves capability.

The oracle is not independent evidence: its bundles and the counterfactual effects are part of this simulator. Matching it establishes internal consistency and specificity, not deployment validity. The next real gate is an approved prospective comparison in which later episodes test unaided transfer, removal recovery, and intervention viability.

## Decision

The log-to-design path is **provisionally supported in the synthetic laboratory**. It should remain a review workflow: evidence-linked proposal, structural validation, human approval, versioned rollout, and prospective re-assessment.
