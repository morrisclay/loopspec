# From Representation Mapping to Reasoning Projection

The charter's architecture and the evidence have come apart. This records the shift, what it
buys, and what it costs — because it is a genuine reduction in ambition and should not be
adopted without saying so.

---

## The two frames

**Representation mapping** — the charter, stated in its own words:

> The IR is the canonical truth. Everything else is a projection.

```
world  →  canonical IR  →  { diagram, DSL, YAML, execution }
```

The IR is sovereign. Surfaces are lossless views of it. Determinacy matters because there must
be *one* model. Success is two encoders producing the same IR.

**Reasoning projection** — what the measurements support:

```
world  →  ( description + structure )  →  projections, each for a reasoning task
```

Neither component is the truth. Together they support reasoning better than either alone.
A projection is a **lossy rendering optimised for a particular question**. Success is that
reasoning over the pair beats reasoning over the description alone.

## Why the first frame fails on this project's own evidence

**The IR is not sovereign, because prose carries what it does not.** The blind experiment:
prose 10.7, encoding 12.0, **both 13.3**. If the IR were canonical and prose merely a
projection of it, `both` could not beat `encoding` — there would be nothing extra to add. It
does, so prose is not a view of the IR. It is a second source.

That single result contradicts the architecture diagram at the top of the charter.

**Projections are not lossless, and should not be.** Four primitives have no Flue mapping —
`Consequence`, `PreferenceOrdering`, `Resource`, uncertainty. Under representation-mapping
that is a *failure of the backend*. Under reasoning-projection it is **correct lossiness**: an
execution projection should carry exactly what executes and drop what does not. The Phase 7
"gap" was an artifact of the frame.

**Determinacy is task-relative, not global.** A projection a machine acts on needs high
determinacy. A projection that explains a system to a new hire needs almost none. The current
score computes one global `D` and treats every divergence as debt. Most of it is not.

**The vocabulary cannot close because there is no single target.** Thirteen demanded relation
roles looked like an unfinished ontology. Under the second frame it is expected: different
reasoning tasks want different distinctions, and no closed list serves all of them.

## The honest analogy: notation, not IR

The charter aimed at **LLVM IR and SQL** — a stable intermediate form that outlives its
backends and to which everything compiles.

The evidence supports something closer to **Feynman diagrams**.

Feynman diagrams do not replace the Lagrangian and are not the canonical truth of quantum
field theory. They are a projection that makes one class of reasoning — perturbative expansion
— tractable for a human. They are lossy. They are task-specific. They are enormously valuable,
and nobody confuses them with the physics.

Musical notation, chess algebraic notation, double-entry bookkeeping, circuit diagrams: all
the same shape. None is the object. Each makes a specific kind of reasoning possible that was
not possible before, and each is judged on that and nothing else.

**That is a smaller claim than the charter's, and it may be the true one.**

## What this changes concretely

| Charter position | Revised position |
|---|---|
| The IR is canonical truth | The IR is one component; the description is the other, and it ships |
| Projections are lossless views | Projections are lossy and task-specific — lossiness is the design |
| One global determinacy target | Determinacy per projection: high for execution, low for explanation |
| Closed relation vocabulary | Open, because different tasks want different distinctions |
| Flue gaps are failures | Flue gaps are correct filtering by an execution projection |
| Success = encoders converge | Success = the pair reasons better than the description alone |
| Compile the IR | Compilation is one projection among several |

The measurement follows the frame: for each projection, state its reasoning task and measure
lift against the description-only baseline. That is a per-artifact falsifiable test, and a
better instrument than a five-term geometric mean whose coefficients I invented.

## What it costs — the part not to skip

**The ambition shrinks, and it should be stated plainly.** "A durable, domain-independent IR
that separates specification from execution, as SQL did for data" is a much larger claim than
"a notation that helps people and models reason about adaptive systems." The charter's Final
Goal is written for the first. The evidence supports the second.

**Three real losses:**

1. **Versioning and drift.** Comparing a system to its past self needs something stable.
   Without a canonical form, "has this changed" gets harder, and it was one of the stated
   design principles.
2. **Falsifiability erodes.** "The projection improves reasoning" is soft unless measured every
   time. Representation-mapping was at least brutally checkable — either the encodings match or
   they do not. The new frame demands continuous measurement to stay honest, and measurement
   discipline is the first thing to lapse.
3. **Composition weakens.** A canonical IR composes: two models of subsystems join into one.
   Task-specific projections do not obviously compose at all, and recursive `System` was
   supposed to be load-bearing.

**The risk of over-rotating.** Structure did win the experiment — encoding beat prose on the
mean and on two of three systems. The finding is that structure is a *supplement*, not that it
is optional. A frame that treats the structure as merely one useful lens could licence
abandoning the discipline that produced the validator, the invariants, and the Flue mapping —
all of which caught real defects that no amount of reasoning-over-prose surfaced.

## Where this leaves the project

The honest position is **both frames, scoped**:

- **Representation mapping holds for the executable core** — loops, signals, interventions,
  authority, idempotency. A machine acts on it, so it needs canonical form, determinacy, and
  a closed vocabulary. This is the part the validator already checks and Flue already maps.
- **Reasoning projection holds for everything else** — which is most of it. Open vocabulary,
  prose alongside, task-specific renderings, measured by lift rather than by convergence.

The mistake was applying the first frame to the whole thing because it was the frame with the
better metrics.
