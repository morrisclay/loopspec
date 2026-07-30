# Status

```
SCORE                     0.534     first non-zero score
binding term              U_usefulness = 0.129

S simplicity              0.812
E expressivity            0.924     adjudicated, not self-assessed
D determinacy             0.790     5 vendors, 20 pairs
U usefulness              0.129     2 genuine claims out of 20 attempts
C comprehensibility       0.569
gate negative_control     pass
gate reduction            pass      independently confirmed by 5 encoders
```

**The score was 0.000 for most of this work and is now 0.534.** The move came from exactly one
thing: two claims survived blind adjudication, so `U` left zero and stopped collapsing the
geometric mean. `U` remains the binding term by a wide margin.

Cumulative claim record: **20 attempts, 2 genuine (10%).** All 11 hand-asserted claims were
rejected. Of 9 computed by graph query, 2 survived.

---

## 1. Determinacy is real. My caveat about it was wrong.

Five encoders across five vendors, same stripped inputs, independently, no shared context:
`claude-opus-5` (anthropic), `gpt-5-codex` (openai), `gemini-2.5-pro` (google),
`deepseek-v3.2` (deepseek), `kimi-k2-thinking` (moonshot). **D = 0.805 over 20 pairs.**

I had warned `D` was inflated by including the ontology's own author. Measured:

| | D | pairs |
|---|---|---|
| author pairs | 0.790 | 8 |
| independent-only pairs | 0.789 | 12 |
| **author effect** | **+0.001** | |

One thousandth. And the single lowest pair in the whole set is an *author* pair
(`claude vs gemini`, 0.599). The caveat is refuted by measurement, not argued away.

**Thermostat, across all five vendors: estimand agreement 1.00, loop agreement 1.00**, every
one independently setting `reduces_to: classical_control_loop`. The reduction floor from
`research/prior_art_gate.md` is now confirmed by five independent parties rather than asserted.

**Hospital is where the ontology is weak**: pairs 0.599–0.724, with estimand individuation
the weak component at 0.43–0.67. Whether five parties assessing discharge readiness is five
estimands or five estimates of one contested aggregate. I wrote that fork down before
comparing, so it is a known ambiguity — knowing it has not resolved it.

## 2. Every hand-ASSERTED claim was rejected — 11 of 11, four different models

Blind adjudication — a model that wrote neither the encodings, the ontology, nor the prose,
on anonymised claims with encoder identity stripped, with three ways to fail and one to pass.

| verdict | count |
|---|---|
| restatement | 8 |
| unsupported | 3 |
| **genuine** | **0** |

**This is a much stronger finding than round 1, and it points somewhere different.** In round
1 only my own six claims had been judged, and the obvious reading was author privilege — I
knew what the prose was written to illustrate. Round 2 adds claims from Gemini and DeepSeek,
which had no such privilege. They failed identically.

So it is not that one encoder was bad at finding insight. **No encoder could.** The
adjudicator's diagnosis is the sharpest sentence produced in this project:

> The encodings repeatedly mistake typed paraphrase or an excluded-variable list for
> explanatory structure, so their declared handling and surfaced insights substantially
> overstate what they actually establish.

*Typed paraphrase.* The encodings retype the prose with primitive labels attached and the
result reads as analysis. That was the honest description of hand-asserted claims, and no
amount of work on the other four terms addressed it — which is what motivated the derivation
experiment in section 8, the only thing that has since moved `U` off zero.

**Adjudication is reproducible:** re-run on the six round-1 claims, it returned **6/6
identical verdicts**.

## 3. Expressivity fell as adjudication widened — the honest direction

`E` went 0.950 when self-assessed, then 0.896 and 0.821 as adjudication widened across 47
claims (41 `handled`, 5 `named_only`, 1 `not_handled`), and now reads **0.924** with the
canonical encodings included.

A term that *falls* as measurement improves is behaving correctly. `named_only` — listing
something under an "excluded" key and calling it handled — caught 5 over-claims, against the
1 found when only 15 claims were judged.

## 4. Two open questions closed, one gap closed at zero cost

**Loop identity — ADOPTED:** one loop per distinct (timescale, closing intervention). Tested
against Toyota, the stated fragmentation risk: it yields five loops matching Toyota's own
separately-named mechanisms, so it reproduces distinctions the organisation already draws.
`gpt-5-codex` independently derived a near-identical rule, correctly excluded A3 and *genchi
genbutsu* as practices rather than loops, and **found a loop I had missed** — kanban
pull-replenishment.

**`Party` — NARROWED:** must bear a Consequence. Codex was right that the written definition
admitted a thermostat controller; narrowed rather than broadened, since the alternative makes
every relay a Party. This links `Party` to `Consequence` constitutively.

**The gap that narrowing created, closed without spending budget.** Authority-holding
mechanisms had nowhere to live. My first attempt invented a `Component` kind; the validator
flagged it as uncatalogued within seconds. A controller *is* a sub-system — so it is a
`System` with `part_of`, using recursion the catalog already had. 19/20 core, unchanged.

## 5. The ontology had primitives but no shape

Five encoders produced five incompatible document structures — lowercase plurals, PascalCase
primitive names as keys, everything nested under one `System`. `D` was measurable only because
the encoding task happened to pin the top-level keys; below that nothing was constrained, and
the validator could not locate sections to check.

`schema/uras.graph.md` now defines the canonical shape: a **flat typed graph** of `nodes` plus
`edges` over a closed `rel` vocabulary. Implemented once, for the thermostat, to test whether
the spec was real rather than aspirational — it validates clean at **depth 4** against the
nested version's 5.

