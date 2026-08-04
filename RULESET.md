# Ruleset contract

The linter reports only what can be derived from the encoded structure. Its source of truth is
[`docs/checks.yaml`](docs/checks.yaml); [`docs/CHECKS.md`](docs/CHECKS.md) and
[`docs/base_rates.json`](docs/base_rates.json) are generated from that metadata and a live
corpus run.

## Two independent axes

Every check has two labels that answer different questions.

**Assurance** describes what one finding establishes:

- `structural` — follows directly from declared fields, nodes, and edges;
- `qualitative-proxy` — a screening pattern that requires domain analysis;
- `quantitative` — follows from explicit numeric dynamics and assumptions;
- `empirical` — supported by observed outcomes over a stated cohort and window.

**Evidence** describes how the check's prevalence or usefulness has been evaluated:

- `robust` — survived an independent encoding exercise;
- `corpus` — measured on the repository corpus;
- `motivated` — justified by real instances but not validated at rate;
- `legacy` — retained for historical hand-authored graph encodings.

A check can be empirically common and still have only structural assurance. Frequency does not
turn a graph pattern into a theorem.

## Active theoretical boundary

The following distinctions are deliberate:

| Check | Assurance | Boundary |
|---|---|---|
| `no_explicit_process_model` | structural | says no `explains` relation is encoded; does not test the Good Regulator theorem |
| `unmeasured_estimand` | structural | says no signal informs a quantity; does not test Kalman observability |
| `target_without_actuator` | structural | says no action declares it moves a target; does not test Kalman controllability |
| `endogenous_feedback_without_crosscheck` | structural | says feedback lacks an independent observation; does not infer causal polarity or stability |
| `process_path_not_declared` | structural | says no action→process→observation path is represented; does not establish actual causation, gain, or dynamics |
| `effect_direction_unspecified` | structural | says a sign is neither declared nor explicitly unknown; a declared sign is still not loop polarity |
| `cascade_cadence_inversion` | qualitative-proxy | compares update cadences; does not know bandwidth or settling time |

The old `insufficient_variety` check is withdrawn. Counting `not_modelling` entries against
actions confused model exclusions with disturbances and headcounts with Ashby's state variety.

## Structural families

The active rules cover five practical families.

### Closure

- target without actuator;
- quantity without observation;
- observation and action present but not joined by one loop;
- action and observation present but not joined through a controlled process;
- target present but no ordered rule explicitly uses it as a reference;
- multiple actions with no selection rule;
- policy inputs that are undeclared or unobserved.

### Epistemics

- belief never scored against outcomes;
- explicit process model absent;
- observation with no declared use;
- entirely endogenous or singly grounded observation channels;
- costly observation source with no review loop;
- named calibration or attention review without the fields needed to close its structural contract.

### Framing and effect

- observer, purpose, or system/environment boundary absent;
- intended action effect has neither a declared direction nor explicit `unknown`;
- exclusions remain boundary notes and are never promoted to disturbances by inference.

### Governance

- irreversible/costly action without approval;
- consequence bearer without authority or information;
- no human or escalation path;
- escalation conditions with no named recipient;
- shared action or shared estimate with no arbiter.

### Resources

- no declared budget;
- consumed resource with no limit or replenishment;
- a ceiling that no decision rule reads.

### Hierarchy

- setpoint assigned to an outer loop that cannot move the referenced quantity;
- inner cadence no faster than outer cadence, reported only as a proxy.

The exact query, felt symptom, repair, prevalence, assurance, and evidence for each check are in
the generated checks reference.

## Admission rule for a new check

A diagnostic may join the active ruleset only when all of the following are true:

1. The source language or IR can represent every premise it inspects.
2. The query combines at least two independent declarations; it is not typed paraphrase.
3. A counterexample test shows when the query must remain silent.
4. Its message states the strongest justified conclusion and an explicit non-claim where a
   reader could confuse it with a theorem.
5. It has an assurance level and actionable repair in `docs/checks.yaml`.
6. The generated checks reference and base rates remain synchronized.
7. Product examples complete expansion, semantic validation, and analysis without hidden
   query failure.

## Withheld analyses

LoopSpec does not currently report these because their premises are absent:

- Kalman observability or controllability;
- Nyquist, Lyapunov, or other stability results;
- signed system-dynamics loop polarity;
- quantitative requisite variety;
- probabilistic calibration quality;
- claims about observer reflexivity or revision of distinctions beyond the declared observer,
  purpose, and boundary.

Adding the names without their mathematical objects would make the tool sound stronger and
be less useful. Each becomes eligible when the IR can state the necessary inputs and an
independent fixture can verify the analysis.
