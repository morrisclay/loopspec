# Design recommendation after the first synthetic run

## Decision

Do not add episode fields to the LoopSpec authoring grammar.

Continue with an **Episode Accounting Profile over typed evidence events**, with the Episode
Ledger and Return Map treated as derived review projections.

This is a narrower result than the initial proposal. It follows from the preregistered strongest
rival: in the frozen synthetic experiment, an ordinary trace containing stable artifact identity,
component probes, configuration changes, and intervention-window checks matched the complete
ledger at 1.000 transition macro F1 and 100% bearer accuracy. The ledger added no categorical
lift and therefore failed H2 and H4.

It did improve confidence calibration and made governance paths more directly inspectable. That
supports a review projection, not a second mutable source of runtime truth.

## Proposed architecture

```text
LoopSpec design contract
        |
        v
typed occurrence events ---------> immutable evidence store
        |                                   |
        +--------------+--------------------+
                       v
             Episode Accounting Profile
                       |
              +--------+---------+
              v                  v
        Episode Ledger       Return Map
              |                  |
              +--------+---------+
                       v
             reviewed design decision
                       |
              possible LoopSpec revision
```

The contract remains versioned intent. Events remain occurrence evidence. The episode view can
be rebuilt when a boundary is contested without rewriting the underlying event history.

## Minimum typed event vocabulary to test

This list is a research candidate, not a language revision:

- `episode_started` and `episode_provisionally_closed` with the boundary claimant and purpose;
- `prediction_frozen` or `judgement_committed` before assistance or outcome;
- `carrier_written`, `carrier_available`, `carrier_read`, and `carrier_transformed` with stable
  identity and source episode;
- `intervention_triggered`, `grounds_presented`, `control_bound`, and `authority_checked`;
- `action_authorized`, `action_invoked`, `action_executed`, `outside_occurrence_observed`,
  `consequence_observed`, and `repair_observed` as separate states;
- `component_probe_scored` with human, AI-in-use, joint, artifact-only, or institutional condition;
- `configuration_changed` with version, expiry, rollback, and responsible authority;
- `rival_registered`, `confounder_observed`, and `claim_reopened`.

An event need not expose private content. Stable hashes, categorical state, and claim-scaled
evidence may be sufficient. The design should minimize retained data rather than make exhaustive
interaction capture the default.

## Derived return rule

A derived return edge may be asserted only when all of the following are present:

1. a difference is recorded at or after source-episode exit;
2. a carrier with stable identity retains it;
3. the carrier is available to a later episode;
4. uptake or retrieval is observed rather than inferred from availability;
5. a later difference material to the focal power is observed;
6. the strongest live rival and evidence status remain attached.

Missing item 2 means repetition. Items 2-3 without 4 mean storage. Items 2-4 without 5 mean
return without demonstrated consequence. A performance change with an unresolved rival remains
unanswerable rather than being forced into a transition label.

## Relationship to current LoopSpec

The profile should reference the normalized semantic hash and node identifiers of the design it
instantiates. It should not add mutable values to `*.loop.yaml`, and persisted events should not
be reclassified as `outputs`. This preserves the existing distinction between versioned design
intent and time-indexed operational evidence.

The design language may later need one small addition: enough structure to declare the intended
human intervention path—trigger, grounds, window, authority, control, and world return. That
decision should wait for real cases because many parts may already be derivable from `observes`,
`people.sees`, `needs_approval`, operations, outputs, and controlled-process observations.

## Next gates

1. Run independent authors over raw event packets and measure episode-boundary and return-edge
   agreement.
2. Encode one real retrospective whose trace is rich enough to be the strongest rival.
3. Run the prospective HITL probe to test delayed unaided transfer and artifact-assisted recovery.
4. Compare trace-only review with the derived Ledger/Return Map for decision quality, review time,
   privacy burden, and non-duplicate design changes.
5. Promote only fields that survive those comparisons and have an executable diagnostic.

## What would reverse this recommendation

A first-class ledger could still earn its place if real traces cannot reconstruct provisional
closure, unresolved returns, bearer-separated afterstates, or rival accounts without unreliable
post-hoc interpretation—and if recording those fields at the episode boundary changes a
consequential decision enough to justify the burden.

## What the log-to-design experiment adds

The follow-on synthetic experiment tested the final arrow rather than assuming it:

```text
typed log -> evidence signature -> candidate LoopSpec diff -> paired future replay
```

The proposer saw only the ordinary typed trace. On an untouched cross-domain holdout, its
candidate designs improved the preregistered resilient-capability/governance score from `0.519`
to `0.549`, compared with `0.527` for shuffled wrong revisions. All 40 materialized candidates
passed LoopSpec structural validation with zero active design findings, and the log-informed path used `0.137` mean declared
design burden versus `1.170` for adding every available control.

This supports a new tool boundary, not new language fields: LoopSpec tooling may offer an
evidence-linked **proposal** command that emits a semantic diff, supporting event citations,
claim ceiling, expiry, and rollback. Applying the diff must remain separately authorized and
versioned. The later outcome must be evaluated prospectively; a simulator score cannot approve a
real change.
