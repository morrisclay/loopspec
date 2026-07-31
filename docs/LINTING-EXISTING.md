# Linting a system that already exists

The primary verb is **lint**, not **author**. Requiring the spec to be written first
reintroduces the wholesale-adoption problem that kills general representation projects —
ElectricSQL's *"adopt incrementally, one route at a time… greenfield **and brownfield**"* is the
adoption evidence this project takes most seriously.

So: you have a running agent. You did not write a spec. This is the procedure.

**It is written from doing it fourteen times** — four real systems, ten published examples —
**including the three occasions it produced a wrong answer.** Those are in §4, and they are the
most useful part.

---

## The one-paragraph version

Read the source. Write a spec that says **only what the source says**. Cite a line for every
field. Lint it. For every finding, go back to the source and check the encoding before you
believe the finding. Show it to whoever wrote the system. Most of your findings will be your
own encoding errors, and that is not a reason to skip this — it is a reason to do step 4.

---

## 1. Decide whether it is a loop at all

Before anything else. **Most "agent patterns" are not loops** — applying this rule removed most
of the OpenAI SDK's canonical `agent_patterns` directory, because `routing`,
`parallelization`, `deterministic`, `agents_as_tools` and both guardrail examples run **once**.

> A one-shot chain is not a loop. Linting it for regulation is a category error, not a finding.

Ask: **does anything come back around?** Does an output become an input on a later pass? If
not, stop — you have a pipeline, and pipelines have their own virtues.

## 2. Find the four things, in this order

Read for these specifically. It is much faster than reading the code linearly.

| look for | in the code | becomes |
|---|---|---|
| **the loop condition** | `while`, `should_continue`, a conditional edge, a router | `when:` and `spends:` |
| **what comes in** | tool calls, retrieval, API reads, user input | `observes:` |
| **what it concludes** | anything an LLM is asked to *judge*, *score*, *rate* or *decide* | `beliefs:` |
| **what it does** | writes, sends, commits, spends | `actions:` |

Then two questions that are usually answered by **absence**, and the absence is the finding:

- **What scores the judgements?** Search the repo for `human`, `label`, `ground_truth`,
  `agreement`, `annotat`. Finding nothing is a result — write no `checked_by`.
- **Who is the person?** Search for `approve`, `interrupt`, `confirm`, `escalate`. Finding
  nothing means `people: {}`, and that is honest.

## 3. Encode only what the source says

This is the whole discipline and it is harder than it sounds, because you will know what you
hope to find.

**The rule:** every field must be traceable to a line. If you cannot cite it, do not write it.
A missing `checked_by` must mean *the code contains no scoring*, not *I did not look for it*.

```yaml
observes:
  test_results:
    informs: task_actually_done
    origin: outside          # `subprocess.run(["pytest"])` — l.142
    how: measured
```

Two encoding decisions cause most of the trouble:

**`origin: outside` vs `ourselves`.** Ask *did something outside this system cause this data to
exist?* An agent reading its own diff is `ourselves`. A test suite is `outside` — it can fail
in a way the agent did not intend. A retrieved document is `outside`. A subagent's report is
`ourselves`.

**`how: measured` vs `reported`.** Orthogonal to the first. A number a mechanism produced is
`measured`; a number someone *says* is `reported`. An agent's self-assessment is
`origin: ourselves` **and** `how: reported`, and that combination is the single most
diagnostic thing in the format.

## 4. Distrust your first result — this is the important step

**On someone else's system the linter produced roughly 4 useful findings out of 14. Ten were
traceable to my own encoding errors.** That ratio is the honest baseline, and three times
during this project a corpus-wide rate turned out to be measuring the encoder:

| what I first reported | what it actually was |
|---|---|
| `belief_never_checked` at **20%** against a 90% prior | a name in both `goal` and `beliefs` was silently typed `computed`, exempting it from calibration checks |
| a defect at **100%** | the check was flagging the English words *plan*, *remain*, *steps* out of prose conditions |
| `unbounded_loop` at **14/14** | the format key for ceilings did not exist yet, so real ceilings sat in prose |

Every one of those first results **flattered the thesis**. That is what makes this step
non-optional rather than good practice.

**So, for each finding:**

1. **Grep the source for the thing the finding says is missing.** Before believing
   `unbounded_loop`, search for `max_iter`, `recursion_limit`, `retry_count`, `max_turns`. It
   takes thirty seconds and it caught a wrong corpus-wide claim three times.
2. **Ask whether the finding is about the system or about your spec.** If your encoding had
   said it differently, would the finding vanish? Then it is about your encoding.
3. **Suspect uniformity.** When four systems produce identical findings, you used a template.
   That is how I discovered Braintrust's judge receives human-authored `expected` and my
   encoding had omitted it — a finding landing in my own favour.

## 5. Get a second encoder

The cheapest instrument in this project, and the one that decides what you may claim.

Hand the raw source and `REFERENCE.md` to a model that has not seen your spec:

> You are encoding an existing agent implementation into a loop specification format.
> Encode ONLY what the source contains. If the code has no scoring of past predictions, omit
> `checked_by` — do not invent one. If no human appears in the code, leave `people` empty.
> Output only the YAML.

Lint both. Compare findings.

**What this bought here:** across five held-out examples, mean Jaccard was **0.53** — and the
average was the wrong statistic. Two checks agreed **5/5**; everything else agreed 2–3/5.

> **Report the checks that agree across encoders. Do not report rates for the ones that do
> not.** Those measure you.

The disagreements are usually honest judgement calls, not errors — *does a tutorial with no
human in the code have an implied user?* — and both encoders will often flag the same problem
through different checks.

## 6. Show the author

Nothing above substitutes for this. On the first real system, **2 of 4 findings were confirmed
genuine by the person who wrote it.** That is a small number and it is the only human-validated
data in this project.

Present findings as questions, because that is what they are:

> `enrich_attio` is marked `costly` and gates on nobody, while `propose_stage_move` gates on
> the partner. Both write to Attio. Is that asymmetry deliberate?

That finding came from the Deal Steward, a system *unusually* careful about human authority —
with ADRs governing ungameability. **The asymmetry was invisible until both acts carried the
same attribute and could be compared.** That is the mechanism working, and it is a question
rather than an accusation.

## 7. Compare it to the published shapes

```bash
python3 tools/compare.py yours.loop.yaml research/published_study/encodings/*.loop.yaml
```

This is often more useful than the findings. Your loop next to ten published reference
implementations, on the columns that matter. `docs/COOKBOOK.md` says what each shape
structurally costs — and if yours matches one, you inherit its cost whether or not you chose it.

---

## What a good outcome looks like

Not zero findings. A spec whose remaining findings you have **read and decided about**, and
which someone who did not write the system can read and argue with.

If the exercise produces nothing but a spec, it has still produced the thing this project
thinks is most valuable: **a form in which two people can disagree about a loop precisely.**
