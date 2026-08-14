# Episode accounting laboratory

This directory is an experimental companion to LoopSpec. It tests whether a time-indexed
episode record helps distinguish repetition from consequential return and helps locate changes
in a bounded causal power.

It is deliberately **not** part of the public authoring language. A `*.loop.yaml` file records
stable design intent. An episode ledger records what happened under one version of that intent,
what remained unresolved, and what may have entered later activity.

The working separation is now:

```text
LoopSpec contract -> typed occurrence log -> evidence-linked candidate diff
                  -> structural validation -> human approval
                  -> versioned LoopSpec -> prospective later-episode test
```

## What the laboratory contains

- `PREREGISTRATION.md` fixes the hypotheses, conditions, metrics, and failure criteria.
- `case_families.yaml` defines four synthetic domains and ten longitudinal mechanisms.
- `episode.schema.json` defines the occurrence-level evidence artifact.
- `series.schema.json` defines a linked episode series with hidden synthetic ground truth.
- `simulate.py` generates deterministic longitudinal cases and blinded evidence packets.
- `assess.py` runs five role-separated executable assessment groups.
- `analyze.py` scores their decisions and writes the result report.
- `DESIGN-EVOLUTION-PREREGISTRATION.md` freezes the log-to-design rules, holdout, metric, and
  promotion gates before the scored design-replay run.
- `design_evolution.py` infers evidence-linked candidate changes from ordinary typed traces,
  materializes valid LoopSpecs, and replays five paired synthetic future episodes.
- `designs/` contains 40 generated, structurally valid candidate LoopSpecs: ten inferred design
  responses in each of four domains.
- `DESIGN-EVOLUTION-RESULTS.md` reports the untouched holdout comparison against no change, a
  shuffled placebo, indiscriminate controls, and the synthetic oracle.
- `test_episode_accounting.py` exercises determinism, privacy of blinded packets, semantic
  distinctions, the full assessment pipeline, and the log-to-design path.
- `data/` contains the frozen generated corpus and assessment outputs.

The assessors are executable baselines, not independent people or model families. Their role
separation tests whether the representation makes relevant evidence mechanically available. It
does not establish external validity.

## Reproduce

From the repository root:

```bash
python3 research/episode_accounting/simulate.py
python3 research/episode_accounting/assess.py
python3 research/episode_accounting/analyze.py
python3 research/episode_accounting/trajectory_report.py
python3 research/episode_accounting/design_evolution.py
python3 research/episode_accounting/design_evolution.py --check-gates
python3 -m unittest research.episode_accounting.test_episode_accounting
```

Start a private prospective human capability probe with:

```bash
python3 research/episode_accounting/human_probe.py new --participant any-local-pseudonym
python3 research/episode_accounting/human_probe.py run --state <path-printed-by-new>
```

Run one eligible phase per invocation. The delayed transfer phase enforces a 24-hour interval.
See `HITL-PROTOCOL.md` before treating the instrument as more than a local personal probe.

All generators use seed `20260813`. Generated JSONL is written with sorted keys, and every
record includes the generator and schema versions used to create it.

## Evidence conditions

Each assessor sees the same underlying series through one of three blinded projections:

1. `performance_only` - task scores, latency, and apparent success;
2. `ordinary_trace` - ordered runtime events and artifact activity;
3. `episode_ledger` - bounded entry/exit profiles, intervention paths, carrier links, delayed
   returns, rivals, and evidence limitations.

No packet includes mechanism names, expected labels, or latent transition state. The frozen
synthetic series retains that ground truth separately for scoring.

## Claim ceiling

The experiment can establish whether, under the declared simulator:

- the ledger distinguishes retained-and-returned changes from repetition and storage alone;
- assessors classify acquisition, loss, redistribution, and tested preservation more accurately;
- the location of a power is more recoverable from separated afterstates;
- provisional closure and intervention-path fields expose failures hidden by a success status.

It cannot establish that the mechanisms describe real people, that episode boundaries will
converge across independent authors, that real records will be honest or ethically collectable,
or that episode accounting improves production outcomes. The prospective HITL instrument can
collect relevant real-person transfer and recovery observations, but has no participant outcomes
until someone actually completes it.

## Log-informed design evolution

The follow-on design experiment uses the ordinary typed trace rather than the richer ledger
because the first experiment found no categorical assessment advantage for the ledger. It
recognizes nine bounded evidence patterns, including falling human-only recovery, a closing
intervention window, saved-but-unused artifacts, provider loss, case-mix shifts, and model
changes. Each pattern maps to a small LoopSpec addition; no pattern maps to changing the public
grammar.

On the untouched 20-series holdout, the log-informed designs scored `0.549` versus `0.519` for an
unchanged design and `0.527` for shuffled wrong revisions. All 40 materialized LoopSpecs passed
structural validation with zero active design findings. These are synthetic counterfactual results under declared policy effects.
They support a reviewable proposal workflow, not autonomous production self-modification.