Writing it produced two findings the nested form had hidden: the `Component` gap above, and
that my nested encoding had **silently omitted the householder's consequence entirely**. Flat
made both visible in one line.

**Recorded in advance:** normalising shape will raise `D` by removing divergence that was
never conceptual. That rise will be a measurement artifact, not progress, and must be reported
as such — exactly as the coverage-measurement fix was.

## 6. Two independent routes to the same gap, twice

`research/external_critiques.md` recorded Scott's prediction that *metis* — local unwritten
practical knowledge — is load-bearing and would be what the representation could not hold.

Both adjudication rounds, which never saw that document, reported it unprompted. Round 2:

> The ontology lacks a way to represent load-bearing unwritten knowledge and its causal
> influence on policy, and it also lacks an artifact/comprehensibility primitive for
> expressing why a bounded representation such as A3 works.

Acted on with an `informal_influence` field on `Party` — recording *that* influence exceeds
declared authority and in which direction, without codifying content, since Scott is right
that codifying metis destroys it.

The second half of that finding is new and lands on my own earliest suggestion: the ontology
cannot represent *representations*, so it cannot say why A3 works. That is the dogfooding gap —
URAS cannot yet describe URAS — arrived at independently from the encodings.

## 7. The validator earns its place

`tools/validate.py` implements graph-level invariants JSON Schema cannot express: loop closure,
referential integrity, closed edge vocabulary, estimator idempotency, algebraic-loop detection,
Party-bears-Consequence, scalarization prohibition, depth ceiling, reserved-word keys.

It caught a real defect in third-party output it had never seen — `gpt-5-codex` used `on:` as a
key in three places, which YAML 1.1 parses as boolean `True` — and it caught my invented
`Component` kind immediately. It would have caught, in under a second, the same
list-then-mapping-key error I made three times by hand.

---

## What is actually blocking

**One thing, and it is not a tooling problem.** `U` is now 0.129 rather than 0, so the score is
no longer zero — but at 20 attempts and 2 genuine, usefulness remains the binding term by a
wide margin and every other term is more than six times higher.

This is the correct binding constraint for the project to have. It says: the representation is
internally consistent (S), broadly expressive (E), determinate across five model families (D),
degrades to classical control (gate), and **has not yet been shown to tell anyone anything**.

Path 1 — derive rather than assert — has now been run, and section 8 reports it: it works, at
22% against 0%, and two thirds of its output was still rejected. More and better queries are
available autonomously and are the obvious next increment.

**Path 2 still needs a human, and it is the only item from round 1 still open.** Model
adjudication catches restatement decisively and reproducibly — 6/6 on re-run — but cannot tell
whether a claim would be news to an actual clinician or founder. `U = 0.129` means "two claims
survived *model* adjudication," which is a necessary condition and not the real bar. The two
survivors are both **absences** — an unmeasured estimand and a missing estimator — and whether
those matter is exactly the kind of question a ward sister answers in one sentence and a model
cannot answer at all.

---

## 8. Derivation vs assertion — the decisive experiment

After 11 of 11 hand-asserted claims were rejected as "typed paraphrase," `tools/derive.py`
tested the alternative: compute claims by query over the graph instead of writing them into a
field. Six queries, each required to combine at least two independent parts of the graph.

**Result: 2 of 9 derived claims adjudicated `genuine`, against 0 of 11 asserted.** The two:

- **`patient_preference` has no signal measuring it** — while appearing in the preference
  ordering and marked `often-unelicited`. The adjudicator: *"exposing a decision-relevant
  evidential gap not stated plainly in the prose."*
- **`e_logistics` has no declared estimator** — a discharge-*blocking* assessment whose
  production is unspecified. *"Not stated in the prose."*

Both are absences. Neither is in the source text. Both were found by a program, not written by
me, and both bear on a real decision — whether to elicit patient preference at all, and who is
accountable for a judgement that can block a discharge.

### The adjudicator disagrees with my reading of this, and it is worth recording

Asked directly whether derivation beats assertion, it said **no**:

> Computing claims from graph structure does not produce better claims than writing them by
> hand: it makes the triggering pattern auditable, but most outputs still restate the prose,
> lack decision relevance, or overinterpret missing and unrelated edges.

The hit rate says otherwise — 22% versus 0%. Both are true and neither should be suppressed:
derivation produced the only genuine claims this project has, *and* two thirds of its output
was still bad. The honest summary is that derivation raises the ceiling and does not raise the
floor.

### It found a real bug class in my own queries

Five of nine were rejected `unsupported`, and the adjudicator identified why with precision:
they **inferred causal and capability conclusions from missing edges.**

`delayed_harm_to_unauthorised_party` claimed a delay "falls on" a party purely because that
party bore an unmeasured consequence — with no edge relating the intervention or its delay to
that consequence. *Co-occurrence in a graph is not a relation in a graph.* That query is now
withdrawn as a claim generator and retained only as a **question generator**, which is what it
always was.

`consequence_without_authority` claimed exposure was "structurally unhedgeable." The graph
supports only that no `authorizes` edge is recorded. Weakened to exactly that, with an explicit
`does_not_claim` field.

`unowned_cross_timescale_coupling` treated `closes` and `revises` as the same kind of contact
with a shared object. They are unlike roles; the query now requires the same relation type.

After the fixes the hospital yields 5 claims and 2 explicit questions instead of 8 claims. Both
genuine claims survive.

### Derivation is sensitive to the encoding, which assertion never was

The thermostat query initially reported the householder as holding zero authority. That was an
**encoding bug** — `set_dial` had never been encoded as an intervention. Adding it made the
claim disappear.

This is the property that makes derivation worth keeping regardless of the hit rate: a derived
claim is wrong for a *locatable* reason. An asserted claim is just wrong.
