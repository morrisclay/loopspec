# Where the field is, and what this can contribute

The argument in one place. Everything here is either **measured** — with the corpus, n, and
the agreement check stated — or marked as an assertion.

Underlying work: `research/published_study/` (two pre-registered studies),
`research/llm_as_compiler.md`, `research/syntax_study/`, `REFERENCES.md`.

---

## Part 0 — The frame: attention and calibration as meta-control

The contribution is **a simple YAML for describing and arguing about loops** — applied
cybernetics, aimed at two concerns underrepresented in the sampled agent-loop specifications.
The linter is a consumer of that notation, not the point, and that distinction changes what a
wrong check costs.

Every framework builds the **operating** loop: observe, believe, decide, act. The sampled
reference loops rarely make the loops *about* observing and believing explicit:

| | **attention** (`ATTENTION.md`) | **calibration** (`CALIBRATION.md`) |
|---|---|---|
| side | the input — what enters | the output — what came out |
| asks | *am I looking at the right things?* | *is what I concluded true?* |
| scores | a **signal** | an **estimator** |
| absent → | paying for information that changes nothing | confidently wrong forever |
| measured | nothing had ever scored a signal (§2.4) | **10/10**, and **4/4** in the eval layer (§1.3, §1.4) |

They are duals. **Calibration is how you find out whether your attention was well spent**; and
attention determines what you can calibrate against, since a belief about something you never
observe has no outcome to be scored on.

These are meta-control mechanisms: they make parts of the observer's performance checkable.
They do not yet constitute a full second-order account. LoopSpec now records who draws the
boundary, which purpose organizes observation, and what is placed inside and outside; it does
not represent how observing changes the system or how those distinctions are revised.
*Applied cybernetics* is accurate; an unqualified second-order claim is not.

Attention itself operates at three levels, worked out in `ATTENTION.md`:

| level | the claim | where the evidence is |
|---|---|---|
| **L1 — the author's attention** | *a field is a place you have to look.* "You do not check for a defect you have no word for" is an **attention** claim, not a knowledge claim | §1.2, §1.4, §2.1 |
| **L2 — the loop's attention** | what it observes, at what cost, from where. The measured baseline scored estimators and never signals; the current format adds an attention-review contract with a value metric, window, and attention-changing response | §1.6, §2.4 |
| **L3 — the humans' attention** | who must look at what, and who pays when it is wrong. O'Reilly names the gap and leaves it: **the human oversight loop at the top of its taxonomy has no exit condition** | §1.8 |

Nobody building agent loops is *ignorant* of calibration. Three careful authors of three real
systems each shipped an estimator nothing scores, and the framework authors' own reference
examples do it 10 out of 10. **These are not people who lack the concept.** They are people
whose tooling never pointed at it.

**Why the frame changes the pitch.** *A linter that finds defects* invites the fair reply —
my evals already tell me when it fails. *A notation for arguing about loops, which happens to
make some defects visible by construction* does not, and it survives its own limitations:

> **A linter that is wrong is a bad product. A notation that is wrong is still useful, because
> you can say precisely what you disagree with.**

That is the right posture given Part 3: only two of these checks survived independent
encoding.

---

## Part 1 — What the field looks like, measured

### 1.1 It converged on taxonomy, not quality

Three canonical statements, all mid-2026, all describing loops as **nested levels**:

| source | the levels |
|---|---|
| swyx, *Loopcraft* (AIEWF keynote) | token → chat → agent turn → goal → automation → software factory |
| LangChain, *The Art of Loop Engineering* | agent → verification → event-driven → hill-climbing |
| O'Reilly Radar, *What the Hell Is a Loop, Anyway?* | execution → task → product → system |

They agree substantially, which is a real convergence and worth respecting. **None of them
says how to tell a good loop from a bad one.** O'Reilly's, asked directly, does not discuss
design quality, calibration, confidence tracking, irreversible-action safeguards, approval
gates, or what quantity the loop is regulating.

The field settled *what a loop is* before settling *whether a given one works*. That ordering
is normal for a young field and it leaves a specific hole.

### 1.2 Verification is built. Calibration has no name. *(L1)*

> **Verification** asks *is this output good?* — grade the artifact in front of you.
> **Calibration** asks *has this thing's confidence historically tracked reality?* — score past
> predictions against what happened.

