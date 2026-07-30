# Status — Round 2

```
SCORE                     0.000
sub-score (excl. U)       0.763     DIAGNOSTIC ONLY
binding term              U_usefulness = 0.000

S simplicity              0.812
E expressivity            0.896     adjudicated, not self-assessed
D determinacy             0.772     4 vendors, 12 pairs
U usefulness              0.000     every claim rejected by blind adjudication
C comprehensibility       0.560
gate negative_control     pass
gate reduction            pass      independently confirmed by 4 encoders
```

**The score is zero and that is the correct answer.** The geometric mean is designed to
collapse when any term fails, and `U` fails: no encoding has been shown to surface anything a
practitioner did not already have. The sub-score exists only so progress on the other four
terms stays visible, and it is not an achievement.

---

## 1. Determinacy is real, and my own caveat was wrong

Four encoders across four vendors — `claude-opus-5` (anthropic), `gpt-5-codex` (openai),
`gemini-2.5-pro` (google), `deepseek-v3.2` (deepseek) — encoded the same two systems from the
same stripped inputs, independently.

I had cautioned that `D` was inflated because one encoder was the author of the ontology and
the prose. **Measured, that caveat is false:**

| | D | pairs |
|---|---|---|
| author pairs | 0.782 | 6 |
| independent-only pairs | 0.762 | 6 |
| **author effect** | **+0.021** | |

Two points. My encoding is not privileged, and the lowest single pair in the whole set is
`claude-opus-5 vs gemini-2.5-pro` at 0.599 — the author pair, not an independent one. `D` is
a real measurement, not an artifact of self-agreement.

### The thermostat result is strong

Across all four vendors: **estimand agreement 1.00, loop agreement 1.00.** Every encoder
independently identified the same single estimand (`room_comfort`), the same single loop, and
independently set `reduces_to: classical_control_loop`. Only primitive *selection* varied
(0.69–0.87).

The reduction floor from `research/prior_art_gate.md` is therefore confirmed by four
independent parties rather than asserted.

### The hospital result is where the ontology is weak

Pairs range 0.599–0.724. The weak component is **estimand individuation, 0.43–0.67**: whether
five parties assessing discharge readiness constitutes five estimands, or five estimates of
one contested aggregate. I predicted this exact fork in writing before comparing, which
makes it a known ambiguity rather than a latent one — but knowing it does not resolve it.

## 2. Usefulness collapsed under blind adjudication

A model that wrote neither the encodings, the ontology, nor the prose adjudicated all claims
with encoder identity stripped and anonymised labels.

**All six of my surfaced claims were rejected** — four `restatement`, two `unsupported`, zero
`genuine`. `gpt-5-codex` had surfaced none at all. So `U = 0`.

The adjudicator's own summary is the sharpest statement of the problem:

> The encodings mostly relabel facts already explicit in the prose as surfaced insights,
> while their stronger hospital conclusions about causal disagreement and cross-timescale
> ownership are not structurally established.

That is exactly right, and note *which* claims died: the two rated `unsupported` were the two
I was most pleased with. I had asserted them in the `surfaced` field; the encoding structure
does not actually derive them.

### A flaw in my own metric, invisible until real data arrived

The original `U` was additive, with an audit-fraction term meant to punish padding:

```
U = 0.6 · clamp(mean_surfaced / 3) + 0.4 · (audited / total)     # WRONG
```

With all six claims audited and **all six failing**, this formula moves `U` from 0.3 to 0.7.
Submitting failing claims for review would have *raised* the score, because the term rewarded
having been audited rather than passing.

Now multiplicative, counting only adjudicated-`genuine` claims. The general caution is worth
keeping: a term with a process component should always be checked for whether it rewards the
process or the outcome, and synthetic reasoning did not reveal this — contact with verdicts did.

## 3. Expressivity is no longer self-assessed

`E` previously let an encoder score its own coverage, and rewarded optimism. It now uses
adjudicated verdicts, with a third verdict `named_only` for the specific failure of listing
something under an "excluded" key and calling it handled.

Round 1 caught exactly one over-claim: `gpt-5-codex` claimed 5/5 breaks handled on the
hospital including `incomplete_specification`; the adjudicator ruled `named_only`, agreeing
with my dissent. `E` fell 0.950 → 0.896, which is the honest number.

## 4. Two open questions resolved

