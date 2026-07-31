# Do evals subsume structural linting? — results

Tests the field's strongest objection to this project. Predictions in `PREREG_EVALS.md`,
committed before any harness was fetched.

## The claim under test

> An eval is itself an estimator, and nothing calibrates it. If judges are never scored
> against ground truth, the mechanism the field uses to check agent quality has exactly the
> defect this project's most-cited check names — the regress is moved one level up, not closed.

## Corpus

Four framework-authored LLM-as-judge implementations, read as source:

| harness | file |
|---|---|
| DeepEval **G-Eval** | `deepeval/metrics/g_eval/g_eval.py` |
| DeepEval **agent loop detection** | `deepeval/metrics/agent_loop_detection/` |
| Braintrust **LLMClassifier** | `py/autoevals/llm.py` |
| Ragas **AspectCritic** | `src/ragas/metrics/_aspect_critic.py` |

DeepEval's `agent_loop_detection` was included deliberately: it is the closest thing in the
eval ecosystem to a structural check on loops, which makes it the fairest possible test.

## Result

**`belief_never_checked` fires on 4 of 4 — and on 4 of 4 in independent encodings too.**

`gpt-5.6-sol`, given only the raw source and `REFERENCE.md`, with no sight of this project:
**none of its four encodings declares `checked_by`.** It read the same code and independently
found nothing that scores the judge.

Its own words for G-Eval's belief:

> `how: An LLM generates a score and reason; when available, token log probabilities are used
> to calculate a weighted score.`

Log-probability weighting makes the number smoother. It does not make it right, and nothing
in the file compares it to a human's verdict.

## The correction I had to make to myself

My first pass had all four harnesses identical on five checks — a pattern that means the
encoder used a template, not that the corpus is uniform. Checking one specifically:

**Braintrust's `_run_eval(output, expected)` receives `expected` — human-authored ground
truth.** That is real per-case grounding and my encoding had omitted it, making
`no_exogenous_grounding` a false finding in my own favour.

Corrected, Braintrust shows `single_point_of_grounding` instead: the human-written `expected`
is its sole exogenous input. That is the accurate characterisation and it **sharpens** the
claim rather than weakening it:

> **Grounding the input is not calibrating the judge.** Braintrust compares the output to a
> human-written answer, which is exactly right. Nothing then asks whether the judge's *verdict*
> agrees with a human's *verdict* on that comparison.

## Scored against the pre-registration

| prediction | predicted | actual | |
|---|---|---|---|
| judge has no `checked_by` | 85% | **100%** (4/4, both encoders) | ✅ |
| `origin: ourselves` on graded output | 100% | 100% | ✅ |
| at least one harness DOES calibrate against human labels | 40% | **0%** | ✗ |

The hedge failed, and its failure is the finding. Judge-human agreement is discussed in these
projects' documentation; **it is absent from every runnable implementation examined.**

## What this does and does not establish

**Establishes:** the eval layer is subject to the defect it exists to catch. Four
framework-authored judges, two independent encoders, zero calibration.

**Does not establish:** that evals are bad or that structural checking replaces them. Both can
be true, and the pre-registration said so before the result was known.

**The partial refutation, reported as required.** G-Eval's method was validated against human
judgments in its originating paper (Liu et al.), and that is genuine pre-validation. But
`criteria: Optional[str]` is arbitrary free text, and `validate_criteria_and_evaluation_steps`
checks only that one of `criteria` or `evaluation_steps` is present — never that the rubric
resembles anything the paper tested.

> A judge validated for one rubric, deployed with another, is not a validated judge. The
> paper's correlation does not travel with the class.

## Limits

- n = 4. Chosen for prominence, but four is four.
- Source files only. A harness might ship calibration in a notebook, a docs page, or a CI job
  I did not read. The claim is specifically about the runnable implementation.
- One independent encoder, one model.
- Overall finding agreement was low (Jaccard 0.25–0.60), consistent with the earlier study:
  peripheral checks are encoder-dependent. **Only `belief_never_checked` is reported, and only
  because it is 4/4 across both encoders.**
