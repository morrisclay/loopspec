# Instrument Review — the judges were flawed, and most findings were noise

Prompted by the suspicion that the judges might be significantly flawed. They were. Quantified
below, along with what survives.

## v1 defects, measured

- **Length confound.** correlation(answer length, total score) = **+0.72** over n=18. More than
  half the score variance was word count. A 204-word truncated answer scored 5/25 while
  700-word answers scored 22–24.
- **Fake precision.** Mean inter-dimension correlation = **+0.86**, with `causal_depth` and
  `cross_level` at exactly **+1.00**. Five dimensions were one judgment wearing five hats; a
  25-point scale carried roughly 6 points of real information.
- **Single judge, single pass**, no anchors, no repeat, no inter-judge agreement.

## v2 design

1. **Length control** — every answer truncated to an identical word budget per question, so
   completeness cannot be rewarded.
2. **Per-question** comparison rather than whole essays of differing scope.
3. **Ranking, not scoring** — LLM judges order more reliably than they score, and a ranking
   has no scale to drift.
4. **Three judges across three vendors** — gpt-5.5, gemini-2.5-pro, deepseek-v3.2 — with
   agreement reported rather than assumed.
5. **One criterion**, since five collapsed to one anyway.

## The three analyses disagree

| arm | v1 raw | v1 length-controlled | v2 |
|---|---|---|---|
| generated | 5th | 4th | **1st** |
| stratified | 6th | 5th | 2nd |
| generated_both | **1st** | 2nd | 3rd |
| encoding | 3rd | 3rd | 4th |
| both | 2nd | **1st** | 5th |
| prose | 4th | 6th | 6th |

**Only one finding is stable across all three: prose alone is never first, and is last in two
of three.** Every other ordering moves, in some cases from first to fifth.

## And v2 is itself only directional

Inter-judge agreement within v2, Spearman on rank vectors, 28 pairwise comparisons:

```
gpt-5.5        vs gemini-2.5-pro    +0.78
gpt-5.5        vs deepseek-v3.2     +0.71
gemini-2.5-pro vs deepseek-v3.2     +0.38
                        MEAN        +0.59
```

Weak-to-moderate. Directional at best. The orderings should not be trusted even in the better
instrument.

## Retractions

Two things reported earlier do not survive:

1. **"`generated_both` wins decisively, and generated structure beats the persisted URAS
   encoding."** Not stable — it is 1st, 2nd and 3rd across the three analyses. The claim was
   made on the instrument with a +0.72 length confound.
2. **"Stratification's prediction was falsified — it came last."** It ranks **2nd** under the
   better instrument. The prediction is untested, not falsified. This retraction matters more
   than the first, because a falsified prediction was reported as a result.

## What is actually supported

- **Structure helps, weakly and consistently.** Prose alone never wins under any analysis.
- **Which structure cannot be determined** by any instrument built here.
- The difference between arms is **smaller than the difference between instruments**, which is
  the real result of this exercise.

## What a trustworthy answer would need

- More than 3 systems. n=3 with 4 questions cannot separate six arms.
- Inter-judge agreement above roughly 0.8 before orderings mean anything.
- At least one human judgment as an anchor, since all three judges share training-distribution
  biases that no amount of cross-vendor sampling removes.
