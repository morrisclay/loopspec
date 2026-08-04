# Independent encoding check — 2026-08-04

## Method

SWE-agent and Browser Use were re-encoded by Anthropic Claude in a new, non-persistent
session with tools disabled. The encoder received only `REFERENCE.md` and the source slices
declared in `independent_packets.json`. It did not receive the primary encodings, linter
output, candidate language changes, or this report.

The raw Browser Use result used qualified references such as
`beliefs.behavioral_loop`, which the grammar rejects. That raw artifact is retained as
`independent_encodings/browser_use.raw.yaml`. The comparison copy removes only the
`goal.`, `beliefs.`, `observes.`, and `spends.` namespace prefixes. No node, edge, field,
or prose claim was added or removed. The mechanical transform is recorded in
`independent_encodings/browser_use.normalization.json`.

Reproduce the exact-pattern comparison:

```sh
python3 research/real_loops/compare_findings.py \
  research/real_loops/encodings/swe_agent.loop.yaml \
  research/real_loops/independent_encodings/swe_agent_default.loop.yaml

python3 research/real_loops/compare_findings.py \
  research/real_loops/encodings/browser_use.loop.yaml \
  research/real_loops/independent_encodings/browser_use.loop.yaml
```

## Exact finding-pattern agreement

| case | shared categories | Jaccard | primary recall |
|---|---|---:|---:|
| SWE-agent | `consequence_without_authority`, `reversibility_unspecified` | 0.167 | 0.333 |
| Browser Use | `belief_never_checked`, `consequence_without_authority`, `reversibility_unspecified` | 0.333 | 1.000 |

This is not sufficient agreement for a defect-rate claim. One of two cases recovered fewer
than half of the primary categories, and the additional categories are mostly consequences
of different boundary and node-type choices.

## Source-adjudicated causal agreement

The disagreement is more specific than “the models saw different systems”:

- Both SWE-agent encoders record that external correctness grading is outside the run.
  The primary encoding represents an in-run `solution_ready` belief and therefore receives
  belief/cross-check/path findings. The replication declines to infer that belief from the
  controller excerpt and instead receives model/reference findings. The root omission is
  shared; its graph projection is not.
- Both SWE-agent encoders leave concrete shell-command reversibility deployment-bound and
  find no source-evidenced human escalation in the default loop.
- Browser Use reproduces all three primary finding categories. Its extra findings come from
  modelling `abort_run` as an intervention on task success and from omitting explicit
  `against:`/`reads:` edges on terminal control flow.
- Both replications were forced to model stop/submission behavior as an action or leave it in
  prose. This independently reproduces the need to distinguish world interventions from
  controller operations and terminal outputs.

## Decision

Do not publish corpus defect rates or use raw finding count as the product metric. Keep the
three proposed language changes as evidence-backed candidates:

1. explicit controller operations and terminal outputs, separate from world interventions;
2. loop-level start, pause, resume, interrupt, and stop authority;
3. deployment-bound action profiles for generic tool runtimes.

Promote a candidate only after it reduces this same blind encoder's graph variance on at
least one further held-out coding loop and one browser loop. Until then, improve authoring
guidance and report findings by causal root.
