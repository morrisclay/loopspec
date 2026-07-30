# First Complete Score — Independent Encoding Round 1

**SCORE 0.640** — first non-partial score. All five terms and both gates computed.

| Term | Value |
|---|---|
| S simplicity | 0.812 |
| E expressivity | 0.950 |
| D determinacy | 0.794 |
| U usefulness | **0.300** |
| C comprehensibility | 0.584 |
| gate negative_control | pass |
| gate reduction | **pass** |

## Method

Two encoders, same source, no shared context:

- **`claude-opus-5`** — wrote both the catalog and the prose. Labelled `author-intent`, not
  an independent sample. Encodings written *blind*, before seeing the other encoder's output.
- **`gpt-5-codex`** — via `codex exec` at xhigh reasoning, read-only isolated workspace.
  Given the catalog and prose with **the answer keys stripped**: the `demands:` front-matter
  list (which names the exact primitives) and every `demanded_by` field and commentary note
  naming the target systems. Without stripping, D would have measured copying.

A third encoder (`gpt-5` via `llm`) failed on `insufficient_quota`. Gemini CLI is dead —
Google dropped individual-tier support. The only local model is a 7B, too weak to pair
meaningfully: its divergence would measure capability gap rather than ontology ambiguity.

So the pair is cross-vendor (anthropic / openai), which avoids shared-family inflation, but
one half is the author. **This D is a necessary-condition check — does the catalog transmit
its author's meaning — not the stronger test of whether two naive readers converge.**

---

## The good result: the reduction floor holds

Both encoders independently set `reduces_to: classical_control_loop` for the thermostat, and
both independently set `null` for the hospital.

This is the two-sided test from `research/prior_art_gate.md` passing on its first real trial.
The representation degrades cleanly to classical control when the extra structure is unused,
and does not degrade when it is needed. Independent agreement makes it meaningful rather than
a self-assessment.

## The bad result: usefulness is 0.300, and the reason is worse than the number

**`gpt-5-codex` surfaced ZERO decision-relevant insights on both systems.** Not a low count —
none. It declared empty lists, which the task explicitly permitted and preferred over padding.

I surfaced three per system. The obvious reading is uncomfortable and probably correct: I
wrote the prose, so I know what each description was *designed to illustrate*, and my
"surfaced" items may be author's privilege rather than discovery. An encoder seeing only the
text found nothing worth telling a practitioner.

Consequences:

1. **This is the first hard evidence that `U` cannot be self-assessed.** It was already
   flagged as un-self-auditable in `ontology/score.md`; now there is a measurement showing my
   own claims are the outlier rather than the baseline.
2. **All six claims remain `audited: false`.** The audit fraction is 0.0 and contributes zero.
   Nothing about usefulness has been established by anyone but me.
3. For the thermostat specifically, zero may be *correct* — it is a toy, and there may be
   genuinely nothing to surface. That excuse is not available for the hospital.

## Divergences, worst first

### `Loop` granularity — 0.333, the worst and the one that matters most

I identified three loops in the hospital (discharge decision / daily, bed allocation /
hourly, readmission feedback / fortnightly). Codex identified **one** (`discharge_bed_flow`).

Both are defensible from the prose. The catalog says nothing about where one loop ends and
another begins.

This is the most consequential divergence because of the Cloudflare finding in
`research/flue_notes.md`: **one alarm per Durable Object means `Loop` is the unit that maps to
a DO.** Loop granularity is therefore not a matter of taste — it determines how many
execution units the compiled system has, and a 3-versus-1 disagreement is a 3-versus-1
disagreement about deployed architecture.

**Action required:** the catalog needs a determination rule for loop identity. Candidate: a
distinct loop per (timescale, closing intervention) pair, which would give three here and
matches the DO mapping. Not yet adopted — it needs testing against Toyota, which has five
timescales and would fragment heavily.

### `Estimand` individuation — 0.571 on the hospital

I predicted in my own encoding that this would be the primary divergence point, and wrote the
fork down before comparing. It was.

- **Mine:** five distinct estimands *plus* a sixth contested aggregate
  (`discharge_readiness`), explicitly not scalarized, resolved by ward-round negotiation.
