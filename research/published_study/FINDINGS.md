# Linting published reference examples — results

Corpus: **10 loops** from LangGraph tutorials, the OpenAI Agents SDK `agent_patterns`, and
CrewAI flows. Written by framework authors to demonstrate best practice, which makes this the
least favourable possible sample for the thesis.

Predictions in `PREREGISTRATION.md`, committed before anything was fetched.

---

## 1. What the corpus turned out to be

Selection followed the pre-registered rule — listing order, not "does it look broken" — with
one exclusion applied: *a one-shot chain is not a loop.*

**That exclusion removed most of the OpenAI `agent_patterns` directory.** `routing`,
`parallelization`, `deterministic`, `agents_as_tools`, `input_guardrails`,
`output_guardrails` and `human_in_the_loop` are pipelines and demos: they run once. Only
`llm_as_a_judge` has a repeated cycle toward a condition.

That is a finding in its own right and not a criticism of the SDK. **The canonical directory
named "agent patterns" is mostly not loops**, which is consistent with the literature review:
the field's vocabulary is about composition, not regulation.

## 2. The instrument was wrong, and the first run was measuring me

The pre-registration named the risk: *"encoding is where the bias enters — I write the spec,
and I know which checks exist."* It arrived immediately, in three places.

| symptom | cause | verdict |
|---|---|---|
| `belief_never_checked` fired on 20% against a 90% prior | a name in **both** `goal` and `beliefs` was fixed as `computed` by whichever ran first, and computed quantities are exempt from calibration checks | instrument bug |
| `policy_reads_undeclared` fired on **100%** | conditions are prose, and the check flagged the English words *plan*, *remain*, *steps* as undeclared quantities | instrument bug |
| `no_escalation_path` fired on 10% against a 75% prior | the check required a declared human before looking for escalation, so it skipped every loop that declares **no** human — the more alarming case | instrument bug, backwards |

All three are fixed. `essay_quality` in both sections is now latent, because a quantity you
steer toward *and* form a view about is a judgement; `policy_reads_undeclared` only considers
identifier-shaped tokens; and a loop with policies and no person now trips `no_human_at_all`.

**The uncomfortable part, stated plainly: I fixed the instrument after seeing the result, and
the fix moved my headline check from 20% to 100% — exactly what I had predicted.** That is
the shape of motivated reasoning whether or not it is motivated reasoning. The defence is that
each bug is independently diagnosable and each fix is principled rather than tuned. The
defence is not sufficient on its own, which is why the next section exists.

## 3. The kill condition — independent encoding

Pre-registered: *if an independent encoder agrees on fewer than half the held-out examples,
this study reports nothing about defect rates.*

Five examples were re-encoded by `gpt-5.6-sol`, given only the raw source and `REFERENCE.md`,
with no sight of this project, my encodings, or the checks.

**Mean Jaccard over findings: 0.53.** Three of five at 0.67 or above, two at ~0.25. The kill
condition is not triggered, narrowly — and the average is the wrong statistic. Per check:

| check | mine | independent | agreement |
|---|---|---|---|
| **`belief_never_checked`** | 5/5 | 5/5 | **5/5** |
| **`regulator_without_model`** | 5/5 | 5/5 | **5/5** |
| `no_human_at_all` | 5/5 | 2/5 | 2/5 |
| `no_escalation_path` | 0/5 | 3/5 | 2/5 |
| `no_exogenous_grounding` | 3/5 | 1/5 | 3/5 |
| `single_point_of_grounding` | 1/5 | 3/5 | 3/5 |
| `open_loop` | 1/5 | 3/5 | 3/5 |
| `reinforcing_loop_no_balancer` | 3/5 | 1/5 | 3/5 |

**Two checks are perfectly robust. Every other check measures the encoder as much as the
corpus.**

The disagreements are honest judgement differences, not errors. Does a tutorial with no human
in the code have an implied user? I said no and encoded `people: {}`; the independent encoder
said yes. Both then flag the absence of oversight, by different checks. Is a reflection node's
critique `origin: ourselves`? Obviously — but whether the loop therefore has *no* exogenous
grounding or *one* point of it depends on how the tool calls are encoded.

## 4. What this study reports, and what it refuses to report

**Reported**, because it survives independent encoding at 5/5:

> Across 10 reference examples written by framework authors to demonstrate best practice,
> **every single one forms a belief by LLM judgement that nothing ever scores against
> outcomes**, and **every single one steers toward a condition with no model of what produces
> it.**

That is the thesis's central claim, on public artifacts, at 100%, robust to who encodes them.
It is not a claim that these examples are bad — a tutorial demonstrating reflection is not
obliged to ship calibration. It is a claim that **the vocabulary is missing**: there is no
place in any of these frameworks to say *"and this is what checks whether the critic was
right."*

**Not reported as rates**, because they are encoder-dependent: `no_human_at_all`,
`no_escalation_path`, `no_exogenous_grounding`, `single_point_of_grounding`, `open_loop`,
`reinforcing_loop_no_balancer`. These stay in the linter — they were useful on the field
loops — but this study is not evidence about how often they occur.

## 5. Pre-registered predictions, scored

| prediction | predicted | actual | |
|---|---|---|---|
| median checks per example ≥ 4 | 4+ | 5 | ✅ |
| ≥80% trip `belief_never_checked` or `regulator_without_model` | 80% | 100% | ✅ |
| `belief_never_checked` | 90% | 100% | ✅ |
| `regulator_without_model` | 70% | 100% | over |
| `single_point_of_grounding` | 50% | 30% | ✗ |
| `unmeasured_estimand` | 40% | 10% | ✗ |
| `orphan_signal` | 30% | 0% | ✗ |
| `irreversible_without_approval` | 20% | 0% | ✗ |
| `no_escalation_path` | 75% | 0%* | ✗ |

\* subsumed by `no_human_at_all`, which did not exist when the prediction was written.

**Both headline predictions hit; five of seven rate predictions failed.** The failures are
informative: `orphan_signal` and `irreversible_without_approval` at 0% because tutorials are
small and only touch scratch state — exactly as the refutation criteria anticipated for
demo-detecting checks.

## 6. Limits

- **n = 10, not the pre-registered 20–30.** The one-shot exclusion removed more of the corpus
  than expected. The two robust checks are at 10/10, so the shortfall does not threaten them;
  it does mean the encoder-dependent rates are even less reportable than the agreement study
  alone implies.
- **One independent encoder, one model, five examples.** A second model might disagree with
  both of us.
- Notebooks were truncated to 30k characters for the independent encoder. Mine were read via
  extracted graph structure. The two encoders did not see identical inputs.
- I chose which frameworks to sample. LangGraph is 7 of 10.
