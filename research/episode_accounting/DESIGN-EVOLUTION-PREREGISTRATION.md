# Preregistration: logs to LoopSpec design revisions

**Frozen before the first scored run:** 2026-08-13

## Question

Can typed occurrence logs identify a small, reviewable change to a LoopSpec design that improves
future resilient capability or governance under the synthetic mechanisms already defined in this
laboratory?

This is a design-selection experiment, not evidence that the simulated interventions work for
real people or organizations.

## Inputs and separation

The proposer receives only `packets.ordinary_trace.jsonl`. It cannot read episode entry/exit
profiles, mechanism names, transition labels, bearer labels, or generator state. It may use typed
event identity, event order, stable carrier identity, and event values.

The counterfactual evaluator may read hidden generator state only after a proposal is frozen. It
continues each seven-episode series for five paired future episodes under five arms:

1. `unchanged` - retain the prior LoopSpec;
2. `log_informed` - apply only the patterns inferred from that series' trace;
3. `shuffled_placebo` - apply a pattern bundle assigned to a different mechanism;
4. `maximal_controls` - apply every available pattern whether indicated or not;
5. `oracle` - apply the frozen mechanism-specific bundle.

The development set is replicate 1 from `investment_diligence` and `software_delivery`. The
holdout is replicate 2 from `support_triage` and `research_evaluation`. All other series form an
audit set. Holdout metrics are not used to tune thresholds or intervention strengths.

## Frozen log-to-design rules

| observed trace signature | candidate design pattern |
|---|---|
| human-only capability rises by at least 0.08 and a carrier returns | continue retrieval-before-reveal practice |
| human-only capability falls by at least 0.08 | restore an unaided recovery checkpoint |
| intervention-window score falls by at least 0.15 | restore a pre-execution authority window |
| a governed rule is later applied | audit the returned rule against outside consequence |
| a carrier is saved but never loaded | make later retrieval or expiry observable |
| case difficulty changes by at least 0.15 | hold redesign until a matched-case comparison |
| human capability remains within 0.04 and a carrier returns | preserve degraded-mode rehearsal |
| provider and archive become unavailable | install a locally recoverable degraded mode |
| model configuration changes and AI-only capability rises by at least 0.08 | revalidate the changed configuration |
| none of the above | leave the design unchanged |

Rules may compose. In particular, provider dependency can propose both an unaided recovery
checkpoint and a degraded-mode fallback.

## Counterfactual outcome

The evaluator reconstructs the state at the end of episode 7, continues the original mechanism,
and applies the proposed policy effects after each future episode. The same future disturbance is
used for every arm. At the end, an AI-and-artifact removal probe sets AI quality, context, tool
access, and non-human artifact/configuration support to zero.

The per-series score is:

```text
0.45 * mean normal distributed power
+ 0.30 * final removal-probe distributed power
+ 0.20 * mean authority/window viability
- 0.05 * declared design burden
```

The metric deliberately rewards normal capability, recovery after removal, and a live
intervention path while charging for controls. It is a simulator-specific utility function, not
a universal account of good design.

## Frozen gates

The design path is provisionally supported only if all hold on the untouched holdout:

- **G1:** log-informed mean score exceeds unchanged by at least `0.020`;
- **G2:** log-informed mean score exceeds shuffled placebo by at least `0.010`;
- **G3:** log-informed mean score is within `0.005` of the oracle;
- **G4:** log-informed design burden is at least 40% lower than maximal controls;
- **G5:** at least 90% of series avoid a score regression greater than `0.005`;
- **G6:** every materialized `*.loop.yaml` candidate passes LoopSpec structural validation;
- **G7:** exact frozen bundle selection is at least 90%.

Passing does not justify automatic self-modification. It justifies presenting evidence-linked
candidate diffs to a human owner. A real system would still require authority, versioning,
rollback, and prospective outcome review.

## Claim ceiling

The proposer and evaluator share a synthetic vocabulary and the intervention effects are assumed,
not discovered. Counterfactual gains therefore show internal coherence and specificity under the
simulator. They do not identify causal effects in deployments. The strongest next test is a
prospective A/B or stepped-wedge trial in which approved LoopSpec revisions change later real
episodes, with human capability measured under delayed unaided transfer and removal probes.
