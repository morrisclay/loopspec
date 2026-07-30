# Status

```
SCORE                     0.000
sub-score (excl. U)       0.748     DIAGNOSTIC ONLY
binding term              U_usefulness = 0.000

S simplicity              0.812
E expressivity            0.821     adjudicated over 47 claims
D determinacy             0.805     5 vendors, 20 pairs
U usefulness              0.000     11 of 11 claims rejected
C comprehensibility       0.582
gate negative_control     pass
gate reduction            pass      independently confirmed by 5 encoders
```

**The score is zero and that is the correct answer.** The geometric mean is built to collapse
when a term fails. `U` fails: no encoding, by any model, has been shown to surface anything a
practitioner did not already have. The sub-score exists only to keep gradient visible on the
other four terms and is not an achievement.

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

## 2. Usefulness: 11 of 11 rejected, by four different models

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
result reads as analysis. That is the honest description of where URAS currently stands, and
no amount of work on the other four terms addresses it.

**Adjudication is reproducible:** re-run on the six round-1 claims, it returned **6/6
identical verdicts**.

## 3. Expressivity fell as adjudication widened — the honest direction

`E` went 0.950 (self-assessed) → 0.896 → **0.821** across 47 adjudicated claims: 41 `handled`,
5 `named_only`, 1 `not_handled`.

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

**One thing, and it is not a tooling problem.** Until a single surfaced claim survives
adjudication, `U = 0` and the score is zero regardless of the other four terms. Eleven attempts
by four models produced none, and the diagnosis is that the encodings are typed paraphrase.

This is the correct binding constraint for the project to have. It says: the representation is
internally consistent (S), broadly expressive (E), determinate across five model families (D),
degrades to classical control (gate), and **has not yet been shown to tell anyone anything**.

Two paths, and they are not equivalent:

1. **Derive rather than assert.** A claim should fall out of the graph structure — for
   instance, computing which parties hold estimates of an estimand they have no authority to
   act on. That is a query over the encoding, not a sentence written into a `surfaced` field.
   Every rejected claim so far was asserted prose.
2. **A real practitioner.** Model adjudication catches restatement decisively and reproducibly,
   but cannot tell whether something would be news to an actual clinician or founder. `U = 0`
   currently means "no claim survived model adjudication" — a necessary condition, not the bar.

Path 1 is available autonomously and is the honest next step. Path 2 needs a human, and it is
the only item on the round-1 list still open.
