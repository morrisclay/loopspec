# Coupling to *Applied Cybernetics* (the book)

Recorded 2026-07-30. Decision by the project owner.

> **The book is tightly coupled to URAS. It publishes only if URAS converges.**

This is not a note about marketing. It changes what URAS is accountable for, and it adds one
failure mode that must be guarded against explicitly.

---

## What the coupling does *not* do

The obvious objection to putting URAS notation in a book is that publication removes the
project's ability to fail: readers depend on the notation, and the kill criteria in
`research/archive/uras/PROJECT_HANDOFF.md` become unexecutable because retreat has been made expensive.

Gating the book on convergence removes that objection by inverting the dependency. **URAS's
kill criteria become the book's kill criteria.** If the Phase 1 residue collapses, if the 2–4
loop cannot converge under the twenty-primitive budget, if inter-encoder agreement stays low,
or if the held-out set demands new core primitives — there is no book. URAS keeps its freedom
to die; the manuscript simply does not ship.

## The failure mode this creates, and the rule against it

A book creates schedule pressure, and schedule pressure will push toward **declaring
convergence early**. That is the same class of error the archived URAS score contract already guards
against with *"no term may be edited in the same commit as the ontology it scores."*

**Rule, adopted now while it is cheap:**

> The convergence declaration is made against the criteria in `research/archive/uras/PROJECT_HANDOFF.md` alone —
> three consecutive adversarial benchmarks with no new primitive required and no unresolved
> contradiction — and no book milestone, deadline or draft may be cited in the commit that
> declares it. If the two are ever argued together in one place, the declaration is void.

Write the convergence commit as though the book did not exist. That is the whole rule.

## What the coupling buys URAS

It is not one-directional. The book is a genuine test of a success criterion that had no test:

> *"experts from multiple domains recognize their systems"* — and, in `score.md`, `C` for
> comprehensibility, currently computable only as compression and undefined-term ratios.

Founders and operators reading encodings of their own companies is a **real usability trial
against a non-expert population**. If they cannot read it, `C` is failing in a way the
formula cannot currently detect. That is a better instrument than the archived URAS score tool
today, and it arrives free.

---

## What the book needs, and from which phase

| Book need | URAS phase | Status |
|---|---|---|
| Stable surface notation for worked examples | Phase 5 (IR) / Phase 6 (grammar) | Not started. **The critical path.** |
| Uncertainty representation — every estimate in the book carries one | Phase 5 | The largest known gap; see `flue_notes.md` |
| Executable examples in Flue | Phase 7 | Not started; API now verified, see below |
| A worked venture/company encoding | Phase 8 | Not started |

**The book cannot have stable notation before Phase 5.** Until then it uses a clearly-marked
provisional notation, generated from `ontology/primitives.yaml` rather than hand-written, so
the two cannot drift silently. Recommend a mechanical check in `tools/` that fails when the
book's notation references a primitive the catalog no longer contains — the same discipline
`score.py` already applies to the coverage matrix.

---

## Candidate finding from the book work: uncertainty on `DesiredCondition`

The owner's first-draft notation for a goal included:

```yaml
confidence_in_target: 0.7
```

**This is not expressible in the v0 catalog.** Uncertainty attaches to `Estimate` — a party's
assessment of an estimand. There is no representation for *"how confident is the holder that
this is the right desired condition"*, which is a different quantity: not uncertainty about
the world, but uncertainty about what one wants.

Why it may be real rather than a modelling slip:

- It is the natural companion to `Revision`. A desired condition held at 0.7 and one held at
  0.99 should have different revision policies, and the catalog currently has no way to say
  so. `Revision.regime` records *how* a goal changes, never *how provisional it was*.
- The reference set has instances. Hop Aero steered by a USAF contract and Lodestar by
  ESA/MoD grants both hold targets set elsewhere and revisable by parties outside the
  boundary — confidence in the target is precisely what is low there, and it is not
  representable.
- It may explain the startup seed's refuted-versus-abandoned distinction from the other end: a
  goal abandoned rather than refuted may be one that was never held with high confidence.

Why it may reduce, and should be attacked before adoption:

- It might be an `Estimate` about a meta-estimand ("is this the right target"), in which case
  it is already expressible and needs only a convention, not a field.
- It might belong to `PreferenceOrdering` as ordinal instability rather than to
  `DesiredCondition` as a scalar.
- One instance from a book sketch is not three benchmarks across two domains. **It does not
  enter the catalog on this evidence.** Logged as a candidate for the 2–4 loop to test
  against `democracy` and `military_command`, both of which should stress goal provenance.

---

## Flue API — now verified

`research/flue_notes.md` was written from the marketing page and lists open questions. Two are
now answered from a running deployment (`@flue/runtime` 1.0.0-beta.9):

- **Agent shape:** `defineAgent(() => ({ model, instructions, actions }))`, with
  `AgentRouteHandler` for routing. Workflows default-export `run(ctx: FlueContext)`.
- **The termination mismatch is confirmed in shipped code, not inferred.** A production
  comment describes a workflow as *"a bounded, result-returning operation … it terminates and
  yields an IC brief; durable state lives in the graph."* Flue workflows terminate; URAS loops
  do not. The Durable Object route remains the resolution.

Still open from the original list: whether subagent nesting is true recursion, whether budget
accounting exists, and the actual shape of durable stream records — whether evidence chains
can be *reconstructed* from them or only replayed. The third matters most; the book's
scoring chapter depends on reconstructing what was believed before an outcome arrived.
