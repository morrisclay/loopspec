# External references — what they are and why they matter

Everything outside this repo that shaped a decision, with the decision it shaped. Kept in one
place because the argument depends on which claims come from measurement, which from
literature, and which from me.

**Legend:** ⚑ changed a design decision · ✎ supplies evidence · ⚠ threatens a claim here

---

## 1. Cybernetics and control theory — where the checks come from

The rule from `RULESET.md`: where a check follows from a **theorem** it is a necessary
condition, not a style opinion, and can be stated as such to a user.

| source | what it gives | where it lands |
|---|---|---|
| ⚑ **Conant & Ashby 1970**, *Every good regulator of a system must be a model of that system* | A loop with a target and no model of what produces it is a reflex, not a regulator | `regulator_without_model` — **100% of published examples** |
| ⚑ **Ashby 1956**, *Introduction to Cybernetics* — Law of Requisite Variety | Only variety can destroy variety: a regulator needs as many distinguishable responses as the disturbance has modes | `insufficient_variety` — **still unimplemented**, blocked on a missing `Disturbance` primitive |
| ⚑ **Kalman** — observability / controllability | A state is observable if inferable from outputs; controllable if drivable to a target | `unmeasured_estimand`, `uncontrollable_target` |
| ⚑ **Forrester / Sterman** — system dynamics loop polarity | Even number of negative links = reinforcing (runaway); odd = balancing | `reinforcing_loop_no_balancer` |
| ⚑ **Nyquist** — gain with delay | High loop gain plus delay produces oscillation | `delay_without_damping` — **unimplemented**; the format carries `effect_after` and `damping` for it |
| ✎ **Beer** — Viable System Model | S1–S5 decomposition; most agent loops are S1 plus a little S3 with no S4 environmental scanning | **Surveyed and deliberately not adopted** — imposing five levels on things that may have one is exactly the failure that killed the org-modelling programme |
| ✎ **Powers** — Perceptual Control Theory | You control the *perception*, not the output | No lint yet. Directly relevant: an agent controlling its *report* of success rather than success is a real failure mode |
| ✎ **Bhaskar** — critical realism | Real / Actual / Empirical; transitive vs intransitive knowledge | Why `Estimand` is separate from `Estimate` — the quantity exists independently of anyone's belief about it |

## 2. The 2026 loop-engineering literature — the field's own words

Full analysis: `research/published_study/LITERATURE.md`.

