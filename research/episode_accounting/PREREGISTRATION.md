# Preregistration: synthetic episode accounting

**Frozen design date:** 2026-08-13
**Generator seed:** 20260813
**Status:** synthetic representation experiment; no human participants

## Question

Does a structured episode ledger improve assessment of causal-power transitions over immediate
performance records and ordinary runtime traces in linked synthetic episodes?

The experiment concerns evidential discrimination, not whether the simulated mechanisms hold
in real human-AI work.

## Unit and labels

The unit is an episode series. Every series contains seven analytically bounded episodes. The
hidden generator labels the focal power at the series horizon as one of:

- `acquired` - unavailable at entry and reliably realizable later;
- `lost` - realizable at entry and unavailable under a later declared test;
- `redistributed` - still realizable, but its principal bearer changed;
- `preserved` - a declared perturbation tested the same bearer and the power remained;
- `none` - no warranted transition claim, including repetition, storage without uptake, and
  performance change explained by case mix.

The bearer label is one of `human`, `ai_in_use`, `institution`, `distributed`, or `none`.

## Synthetic domains

The corpus contains equal numbers of four families:

1. investment diligence;
2. software delivery;
3. support triage;
4. research evaluation.

Each family instantiates every mechanism twice, producing 80 series and 560 episodes.

## Mechanisms

The ten frozen mechanisms are:

- structured reappropriation;
- assisted substitution;
- authority-window erosion;
- institutional rule learning;
- repetition without retention;
- retained but unused artifact;
- case-mix shift;
- stable rehearsal;
- provider dependency exposed by outage;
- AI-in-use model upgrade.

Mechanism names and target labels are never exposed to assessors.

## Evidence conditions

Each series is projected into three conditions:

- `performance_only`: immediate joint result, latency, and success;
- `ordinary_trace`: performance plus ordered events, actor, object, and artifact identifiers;
- `episode_ledger`: the complete occurrence record except hidden generator truth.

The trace is intentionally competent: it records saves, loads, probes, changes, and failures
when they occurred. It lacks an explicit episode boundary argument, separated entry/exit
afterstates, unresolved return state, and claim-scaled rival account.

## Assessment groups

Five deterministic roles inspect each packet independently:

1. boundary and temporal continuity;
2. retention and return;
3. component power trajectory;
4. intervention and governance viability;
5. rivals and claim ceiling.

A fixed aggregation rule produces transition, bearer, confidence, recursion status, and an
intervention-path assessment. These programs are representation probes, not external reviewers.

## Primary outcomes

- macro F1 over the five transition labels;
- bearer accuracy;
- binary recursion F1, where `acquired`, `lost`, and `redistributed` are positive and the
  mechanism includes evidenced retained return;
- multiclass Brier score from assessor confidence distributions.

## Secondary outcomes

- overclaim rate on `none` cases;
- false recursion rate on repetition and retained-unused cases;
- accuracy on delayed `n+k` returns;
- governance-path accuracy for authority-window erosion;
- correct abstention/low confidence when evidence is insufficient.

## Hypotheses

- **H1:** `episode_ledger` transition macro F1 exceeds `performance_only` by at least 0.20.
- **H2:** `episode_ledger` transition macro F1 exceeds `ordinary_trace` by at least 0.08.
- **H3:** `episode_ledger` false-recursion rate is at least 0.15 lower than
  `performance_only`.
- **H4:** `episode_ledger` bearer accuracy is at least 0.15 higher than `ordinary_trace`.

## Promotion rule

Episode accounting is not proposed for the LoopSpec language unless H1-H3 pass and no schema
field is required solely because the assessor implementation was written to expect it. H4 may
fail without defeating the artifact, but bearer claims must then remain explicitly experimental.

Even if all hypotheses pass, the next gate is independent boundary/encoding work over real
retrospectives. Synthetic success alone cannot promote authoring syntax.

## Defeating results

The proposal contracts or stops if:

- ordinary traces match the ledger within 0.08 macro F1;
- the ledger mainly rewards direct restatement of hidden labels;
- boundary decisions cannot be separated from outcome-favouring hindsight;
- exhaustive retention is required for the result;
- assessment succeeds only when afterstates are scalarized into a single score;
- generated cases lack meaningful false positives and ambiguous non-cases.

## Deviations

Any change to mechanisms, labels, seed, thresholds, assessor rules, or evidence projections
after the first frozen run must be recorded below before results are regenerated.

1. **2026-08-13, implementation correction after the first scored pipeline run.** The
   `provider_dependency` target episode generated a narrow window and partial control, but its
   hidden `intervention_viable` label was initialized as true. The label was corrected to false.
   This changed only the secondary governance-path accuracy (performance and trace 100% -> 90%;
   ledger 90% -> 100%). It did not change transition, bearer, recursion, H1-H4, or the failed
   promotion decision. The initially rendered report was overwritten rather than retained as a
   result because it expressed an internally contradictory fixture; this deviation preserves the
   correction.

2. Before the first scored assessment, the retained-unused mechanism was corrected so stored
   artifacts did not increase latent artifact support. Storage remains visible in its carrier
   record; causal support requires retrieval. This was caught during generator inspection and did
   not alter a reported result.
