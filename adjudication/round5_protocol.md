# Task: adjudicate DERIVED claims

Unlike a previous round, these claims were not written by hand. Each was **computed by a
query over the encoding graph** — a program inspected nodes and edges and emitted the claim
when a structural pattern held. You are the ADJUDICATOR. You wrote none of this.

## Inputs
- `source/*.md` — original prose descriptions of each system
- `cases/*.yaml` — the canonical encodings (flat node/edge graphs)
- `surfaced_cases.yaml` — the derived claims

## Your judgement

For each claim decide:

- `genuine` — states something a practitioner in that domain would NOT already have in mind,
  IS actually established by the graph structure, and bears on a real decision
- `restatement` — true, but merely re-describes what the source prose already says plainly
- `unsupported` — the graph does not actually establish this
- `trivial` — true and supported but not decision-relevant

**Be strict and prefer the harsher verdict.** Note the specific trap for derived claims: a
query can be structurally valid and still merely restate the prose, because the encoding was
built FROM the prose. Structural validity is NOT sufficient for `genuine`. Ask whether the
claim tells a practitioner something the prose did not.

Also note the opposite trap: a claim can be `genuine` even if it sounds obvious once stated,
provided the prose does not state it and the graph does establish it.

## Output

Write `verdicts.yaml`:

```yaml
surfaced:
  - id: D01
    verdict: genuine | restatement | unsupported | trivial
    reason: one sentence
    prose_states_it: true | false      # does the source prose say this plainly?
summary:
  harshest_observation: >
    The most important thing wrong with these derived claims.
  best_claim: >
    Which id, if any, comes closest to genuine insight, and why. Say "none" if none do.
  derivation_vs_assertion: >
    Does computing claims from graph structure produce better claims than writing them by
    hand? Answer from this evidence only.
```

Cover every id. Modify nothing except `verdicts.yaml`.