LangChain's post has a verification loop — a rubric grader that fails a run and sends it back —
and human touchpoints before sensitive tool calls. It has **no discussion of confidence
calibration or whether agent confidence aligns with correctness.**

An agent that is verified but uncalibrated passes every rubric and still cannot tell you how
much to trust it *next* time. This is the single most important gap in this document, and the
one everything else follows from.

### 1.3 The eval layer trips the check it exists to catch

**Measured:** 4 framework-authored LLM-as-judge implementations, read as source — DeepEval
`g_eval`, DeepEval `agent_loop_detection`, Braintrust `LLMClassifier`, Ragas `AspectCritic`.
`agent_loop_detection` was included deliberately as the fairest possible test: it is the
closest thing in the eval ecosystem to a structural check on loops.

**Result: 4/4 have a judge that nothing scores. Confirmed 4/4 by an independent encoder**
given only the raw source and the format reference, with no sight of this project — none of
its four specs declares `checked_by`.

The pre-registered hedge failed and its failure is the finding: I predicted **40%** would
calibrate against human labels. Actual **0%**. Judge-human agreement is discussed in these
projects' documentation and absent from every runnable implementation examined.

**Partial refutation, reported as pre-registered:** G-Eval's *method* was validated against
human judgments in its originating paper. But `criteria` is arbitrary free text and the
validator checks only that one of `criteria`/`evaluation_steps` is *present*.

> A judge validated for one rubric, deployed with another, is not a validated judge. The
> paper's correlation does not travel with the class.

**Correction I had to make to myself:** my first pass encoded all four identically, which meant
I had used a template. Braintrust's `_run_eval(output, expected)` receives human-authored
ground truth, and I had omitted it — making a finding land in my own favour. Corrected, it
shows `single_point_of_grounding` instead, which *sharpens* the claim: **grounding the input is
not calibrating the judge.**

### 1.4 Every reference example has the two core defects *(L1)*

**Measured:** 10 loops from LangGraph tutorials, the OpenAI Agents SDK, and CrewAI flows —
written by framework authors to demonstrate best practice, which makes this the least
favourable possible sample for the thesis.

> **10/10 form a belief by LLM judgement that nothing ever scores against outcomes.**
> **10/10 steer toward a condition with no model of what produces it.**

**These are the only two checks that survived independent encoding at 5/5.** That is the
strongest claim in this project and it is deliberately narrow.

This is not a claim that these examples are bad. A tutorial demonstrating reflection is not
obliged to ship calibration. It is a claim that **the vocabulary is missing**: there is nowhere
in any of these frameworks to say *"and this is what checks whether the critic was right."*

### 1.5 "Agent patterns" are mostly not loops

Applying the pre-registered exclusion — *a one-shot chain is not a loop* — removed most of the
OpenAI SDK's canonical `agent_patterns` directory. `routing`, `parallelization`,
`deterministic`, `agents_as_tools` and both guardrail examples run **once**. Only
`llm_as_a_judge` has a repeated cycle toward a condition.

Consistent with §1.1: the field's vocabulary is about **composition**, not regulation.

### 1.6 Budgets exist. Regulation against them does not. *(L2)*

**Measured**, after correcting an encoding artifact that had produced a meaningless 14/14:

| corpus | n | result |
|---|---|---|
| published agent loops | 10 | ceiling nothing reads **5**, no ceiling at all 4, clean 1 |
| eval harnesses | 4 | unbounded **4/4** |
| field loops | 4 | unbounded 3, spends-without-limit 1 |

**Half the published loops have a ceiling nothing reads.** Four have none at all — including
`lats`, an unbounded *tree search*. Four LangGraph examples are bounded only by
`recursion_limit`, the framework's **default of 25**: a platform backstop, not a choice the
example made.

### 1.7 Practitioners name the gap without a way to check it

O'Reilly's piece, on a failure it identifies and does not resolve:

> *"a loop without its signal doesn't converge. It just runs until something external stops
> it."*

That is `no_loop_closed` and `orphan_signal`, arrived at independently, in prose. And three
independent real systems — different authors, one a widely-copied public technique — each had
an estimator nothing scores. None of those authors is careless. **That is what a vocabulary
problem looks like from the inside.**

### 1.8 No published example names a human at all *(L3)*

