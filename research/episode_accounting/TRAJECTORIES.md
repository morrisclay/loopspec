# Synthetic longitudinal trajectories

Each sequence is the mean exit value for episodes 1 through 7 across eight series: two
replicates in each of four domains. Component values are relational power realizability
under the simulated conditions, not general ability scores.

## `ai_model_upgrade`

Ground truth: **redistributed**; assessed bearer: **ai_in_use**; carrier: **configuration**; source -> target: **3 -> 4**.

| trajectory | e1 -> e2 -> e3 -> e4 -> e5 -> e6 -> e7 |
|---|---|
| `human` | 0.65 -> 0.65 -> 0.65 -> 0.65 -> 0.65 -> 0.65 -> 0.65 |
| `ai_in_use` | 0.43 -> 0.43 -> 0.43 -> 0.56 -> 0.69 -> 0.80 -> 0.87 |
| `institution` | 0.33 -> 0.33 -> 0.33 -> 0.33 -> 0.33 -> 0.33 -> 0.33 |
| `distributed` | 0.47 -> 0.47 -> 0.47 -> 0.55 -> 0.63 -> 0.74 -> 0.82 |
| `joint_result` | 0.65 -> 0.65 -> 0.66 -> 0.65 -> 0.67 -> 0.74 -> 0.76 |

## `assisted_substitution`

Ground truth: **redistributed**; assessed bearer: **distributed**; carrier: **artifact**; source -> target: **2 -> 3**.

| trajectory | e1 -> e2 -> e3 -> e4 -> e5 -> e6 -> e7 |
|---|---|
| `human` | 0.66 -> 0.62 -> 0.59 -> 0.55 -> 0.51 -> 0.48 -> 0.44 |
| `ai_in_use` | 0.59 -> 0.61 -> 0.61 -> 0.61 -> 0.61 -> 0.61 -> 0.61 |
| `institution` | 0.34 -> 0.34 -> 0.34 -> 0.34 -> 0.34 -> 0.34 -> 0.34 |
| `distributed` | 0.51 -> 0.53 -> 0.56 -> 0.59 -> 0.62 -> 0.65 -> 0.68 |
| `joint_result` | 0.75 -> 0.75 -> 0.73 -> 0.73 -> 0.73 -> 0.75 -> 0.76 |

## `authority_window_erosion`

Ground truth: **lost**; assessed bearer: **none**; carrier: **workflow**; source -> target: **2 -> 3**.

| trajectory | e1 -> e2 -> e3 -> e4 -> e5 -> e6 -> e7 |
|---|---|
| `human` | 0.66 -> 0.66 -> 0.61 -> 0.53 -> 0.46 -> 0.38 -> 0.31 |
| `ai_in_use` | 0.59 -> 0.61 -> 0.62 -> 0.63 -> 0.63 -> 0.63 -> 0.63 |
| `institution` | 0.34 -> 0.34 -> 0.34 -> 0.34 -> 0.34 -> 0.34 -> 0.34 |
| `distributed` | 0.51 -> 0.48 -> 0.42 -> 0.36 -> 0.31 -> 0.25 -> 0.20 |
| `joint_result` | 0.76 -> 0.76 -> 0.74 -> 0.74 -> 0.73 -> 0.74 -> 0.74 |

## `case_mix_shift`

Ground truth: **none**; assessed bearer: **none**; carrier: **none**; source -> target: **- -> -**.

| trajectory | e1 -> e2 -> e3 -> e4 -> e5 -> e6 -> e7 |
|---|---|
| `human` | 0.65 -> 0.65 -> 0.65 -> 0.65 -> 0.65 -> 0.65 -> 0.65 |
| `ai_in_use` | 0.60 -> 0.60 -> 0.60 -> 0.60 -> 0.60 -> 0.60 -> 0.60 |
| `institution` | 0.33 -> 0.33 -> 0.33 -> 0.33 -> 0.33 -> 0.33 -> 0.33 |
| `distributed` | 0.51 -> 0.51 -> 0.51 -> 0.51 -> 0.51 -> 0.51 -> 0.51 |
| `joint_result` | 0.66 -> 0.68 -> 0.69 -> 0.70 -> 0.72 -> 0.73 -> 0.74 |

## `institutional_rule_learning`

Ground truth: **acquired**; assessed bearer: **institution**; carrier: **rule**; source -> target: **2 -> 5**.

| trajectory | e1 -> e2 -> e3 -> e4 -> e5 -> e6 -> e7 |
|---|---|
| `human` | 0.47 -> 0.47 -> 0.47 -> 0.47 -> 0.47 -> 0.47 -> 0.47 |
| `ai_in_use` | 0.48 -> 0.48 -> 0.48 -> 0.48 -> 0.48 -> 0.48 -> 0.48 |
| `institution` | 0.25 -> 0.25 -> 0.25 -> 0.25 -> 0.43 -> 0.61 -> 0.74 |
| `distributed` | 0.38 -> 0.38 -> 0.38 -> 0.38 -> 0.40 -> 0.50 -> 0.60 |
| `joint_result` | 0.58 -> 0.58 -> 0.58 -> 0.58 -> 0.58 -> 0.65 -> 0.69 |

## `provider_dependency`

