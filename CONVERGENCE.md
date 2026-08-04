# Convergence plan — a cybernetic loop language and design tool

**Status (2026-08-04):** active convergence record, not a normative language document.

Verified milestones:

- the authoring → IR → semantic validation → analysis path is fail-closed;
- IR v2.1 has order-independent loop membership, typed policy-input and world-path edges,
  and observer-relative boundaries;
- authoring aliases, types, references, slugs, and shared meanings fail on ambiguity;
- partial designs remain valid IR and receive `incomplete_loop` findings;
- belief calibration can declare outcome, scoring rule, window, and revision target;
- observation review can declare value metric, window, and an attention-changing response;
- boundary declarations record observer, purpose, inside, and outside;
- action → controlled-process → observation paths and explicit effect direction are represented;
- ordered policy rules retain their own inputs/actions and explicitly name reference use;
- every finding carries an assurance level; theorem-inflated checks were renamed or withdrawn;
- one unified CLI and one zero-finding complete example exercise the product path;
- semantic diff compares validated IR, loop membership, relations, and finding deltas without
  depending on YAML order;
- a normative conformance manifest pins normalized IR and complete finding-set hashes for all
  shipped product fixtures;
- 38 authoring checks have executable positive coverage and are separated from 12
  compatibility-only graph checks;
- the external-study manifest is generated only from committed semantic artifacts after the
  source release gate passes;
- the working suite and independent metamorphic/historical checks pass.
- the real-loop gate covers 25 encodings and 7 exact upstream revisions; a blinded SWE-agent /
  Browser Use replication rejects defect-rate claims from raw finding counts while reproducing
  controller-operation, conditional-authority, and deployment-binding language pressure.

Still open: controller operations and terminal outputs distinct from world interventions,
conditional and loop-level authority, deployment-bound action profiles, quantitative
process/environment dynamics, full-cycle signed influence,
disturbance/response semantics, revision of observer distinctions, external-author usefulness,
and prospective outcome evidence. Those gates limit the release claim even though the local
structural system is now coherent.

This project is converging on a useful and defensible thing:

> A human-readable, machine-checkable language for specifying agent feedback loops, plus a
> design analyzer that finds missing feedback, weak epistemics, unsafe authority, and unmanaged
> resource use before deployment.

The YAML is the authoring surface. A typed loop model is the semantic artifact. The linter,
diagrams, comparisons, code readers, and execution adapters are projections over that model.
Compilation is useful, but it is not the definition of the language and an LLM is not the
trusted semantic boundary.

This is narrower than a universal representation for adaptive systems and stronger than a
checklist. It is also a better fit for the evidence in this repository.

---

## 1. What the folder currently contains

The repository already has most of the pieces of a serious language programme:

- a plain-language authoring format and generated grammar;
- a flat graph representation;
- structural validation and derived diagnostics;
- diagrams, comparisons, compile experiments, and post-compile checks;
- adversarial, held-out, published, and field examples;
- pre-registration, independent encoding, adjudication, and a record of failed hypotheses.

Its strongest conceptual contribution is the combination of:

- **operating regulation** — observe, estimate, decide, act;
- **attention** — whether a signal is worth its cost and affects a decision;
- **calibration** — whether estimates track later outcomes;
- **governance** — who sees, approves, can undo, and bears the loss;
- **viability** — what the loop consumes and how it adapts before exhaustion.

The core idea is sound. The baseline blocker was that the authored language, canonical graph,
checks, diagrams, and product story did not make exactly the same claim. Phases 0, 1, and the
assurance part of Phase 3 have now repaired that baseline.

---

## 2. Baseline critique (the failure state this plan is controlling)

**At baseline, LoopSpec had a strong vocabulary for talking about feedback but no single lossless,
operationally defined feedback-loop semantics.** Phases 0–3 repaired that source-to-analysis
path; this section is retained as the failure record that the current gates must prevent.

That shows up in four ways.

### 2.1 Product ambiguity

At baseline, documents variously said that:

- the linter is the product;
- the notation is the contribution and the linter is a consumer;
- any LLM should compile the spec;
- the spec is mainly for comparison and argument.

Those can coexist only after one is made primary. The proposed order is:

1. **semantic language** — the durable artifact;
2. **design analyzer** — the primary user value;
3. **diagram and comparison** — reasoning projections;
4. **code extraction and compilation** — adoption and execution adapters.

### 2.2 The semantic pipeline was not closed

Concrete failures found at baseline:

- `runs:` is the canonical cadence key, but expansion reads `every:`, so current v1 specs lose
  their timescale;
