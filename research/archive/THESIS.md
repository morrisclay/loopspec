# Thesis — a loop design layer above agent frameworks

> [!NOTE]
> **Research thesis snapshot.** Several claims and finding names in this document were corrected
> by later encodings and adjudication. It is preserved as argument history. Current product and
> evidence claims live in the product [`README`](../../README.md), current
> [`SYNTHESIS`](../SYNTHESIS.md), and [`research index`](../README.md).

**An abstraction over agent frameworks for cybernetic loop design. Machine-writable,
human-readable, diagram-native. The linter is the product.**

---

## 1. The space is empty, and for a specific reason

The 2026 standards landscape is **interoperability**, not design:

- **MCP** — how an agent reaches a tool
- **A2A** — how an agent reaches another agent (150+ organisations)
- **LangGraph** — nodes and edges with explicit state
- **CrewAI** — roles, goals, backstory; the framework infers coordination
- **AG2** — event-driven core, GroupChat

Every one is about **connection**. None is about whether the loop is any good.

### Control-flow graph ≠ control-loop graph

LangGraph is the closest existing thing, and the distinction matters:

| LangGraph | what a loop needs |
|---|---|
| node A → node B → conditional → node C | what quantity are you trying to know? |
| explicit *state* | what signal measures it? |
| transitions and conditions | what target are you regulating toward? |
| checkpoints | what closes the loop, on what cadence? |
| | what scores the estimator? |

**You can write a perfectly valid LangGraph that contains no estimand at all.** It will run,
check out, deploy — and be a flowchart with a model in it rather than a regulator.

That is the wedge, and it is orthogonal to MCP and A2A rather than competing with them. This
layer sits above all of them and compiles down.

## 1b. "Loop engineering" already exists — and means something else

The term is taken. June 2026, a post reaching 6.5M views: *"Stop prompting your AI agent.
Start designing the loop that prompts it for you."* Ralph Wiggum loops, harness engineering,
context-rot management. Gergely Orosz is publicly sceptical of the market: *"outside of the
increasingly few people who have unlimited AI token budgets… I don't think many have a use
case."*

**That is OPERATIONAL loop engineering: how to keep an agent iterating productively.**

This thesis is about something orthogonal — **whether the loop is a regulator at all.** Same
distinction as control-flow versus control-loop, one level up:

| operational loop engineering | cybernetic loop design |
|---|---|
| how do I avoid context rot? | what quantity is this loop regulating? |
| how do I keep it iterating? | what signal measures it? |
| how do I allocate context per turn? | what scores the estimator? |
| when does it stop? | is the stop condition self-assessed? |

Orosz's scepticism targets the operational version and is probably right about it. The
epistemic version has a different audience: **anyone whose agent confidently does the wrong
thing**, which is not a token-budget problem.

### Worked example: linting the Ralph Wiggum loop

Ralph is the canonical loop-engineering artifact — a `while true` feeding the same prompt back
until the agent emits a completion promise. Encoded and linted cold, it produces:

- **`orphan_signal: files_and_git`** — the loop's *primary* signal is its own modified files
  and git history, and that signal is connected to no estimand. Reading your own diff does not
  tell you whether the task is done.
- **`uncalibrated_estimator: self_assessment`** — the agent decides it is finished and nothing
  scores that judgement.
- The completion promise is a **self-assessed** DesiredCondition, and `max-iterations` is a
  hard ceiling rather than a correction.

**Correction, from re-encoding Ralph in the authoring format** (`examples/field/`): the
`orphan_signal` above was an encoding gap, and the claim below was nearly stated wrongly. An
earlier graph encoding had Ralph tripping `no_exogenous_grounding` — *nothing outside reaches
it* — which is false. Ralph reads test results, which are exogenous. The firing was an
artifact of the graph naming only one of Ralph's two signals. The property is real but
narrower, and is now a derived check (`single_point_of_grounding`) rather than a description:

> **Ralph is grounded only through the test signal.** Tests are the sole exogenous input — the
> one thing that can fail in a way the agent did not intend. Everything else in the loop is
> produced by the loop. With a strong test suite Ralph is a genuine regulator; without one it
> is epistemically closed and can iterate indefinitely on its own output before declaring
> victory.

That matches what practitioners report, and it is now **literally derived from the loop's
shape** — the linter emits it from `examples/field/ralph.loop.yaml` without being told. That
is precisely what this layer is supposed to do, and it took a wrong version first.

It is not a criticism of Ralph. Ralph is excellent *operational* loop engineering. It is a poor
*cybernetic* loop, and knowing which parts are which tells you when to trust it.

Independent convergence worth noting: there is already academic work — *"Supervising Ralph
Wiggum: a Metacognitive Co-Regulation Agentic AI Loop"* — adding a regulation layer to exactly
this technique. Someone else reached the same gap from the other direction.

## 2. "People are not good at loop engineering" — the evidence so far

