# Results: synthetic episode accounting

**Run date:** 2026-08-13
**Corpus:** 80 series / 560 episodes / 4 equally represented domains

This is a deterministic synthetic representation experiment. Its assessors are executable
role-separated baselines, not independent human reviewers or model families.

## Primary comparison

| condition | transition macro F1 | accuracy | bearer accuracy | recursion F1 | Brier ↓ | false recursion | overclaim on no-transition | governance accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `performance_only` | 0.367 | 50.0% | 41.2% | 0.660 | 0.703 | 29.2% | 29.2% | 90.0% |
| `ordinary_trace` | 1.000 | 100.0% | 100.0% | 1.000 | 0.125 | 0.0% | 0.0% | 90.0% |
| `episode_ledger` | 1.000 | 100.0% | 100.0% | 1.000 | 0.011 | 0.0% | 0.0% | 100.0% |

## Preregistered hypotheses

- **H1 passed:** ledger macro F1 exceeds performance-only by at least 0.20.
- **H2 failed:** ledger macro F1 exceeds ordinary trace by at least 0.08.
- **H3 passed:** ledger false-recursion rate is at least 0.15 below performance-only.
- **H4 failed:** ledger bearer accuracy exceeds ordinary trace by at least 0.15.

## Interpretation

The ledger changed transition macro F1 by **+0.633** against performance-only and **+0.000** against an ordinary trace.
Its bearer-accuracy lift over trace was **+0.000**.

The useful distinction is not greater log volume. The ledger exposes a joined claim:
a difference at exit, an identified carrier, later availability and retrieval, a separated
entry/exit profile, and evidence that the returned difference affected realization of the
focal power. Storage without later uptake and improvement caused by easier cases therefore
remain non-cases.

## Per-label transition F1

| label | performance only | ordinary trace | episode ledger |
|---|---:|---:|---:|
| `acquired` | 0.652 | 1.000 | 1.000 |
| `lost` | 0.667 | 1.000 | 1.000 |
| `redistributed` | 0.000 | 1.000 | 1.000 |
| `preserved` | 0.000 | 1.000 | 1.000 |
| `none` | 0.515 | 1.000 | 1.000 |

## Mechanism-level accuracy

| mechanism | performance only | ordinary trace | episode ledger |
|---|---:|---:|---:|
| `ai_model_upgrade` | 0.0% | 100.0% | 100.0% |
| `assisted_substitution` | 0.0% | 100.0% | 100.0% |
| `authority_window_erosion` | 0.0% | 100.0% | 100.0% |
| `case_mix_shift` | 12.5% | 100.0% | 100.0% |
| `institutional_rule_learning` | 100.0% | 100.0% | 100.0% |
| `provider_dependency` | 100.0% | 100.0% | 100.0% |
| `repetition_without_retention` | 100.0% | 100.0% | 100.0% |
| `retained_but_unused` | 100.0% | 100.0% | 100.0% |
| `stable_rehearsal` | 0.0% | 100.0% | 100.0% |
| `structured_reappropriation` | 87.5% | 100.0% | 100.0% |

## Decision

The synthetic promotion gate **does not pass**.

Passing would justify continuing the episode artifact as an experimental evidence layer,
not adding it to the public LoopSpec grammar. The next required gates are independent
episode-boundary encoding, a retrospective real case, and the prospective HITL capability
probe in this directory.

## Limits and strongest rival

The simulator and assessors share a designed vocabulary. High ledger performance may partly
show that the assessor can read fields written for its task. The strongest rival is a
well-instrumented event trace with explicit component probes and stable artifact identity.
If such a trace reaches the ledger within 0.08 macro F1, episode accounting has not earned
its extra burden under the preregistered rule.

The synthetic run says nothing by itself about actual human learning. Human capability
requires prospective evidence under delay, transfer, removal, and recovery conditions.
The included HITL probe creates that path but has no participant outcomes yet.
