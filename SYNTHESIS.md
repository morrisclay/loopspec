# Where the field is, and what this can contribute

The argument in one place. Everything here is either **measured** — with the corpus, n, and
the agreement check stated — or marked as an assertion.

Underlying work: `research/published_study/` (two pre-registered studies),
`research/llm_as_compiler.md`, `research/syntax_study/`, `REFERENCES.md`.

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

### 1.2 Verification is built. Calibration has no name.

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

### 1.4 Every reference example has the two core defects

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

### 1.6 Budgets exist. Regulation against them does not.

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

---

## Part 2 — What this project can contribute

### 2.1 The vocabulary. This is the whole thesis.

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

### 2.3 Theorem-grounded necessary conditions

Where a check follows from a proved result it is not a style opinion:

- **Conant & Ashby 1970** — every good regulator must be a model of the system → a loop with a
  target and no model is a *reflex*. **100% of reference examples.**
- **Kalman** — observability, controllability → a target nothing can drive is a wish.
- **Forrester/Sterman** — loop polarity → a reinforcing loop with no balancer diverges.

The pitch changes with it: not *"here are things I noticed"* but *"your loop violates the Good
Regulator theorem, and here is the line."*

### 2.4 One idea that goes beyond its source

The field has budgets, step ceilings and stall detection. The question after it:

> **A ceiling is a stop, not a correction.**

A loop that runs at full rate into a wall and halts has not regulated anything — it has been
**truncated**. Ashby's point about variety is exactly this: a stop absorbs no disturbance. The
halt is indistinguishable from failure and arrives without warning.

*Known limit:* the check clears as soon as any rule reads the resource, and does not
distinguish **reading-to-halt** from **reading-to-adapt**. A clear result means *something
watches the budget* — necessary, not sufficient.

### 2.5 A format any LLM compiles

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

1. **Only two checks are robust to who encodes.** `belief_never_checked` and
   `regulator_without_model` agreed 5/5 with an independent encoder. Every other check agreed
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

## In one sentence

The field can tell you **that** your agent failed, and increasingly **how much**. This can tell
you that **your agent cannot know whether it is failing** — before it runs. That turns out to
be true of 100% of the reference examples, and of 100% of the eval harnesses built to catch it.