The assumption is testable and partially tested.

**Four loops examined, all by capable authors:**

| loop | defect found |
|---|---|
| `/complicate` conviction engine | estimator never scored; loop produces its own evidence |
| Deal Steward | readiness rule never scored against whether deals advanced |
| conviction-termination | stop rule reads *expected information gain*; nothing computes it |
| Customer Acquisition spec | 2 estimands tracked by nothing; 3 signals + 2 interventions and no loop closing between them |
| Ralph Wiggum loop | primary signal measures nothing; self-assessed termination; estimator unscored |

**The strongest single fact: THREE independent loops — different authors, different purposes,
one of them a widely-adopted public technique — all have an estimator nothing scores.** `/complicate` never asks whether hypotheses resolved
correctly. The Steward never asks whether proposed deals advanced. Ralph never asks whether it
was right to declare itself done. None of these authors is careless — the t-minus specs are
unusually rigorous, with ADRs, feature files and ratified rules, and Ralph is a deliberate,
widely-copied design.

That is what the assumption predicts: this is not a carefulness problem, it is a **vocabulary**
problem. You do not check for a defect you have no word for.

**Honest counterweight:** on someone else's system the linter ran ~4 useful findings out of 14,
with ten traceable to my own encoding errors. It is reliable as a completeness checker (14/14)
and unproven as a design critic.

## 3. Three design consequences

### (a) It must read existing loops, not only generate new ones

The strongest adoption evidence in this repo is ElectricSQL's shift to *"adopt incrementally,
one route at a time… greenfield **and brownfield**"*. Every general representation project in
the corpus that required wholesale adoption lost.

So the primary verb is **lint**, not **author**: point it at a LangGraph app or a Flue agent
that already exists and get findings. Requiring the spec to be written first reintroduces the
wholesale-adoption problem that killed the general programme.

Authoring is the second use, not the first.

### (b) Framework-agnostic changes what the IR may assume

The Flue mapping is instructive precisely because it is **incomplete**: four primitives —
`Calibration`, `Resource`, `DesiredCondition` as anything but prose, and uncertainty — have no
Flue construct. That is evidence the IR is not Flue-shaped. It should stay that way: Flue,
LangGraph, CrewAI and AG2 become compile targets, and what fails to compile in each is
*reported*, not hidden.

A target's gaps are information about the target.

### (c) Diagram-native is already satisfied, and constrains the IR

The canonical form is a **flat typed graph of nodes and edges** — literally diagram-shaped.
That was adopted for determinacy reasons and happens to be exactly right here.

Three projections over one IR: flat graph for tooling, loop-centric form for authoring,
diagram for reasoning. Keeping the IR flat is what makes the diagram derivable rather than
drawn.

## 4. The wedge problem, stated plainly

**Nobody searches for a cybernetic loop linter.** The checks have to map onto symptoms people
already feel:

| check | felt symptom |
|---|---|
| uncalibrated estimator | *"my agent's confidence doesn't track reality"* |
| policy on unmeasured inputs | *"it decides on things it can't actually see"* |
| no loop closed | *"it doesn't respond to what it observes"* |
| endogenous signal | *"it confirms its own beliefs"* |
| estimand never estimated | *"it claims to track things it doesn't"* |
| no delay declared | *"it thrashes"* |
| no revision path | *"it can't tell me it was wrong about the wrong thing"* |

Right-hand column is the marketing and the left is the mechanism. If a check has no felt
symptom it is probably not worth shipping.

## 5. The study that would validate the thesis

Four loops is not evidence of a general defect rate. The runnable version:

> **Lint 20–30 published agent examples** — LangGraph tutorials, CrewAI templates, AG2
> samples, Flue quickstarts. These are written by framework authors to demonstrate best
> practice. If the same defects appear at high rates *in the reference implementations*, the
> thesis is established on public, checkable artifacts.

Pre-register the expected rates first, as with the archive study — where four of five
pre-registered predictions failed and the failure was the useful part.

Two outcomes, both worth having:

- **High defect rate in reference examples** — the thesis holds, publicly demonstrable, and
  the examples become the demo.
- **Low rate** — either practitioners are better at this than assumed, or the checks encode a
  standard nobody needs. Both are worth knowing before building.

## 6. Where this could fail

- **Vitamin, not painkiller.** The defects are real but slow-acting. An uncalibrated estimator
  costs you nothing today. Section 4 is the mitigation and it is unproven.
- **The 4/14 rate.** On someone else's system most findings were my encoding errors. If that
  ratio holds when reading real code, the signal drowns.
- **Frameworks may absorb it.** LangGraph already has nodes, edges and explicit state; adding
  "what does this node estimate" is a plausible feature rather than a product.
- **One validated data point.** Everything human-validated here is 2 of 4 claims on one loop,
  judged by its author. The general programme died of exactly that at n=19.
