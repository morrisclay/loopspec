# Cookbook — the common loop shapes, and what each one costs

Every shape here is taken from a published reference implementation, encoded in
`research/published_study/encodings/` and linted. The findings quoted are real.

**These are not bugs.** Each shape has a *structural* property that follows from its design.
Reflection cannot ground itself; that is what reflection is. The value of naming it is that you
can then decide whether it matters for your case — and add the one line that fixes it if it
does.

---

## 1. Reflection — generate, critique, repeat

**Reach for it when:** output quality improves with a second look and you have no external
scorer.

```yaml
loop: reflection
runs: per_iteration

goal:
  essay_quality: { keep: "good enough to stop revising" }

beliefs:
  essay_quality:
    question: "Is this any good?"
    from: [critique]
    how: judgement

observes:
  critique:
    informs: essay_quality
    origin: ourselves        # ← the critic is inside the loop
    how: reported
    produced_by: reflect

actions:
  generate: { moves: essay_quality, can_undo: yes }
  reflect:  { moves: essay_quality, can_undo: yes }

spends:
  messages: { limit: "N messages", spent_by: [generate, reflect] }
```

**What it costs you:**

> **`no_exogenous_grounding`** — every observation is produced by an act inside this group.
> Nothing it observes can surprise it, so it converges on agreement rather than on truth.

The critic and the generator are the same model with different prompts. A reflection loop
polishes; it does not verify. If the first draft is confidently wrong in a way the critic
shares, iterating makes it more confident and no more right.

**The one line that fixes it:** add any observation with `origin: outside`. Even a weak
external signal changes the shape entirely — which is exactly what the next pattern is.

---

## 2. Reflexion — reflection plus tools

**Reach for it when:** you can check claims against something outside the model.

The same shape with one addition:

```yaml
observes:
  search_results:
    informs: answer_quality
    origin: outside          # ← the difference
    how: measured
  self_critique:
    informs: answer_quality
    origin: ourselves
    how: reported
    produced_by: draft
```

**What it costs you:**

> **`single_point_of_grounding`** — reads 2 observations and exactly one comes from outside
> itself. The loop is exactly as trustworthy as that one input.

**Reflection and reflexion differ in exactly one column of `tools/compare.py`, and that column
is the entire argument between them.** That is the clearest demonstration in this repo of why
a notation is worth having: the difference was always there and there was no way to say it.

---

## 3. LLM-as-judge — generate, score, loop until pass

**Reach for it when:** you want a numeric gate on output quality.

Structurally identical to reflection, and it inherits the same cost — the judge is inside the
loop. Two things specific to it are worth naming, because both appear in the OpenAI SDK's own
example:

```yaml
beliefs:
  outline_quality:
    from: [evaluator_feedback]
    how: judgement
    # no checked_by — nothing scores the JUDGE
```

- *"Never give it a pass on the first try"* in the evaluator's instructions is a **prompt-level
  hack standing in for a missing calibration**. It forces a behaviour rather than measuring
  one.
- *"After 5 attempts you can give it a pass"* is a **ceiling, not a correction**. The loop stops
  because it ran out, not because it succeeded.

**What it costs you:** `belief_never_checked` — and this is the one that generalises furthest.
**Every eval harness examined has the same shape**, which is why the layer built to catch this
defect has it: 4 of 4.

**The one line that fixes it:** `checked_by:` naming what compares the judge's verdicts to a
human's on a sample. That is the whole of judge-human agreement, and it is discussed in the
documentation of every eval framework and present in none of their runnable examples.

---

## 4. Plan-and-execute — plan, do a step, replan

**Reach for it when:** the task decomposes and steps take real time.

```yaml
goal:
  objective_met: { keep: "the replanner returns a final response" }
beliefs:
  objective_met:
    question: "Have the remaining steps become unnecessary?"
    from: [step_results]
    how: judgement
observes:
  step_results: { informs: objective_met, origin: outside, how: measured }
```

**What it costs you:** `regulator_without_model`. The loop steers toward *objective met* and
has no model of what produces it — it re-plans by asking the model to look at the transcript
again. That is a reflex against a setpoint. It corrects, and it cannot anticipate.

**Worth knowing:** in the LangGraph example this is bounded only by `recursion_limit`,
LangGraph's **default of 25**. That is a platform backstop, not a choice — an undeclared budget
is still a budget, just one nobody chose.

---

## 5. Self-RAG — retrieve, grade, generate, grade again

**Reach for it when:** retrieval quality varies and hallucination is the failure you fear.

The most instrumented shape in the corpus. Three separate graders:

