# Projections and the LLM encoder

Recorded 2026-07-30, from the book-coupling work.

Two questions: can a converged URAS generate diagrams, and can an LLM turn ordinary material
into URAS encodings from a system prompt plus the catalog? Yes to both. The second is the
interesting one, because **it is not primarily a product feature — it is the missing
instrument for the project's most important success criterion.**

---

## 1. Diagrams are already the architecture, not an add-on

`PROJECT_HANDOFF.md` states it: *"The IR is the canonical truth. Everything else is a
projection."* Diagram, DSL, JSON and YAML are four renderings of one typed graph, and Phase 6
is the visual grammar. Nothing new is required for this to be true — it is what the design
already commits to.

The non-obvious part is what makes generated diagrams worth more than whiteboard ones:
**because the IR carries invariants, the renderer can draw what is broken.** The Phase 5
invariant list already includes *every feedback loop must close*, *every referenced observer,
sensor and estimand must exist*, *no estimator may depend on its own output without a Delay*.

So a dangling reference is not a lint warning in a terminal — it is a node on the canvas with
nothing running into it. An estimator with no delay on its own output is a visible tight
cycle. An unclosed loop is an arrow ending in space. **The diagram becomes a diagnostic
surface rather than documentation**, which is the difference between a drawing people make
once and one they keep open.

This also gives the visual grammar a hard design constraint that Phase 6 otherwise lacks:
every invariant in the validator must have a visual failure mode. If it cannot be drawn
wrong, it probably should not be an invariant.

---

## 2. The LLM encoder is the instrument for `D`

`ontology/score.md` is unambiguous about which term matters:

> **D — Determinacy (inter-encoder agreement). The most important term.** If the ontology is
> determinate, independent encoders converge. If it is merely suggestive, they diverge — and
> no amount of documentation fixes that, because divergence means the primitives do not have
> single meanings.

And `PROJECT_HANDOFF.md` calls inter-encoder agreement *"the only proposed measure that tests
whether the representation means anything."*

That term currently has no practical instrument. It requires two independent encoders given
the same source with no shared context — which, done with humans, is slow, expensive, and
yields n=2. **An LLM encoder given the catalog as context produces n=20 in an afternoon**, and
`score.md` already specifies exactly how to compare them: Jaccard on primitive types, fuzzy
Jaccard on the estimand set, agreement on loop count and topology.

This is the single cheapest available improvement to the project's measurement, and it argues
for building a thin encoder **now**, during the 2–4 loop, rather than after convergence. That
is not premature implementation — the charter's prohibition is on building *execution* before
the primitives settle. An encoder is instrumentation for the convergence test itself. In the
book's own vocabulary it is a structural intervention that lowers the cost of the evidence the
project most needs.

### Three traps, each with a specific guard

**Trap one: same-model reruns flatter `D`.** t-minus P5, measured: *"cross-provider beats
same-model reruns (cuts bias, not just variance)"* — independent blind spots are the point.
Two runs of one model share a prior and will agree for reasons that have nothing to do with
the ontology being determinate.
*Guard: `D` is only computed across providers. A same-model figure is reported separately and
never enters the score.*

**Trap two — and this is the serious one: a capable model can paper over a vague ontology.**
A strong model given a suggestive catalog will still produce plausible, mutually consistent
encodings, because its own competence supplies the determinacy the ontology lacks. High
agreement from a frontier model is therefore ambiguous evidence, and it is ambiguous in the
flattering direction.

*Guard — the discriminating experiment: sweep model capability and watch the gradient.* A
determinate ontology should be encodable by a weak model, because the primitives do the work.
A suggestive one needs a strong model to fill gaps, so agreement will fall off sharply as
capability drops. **The slope of `D` against model capability is a better measure of
determinacy than `D` itself.** A flat slope is the result to want; a steep one means the model
is carrying the ontology.

This should be run before any `D` figure is quoted as evidence of convergence.

**Trap three: the encoder can quietly become the specification.** If encoding behaviour is
tuned by editing the system prompt, the prompt accumulates the disambiguation that should have
been in the catalog — and `D` rises while the ontology stays vague.
*Guard: the encoder's system prompt is generated from `primitives.yaml` and may contain no
disambiguation absent from the catalog. Any clarification needed to make encoding work is a
finding about the catalog and belongs there. This is the same rule as "no term may be edited
in the same commit as the ontology it scores."*

---

## 3. The valuable direction is backwards, and corrections are data

The obvious product is *human writes intent → LLM emits DSL*. The more valuable one is the
reverse: **read the material an organisation already has — board decks, metrics, Slack,
incident reports, meeting notes — and propose the loop. The human's job becomes correction.**

Correction is far easier than composition, and it produces something composition does not:
**every correction is evidence about where the ontology is unclear.** A human moving something
from `Signal` to `Estimand`, or splitting one `DesiredCondition` into two held by different
parties, is a labelled instance of a primitive boundary being ambiguous. Aggregate those and
you have a map of the catalog's soft spots — generated by use, at no extra cost, from exactly
the population the ontology claims to serve.

That closes a loop on the ontology itself, which is the thing the project keeps saying it
wants and has no mechanism for.

---

## 4. The design constraint the book imposes

The book teaches a founder to notice that their signal is not the thing they care about — that
is its central lesson. **A tool that fills in `want`, `observe` and `estimate` for them does
the thinking the book exists to teach**, and the reader ends with a correct-looking loop and
none of the understanding.

So the interaction is Socratic, not autocomplete:

> *You asked for runway over 18 months. I can find cash balance and burn rate in your
> material. Neither of those is runway — runway is what you get by assuming burn stays flat,
> and your burn moved 40% in the last two quarters. What would you actually want to know?*

**The rule: the tool makes gaps visible; it does not fill them.** It should be better at
finding what is missing, dangling, unowned, unscored and unobservable than at producing a
complete-looking encoding. A tool that returns a tidy loop with no open questions has failed,
in the same way an encoding that surfaces nothing scores zero on `U`.

This also happens to be the honest position given trap two: a system built to *interrogate*
cannot substitute its own competence for the ontology's, because its output is a list of
questions rather than an answer.

---

## Consequences

1. **Build a thin encoder during the 2–4 loop**, not after. It is the instrument for `D`.
2. **Run the capability sweep** before quoting `D` as evidence of convergence. The slope
   matters more than the value.
3. **Compute `D` cross-provider only.**
4. **Generate the encoder's system prompt from `primitives.yaml`** — no disambiguation may
   live in the prompt.
5. **Log human corrections as ontology evidence**; they are the cheapest signal available
   about primitive boundaries.
6. **Every validator invariant needs a visual failure mode** — a Phase 6 design constraint
   falling out of Phase 5.
7. **The book's chapter 3 becomes an hour instead of a week** if drafting is assisted, which
   is what makes its spiral structure viable rather than aspirational — provided the tool
   interrogates rather than completes.
