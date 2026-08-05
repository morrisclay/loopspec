# Task: adjudicate claims made by two anonymous encoders

Two encoders independently encoded the same systems using a shared ontology. Each made
claims. You are the ADJUDICATOR. You did not write the encodings, the ontology, or the
source prose. Be skeptical: your job is to find claims that do not hold up.

## Inputs
- `source/*.md` — the original prose descriptions of each system
- `cases/*.yaml` — the encodings, anonymised (labels like `hospital-A`, `hospital-B`)
- `surfaced_cases.yaml` — claims that the encoding SURFACED something useful
- `breaks_cases.yaml` — claims that the encoding HANDLES a stated difficulty

## Part 1 — surfaced claims

For each entry in `surfaced_cases.yaml`, decide whether the claim is:

- `genuine` — states something a practitioner in that domain would NOT already have in
  mind, is actually supported by the encoding, and bears on the named decision
- `restatement` — true but merely re-describes what the source prose already says plainly
- `unsupported` — the encoding does not actually establish this
- `trivial` — true and supported but not decision-relevant

Default to the harsher verdict when uncertain. A claim that merely reorganises what the
prose already states is a `restatement`, not `genuine` — this distinction is the entire
point of the exercise, so apply it strictly.

## Part 2 — breaks claims

For each entry in `breaks_cases.yaml`, read the matching `## What this should break` section
of the source, then decide whether the encoding genuinely handles that difficulty:

- `handled` — the encoding structurally represents it
- `named_only` — the encoding mentions or labels it but does not represent it
- `not_handled` — the encoding does not address it

`named_only` is NOT `handled`. An encoding that lists something under an "excluded" or
"unwritten" key has NAMED it, not handled it.

## Output

Write `verdicts.yaml`, exactly:

```yaml
surfaced:
  - id: S01
    verdict: genuine | restatement | unsupported | trivial
    reason: one sentence
breaks:
  - id: B01
    verdict: handled | named_only | not_handled
    reason: one sentence
summary:
  harshest_observation: >
    The single most important thing wrong with these encodings.
  ontology_gap: >
    Anything the ontology itself appears to be missing, based on what the encoders
    struggled to express. Empty string if none.
```

Cover EVERY id. Do not modify anything except `verdicts.yaml`.
