# The LoopSpec Score — A Self-Optimization Function

A single number the project can be iterated against: change the ontology, rescore, keep or
revert. This is what makes sustained autonomous work on the ontology safe, because the
specific failure mode of unsupervised ontology design is generating plausible,
well-organized structure indefinitely — nothing in the work itself pushes back. This
pushes back.

---

## The central design problem: every single term is degenerate alone

A naive score would be *"minimize primitive count"* — and it is maximized by one primitive
called `Thing`, which scores perfectly and describes nothing.

Every candidate term has an equivalent degenerate optimum:

| Term optimized alone | Degenerate winner | Blocked by |
|---|---|---|
| Simplicity | one universal `Node` primitive | Expressivity, Determinacy |
| Expressivity | one primitive per domain concept | Simplicity |
| Determinacy | an ontology so rigid only one encoding is legal | Expressivity |
| Usefulness | inflate the surfaced-insight count with trivia | audit requirement, decision-relevance filter |
| Comprehensibility | terse but cryptic notation | Determinacy — cryptic notation makes encoders diverge |
| Coverage | fold every benchmark into one abstract shape | negative-control gate |

**Therefore: the terms are combined by geometric mean, never a weighted sum.** A weighted
sum lets a strong term carry a near-zero one; a geometric mean collapses to zero if any
term does. This is the same reason F1 uses a harmonic rather than arithmetic mean, and it is
the whole reason the function is trustworthy.

And two **binary gates** multiply the result, because they are not tradeable:

- **Negative control** — a sorting algorithm must *fail* to encode. This is the direct
  anti-vacuity guard. Without it, "domain independent" is unfalsifiable and every other
  term can be improved by increasing abstraction.
- **Reduction floor** — the thermostat must reduce mechanically to a classical control
  loop, and a single-locus system to a POMDP.

---

## Definition

```
SCORE = (S · E · D · U · C)^(1/5)  ×  gate_negative  ×  gate_reduction
```

All of `S, E, D, U, C` ∈ [0,1]. Both gates ∈ {0,1}.

### S — Simplicity

```
S = 0.5 · budget_term + 0.3 · depth_term + 0.2 · orphan_term

budget_term  = clamp((24 - core_count) / 8)        # 1.0 at ≤16 primitives, 0 at ≥24
depth_term   = clamp((5 - mean_composition_depth) / 3)
orphan_term  = 1 - (orphan_primitives / core_count)
```

An orphan is a core primitive appearing in fewer than 3 benchmark encodings, or in fewer
than 2 domains. Orphans are the mechanical enforcement of *"every primitive must justify
its existence"* — the rule the charter states and previously had no way to check.

### E — Expressive coverage

Every benchmark declares, in its front matter, the hard features it should break
(`breaks:`). An encoding declares which it represents faithfully.

```
E = weighted_fraction(breaks_handled / breaks_declared)
```

Adversarial benchmarks weight 1.0, seed 0.7, held-out 1.5 — held-out weighs most because it
is the only honest generalization signal.

**A `break` may be legitimately answered "cannot represent, by design."** That counts as
handled *if* the negative-control gate still passes and the exclusion is recorded. Refusing
to represent something is a valid design position; failing to notice you cannot is not.

### D — Determinacy (inter-encoder agreement)

Two encoders, same source material, no shared context. Compare structurally.

```
D = mean over paired encodings of:
      0.5 · jaccard(primitive types used)
    + 0.3 · jaccard(estimand set, fuzzy-matched on name)
    + 0.2 · agreement(loop count and topology)
```

**The most important term.** If the ontology is determinate, independent encoders converge.
If it is merely suggestive, they diverge — and no amount of documentation fixes that,
because divergence means the primitives do not have single meanings.

### U — Usefulness

The term added because every other term can be satisfied by a representation nobody would
choose to write.

Each encoding declares `surfaced:` — things the encoding makes explicit that the source
prose left implicit **and** that are decision-relevant.

```
U = clamp(mean_GENUINE_claims_per_encoding / 2) × audit_coverage
```

**Multiplicative, and only adjudicated-genuine claims count.** Unaudited claims contribute
nothing; rejected claims contribute nothing. Usefulness cannot be self-asserted.

