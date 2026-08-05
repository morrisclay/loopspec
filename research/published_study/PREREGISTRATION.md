# Pre-registration — linting published agent examples

**Written before any example was fetched, read or encoded.** Committed alone, before the
corpus commit, so the timestamps prove ordering.

The archive study is the precedent: four of five pre-registered predictions failed, and the
failure was the useful part. Predictions written after seeing data are not predictions.

## The claim under test

`research/archive/THESIS.md` §2: *"people are not good at loop engineering… this is not a carefulness problem,
it is a vocabulary problem. You do not check for a defect you have no word for."*

Evidence so far is four loops, all hand-picked by me, three of them from one codebase. That
is an anecdote. This study uses **published reference examples written by framework authors
to demonstrate best practice** — the most favourable possible sample for the frameworks, and
the least favourable for the thesis.

## Corpus rule, fixed now

- 20–30 examples from **framework-authored or framework-featured** sources: LangGraph,
  CrewAI, AG2/AutoGen, OpenAI Agents SDK, Goose, Pydantic-AI, smolagents.
- Selected by **search rank and star count, not by whether they look broken.** The selection
  rule is fixed before searching. Any example I skip must be recorded with a reason.
- Excluded: pure tool-calling demos with no repeated cycle. A one-shot chain is not a loop
  and linting it for regulation would be a category error, not a finding.

## Predictions

Rates are the fraction of examples tripping each check. I commit to these numbers.

| check | predicted | reasoning |
|---|---|---|
| `belief_never_checked` | **90%** | The strongest prior in the project. Three independent real systems, three careful authors, all missing it. Frameworks have no construct for calibration, so there is nothing to copy. |
| `no_escalation_path` | **75%** | Tutorials demonstrate autonomy; a human gate is friction in a demo. |
| `single_point_of_grounding` | **50%** | Common in agentic RAG and self-critique examples. |
| `regulator_without_model` | **70%** | Prompts and tools, no model of the controlled quantity. |
| `orphan_signal` | **30%** | Tutorials are small; unused inputs are unlikely at that size. |
| `irreversible_without_approval` | **20%** | Most tutorials only read or write scratch state. |
| `unmeasured_estimand` | **40%** | Requires the example to declare a target at all. |
| `shared_estimand_no_arbiter` | **60% of multi-agent examples** | The verifier pattern with no reconciliation. |

**Headline prediction: median 4+ distinct checks per example, and ≥80% tripping at least one
of `belief_never_checked` or `regulator_without_model`.**

## What would refute the thesis

- **Median under 2 checks per example**, or `belief_never_checked` under 40%. Either means
  practitioners handle this better than assumed, or the checks encode a standard nobody needs.
- If most examples trip only `no_escalation_path`, the linter is detecting *"this is a demo"*
  rather than a defect. That is a finding **against** the check, not against the authors, and
  the check should be scoped to production loops.

## The encoding-error problem, stated in advance

The known weakness: on someone else's system the linter previously ran ~4 useful findings out
of 14, with ten traceable to **my own encoding errors**. Encoding is where the bias enters —
I write the spec, and I know which checks exist.

Mitigations, fixed now:

1. Encode **only what the source states**. A missing `checked_by` must mean the example
   contains no scoring code, not that I did not look for it.
2. For every finding, record the **line or file** in the source that justifies the encoding.
   A finding whose encoding cannot be cited is discarded.
3. **Hold out a random 5** for independent encoding by a different model, and report agreement.
   If a model that has never read this project encodes them and the findings diverge, the
   defect rate measures me, not the corpus.

## Kill condition

If the independent encoder's findings agree with mine on fewer than half the held-out
examples, **this study reports nothing about defect rates** and reports the disagreement
instead.