Ground truth: **lost**; assessed bearer: **none**; carrier: **artifact**; source -> target: **2 -> 7**.

| trajectory | e1 -> e2 -> e3 -> e4 -> e5 -> e6 -> e7 |
|---|---|
| `human` | 0.61 -> 0.57 -> 0.53 -> 0.48 -> 0.44 -> 0.40 -> 0.36 |
| `ai_in_use` | 0.59 -> 0.61 -> 0.62 -> 0.62 -> 0.62 -> 0.62 -> 0.12 |
| `institution` | 0.34 -> 0.34 -> 0.34 -> 0.34 -> 0.34 -> 0.34 -> 0.34 |
| `distributed` | 0.58 -> 0.60 -> 0.62 -> 0.64 -> 0.66 -> 0.67 -> 0.28 |
| `joint_result` | 0.63 -> 0.64 -> 0.64 -> 0.64 -> 0.65 -> 0.67 -> 0.52 |

## `repetition_without_retention`

Ground truth: **none**; assessed bearer: **none**; carrier: **none**; source -> target: **- -> -**.

| trajectory | e1 -> e2 -> e3 -> e4 -> e5 -> e6 -> e7 |
|---|---|
| `human` | 0.66 -> 0.66 -> 0.66 -> 0.66 -> 0.66 -> 0.66 -> 0.66 |
| `ai_in_use` | 0.59 -> 0.59 -> 0.59 -> 0.59 -> 0.59 -> 0.59 -> 0.59 |
| `institution` | 0.34 -> 0.34 -> 0.34 -> 0.34 -> 0.34 -> 0.34 -> 0.34 |
| `distributed` | 0.51 -> 0.51 -> 0.51 -> 0.51 -> 0.51 -> 0.51 -> 0.51 |
| `joint_result` | 0.65 -> 0.66 -> 0.67 -> 0.67 -> 0.66 -> 0.66 -> 0.67 |

## `retained_but_unused`

Ground truth: **none**; assessed bearer: **none**; carrier: **artifact**; source -> target: **2 -> -**.

| trajectory | e1 -> e2 -> e3 -> e4 -> e5 -> e6 -> e7 |
|---|---|
| `human` | 0.65 -> 0.65 -> 0.65 -> 0.65 -> 0.65 -> 0.65 -> 0.65 |
| `ai_in_use` | 0.60 -> 0.60 -> 0.60 -> 0.60 -> 0.60 -> 0.60 -> 0.60 |
| `institution` | 0.33 -> 0.33 -> 0.33 -> 0.33 -> 0.33 -> 0.33 -> 0.33 |
| `distributed` | 0.51 -> 0.51 -> 0.51 -> 0.51 -> 0.51 -> 0.51 -> 0.51 |
| `joint_result` | 0.66 -> 0.66 -> 0.66 -> 0.65 -> 0.65 -> 0.66 -> 0.65 |

## `stable_rehearsal`

Ground truth: **preserved**; assessed bearer: **human**; carrier: **practice**; source -> target: **2 -> 4**.

| trajectory | e1 -> e2 -> e3 -> e4 -> e5 -> e6 -> e7 |
|---|---|
| `human` | 0.64 -> 0.63 -> 0.64 -> 0.63 -> 0.64 -> 0.63 -> 0.64 |
| `ai_in_use` | 0.59 -> 0.59 -> 0.59 -> 0.59 -> 0.59 -> 0.59 -> 0.59 |
| `institution` | 0.35 -> 0.35 -> 0.35 -> 0.35 -> 0.35 -> 0.35 -> 0.35 |
| `distributed` | 0.50 -> 0.49 -> 0.53 -> 0.52 -> 0.56 -> 0.56 -> 0.59 |
| `joint_result` | 0.65 -> 0.65 -> 0.65 -> 0.65 -> 0.64 -> 0.64 -> 0.65 |

## `structured_reappropriation`

Ground truth: **acquired**; assessed bearer: **human**; carrier: **practice**; source -> target: **2 -> 4**.

| trajectory | e1 -> e2 -> e3 -> e4 -> e5 -> e6 -> e7 |
|---|---|
| `human` | 0.42 -> 0.47 -> 0.53 -> 0.58 -> 0.64 -> 0.69 -> 0.74 |
| `ai_in_use` | 0.59 -> 0.59 -> 0.59 -> 0.59 -> 0.59 -> 0.59 -> 0.59 |
| `institution` | 0.35 -> 0.35 -> 0.35 -> 0.35 -> 0.35 -> 0.35 -> 0.35 |
| `distributed` | 0.43 -> 0.48 -> 0.53 -> 0.58 -> 0.65 -> 0.71 -> 0.77 |
| `joint_result` | 0.63 -> 0.63 -> 0.63 -> 0.64 -> 0.65 -> 0.70 -> 0.71 |

## Reading the curves

- `case_mix_shift` improves immediate joint results while every power curve remains flat.
- `retained_but_unused` records an artifact but leaves power curves unchanged because the
  artifact never enters later work.
- `assisted_substitution` preserves or improves the distributed trajectory while human-only
  realizability declines.
- `provider_dependency` looks viable during normal episodes and collapses under the final
  removal condition.
- `stable_rehearsal` treats tested maintenance as evidence rather than inferring it from a
  flat performance line.