**Loop identity — ADOPTED:** one loop per distinct (timescale, closing intervention).

Tested against Toyota, which was the stated risk — five timescales that might fragment. It
yields five loops: station cycle, line stoppage, improvement, quality, platform. Those have
different signals, different closing interventions and different authorities, and Toyota
itself treats them as separate named mechanisms — jidoka, kaizen and hoshin kanri are not one
loop in Toyota's own account. The rule reproduces distinctions the organisation already
draws, which is the best available evidence it carves at a real joint.

Corroboration: `gpt-5-codex` independently derived a near-identical rule for round 2
("only a cycle with a returning measured signal and an intervention that changes the source
of the next signal"), correctly excluded practices like A3 and *genchi genbutsu* as non-loops,
and **found a loop I had missed** — kanban pull-replenishment.

**`Party` — NARROWED:** a Party must bear a Consequence. It may also hold estimates, hold
desired conditions and exercise authority, but consequence-bearing is the discriminator.

Round 1 showed my definition was broader than my use of it — codex counted a thermostat
controller as a Party because it exercises authority, and by the written definition codex was
right. Narrowed rather than broadened, because the alternative makes every relay a Party.
Side benefit: this links `Party` to `Consequence` constitutively, justifying `Consequence`
beyond its coverage count.

## 5. Scott and the adjudicator converged independently

`research/external_critiques.md` recorded a prediction from James C. Scott: *metis* — local
unwritten practical knowledge — is load-bearing and would be what the representation could
not hold.

The adjudicator, which never saw that document and worked only from encodings, reported
unprompted:

> The ontology appears to lack a way to represent load-bearing tacit institutional rules,
> contextual exceptions, and informal credibility, forcing both hospital encodings to relegate
> them to excluded variables rather than make them behaviorally operative.

Two fully independent routes to the same gap is the strongest evidence available that the
philosophical critique was substantive rather than decorative.

Acted on with an `informal_influence` field on `Party` — recording *that* influence exceeds
declared authority and in which direction, without codifying its content. Scott is right that
codifying metis destroys it; recording the discrepancy is enough to make it operative in a
policy. A field, not a primitive: no budget cost.

## 6. The biggest structural finding: the ontology had primitives but no shape

Four encoders produced four incompatible document structures — lowercase plurals, PascalCase
primitive names as keys, everything nested under one `System`.

`D` was measurable only because the encoding task happened to pin the top-level keys. Below
that, nothing was constrained, and the Semantic Validator could not locate sections to check
referential integrity or loop closure across encoders.

`schema/uras.graph.md` now defines the canonical shape: a **flat typed graph** of `nodes` plus
`edges` with a closed `rel` vocabulary, replacing nesting. Flat wins twice — more comparable
and more readable, and nesting was already the cause of the two worst `C` results (depth 5–6
against a target of 4).

**Recorded in advance:** normalising shape will raise `D` by removing divergence that was
never conceptual. That rise is a measurement artifact and must be reported as such. The real
ambiguities — estimand individuation, whether `Estimator` is needed when a party already holds
an estimate — are untouched by it.

## 7. The validator earns its place

`tools/validate.py` implements 11 graph-level invariants that JSON Schema cannot express:
loop closure, referential integrity, estimator idempotency, algebraic-loop detection,
scalarization prohibition, depth ceiling, reserved-word keys.

It caught a real defect in third-party output it had never seen: `gpt-5-codex` used `on:` as a
key in three places, which YAML 1.1 parses as boolean `True`. It also would have caught, in
under a second, the same list-then-mapping-key error I made three times by hand.

---

## Where a human is still required

**Auditing whether an encoding is useful to a practitioner.** The adjudicator can catch
restatement — and did, decisively — but it cannot tell whether a claim would tell a real
clinician or founder something new. `U = 0` currently means "no claim survived model
adjudication," which is a necessary condition and not the real bar.

Everything else on the round-1 list is now closed.

## Next, in order of leverage

1. **Re-encode in the canonical shape** and separate the artifact rise in `D` from real
   convergence.
2. **Resolve estimand individuation** — the dominant remaining conceptual divergence.
3. **Try to produce one genuinely `genuine` surfaced claim.** Until one exists, `U = 0` and
   the total score is zero regardless of the other four terms. This is the whole project's
   binding constraint.
4. Flatten encodings to lift `C` from 0.560.