- **Codex:** five distinct estimands, no aggregate.

Also `patient_preference` versus `patient_acceptability` for the same thing — pure naming
divergence, which is a smaller but real determinacy cost.

Predicting the divergence point correctly is mild evidence the ontology's ambiguities are
known rather than latent. It does not make them less ambiguous.

### `Party` — the definition is broader than my own use of it

Parties on the hospital: **identical, 5/5.** Consultant, nurse, discharge coordinator, bed
manager, patient. For the primitive doing the most work in the ontology, that is a strong
result.

But on the thermostat, Codex included `controller` as a party and I included only
`householder`. Checking the definition — *"a locus that may hold estimates, hold desired
conditions, exercise authority, and bear consequences"* — the controller **does** exercise
authority over `fire_boiler`.

**Codex is right and I was wrong, by my own definition.** The definition admits any
authority-exercising locus; I had been using it to mean something narrower, closer to "an
interested party." Either the definition narrows or my usage corrects, and the ontology
cannot tell which until this is settled.

### Primitive selection — 0.833 / 0.867

- Hospital: Codex omitted `Evidence`, `Estimator`, `Constraint`. The `Estimator` omission is
  notable given five parties are visibly estimating; it suggests `Estimator` reads as optional
  when estimation is implicit in a party holding an estimate — which is an argument that
  `Estimator` and `Estimate` are a merge candidate not yet on the list.
- Thermostat: I used `Constraint` for the deadband; Codex used `Consequence`. Mine is better
  founded — the prose is explicit that the deadband exists to prevent relay chatter, which is
  structural — but the divergence shows the two are confusable.

---

## A flaw in the `E` term

Codex claimed **5 of 5** breaks handled on the hospital, including `complete_specification` —
the break asserting that load-bearing unwritten knowledge cannot be represented. I claimed
4 of 5, judging that one explicitly *not* handled: the representation can *name* the unwritten
items as excluded variables but cannot represent them.

I believe I am right and Codex over-claimed. But the mechanism is the problem, not the
instance: **`breaks_handled` is self-assessed, so `E` rewards optimism.** An encoder that
declares everything handled scores 1.0.

`E` is currently the second-highest term at 0.950 and should be treated as unreliable until
`breaks_handled` is adjudicated by something other than the encoder that produced it. The
fix is symmetric with `U`'s audit fraction: a handled-claim needs a second party's assent.

## `C` is dragged down by nesting, not length

Compression 0.523 (encodings are roughly half the prose — acceptable), undefined terms 0.0,
but **flatness 0.25**: my encodings nest five to six levels deep.

Toyota's A3 constraint says a representation should fit one sheet and be readable by someone
who was not involved. A six-level nested YAML document does not meet that bar. The prose is
currently more readable than its own encoding, which is a direct argument that `C` is
measuring something real.

## Two YAML findings worth keeping

**`on:` is a reserved word.** YAML 1.1 parses `on`, `off`, `yes`, `no` as booleans, so `on:`
became the key `True` and broke traversal. For a project intending YAML as a serialization
this is spec-level: either ban reserved-word keys in the schema or specify YAML 1.2 / JSON as
the canonical wire format. Recorded for `schema/`.

**I made the same structural error three times** — list items followed by a mapping key at the
same indentation, in `primitives.yaml` and both of my encodings. Silent until parse. That is
three instances of a class of error a validator would have caught instantly, and it is the
strongest practical argument so far for the Semantic Validator being executable and run on
write rather than specified in a document.

---

## What to do next, in order

1. **A loop-identity rule.** Highest leverage: it is the worst divergence and it has direct
   execution consequences via the DO mapping.
2. **Settle `Party`** — narrow the definition or correct my usage.
3. **Get `breaks_handled` adjudicated independently**, or `E` stays untrustworthy.
4. **Flatten the encoding shape** to lift `C` toward the A3 bar.
5. **A genuinely independent second encoder.** The current pair includes the author. An
   OpenRouter key would allow a non-OpenAI, non-Anthropic family and turn D from a
   necessary-condition check into a real measurement. This is the one item that needs
   something I cannot obtain myself.
