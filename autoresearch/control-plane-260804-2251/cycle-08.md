# Cycle 08 — ceiling diagnosis

## Cycle-07 result

The different-model replication produced two valid raw documents but failed promotion:

| case | precision | recall | F1 |
|---|---:|---:|---:|
| SWE-agent | 0.500 | 0.800 | 0.615 |
| Browser Use | 0.300 | 0.429 | 0.353 |
| **micro** | **0.389** | **0.583** | **0.467** |

The micro row is 14 shared fingerprints, 24 primary fingerprints, and 36 replication
fingerprints.

## Residual instability

The replication over-encoded four recurring categories:

1. ordinary invocation as an explicit `start` operation;
2. logs, hooks, nested result fields, and demo logging as independent outputs;
3. action profiles where no safety property varies, including lone default profiles;
4. human authority inferred from a generic caller, plus safe-boundary stop flags classified as
   asynchronous interrupts.

Cycle 08 makes those distinctions explicit and machine-checks the profile cases. It does not run
another adapted holdout: the preregistered eight-cycle ceiling is reached.

## Decision

Stop at **CEILING**. Retain the implementation as an experimental candidate and the complete
negative-result ledger. Do not claim v1.2 convergence until a future fresh, source-pinned
confirmation reaches the unchanged 0.80 raw micro-F1 threshold.