#### The original formula was broken, and only real data revealed it

The first version was additive:

```
U = 0.6 · clamp(mean_surfaced / 3) + 0.4 · (audited / total)      # WRONG
```

That second term rewarded *having been audited* rather than *passing audit*. When round 1's
verdicts arrived — all six claims rejected — this formula would have moved `U` from 0.3 to
0.7. **Submitting failing claims for review would have raised the score.**

Worth recording as a general caution: the flaw was invisible under synthetic reasoning and
appeared immediately on contact with real verdicts. Any term with a coverage or process
component should be checked for whether it rewards the process or the outcome.

**The honest bar, per the startup seed:** an encoding must surface at least one thing the
domain party did not already know, or force one question they were avoiding. Reorganizing
what a good board deck already says scores zero — and in round 1, four of six claims were
adjudicated exactly that: `restatement`.

### Adjudication protocol

`E` and `U` were both self-assessed in round 1, which made both untrustworthy in the same
way: an encoder scoring its own coverage and its own insight.

Both are now adjudicated by a model that wrote neither the encodings, the ontology, nor the
prose, on **anonymised** claims with encoder identity stripped. See
`adjudication/round1_protocol.md`.

Verdicts are deliberately asymmetric — three ways to fail, one way to pass, with instructions
to prefer the harsher verdict under uncertainty:

- surfaced: `genuine` | `restatement` | `unsupported` | `trivial`
- breaks: `handled` | `named_only` | `not_handled`

`named_only` exists because listing something under an "excluded" or "unwritten" key is
naming it, not representing it. In round 1 it caught exactly one over-claim, agreeing with
the author's dissent against the other encoder's self-assessment.

### C — Comprehensibility

```
C = 0.4 · compression_term + 0.3 · undefined_term + 0.3 · flatness_term

compression_term = clamp(1 - encoding_tokens / source_tokens)
undefined_term   = 1 - (terms used but absent from the catalog / total terms)
flatness_term    = clamp((6 - max_nesting_depth) / 4)
```

Compression matters: an encoding longer than the prose it replaces has negative value as an
explanation, whatever else it does.

---

## Partial scores

Terms requiring data that does not yet exist are **excluded from the geometric mean and
reported as unavailable** — never defaulted to 1.0.

This matters more than it looks. Defaulting a missing term to 1.0 would let the score climb
as data goes missing, which is precisely backwards, and is how metric systems quietly stop
measuring anything. The tool prints `PARTIAL (3/5 terms)` and refuses to compare a partial
score against a full one.

---

## Anti-gaming rules

Binding on any process optimizing this function, including autonomous ones:

1. **No term may be edited in the same commit as the ontology it scores.** Changing the
   ruler and the object together makes the measurement meaningless.
2. **The held-out benchmark set stays sealed.** Encoding held-out systems to raise `E`
   destroys the only generalization signal available, permanently and irrecoverably.
3. **A primitive may not be added to fix exactly one benchmark.** The 3-benchmarks /
   2-domains rule is checked mechanically; adding a primitive to raise `E` will lower `S`
   through the orphan term. This is the intended tension.
4. **Score movements under 0.02 are noise.** Do not chase them.
5. **A revision that raises the score while lowering `D` is rejected regardless of total.**
   Determinacy is the load-bearing term — a representation that means different things to
   different readers has failed whatever else it achieves.

---

## Where you are needed

Not mechanizable, and marked as such rather than faked:

- **Auditing `surfaced:` claims.** Whether an encoding genuinely surfaced something a
  founder or clinician did not know requires the founder or clinician. I can generate
  candidates; I cannot validate them. Currently the largest hole in the function.
- **Adjudicating "cannot represent, by design."** Legitimate design position or excuse —
  the distinction is judgement.
- **Weights.** Every coefficient above is a guess. They should be revised once there is
  enough data to see which terms actually move.
- **Whether a merge lost something.** The score cannot see a distinction that mattered
  disappearing into a collapsed primitive.

I can compute `S` and `C` fully, `E` and `D` once encodings exist, and only propose `U`.