| source | what it says | why it matters |
|---|---|---|
| ✎ **swyx, *Loopcraft: The Art of Stacking Loops*** (AI Engineer World's Fair keynote) — [x.com](https://x.com/swyx/status/2065307558198567206) | Six nested loops: token → chat → agent turn → goal → automation → software factory | The field's canonical taxonomy. Establishes that "loop" is now the unit of design |
| ⚠ **LangChain, *The Art of Loop Engineering*** — [langchain.com](https://www.langchain.com/blog/the-art-of-loop-engineering) | agent → verification → event-driven → hill-climbing. Rubric grading, human touchpoints before sensitive calls | **The most important single reference here.** It has *verification* and **no discussion of calibration or whether agent confidence aligns with correctness.** That gap is the entire wedge |
| ✎ **O'Reilly Radar, *What the Hell Is a Loop, Anyway?*** — [oreilly.com](https://www.oreilly.com/radar/what-the-hell-is-a-loop-anyway/) | execution → task → product → system. *"a loop without its signal doesn't converge. It just runs until something external stops it"* | A practitioner independently arriving at `no_loop_closed` / `orphan_signal`, in prose, with no way to check for it. Explicitly does **not** discuss design quality, calibration, irreversible actions, approval gates, or what quantity is regulated |
| ⚑ **AIEWF 2026 recap** — [truefoundry.com](https://www.truefoundry.com/blog/aiewf-2026-loops-harness-engineering) | Harness engineering: budgets, step ceilings, stall detection, quotas, brokered credentials, per-step traces. Mike Krieger on delegation; *"the harness changes failure economics, not failure existence"* | **Was the clearest place the literature was ahead of this project, and is now closed.** Produced `spends:` in the format and three checks — `unbounded_loop`, `ceiling_without_correction`, `spends_without_limit`. The second goes beyond the source: *a ceiling is a stop, not a correction* |
| ✎ **latent.space, AIEWF trends** — [latent.space](https://www.latent.space/p/aiewf26trends) | *"evaluation + traces + tooling"* as the connective tissue | Confirms the field's answer to loop quality is outcome measurement, which is the threat in §5 |
| ✎ **Orosz** on loop engineering scepticism | *"outside of the increasingly few people who have unlimited AI token budgets… I don't think many have a use case"* | Probably right about *operational* loop engineering. This project targets the epistemic version, whose audience is anyone whose agent confidently does the wrong thing |
| ✎ **ghuntley.com/ralph** + the ralph-loop plugin | The `while true` agent loop | Encoded as `examples/field/ralph.loop.yaml`. Produced `single_point_of_grounding` and **corrected a wrong claim in `THESIS.md`** |
| ✎ *Supervising Ralph Wiggum: a Metacognitive Co-Regulation Agentic AI Loop* | Academic work adding a regulation layer to Ralph | Independent convergence on the same gap from the other direction |

## 3. The code corpus — what was measured

`research/published_study/` holds sources, encodings and findings.

| source | role | result |
|---|---|---|
| ✎ **LangGraph tutorials** (reflection, reflexion, rewoo, plan-and-execute, LATS, self-RAG, CRAG, adaptive-RAG, code assistant, multi-agent) | 7 of 10 loops in the study | Fetched from pinned docs commit `23961cff` — the `examples/` tree now redirects there |
| ✎ **OpenAI Agents SDK** `agent_patterns` | Intended as a major sample | **Mostly excluded: they are not loops.** routing, parallelization, deterministic, agents_as_tools and both guardrail examples run once. Only `llm_as_a_judge` cycles. A finding in itself |
| ✎ **CrewAI** `flows/self_evaluation_loop_flow` | Generate → review → retry, ceiling at 3 | Encoded and linted |
| ⚠ **DeepEval** `g_eval`, `agent_loop_detection` | The eval-layer test | `criteria` is arbitrary free text; `validate_criteria_and_evaluation_steps` checks only presence |
| ⚠ **Braintrust autoevals** `llm.py` `LLMClassifier` | The eval-layer test | Takes `expected` — **real per-case grounding**, which corrected my own over-strong encoding. Grounding the input is not calibrating the judge |
| ⚠ **Ragas** `_aspect_critic`, `_faithfulness` | The eval-layer test | Binary LLM verdict on a free-text aspect definition |

## 4. Flue — the first compile target

| source | what it settles |
|---|---|
| ⚑ **`@flue/runtime` 1.0.0-beta.9**, verified in a running deployment | `defineAgent` / `defineAction` / `defineTool`; workflows default-export `run(ctx)` |
| ⚑ **Flue's own docs on at-least-once execution** — *"recovery may re-dispatch the provider once… use application-owned idempotency keys where repeated effects would be harmful"* | Why every belief carries `safe_to_repeat`. A Bayesian update applied twice double-counts into a well-formed **wrong** posterior |
| ⚑ A production comment describing a workflow as *"a bounded, result-returning operation… it terminates"* | **Loop → Agent, not Workflow.** Flue workflows terminate; URAS loops do not |
| ⚠ **Open question** — can evidence chains be *reconstructed* from durable stream records, or only replayed? | Calibration needs an immutable record of what was believed *before* an outcome arrived. If replay-only, calibration cannot be built on them |

## 5. Prior art — what this must beat

| source | the bar |
|---|---|
| ⚑ **Dec-POMDP / I-POMDP** | The gate the *general* programme had to clear. Three genuine expressivity gaps survived |
| ⚑ **The pivot changed the opponent** | An agent-loop representation must beat **TypeScript plus a prose prompt** — which has no goal representation, no uncertainty, no calibration and no authority model. Not a lower bar dishonestly chosen; the actual competition in the actual domain |
| ✎ **MCP, A2A, LangGraph, CrewAI, AG2** | All about *connection*. None about whether the loop is any good. You can write a valid LangGraph containing no estimand at all |

## 6. Methodology borrowed from elsewhere

| source | what was taken |
|---|---|
| ⚑ **t-minus P5** — cross-provider beats same-model reruns | Two runs of one model share a prior and agree for reasons unrelated to determinacy. Same-model figures may be reported but never enter a score |
| ⚑ **The capability sweep** (`BRIEFING-2026-07-31.md` §4) | *A strong model given a suggestive format supplies the determinacy the format lacks.* **Measure the slope, not the value. Flat is what you want.** Applied to compilation: 0.898 at 8B → 0.993 at frontier |
| ⚑ **Pre-registration**, after the archive study | Four of five predictions failed there and the failure was the useful part. Both studies here are pre-registered with stated kill conditions |
| ⚑ **Toyota's A3** | One sheet, readable by someone not involved. Why the IR is flat rather than nested |
| ⚑ **ElectricSQL's adoption posture** — *"adopt incrementally, one route at a time… greenfield and brownfield"* | Why the primary verb is **lint**, not **author**. Every general-representation project in the corpus that required wholesale adoption lost |

## 7. The strongest threats, collected

Kept together because they are easy to lose in the detail.

1. ⚠ **Evals may subsume structural linting.** The field measures outcomes; this project reads
   structure. Under test in `PREREG_EVALS.md`. The counter — *an eval is itself an estimator
   and nothing calibrates it* — is the load-bearing claim.
2. ⚠ **Frameworks may absorb it.** LangGraph already has nodes, edges and explicit state.
   "What does this node estimate" is a plausible feature rather than a product.
3. ⚠ **Vitamin, not painkiller.** An uncalibrated belief costs nothing today.
4. ⚠ **The encoding-bias problem, repeatedly demonstrated.** Two checks survived independent
   encoding at 5/5; every other check measured the encoder as much as the corpus.
5. ⚠ **Target knowledge, not format legibility, is the compile bottleneck** — 18% → 100% on
   Flue once one page of API travelled with the spec.
