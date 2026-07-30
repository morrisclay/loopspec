# Third-Order Regulation

```
1. First-order   — How does a system regulate itself?
2. Second-order  — How does the observer participate in regulation?
3. Third-order   — How does an intelligent system continuously improve its ONTOLOGY
                   of the world in order to intervene more effectively?
```

The first two are established: Wiener and Ashby; then von Foerster, Maturana, Varela, Pask.
The third is a synthesis rather than a school, and this document treats it as the project's
actual claim.

---

## Why this is the right name for what was already being built

It names the thing `research/prior_art_gate.md` identified as the sole genuine expressivity
gap and then never built.

That document argued URAS differs from every POMDP variant — Dec-POMDP, I-POMDP, factored,
hierarchical — because those formalisms **fix `S` at specification time**. Real systems
discover variables nobody had conceived. That was the differentiator on which the project was
allowed to proceed, and it has sat unimplemented ever since.

**"Improving its ontology in order to intervene more effectively" is that gap, stated as a
capability rather than as an absence.**

Several loose findings snap into place under it:

| Existing artifact | Under third-order framing |
|---|---|
| `Revision` — schema change, not parameter change | the third-order operation itself |
| `excluded_variables` — the declared frontier | the candidate set for ontology expansion |
| The startup discovering "proving fault" was outside its vocabulary | retroduction, and the canonical example |
| `Calibration` — a loop that closes on the estimator | second-order, and the rung below |
| Bhaskar's Real domain, missing from the catalog | what an improving ontology is improving *toward* |

`Calibration` sitting one rung below is the useful structural point. Calibration asks *is my
estimator well-tuned*. Third-order asks *are my categories the right categories at all* — and
those are different operations that the catalog currently blurs.

## What is genuinely new, stated conservatively

The components are all borrowed: retroduction from Bhaskar, intervention-as-epistemic-operator
from Pearl, uncertainty-reducing action from active inference, the closed loop from
cybernetics, ontology revision from AI.

**What is not borrowed is the conjunction plus an executable target.** Bhaskar describes how
science discovers mechanisms but specifies no machinery. Cybernetics specifies machinery but
assumes the categories are given. Active inference formalises uncertainty reduction within a
fixed generative model. Pearl formalises intervention within a fixed causal graph.

Third-order regulation is the claim that **the graph itself is the thing under revision, and
the revision is driven by whether interventions work.** That conjunction is the contribution,
and it is a smaller and more defensible claim than "a universal representation."

## The caution about the label

"Third-order cybernetics" has scattered prior use, usually meaning observing systems of
observing systems — a recursion of second-order rather than a new operation. Adopting the
number claims a place in a lineage and invites the objection that this is second-order
restated.

The defence has to be that the *operation* differs. Second-order says the observer is inside
the system and cannot be eliminated. Third-order says the observer's **categories** are inside
the system, are wrong in identifiable ways, and are revised by acting. That is a different
claim, and it should be argued rather than assumed by numbering.

## The test this implies, which has never been run

This is the sharpest consequence and it is uncomfortable.

The claim is ontology improvement **in order to intervene more effectively**. Everything
measured in this repository so far is upstream of that:

- `S`, `E`, `D`, `C` measure properties of the ontology
- `U` measures whether an encoding surfaces something
- the reasoning experiment measures answer quality on hypothetical questions

**Not one measurement touches whether an intervention worked.** The entire justification is
effectiveness, and effectiveness has never been an outcome variable. That is a hole at the
centre of the claim, not at its edge.

A real test needs:

1. A system whose ontology is revised over time — recorded, versioned, dated.
2. Interventions chosen under each ontology version.
3. Outcomes of those interventions.
4. The question: **did interventions chosen under later ontologies do better?**

Sourcing and portfolio work already has the shape — theses, decisions, and an `/outcome`
record of what actually happened. If ontology versions were stamped against decisions, the
third-order claim becomes measurable on data that already exists rather than on a new
benchmark.

Until then the claim is philosophically coherent and empirically untested, and should be
described that way.

## The available demonstration, and its limits

This project has been running a third-order loop on itself, manually, throughout:

- an ontology of adaptive systems was proposed
- systems were encoded under it, and the encodings failed in specific ways
- the ontology was revised — `Evidence` retired as a phantom, `Calibration` restored, `Party`
  narrowed to consequence-bearing, three relations added and then found to be orphans
- each revision was driven by a measurement rather than by taste

That is ontology improvement driven by whether the ontology *worked*. It is the best available
demonstration, and it is weak in exactly the way the framing predicts: **"worked" has meant
"encoded cleanly" and "reasoned well", never "intervened effectively"** — because this
particular system has no interventions in the world to be right or wrong about.

The venture case is the one where all three rungs close: a thesis about what makes ventures
succeed is an ontology, an investment is an intervention, and an outcome is feedback on both
the decision and the categories that produced it.
