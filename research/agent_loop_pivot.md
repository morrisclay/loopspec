# The agent-loop pivot

Proposed 2026-07-31: reposition URAS as a cybernetic representation language for agent loop
engineering, rather than a universal representation for adaptive systems across hospitals,
governments, ecosystems and ventures.

**Assessment: methodologically orthodox, probably right, and one specific failure mode away
from becoming the thing the prior-art gate exists to prevent.**

---

## Why this is not a narrowing, if framed correctly

The weak framing is *"universal was too ambitious, so we scoped down."* That is a retreat and
it will read as one.

The strong framing is the project's own methodology applied to itself:

> **Agent loops are the first domain in which cybernetic claims can actually be checked.
> Therefore they are where the representation should be built and validated. Universality
> stops being a premise and becomes a hypothesis to test afterwards.**

`benchmarks/reference_set.md` already contains the argument: *"A GAP IN THE CORPUS PRODUCED A
WRONG FINDING ABOUT THE ONTOLOGY … derivation from data is only as good as the data
selected."* The current corpus is prose descriptions of hospitals and immune systems, written
by one person, with no ground truth and no way to check an encoding against what the system
actually did. Agent loops are a corpus with **unlimited real instances, complete traces, and
outcomes that arrive.** Every methodological commitment in the charter points at them.

Four things the pivot fixes that the project has been unable to fix by effort:

1. **The prior-art gate changes opponent.** A universal representation must beat Dec-POMDPs on
   expressivity. A representation language for agent loops must beat *TypeScript plus a prose
   prompt* — an incumbent with no goal representation, no uncertainty, no calibration and no
   authority model. That is not a lower bar dishonestly chosen; it is the actual competition
   in the actual domain.
2. **`D` becomes measurable properly.** Inter-encoder agreement — the load-bearing term —
   needs many independent encodings of the same source. Agent loops supply them cheaply.
3. **Execution stops being Phase 7.** The compile target already exists and is already in use.
4. **The overclaim goes.** *"A hospital and a venture can be represented using the same
   ontology"* was always the most exposed success criterion, and it was never going to be
   demonstrated with the corpus available.

---

## The failure mode, and it is the important part of this note

An agent loop **has no politics.** It has no standing, no legitimacy, no parties bearing
asymmetric consequences, no informal influence, no contested boundary. So the primitives that
represent those things will look like dead weight against every agent benchmark, and the
twenty-primitive budget creates constant pressure to delete them.

Those primitives are precisely the defensible residue the prior-art gate identified:
**observer plurality, negotiable boundary, legitimacy, recursive viability.** They are what
distinguishes URAS from a POMDP.

> **So the pivot's specific danger is that optimising against agent loops deletes exactly the
> primitives that made the project non-trivial — leaving a POMDP with better ergonomics for
> agents, which is the outcome the gate was written to catch, arriving through the back
> door.**

### Rule, adopted with the pivot

> **No primitive may be deleted on the grounds that agent loops do not demand it.**
> Deletion requires a positive argument that the concept is not needed *by adaptive systems*,
> not merely that it is unexercised by the new corpus. Under-exercised primitives are marked
> `institution-only` and retained, and the count of them is tracked as a project metric.

This is the same shape as the existing anti-gaming rules and is cheap to adopt now. It will be
expensive to adopt after three rounds of budget pressure.

### The discriminating test

The question of whether this pivot is a breakthrough or a retreat has a cheap answer, and it
should be run rather than argued:

> **Build against agent loops. Then encode a hospital.**

- **If the ontology still encodes it** — universality survives as a *finding* rather than an
  assumption, which is far stronger than the original claim ever was, because it was derived
  somewhere it could be checked and then transported somewhere it could not.
- **If it does not** — you have learned that the institutional primitives were doing real work
  and that agent loops were too easy a corpus. That is also a result, and it is one the
  project could not otherwise obtain.

Either outcome is worth having. Neither is available without the pivot.

**Keep the held-out set sealed regardless.** `ecosystem`, `family`, `factory`, `llm_agent_system`
— note that the fourth is now the *native* domain, so it should be resealed with an
institutional substitute, or the generalisation signal is destroyed by the pivot itself.

---

## What the pivot must not import

The charter's standing directive — *prefer concepts that survive the replacement of today's
LLMs* — becomes harder to honour, not easier, when the validation domain is a 2026 practice.
Agent frameworks will churn. `Skills`-as-markdown, subagents, MCP, context windows and tool
schemas are all current-generation and none of them belong in the representation.

The firewall in `flue_notes.md` was written for Phase 7 and now applies to the whole project:
two columns, kept separate, and nothing flows right-to-left. `Estimator`, `Explanation`,
`Calibration` and `Delay` survive an architecture change. `Subagent` does not.

---

## What it unblocks

The book (`~/AI/applied_cybernetics`) is currently gated on URAS converging, and URAS is gated
on a corpus it cannot validate. The pivot collapses both:

- The book's blocking study — a pre-registered end-to-end cost comparison — is specified to run
  on an agent loop first precisely because that is where the instrumentation exists.
- The book's notation is generated from `primitives.yaml`; if the catalog is agent-native, the
  notation is executable rather than illustrative, and the reader can run chapter 3's loop
  instead of writing it on paper.
- The validator, the compile target, the encoder and the study all land in one place.

**Consequence for the book, which is not free.** The book's chapters on authority, standing,
disagreement and legibility carry no agent evidence and were explicitly forbidden from
borrowing any. If the notation becomes agent-native, those chapters lose notation and revert
to prose. That is acceptable — they were always the institutional half — but it should be a
decision rather than a discovery, and it argues for keeping the `institution-only` primitives
in the catalog even when nothing in the agent corpus exercises them.

---

## One honest caution about the claim

*"Incredibly helpful"* is almost certainly true. A checker that tells an engineer *your success
criterion is a signal, not the thing you want; your estimator learns from its own unverified
output; nothing scores this loop; you have one observer and no representation of disagreement*
would be immediately and obviously useful. That is a real product with real users and no
incumbent.

*"The best applied cybernetics way"* is a different claim. What the pivot actually optimises
for is **testability** — and testability is a proxy for value, not value itself. It is very
probably the right proxy here, given that the alternative was unfalsifiable prose about
hospitals. But the project should name it as a proxy and hold the discriminating test above,
rather than let *"we can measure it here"* quietly become *"this is where it matters."*

That failure has a name in the book this work feeds: it is chapter 4.
