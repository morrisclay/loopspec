# Pre-registration — do evals subsume the need for structural linting?

**Written before fetching any eval harness.** Second pre-registration; same discipline.

## The objection this tests

The field's answer to loop quality is **evals and traces**: measure outcomes in production,
feed them back. It is powerful and it is the honest threat to this project. If outcomes can be
measured well enough, why check structure before it runs?

`LITERATURE.md` states the counter-claim. This tests it.

> **An eval is itself an estimator, and nothing calibrates it.**
>
> LLM-as-judge scoring is a belief formed by judgement. If judges are never scored against
> ground truth, then the mechanism the field uses to check agent quality has exactly the
> defect this project's most-cited check names — and the regress is not closed, merely moved
> one level up.

## Corpus rule, fixed now

Published, framework-authored evaluation harnesses that use a model as the grader:
LangSmith/LangChain evaluators, Ragas, DeepEval, OpenAI Evals, Braintrust autoevals.
Selected by prominence, not by whether they look broken.

## Predictions

| prediction | rate |
|---|---|
| The judge itself has no `checked_by` — nothing scores the judge against human labels or ground truth | **85%** |
| `origin: ourselves` on the graded output — the judge reads what the system produced | 100% |
| The harness declares a threshold (pass/fail score) with no model of what produces the score | 70% |
| At least one harness DOES calibrate its judge, and documents agreement with human labels | **40%** |

That last one is the honest hedge and it matters. Judge-human agreement is a known practice —
Ragas and DeepEval both discuss it in principle. **If most harnesses report human-agreement
numbers, the counter-claim is refuted and the field has closed the regress.** I expect a split:
the concept exists in the documentation and is absent from the runnable example.

## What refutes the counter-claim

- If **more than half** the harnesses ship a judge that is scored against human labels in the
  example itself, the objection stands and `LITERATURE.md`'s point 3 must be withdrawn.
- If harnesses cite human-agreement studies for their *built-in* metrics — that is a partial
  refutation and must be reported as one, since a pre-validated judge is calibrated even if the
  user's own run does not re-check it.

## What is NOT claimed either way

That evals are bad, or that structural checking replaces them. The claim under test is narrow:
whether the eval layer is itself subject to the defect it exists to catch. Both can be true.