- `tools/loop.py --lint` does not run the canonical semantic validator;
- an expanded flagship example fails that validator because required metadata and the authoring
  contract disagree;
- expansion creates `Disturbance` nodes although `Disturbance` is absent from the catalog;
- a loop record chooses the first observation and first action in YAML order, even when several
  are declared;
- loop closure is therefore metadata, not a closed path through the graph;
- group members are merged by slug equality, with conflicting meanings able to collapse
  silently;
- policy inputs are inferred by regular expressions over prose, so lint semantics depend on
  spelling rather than a condition grammar;
- several current examples and the tour still teach deprecated aliases.

Until these are fixed, adding primitives or checks increases apparent expressivity while the
actual semantics remain lossy.

### 2.3 The cybernetic claims exceeded the represented information

The baseline checks contained useful prompts, but some were named as stronger results than the
model could establish:

| current claim | what the current graph can honestly establish | what a formal claim needs |
|---|---|---|
| Good Regulator violation | no **declared explanatory model** | a defined reguland, outcome set, regulator mapping, performance criterion, and the theorem's optimality/simplicity assumptions |
| unobservable | no declared measurement/estimation path | system dynamics and an observation model over time |
| uncontrollable | no declared action/effect path | system dynamics and control influence over reachable states |
| reinforcing polarity | self-produced evidence with no independent corrective channel | signed causal links around an actual cycle |
| insufficient variety | few named response types relative to named concerns | distinguishable disturbance states, response states, channel capacity, and outcome variety |
| oscillation risk | delay is present and damping is not declared | delay relative to cadence, loop gain or response sensitivity, and stability assumptions |
| cascade inversion | the inner loop's declared run period is not shorter than the outer's | inner closed-loop settling time or bandwidth relative to the outer update period |

These checks should be retained after being renamed as structural preconditions or risks. A
theorem should be cited as motivation unless its assumptions are represented and checked.

There is a second naming issue. A loop that monitors another loop is **meta-control**, but that
alone does not make it second-order cybernetics. In von Foerster's sense, second-order
cybernetics concerns observing systems: the observer, the distinctions used to observe, and the
observer's purpose enter the account. Attention and calibration become second-order in that
stronger sense only when the language represents who selected the signal, target, category, and
boundary, and how those choices are themselves revised. Until then, call them higher-order or
meta-regulatory loops. Likewise, “third-order” should remain a research hypothesis; use the
operational name **schema/model revision** in the language.

### 2.4 Higher-order loops were declarations, not loops

At baseline, `checked_by:` was an opaque name. Belief calibration now supports the first four
items below plus an explicit revision target. Attention review separately declares a value
metric, review window, and change to sampling/source/routing/retirement:

- which past prediction is joined to which later outcome;
- what scoring rule or loss is used;
- over what cohort or time window;
- which threshold matters;
- what action changes the estimator or signal policy.

The same is true of attention review. Naming a review clears a check without proving that a
feedback path closes. Calibration and attention become deeply cybernetic only when they reuse
the loop kernel: measure performance, compare it with a reference, and change the component
being regulated.

---

## 3. Design commitments

These are the constraints the next language version should optimize, in order.

1. **One meaning, end to end.** Every authored declaration either has one deterministic IR
   meaning or is rejected. Nothing disappears silently.
2. **A loop is a cycle, not a bag of parts.** Closure must be traversable in the semantic graph.
3. **Boundaries are explicit and observer-relative.** “Outside” means outside a named boundary,
   and the spec records who drew that boundary and whose purpose is being declared.
4. **Declared intent and observed behavior stay distinct.** A goal says what someone intends;
   traces say what the system in fact regulates.
5. **Structural checks do not impersonate dynamical proofs.** Each diagnostic states its
   assumptions and assurance level.
6. **Higher-order regulation reuses the same kernel.** Attention, calibration, and adaptation
   are loops acting on signals, estimators, policies, goals, or boundaries.
7. **Plain language is a surface property, not an excuse for hidden semantics.** Prose may
   explain a policy, but machine reasoning uses declared reads or a real expression grammar.
8. **Framework details flow outward only.** MCP, prompts, subagents, context windows, and any
   one runtime belong in adapters, never in the semantic core.
9. **Safety fails closed.** A broken query, lost approval, unresolved reference, alias collision,
   or unrepresentable target is an error, not a partial success.
10. **The language can say “unknown.”** Unknown sign, effect, delay, confidence, or boundary is
    different from absent and must not be invented by an encoder.

---

## 4. The semantic kernel to converge on

A loop is closed when the following path is explicit or mechanically derivable without a
modelling choice:

