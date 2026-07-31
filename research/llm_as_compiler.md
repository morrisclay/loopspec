# Can any LLM act as the compiler?

The requirement is *"any LLM should be able to act as a compiler eg to flue or something else
like langchain or goose."* That is a **legibility requirement on the format**, not a tooling
requirement, and it is falsifiable. This is the test.

`tools/compile_flue.py` — a hand-written Python compiler — quietly contradicts the
requirement. It stays as a reference implementation and a demonstration of what the mapping
should be. It is not the mechanism.

---

## Design

**The entire compile contract given to each model:**

> Here is a loop spec. Emit a working implementation for **&lt;target&gt;**.
> Report anything the target cannot express rather than dropping it: end your output with a
> section `## did not survive`.
>
> ```yaml
> <the spec>
> ```

**No format documentation. No primitive catalog. No examples. No schema.** If the model needs
`SPEC-FORMAT.md` to compile, the format has failed the requirement.

- **Spec:** `examples/customer_acquisition.loop.yaml` — 4 signals, 3 acts, 2 targets, 2 latent
  estimates, 3 rules, 3 parties, 1 constraint, an approval gate, and two deliberate defects.
- **Targets:** LangGraph (Python), a Goose recipe (YAML), Flue (TypeScript). Three unrelated
  execution models — a state graph, a declarative recipe, and a durable actor runtime.
- **Models, eight, across four capability tiers:** llama-3.1-8b and qwen3-8b (very weak),
  mistral-small-24b (weak), deepseek-v3.2 (mid), gpt-5.6-sol, claude-opus-5, grok-4.5,
  gemini-2.5-pro (strong).
- **Grading:** mechanical presence of 18 load-bearing elements. Truncated or errored responses
  are **excluded, not scored** — a response cut at the token cap reads as low fidelity and is
  not a fidelity result. Four of 24 were excluded on that rule.

The capability sweep is Briefing §4's method, applied to compilation rather than encoding.
Its logic is the point: *a strong model given a suggestive format produces a plausible
compilation because its competence supplies the determinacy the format lacks.* **The slope is
the measure. Flat is the result to want.**

## Result

| tier | mean fidelity | n |
|---|---|---|
| very weak (8B) | **0.898** | 6 |
| weak (24B) | 0.981 | 3 |
| mid | 0.981 | 3 |
| strong (frontier) | **0.993** | 8 |

**The slope is nearly flat across a roughly two-order-of-magnitude capability range.** An 8B
model compiles the format at 90% fidelity to frameworks it was given no documentation for.
That is the result the sweep was designed to be able to refute, and it did not refute it.

**Approval gate preserved: 20 of 20.** Every scored compilation, across all three targets and
all eight models, carried through some representation of the human approval gate —
LangGraph `interrupt()`, a Goose approval field, a Flue guard. `reversibility` and `approval`
survive compilation to frameworks that have no such concept, because the words say what they
mean.

**Gap reporting worked and was not sycophantic.** gpt-5.6-sol's `## did not survive` named
things worth naming: that LangGraph is not a scheduler so the cadence is metadata; that
`method: bayesian` specifies no prior or likelihood and its Beta-Bernoulli choice is *"an
interpretation rather than an exact preservation"*; that `moves:` gives no direction or
magnitude. Those are real underspecifications in the format, found by a compiler rather than
by me.

## The finding that matters most, and it is a warning

**The most-dropped element was `exit_channel` — 4 of 20.** That is the *irreversible act with
no approval gate*: the single most dangerous line in the spec.

Two of the four drops are llama-3.1-8b. The other two are deepseek-v3.2 and gemini-2.5-pro
compiling to LangGraph, and neither listed the omission under `did not survive`. It was not
declined; it was silently lost.

> **A compiler that silently drops the irreversible act is worse than no compiler**, because
> the spec now says a dangerous thing exists and the running system does not gate it.

This is not an argument against LLM-as-compiler. It is an argument that compilation output
must be checked against the spec rather than trusted — which is cheap, because the spec is
machine-readable and the check is the one this study already ran. **`tools/verify.py` now exists** and was built from this
finding: it checks a compiled artifact back against its source spec, in any language, and
ranks a lost approval gate above a lost act. Run across all 43 archived compilations it flags
a CRITICAL in 5 of 21 (v0) and 3 of 22 (v1) — every one of the known drops, plus two
non-answers the fidelity grader had excluded on length.

## CORRECTION — the headline was measuring the wrong thing

The fidelity numbers above are real and they do not mean what I said they meant.

Fidelity asks *did every element of the spec survive*. It cannot ask *is this the target's
actual API*, and the difference turns out to be most of the result. `gpt-5.6-sol` compiling to
Flue produced 17k characters that carry every element of the spec perfectly — inside an
invented `FlueWorkflow` interface it made up. `@flue/runtime` is never imported.
`gemini-2.5-pro`'s "Goose recipe" uses `metrics:` and `guardrails:`, which is not Goose's
format; it is my spec transliterated into plausible YAML. Both score near 1.00.

`research/compile_study/target_knowledge.py` asks the other question:

| target | uses the real API |
|---|---|
| LangGraph | **86%** (12/14) |
| Goose | 38% (6/16) |
| Flue | **18%** (2/11) |

**That is a ranking of how well these models know the target, not of how legible the format
is.** LangGraph is everywhere in training data; Flue is a beta nobody has seen.

### The experiment that separates them

If the format were the bottleneck, supplying the target's API would not help much. So: same
spec, same eight models, Flue again, with **one page** of Flue API appended
(`flue_api.md`, ~40 lines).

> **Flue, without the API: 18%. Flue, with it: 100%** — 6 of 6 scored, including
> `qwen3-8b` and `llama-3.1-8b`.

The format is not the bottleneck. **Target knowledge is, and one page of API reference closes
it completely.** This strengthens the original claim while correcting its evidence: any LLM
can act as the compiler, for any target, *provided the target's API travels with the spec*.
For LangGraph that is already in the weights. For anything newer than the model, it is a
required input — and cheap.

## Limits, stated

- **The grader checks presence, not semantics and not execution.** It measures whether the
  compiler carried an element through, not whether the emitted code runs or is correct. A high
  score means *nothing was dropped*, which is necessary and not sufficient.
- **n = 1 spec.** One loop, 8 models, 3 targets, 24 compilations. The flatness claim is about
  this spec's legibility. A spec using every corner of the format could slope differently.
- **Four exclusions** (2 truncation, 1 provider error, 1 empty). All strong-tier, so the
  strong-tier mean rests on 8 of 12.
- Grading regexes are generous by design — they test whether the *format* was understood, not
  whether identifier style matched.

## What it changes

The format is legible enough that compilation does not need a specification document, which
is the requirement. That in turn means **the compile target list is not a roadmap item** —
targets are prompts, and a new one costs a sentence rather than a compiler.

Reproduce: `research/compile_study/` holds the runner and grader.
