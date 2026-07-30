---
set: negative
domain: computation
encoded_by: claude-opus-5
must_not_encode: true
---

# Negative Control — Quicksort

**This must NOT be encodable. If it becomes encodable, the ontology has become vacuous.**

## The system

Quicksort. Input: a list. Output: the same elements, ordered. Picks a pivot, partitions,
recurses.

## Why it must fail

Test each core primitive against it honestly:

- **`Estimand`** — nothing is estimated. Every quantity is directly and exactly known.
  There is no quantity of interest hidden behind a proxy.
- **`Signal`** — no measurement. Reading a list element is not observation under
  uncertainty; it is exact retrieval.
- **`Estimate`** — nothing is uncertain, so nothing is estimated with confidence.
- **`Evidence`** — nothing updates any belief, because there is no belief.
- **`DesiredCondition`** — "sorted" is a postcondition, not a target the algorithm could
  fail to meet and then correct toward. It cannot be off-target and adjust.
- **`Loop`** — recursion is not feedback. Nothing observes the result and acts on the
  difference. The output never re-enters as input to a correction.
- **`Revision`** — the algorithm cannot come to want something else.
- **`Party`** — nobody inside holds anything.

## The distinction being protected

Quicksort **computes**. It does not **regulate**.

The difference is that a regulator observes a difference between what it wants and what it
gets, and acts to reduce that difference, under uncertainty about both. Quicksort has no
want, no uncertainty, and no difference to reduce.

## What would constitute failure of the gate

If someone produces a plausible URAS encoding of quicksort by treating "sortedness" as an
estimand, comparisons as observations, and swaps as interventions — and the encoding looks
reasonable — then the primitives have become so general they have stopped distinguishing
anything. `Estimand` would mean "any quantity," `Observation` would mean "any read," and
`Intervention` would mean "any write."

At that point URAS describes all computation, which is to say it describes nothing, and
"domain independent" would be unfalsifiable.

## Adjacent cases worth testing later

- **Adaptive quicksort** that switches strategy on measured input characteristics — this
  one arguably SHOULD encode, and finding the exact line between it and plain quicksort
  is a genuinely useful boundary test.
- **A retry loop with exponential backoff** — feedback without estimation. Should probably
  fail, but less clearly.