```text
reference ──┐
            ├─> comparison/error -> policy -> action -> process/environment
perception ─┘                                      |              |
     ^                                             | effect       | outcome
     |                                             v              v
     +------------- estimator <- observation <- sensor <----------+
```

The minimum semantic record for one loop is:

| concept | required meaning |
|---|---|
| boundary | what is treated as system, environment, and interface |
| observer/author | who chose the boundary, variables, and reference |
| controlled variable | the environmental or perceived condition being regulated |
| reference | desired value, range, ordering, or termination condition |
| observation | what actually arrives, with provenance and sampling cadence |
| estimator/perception | how observations become the value used for control |
| comparison | how reference and perception produce an error or decision-relevant difference |
| policy/controller | what it reads and how it selects actions |
| action/actuator | what can be done, by whom, with reversibility and authority |
| effect path | what an action is believed to change, with sign, delay, and uncertainty when known |
| process/environment | the thing through which actions change later observations |
| disturbance | an influence on the controlled process, distinct from something merely omitted |
| cadence and delay | when sensing, deciding, acting, and effects occur |
| constraint/resource | invariants and depletable stocks that bound viable operation |

The authoring surface does not need a separate noun for every row. Comparators and error values,
for example, may be derived from a reference and a perception of the same controlled variable.
But the IR must contain their meaning, and the derivation must be total and unique.

### Higher-order loops

Use the same kernel recursively:

- an **attention loop** regulates a signal's decision value relative to acquisition cost; its
  actions change sampling, routing, source, or retirement;
- a **calibration loop** regulates estimator loss or reliability; its observations join frozen
  predictions to later outcomes and its actions revise or retire the estimator;
- an **adaptation loop** regulates lower-order viability; its actions change a policy, model,
  reference, action set, or boundary;
- a **governance loop** regulates delegated authority and exposure; its actions approve,
  revoke, constrain, or escalate.

`checked_by: monthly_review` remains accepted as an explicitly incomplete declaration so an
early design can be linted. It does not count as a closed calibration or attention contract by
itself; the corresponding `incomplete_*_contract` finding names the missing closure fields.

---

## 5. Assurance levels for the analyzer

Every check must declare one of these levels in machine-readable metadata.

| level | allowed claim | example |
|---|---|---|
| A — syntax | the artifact is malformed or ambiguous | unknown key, duplicate id, alias collision |
| B — structural | a necessary declared path is absent | no observation path, no action effect path, ungated irreversible action |
| C — qualitative dynamic | a represented causal structure carries a known risk | reinforcing signed cycle, delay large relative to cadence, competing loops |
| D — quantitative | a property is computed from an adequate model or trace | observability rank, controllability rank, calibration error, simulated stability margin |
| E — empirical | a pattern predicts trouble in the reference population | base rate and author-validated action rate |

Rules:

- a level-B check may cite a theorem as motivation but may not say the theorem was violated;
- level C requires signed or otherwise typed causal effects, not provenance alone;
- level D must list its model assumptions and return `unknown` when inputs are absent;
- empirical rarity affects prioritization, not truth;
- every diagnostic has a minimal positive fixture, a minimal negative fixture, and a documented
  counterexample that it must not flag.

---

## 6. Work plan

### Phase 0 — freeze and establish one contract — **verified locally**

**Goal:** stop narrative and semantic drift before changing the language again.

Work:

- declare the product order from section 2.1;
- name one current language version and one normative entry point;
- mark the original universal charter and pre-normal graph as historical research;
- freeze new primitives, fields, and checks until Phase 1 passes;
- keep the control-diagram projection explicit about loss: reference use and process paths now
  come from IR, while the displayed numeric error remains a non-executable convention;
- add a decision log for changes to syntax, semantics, and diagnostic claims.

Exit gate:

- README, format tour, reference, examples, and CLI all describe the same pipeline;
- one command is documented as the release gate.

### Phase 1 — make v1 semantically lossless — **verified locally**

**Goal:** earn the right to redesign by making the existing path trustworthy.

Work:

- fix canonical key consumption, beginning with `runs:`;
- run authoring validation, expansion, canonical validation, and checks in one fail-closed
  command;
- reconcile required canonical metadata with what the authoring surface can supply;
- remove or catalogue generated `Disturbance` nodes; do not equate `not_modelling` with
  disturbances;
- replace first-observation/first-action loop identity with explicit loop membership;
- reject slug collisions, alias-plus-canonical duplicates, and conflicting shared-node fields;
- validate types and required subfields, not only unknown keys and enums;
- replace fixed temporary files with safe per-run artifacts;
- migrate the tour and flagship examples off deprecated vocabulary;
- turn every shipped example into an executable golden test.