**Measured:** `no_human_at_all` fires on **10/10** published reference examples. Not one names
a person who approves anything, is escalated to, or is recorded as bearing the cost when the
loop is wrong.

Two caveats keep this honest. First, these are tutorials, and a tutorial demonstrating
reflection is not obliged to wire an approval flow — so this is weak evidence about production
systems and strong evidence about what the *reference material* teaches. Second, and more
seriously, **this check is encoder-dependent**: my encodings said `people: {}` where an
independent encoder inferred an implied user, and the two disagreed 3 of 5 times. It is
reported here as a *pattern*, not as a rate that would survive the bar §1.4 clears.

What survives regardless is the structural point. Both encoders then flagged missing
oversight — they simply disagreed about which check should say so. **Attention is assumed by
this material and never allocated**, and that is the level at which swyx stacks six loops with
a human at the top of all of them and nobody says what that costs.

---

## Part 2 — What this project can contribute

### 2.1 The vocabulary. This is the whole thesis. *(L1)*

*You do not check for a defect you have no word for.* Three words the field lacks:

| word | what it lets you say | why nothing else can |
|---|---|---|
| **`checked_by`** | *this is what scores the belief against what happened* | frameworks have verification; calibration has no construct |
| **`can_undo` / `needs_approval`** | *what may this thing do without approval, and irreversibly* | the question every deployment turns on, represented by no framework |
| **`origin` × `how`** | *this observation is ours AND is a claim, not a measurement* | **everyone collapses these** — including three independent blind designers and me |

The two-axis provenance is the subtlest and the one I would defend hardest.
`origin: ourselves` + `how: reported` is **an agent grading its own homework**, and a single
provenance axis cannot express it. That shape is the Ralph failure mode, the self-critique
failure mode, and the LLM-as-judge failure mode, all at once.

### 2.2 Checks that run before deployment

Evals require the failure to have already happened. A structural check reads the spec and
catches an irreversible ungated act while it is still cheap. The two mechanisms are
complementary and this project should stop implying otherwise.

### 2.3 Theory-inspired checks with explicit limits

Cybernetics supplies the questions, while LoopSpec v1 supplies only structural evidence:

- **Conant & Ashby 1970** motivates asking where a process model is represented.
  `no_explicit_process_model` says no `explains` relation is encoded; it does not test the
  theorem's optimal-regulation assumptions or regulator↔system mapping.
- **Kalman** clarifies why sensing and actuation matter. `unmeasured_estimand` and
  `target_without_actuator` check declarations, not state-space observability/controllability.
- **Forrester/Sterman** clarifies polarity. LoopSpec records an intervention's intended effect
  direction but not signed influence around a complete cycle, so
  `endogenous_feedback_without_crosscheck` reports provenance rather than divergence.

This narrower pitch is stronger: every message names the evidence it actually has, and the
tool stays quiet about dynamic guarantees it cannot calculate.

### 2.4 Scoring the looking, not just the conclusion *(L2 — the newest, and least proven)*

The baseline asymmetry that was invisible until it was named: **every `Calibration` in this
project scored an `Estimator`. Nothing scored a `Signal`.** The current language responds with
a distinct attention contract; the statement remains a finding about the measured baseline,
not the current expressiveness of the format.

Three instances were already in the corpus from three authors — this project's own bar — and
one of them had been flagged as *"unusual"* and *"the shape to copy"* before it had a name:

- `meeseeks_sourcing` — `viability_review` **retires a channel that finds nothing**. It scores
  the source, not the candidate.
- `conviction_termination` — the stop rule reads `expected_info_gain`, *is more looking worth
  it?*, and nothing computes it.
- `customer_acquisition` — a `cost: high` source nothing reviews.

`observes.*.checked_by` makes it first-class, and `informs_no_decision` is the sharp check:
sharper than `orphan_signal`, which catches a signal informing *nothing*, this catches a signal
informing a belief **no rule reads**. The loop is not wrong about anything. It is spending
attention it will not get back.

**This is value-of-information, which decision theory has had for decades and agent frameworks
have not.** Calibrating the estimator tells you how much to trust the answer; calibrating the
signal tells you whether the question was worth asking.

**Honest rate: 1 of 10 published examples.** Motivated by three real instances and **not yet
evidenced at rate.** Included here as a contribution *claim*, not a finding.

