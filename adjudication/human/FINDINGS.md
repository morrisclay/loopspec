# First Human Adjudication

Every prior usefulness measurement in this project was a model judging a model. This is the
first from the person who builds and runs the system being encoded.

**2 of 4 genuine, both rated "changes a decision."**

| # | source | claim | verdict |
|---|---|---|---|
| H1 | **automated query** | the resolution estimator is never checked — nothing asks whether a hypothesis resolved the *right* way | **genuine — changes a decision** |
| H2 | encoding | conviction is a decision wearing the clothes of a measurement | restatement |
| H3 | encoding | the loop produces its own evidence; `balance_rule` is the only guard against self-confirmation | **genuine — changes a decision** |
| H4 | encoding | the three variables most likely to distort conviction are the three not recorded | conversation |

## Against the record

| round | claims | genuine | judge |
|---|---|---|---|
| hand-asserted | 11 | **0** | model |
| graph-derived | 9 | 2 | model |
| **this** | **4** | **2** | **human operator** |

## The pre-committed diagnostic did not resolve as predicted

I wrote, before seeing any answer:

> Only item 1 came from the automated query. If items 2–4 land and item 1 doesn't, the value is
> in the act of encoding rather than in anything computed afterward, and the tooling should
> shrink accordingly.

**Neither branch happened.** Both sources produced a decision-changing claim:

```
automated query          1/1 genuine
encoding forced choice   1/3 genuine
```

The query went 1-for-1. That is the **first evidence in this project that `tools/derive.py`
earns its place** — every earlier derived claim was adjudicated by a model, and the one that
reached a human landed.

The dichotomy I framed was false. Encoding and querying are not competing sources; the encoding
supplies the structure the query needs, and the query finds what the encoder does not think to
look at. H1 is a pure absence — no `Calibration` node — which a person reading the same 63 lines
would very likely skim past.

## The claim I found most interesting was the one rated obvious

H2 — conviction as a decision rather than a measurement — is the item I thought was the sharpest.
It connects to the hospital's `discharge_readiness` finding and to the individuation rule, and it
was the most intellectually satisfying thing in the encoding.

**It scored "knew it — obvious."**

Recorded because it is a direct check on my judgement: *my taste is not a predictor of
usefulness.* The two that landed were a missing node and a structural property of the loop's
wiring — both mundane, both mechanical. The philosophically interesting one was worthless.

This is the same lesson as the adjudicator's "typed paraphrase" verdict, arriving from the
opposite direction.

## Scoring, stated carefully

This encoding **in isolation**: `U = clamp(2/2) × 1.0 = 1.00`.

Aggregate `U` remains ~0.04, because it averages across ~24 encodings whose claims were never
human-audited or were rejected by model adjudication.

**I am not re-weighting the metric to reflect this.** Human adjudication is plainly the better
signal and model adjudication was always described as a necessary condition rather than the bar
— but changing the aggregation now, immediately after a favourable result, is exactly the move
the anti-gaming rules exist to prevent. If the weighting changes it should be argued on its
merits, in a separate commit, and not on the day it helps.

## Honest limits

- **n = 4 claims, one encoding, one adjudicator**, who is invested in the project.
- That adjudicator **built the system being encoded**, which cuts both ways: maximally qualified
  to judge, and maximally likely to find an outside view of their own work interesting.
- Mitigating evidence that the answers were not generous: the flashiest claim was marked
  obvious, and only one of the remaining three reached "changes a decision" on its own.
- One encoding does not establish a rate. It establishes that the rate is **not zero**, which
  after 20 prior attempts is the thing that was in doubt.