Exit gate:

- all current v1 examples pass the complete pipeline;
- every authored key is either preserved in the IR or rejected;
- permuting YAML map order produces an identical semantic hash and identical findings;
- intentionally deleting or misspelling each safety-relevant field fails a test;
- the generated graph passes the same validator used for hand-authored graphs.

### Phase 2 — specify Loop IR v2.1 before choosing syntax — **core implemented; independent implementation conformance remains unevidenced**

**Goal:** define real loop closure and only then test surface syntax.

Work:

- write a small normative semantics document for the kernel in section 4;
- add explicit boundary, observer, controlled-variable, loop-membership, and process/effect
  semantics; disturbance semantics remain withheld rather than inferred;
- represent intervention effect sign as `increase | decrease | unknown`; complete-cycle causal
  sign and confidence remain future dynamic semantics;
- represent all observations and actions belonging to a loop rather than selecting one of each;
- define nested and coupled loops with namespaces and explicit sharing;
- retain prose conditions while requiring typed `reads:` and `against:` semantics beside them;
- define calibration and attention as structural contracts over components; adaptation and
  governance remain composable loop patterns rather than special syntax;
- represent the observer's distinctions and purpose before claiming second-order cybernetics;
- specify `unknown`, `not_applicable`, and `not_modelled` separately;
- create migrations from v1 and preserve old files as evidence;
- publish an executable conformance manifest that pins normalized IR and complete finding-set
  hashes for every normative product fixture.

Exit gate:

- thermostat, Ralph, a judge loop, a multi-agent verifier, and a resource-bounded autonomous
  loop all produce actual closed cycles;
- two independent implementations can construct the same canonical IR from the normative
  fixtures; the comparison target exists, while independent agreement is still unevidenced;
- no target-framework concept appears in the kernel.

### Phase 3 — rebuild diagnostics on the assurance ladder — **active checks completed**

**Goal:** keep the useful findings while eliminating theorem inflation.

Work:

- inventory every current check and assign level A–E;
- rename `regulator_without_model`, current observability/controllability claims, polarity, and
  variety checks to match what they actually establish;
- implement true qualitative polarity only after signed cycles exist;
- compare delay with cadence and represented damping before reporting a dynamic risk;
- compare cascade settling time or bandwidth with the outer update period; cadence ordering
  alone may remain a risk heuristic but not a necessary-condition claim;
- make missing data produce `unknown` rather than a clean bill of health;
- include assumptions, evidence path, confidence, likely symptom, and next observation in each
  finding;
- preserve `consider:` as an auditable decision, not suppression;
- fail the analyzer if any query crashes.

Current local coverage gives every active authoring check an executable positive case, uses the
complete design as a shared zero-finding negative, mutates safety-relevant declarations, and
holds theory-inspired claims below their represented premises. It establishes analyzer
consistency, not empirical precision; author adjudication remains the Phase 5 gate.

Exit gate:

- every check passes its positive, negative, mutation, and counterexample fixtures;
- no theorem-labelled result can be produced without its required formal inputs;
- a proportional thermostat without an explicit prose `Explanation` is not falsely declared
  a non-regulator;
- a self-produced but negatively coupled signal is not falsely called reinforcing;
- one action capable of handling several disturbance modes is not rejected by node counting.

### Phase 4 — converge the tool experience — **core local workflow completed; adapters remain experimental**

**Goal:** make one artifact support design, inspection, and adoption.

Work:

- one command performs format, validate, analyze, and render;
- render a control-loop view from the actual cyclic IR and a dependency/governance view as a
  separate projection;
- make semantic diff the core comparison operation — implemented as `loopspec diff` over validated
  canonical documents and finding sets;
- have code readers emit a draft spec plus provenance and explicit uncertainty for every
  inferred declaration;
- log human corrections as language-design evidence;
- keep LLM compilation optional and require adapters to emit a machine-readable preservation
  manifest: `preserved | degraded | omitted | externally_enforced`;
- replace text-scan verification with target adapters where safety claims are made; retain text
  scan only as a labelled heuristic fallback.

The code-reader and compilation-adapter items are adoption experiments, not prerequisites for
the v1.1 structural design-tool claim. They must stay labelled experimental until their own
preservation manifests and correction-rate evidence pass.

Exit gate:

- a new user can lint an existing loop, inspect evidence for a finding, correct the inferred
  spec, and see the diagram change without learning the IR vocabulary;
- every projection names what it loses;
- an omitted approval, constraint, or irreversible action fails closed.

### Phase 5 — validate usefulness and generalization

**Goal:** determine whether this is a design tool, a completeness checker, or only a useful
notation.