### 2.5 One idea that goes beyond its source

The field has budgets, step ceilings and stall detection. The question after it:

> **A ceiling is a stop, not a correction.**

A loop that runs at full rate into a wall and halts has been **truncated**, not corrected. A
ceiling is a constraint; it is not by itself a policy that changes behaviour as resources run
low. This is a structural runtime distinction, not an Ashby requisite-variety result.

*Known limit:* the check clears as soon as any rule reads the resource, and does not
distinguish **reading-to-halt** from **reading-to-adapt**. A clear result means *something
watches the budget* — necessary, not sufficient.

### 2.6 A format any LLM compiles

**Measured:** 8 models × 3 targets, each given only the spec file and a target name.

| tier | fidelity |
|---|---|
| very weak (8B) | 0.898 |
| frontier | 0.993 |

**Nearly flat across two orders of magnitude of capability** — which is the result to want,
since a format needing a frontier model is one whose determinacy the reader is supplying.

And plain words are **harder to lose**: the irreversible ungated act was silently dropped in
4/20 compilations as `reversibility: irreversible`, and 1/21 as `can_undo: no`.

The naming came from a blind test, not taste: three models designed the syntax from scratch
without seeing this one, and **3/3 rejected every jargon word** (`regulates`→`goal`,
`estimates`→`beliefs`, `calibrated_by`→`checked_by`, `measures`→`informs`, `acts`→`actions`).

---

## Part 3 — What this cannot claim

Stated plainly, because the value of the above depends on it.

1. **Only two historical checks were robust to who encodes.** `belief_never_checked` and the
   check then named `regulator_without_model` agreed 5/5 with an independent encoder. The
   current, narrower name is `no_explicit_process_model`. Every other check agreed
   2–3/5 and **is not reported as a rate**. That is the honest ceiling on current evidence.

2. **The encoding-bias problem recurred three times, and each time the first result flattered
   the thesis.** A goal/belief name collision suppressed the headline check to 20%; a naive
   tokeniser reported a defect at 100% that was my prose style; a missing format key produced a
   meaningless 14/14. All three were caught, but the pattern is structural to the method, not
   bad luck. **Fixing an instrument after seeing a result is the shape of motivated reasoning
   whether or not it is motivated reasoning** — which is why every study here has an
   independent-encoder check with a pre-registered kill condition.

3. **Vitamin, not painkiller.** An uncalibrated belief costs nothing today. The felt-symptom
   framing is the mitigation and it is unproven.

4. **Frameworks may absorb it.** LangGraph already has nodes, edges and explicit state.
   "What does this node estimate" is a plausible feature, not a company.

5. **Target knowledge, not format legibility, is the compile bottleneck.** Flue compiled to its
   real API 18% of the time; with one page of API alongside the spec, **100%**. The format was
   never the constraint, and the original write-up said otherwise until this was measured.

6. **n is small everywhere.** 10 published loops, 4 eval harnesses, 4 field loops, 1 spec in
   the compile study, one independent encoder throughout.

---

## The artifact that makes the frame concrete

`tools/compare.py` — ten published loops from three frameworks, side by side, generated from
their specs:

| loop | scored | exogenous input | ceiling | humans |
|---|---|---|---|---|
| `langgraph_reflection` | 0/1 ✗ | none (1 own) | messages | none ✗ |
| `langgraph_reflexion` | 0/1 ✗ | 1 of 2 | none ✗ | none ✗ |
| `langgraph_self_rag` | 0/3 ✗ | 1 of 2 | none ✗ | none ✗ |
| `openai_llm_as_a_judge` | 0/1 ✗ | none (1 own) | rounds | none ✗ |
| `crewai_self_evaluation` | 0/1 ✗ | none (1 own) | retries | none ✗ |

Nobody could previously put LangGraph's reflection tutorial next to CrewAI's self-evaluation
flow and say precisely what differs — not because it is hard, but because there was no shared
form to say it in. **Reflection and reflexion differ in exactly one column, and that column is
the whole argument between them.**

You cannot diff two blog posts. You can diff two specs.

## In one sentence

The field can tell you **that** your agent failed, and increasingly **how much**. This can tell
you that **your agent cannot know whether it is failing** — before it runs. That turns out to
be true of 100% of the reference examples, and of 100% of the eval harnesses built to catch it.