```yaml
beliefs:
  document_relevance: { from: [retrieved_docs], how: judgement }   # retrieval_grader
  answer_grounded:    { from: [generation], how: judgement }       # hallucination_grader
  answer_useful:      { from: [generation], how: judgement }       # answer_grader
```

**What it costs you:** `belief_never_checked` on **all three**. This is the important lesson in
the cookbook — *more graders is not more calibration.* Three unscored judges are three
opportunities to be confidently wrong, not a triangulation.

Adding graders improves **verification**. Only `checked_by` improves **calibration**. They are
different axes and the distinction is worth internalising before you add a fourth grader.

---

## 6. Tree search — expand, score, expand the best

**Reach for it when:** the solution space branches and a partial answer can be ranked.

**What it costs you:** the scorer steering the entire search is itself unscored — and in the
published LATS example, **no depth ceiling at all**. An unbounded tree search whose ranking
function nothing validates.

```yaml
spends:
  expansions:
    limit: "25 nodes"
    spent_by: [expand]
```

If you write one line from this whole document, make it that one.

---

## 7. Orchestrator / worker / verifier — the multi-agent shape

**Reach for it when:** a task splits and you want an independent check.

Loops in one file, separated by `---`. **Names resolve across the file**, which is what makes
them a group:

```yaml
loop: worker
beliefs:
  claim_truth: { from: [web_search], how: judgement }
observes:
  web_search: { informs: claim_truth, origin: outside, how: measured }
---
loop: verifier
beliefs:
  claim_truth:                      # THE SAME quantity
    from: [worker_report]           # and its only input is the worker's output
    how: judgement
observes:
  worker_report:
    informs: claim_truth
    origin: ourselves
    produced_by: emit_report
```

**What it costs you, and this is the shape that fails hardest:**

> **`shared_estimand_no_arbiter`** — two estimators, no policy reads it. When they disagree
> nothing reconciles them, so the value that survives is whichever wrote last.
>
> **`no_exogenous_grounding` on the verifier** — its only input is the thing it is verifying. A
> verifier that cannot be surprised converges on agreement, not truth.

**The two lines that fix it:** give the verifier its own `origin: outside` observation, and have
a rule in `when:` read the shared quantity so disagreement resolves by decision rather than by
arrival order.

---

## 8. The autonomous work loop — Ralph

**Reach for it when:** you have a strong test suite and a long task.

```yaml
observes:
  files_and_git:
    informs: task_actually_done
    origin: ourselves        # the agent reads its own past work
    how: reported            # and this is its own account of it
  test_results:
    informs: task_actually_done
    origin: outside          # THE ONLY thing that can fail unintended
    how: measured
```

**What it costs you:**

> **`single_point_of_grounding`** — reads 2 observations, exactly one from outside. The loop is
> exactly as trustworthy as that one input.

That is the whole of Ralph, stated structurally. **With a strong suite it is a genuine
regulator; without one it is sealed and can iterate indefinitely on its own output before
declaring victory.** Not a criticism — it is excellent *operational* loop engineering, and
knowing which part is load-bearing tells you when to trust it.

**Note the two-axis provenance doing real work.** `files_and_git` is `ourselves` **and**
`reported` — the agent's own account of its own work. A single provenance field cannot say
that, and it is the exact shape of the failure.

---

## 9. Sourcing — the one that scores its own source

**Reach for it when:** you are searching channels and some are duds.

The only loop in the entire corpus that calibrates **attention** rather than only conclusions:

```yaml
beliefs:
  candidate_quality:
    how: rubric
    checked_by: viability_review     # retires a channel that finds nothing
    every: trial_window_7d
```

`viability_review` scores the **source**, not the candidate — *was this channel worth
searching?* Every other loop here, if it scores anything, scores its own judgements.

**This is the shape to copy.** It is the concrete form of the attention half, and it was
flagged as "unusual" in this repo before anyone had a word for what made it unusual.

---

## Quick reference

| shape | structural cost | the one line |
|---|---|---|
| reflection | no exogenous grounding | any `origin: outside` observation |
| reflexion | single point of grounding | know what that point is |
| llm-as-judge | judge nothing scores | `checked_by:` on the judge |
| plan-execute | reflex, not a regulator | `explains:` on the belief |
| self-RAG | 3 unscored graders | `checked_by:`, not a 4th grader |
| tree search | unbounded, unscored ranker | `spends:` with a limit |
| orchestrator/verifier | last writer wins | a rule reading the shared quantity |
| Ralph | one point of grounding | keep the tests strong |
| sourcing | *none — copy this one* | — |

**None of these shapes is wrong.** Each buys something and costs something, and the cost is
usually invisible until it is written down. That is the entire proposition.
