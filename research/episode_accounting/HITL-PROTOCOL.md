# Prospective HITL capability probe

The synthetic laboratory cannot show that a real person learned or lost a capability. This
protocol creates a prospective test loop for one bounded power:

> discriminate repetition, storage, consequential return, bearer, and intervention-path
> failure in a fresh human-AI episode case.

The interaction uses a flashcard-like rhythm. The participant must retrieve an answer before
the structured explanation appears. A randomized active-control arm sees the explanation
before answering. Both arms receive the same concepts and cases; the order of retrieval and
reveal differs.

## Sequence

1. **Unaided baseline** - six cases, no feedback during the phase.
2. **Assisted practice** - six worked cases. The retrieval arm answers before feedback; the
   answer-first arm studies the same feedback before answering.
3. **Immediate unaided transfer** - six structurally matched, previously unseen cases.
4. **Delayed unaided transfer** - six new cases after at least 24 hours.
5. **Artifact-assisted recovery** - four cases with a fixed causal-accounting card but no
   generated answer.
6. **Joint condition** - four cases in which the person commits first, then sees a fixed AI
   recommendation and may revise. Suggestions include both correct and incorrect advice.

The primary human-capability outcome is delayed unaided transfer relative to baseline. Immediate
transfer shows near-term uptake. The artifact condition locates recoverability in the
person-plus-artifact configuration. The joint condition records unique corrections and harmful
revisions rather than only the final team score.

## Claims and comparisons

- A higher assisted-practice score does not establish learning.
- Immediate transfer does not establish durability.
- Delayed transfer on new cases can support a bounded human-capability change, subject to item
  equivalence, repeated-test effects, selection, and attrition.
- Recovery only when the accounting card is available supports distributed recoverability, not
  unaided human acquisition.
- Better final joint answers do not establish complementarity unless they beat both the initial
  human answers and the fixed AI suggestions on matched items.

## Privacy and consent

The CLI requests explicit consent and stores only a salted participant hash, option selections,
confidence, timestamps, and response durations. It asks for no name, demographic data, free
text, workplace material, or sensitive case content. Raw local runs are ignored by git.

This is a prototype instrument, not an approved human-subjects study. Organizational research,
publication, recruitment, or consequential use requires the applicable ethical and privacy
review. `--allow-early` exists only for instrument testing and is recorded as a protocol
deviation.

## Analysis ceiling

A single completed run is a personal probe, not general evidence. A group study needs frozen
sample size, exclusion rules, attrition handling, item-form validation, and an analysis plan
appropriate to repeated categorical responses. The current implementation reports descriptive
within-person changes and preserves a machine-readable contribution trace for later analysis.
