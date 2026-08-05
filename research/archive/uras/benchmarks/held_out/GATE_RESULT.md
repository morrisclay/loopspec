# Held-Out Gate — Result

The one-shot generalization test. Four systems sealed since the corpus was designed,
described by a model with **no sight of the ontology**, then encoded against the frozen
19-primitive catalog by two independent encoders.

**Verdict: the primitive set generalised. The relation vocabulary did not.**

---

## What was measured

`new_primitives_needed` across 8 encodings (4 systems × 2 encoders):

| System | gpt-5-codex | deepseek-v3.2 |
|---|---|---|
| ecosystem | 1 proposed — `Report` | none |
| factory | 1 proposed — `ProcessCoupling` | none |
| family | 1 proposed — `ResourceFlow` | none |
| llm_agent_system | 1 proposed — `SemanticArtifact` | none |

**Invented node kinds outside the catalog: zero.** Across all 8 encodings, no encoder
silently stretched a primitive or introduced an uncatalogued kind. Every gap was reported
through the declared channel, which is what the protocol asked for.

## The proposals were relation gaps, not primitive gaps

This is the finding, and the encoder's own reasoning is what establishes it. Each proposal
had to state which existing primitive it tried first and why that failed:

> *family:* "Resource represents a depletable stock, while consumes represents only
> depletion... **no closed relation means replenishes or produces.**"
>
> *llm_agent_system:* "System contains components but **the closed relations cannot express
> production, consumption**..."
>
> *ecosystem:* "**Signal** is what is actually measured and **has no reporting-party
> relation.**"

Three of four proposals diagnose themselves as missing *edges*. The node vocabulary held; the
edge vocabulary was under-specified. The canonical shape declared twelve relations and all
twelve are structural — none could express **assertion**, **replenishment**, or
**production**.

### Relations added: 12 → 15

| rel | Demanded by | Why |
|---|---|---|
| `asserts` | ecosystem | A reported quantity is not a measured one |
| `replenishes` | family | Stocks could only deplete, never refill |
| `produces` | llm_agent_system | A produced artifact is not an observed signal |

**`asserts` is the most consequential and it was not confined to the system that demanded
it.** Reported fish landings are assertions by parties under economic pressure that may
knowingly differ from the catch. The same structure runs through the existing corpus and was
invisible until now: how arrival time gets recorded against a four-hour target, why Toyota
needs *genchi genbutsu* as doctrine at all, a founder's pipeline number, a competitor's
selectively published result.

The representation had no way to distinguish **a measurement from a claim**. For
institutional systems that is close to the central fact, and four prior benchmarks had
gestured at it without any of them forcing it into the schema.

### Rejected: `ProcessCoupling`

"A contingent transfer of difficulty between interventions." Weakest of the four — this is
expressible as a conditional `Constraint` or an edge between interventions, and promoting it
would spend budget on something one system needed once. Recorded, not adopted.

## The score fell, which is the point

```
before held-out    S 0.802  E 0.938  D 0.739  U 0.055  C 0.601  ->  0.449
with held-out      S 0.802  E 0.856  D 0.751  U 0.042  C 0.610  ->  0.422
```

`E` fell because held-out benchmarks weigh 1.5× and these systems broke things the corpus had
not. `U` fell because eight new encodings diluted the genuine-claim mean. **A generalization
test that did not lower the score would not have been a test.**

## Honest limits of this result

- **Only two encoders produced output.** Gemini and Kimi did not return usable encodings on
  this run, so the split is 1-versus-1 rather than a majority. A single dissenting encoder
  finding a gap in every system is a weaker signal than three would be.
- **The split itself is unexplained.** One encoder found a gap in all four systems and the
  other in none. That is a large difference in disposition, and it is not obvious whether
  codex is more perceptive or simply more willing to propose.
- **Three encodings failed validation** on a missing `uses` key. Their gap proposals still
  count, but the encodings need repair before they contribute to `D`.
- **The set is now spent.** It cannot be re-run. Any future generalization claim needs new
  sealed systems.

## What this means for building

**The primitive set is stable enough to build on.** Nineteen primitives absorbed four systems
they were never designed against, with zero silent stretching, and one encoder needed nothing
at all.

**The relation vocabulary just moved, so it is not yet frozen.** A diagram notation and a
surface syntax are both *about* nodes and relations. Committing a compiler to a vocabulary
that changed today would be premature.

Recommended sequence:

1. **Phase 6 visual grammar — proceed.** It is a specification, it is cheap, and drawing the
   fifteen relations will itself stress whether the three new ones are right.
2. **One confirmation round on the new relations** — re-encode two existing adversarial
   systems and check that `asserts`, `replenishes` and `produces` get used where expected and
   that nothing further is demanded.
3. **Compiler after that**, not before.