Pre-register before running:

1. **Construct validity.** Paired synthetic loops differing in exactly one property for every
   check.
2. **Encoding reliability.** Cross-provider encodings plus a weak-to-frontier capability sweep;
   correction rate is tracked, not only agreement.
3. **Existing external-loop evidence.** Retain the published reference-loop encodings and
   independent-encoder corrections as historical evidence; do not relabel them prospective.
4. **Author usefulness.** At least twelve loops whose authors did not build the language,
   spanning at least three domains, six operating systems, four designs, and two encoders;
   authors
   classify each finding as wrong, known/no-action, changes understanding, changes spec, or
   changes implementation.
5. **Prospective value.** For acted-on findings, record the intervention and later outcome.
6. **Held-out transport.** The repository's earlier sealed set has already been opened and is
   now compatibility evidence. Treat the preregistered external-author systems—not that
   historical set—as the prospective transport test for v1.1.

Initial release thresholds, to be frozen in the pre-registration:

- 100% semantic preservation on the golden and mutation suites;
- no order-dependent IR or findings;
- at least 70% precision for high-severity findings after encoder correction;
- fewer than 20% of surfaced findings attributable to encoding mistakes;
- at least half of external authors receive one finding that changes a spec, decision, or
  implementation;
- no single domain or encoder is necessary for the three primary thresholds to pass;
- no external result requires changing the frozen grammar, semantics, ranking, or message.

The exact thresholds may be changed before the study, with a reason. They may not be moved
after results are seen.

### Phase 6 — release or narrow honestly

Release the language only if Phases 1–5 pass. At release:

- freeze the semantic core and version it separately from surface syntax;
- publish the assumptions and evidence level of every check;
- ship migrations and a compatibility policy;
- remove historical charter material from the primary onboarding path without deleting the
  research record;
- state the achieved claim, not the original ambition.

If the external study yields low precision but the completeness checks remain reliable, narrow
the product to a **loop specification and review tool**. If the notation improves comparison
but does not change decisions, call it a **reasoning notation**. Both are legitimate outcomes.

---

## 7. The convergence process is itself a control loop

The project should regulate four variables rather than optimize a single score:

| controlled variable | measurement | corrective action |
|---|---|---|
| semantic preservation | golden, mutation, round-trip, and order tests | fix grammar/normalizer/IR; no new features |
| theoretical validity | assumption audit and counterexample suite | weaken claim, add required semantics, or remove check |
| encoding reliability | cross-provider agreement and human correction rate | clarify boundaries or simplify syntax |
| practical usefulness | external-author precision and action rate | improve evidence, ranking, extraction, or narrow product claim |

Cadence:

- run the complete suite on every semantic change;
- review the four controlled variables weekly during active language work;
- admit a new core concept only when three independent cases across two loop families require
  it and no composition of existing concepts works;
- freeze the language before every held-out evaluation;
- record rejected changes and counterexamples, not only accepted ones.

Disturbances to watch:

- framework churn pulling runtime concepts into the core;
- strong models supplying semantics the language failed to state;
- benchmark encoders copying each other's assumptions;
- base-rate ranking hiding universally important defects;
- book, demo, or release pressure causing premature convergence;
- attractive diagrams inventing closure absent from the IR.

### Kill and pivot criteria

- If high-severity precision remains below 60% after two correction cycles, stop calling the
  analyzer a design critic.
- If code-to-spec extraction still causes more than 25% of findings after two iterations, make
  authoring/review the primary workflow and label extraction experimental.
- If a core relation cannot be given deterministic semantics without prose interpretation,
  keep it as an annotation and do not lint it.
- If higher-order loops cannot reuse the loop kernel, stop describing opaque `checked_by`
  declarations as cybernetic closure and model them as workflow metadata until they can.
- If no external author changes a decision or implementation, preserve the notation research
  and stop product expansion.

---

## 8. Immediate queue

Do these next, in this order:

1. Freeze the current authoring v1.1 / IR v2.1 structural contract and publish no new theoretical
   check.
2. Keep dynamic polarity, stability, and variety checks withheld until their formal inputs and
   counterexamples exist.
3. Run the pre-registered external-author usefulness study in Phase 5.
4. Record finding precision, encoding correction rate, action rate, and later outcomes.
5. Keep the already-open historical transport set labelled compatibility evidence; do not
   reuse it as prospective validation.
6. Release as a structural loop specification/review tool unless external evidence justifies a
   stronger claim.

The project has already done the hard cultural work: it records reversals, failed predictions,
and encoding bias. Convergence now depends on applying that discipline to the semantic pipeline
and to the cybernetic claims themselves.
