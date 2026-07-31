# Write your first loop spec

Ten minutes. You will end up with a file you can lint, draw, compare against published loops,
and hand to any LLM to compile.

**Requirements:** Python 3 and `pyyaml`. That is all — there is no framework to install,
because the spec is the artifact and every tool just reads it.

---

## 1. Start with the two questions that matter

Before any syntax. Most loops are badly built because nobody wrote these down, not because
anyone lacked the skill.

> **What quantity is this loop trying to move?**
> **What does it believe that it cannot see directly?**

If you cannot answer the first, you have a script, not a loop. If you cannot answer the
second, you have a thermostat — which is fine, and means most of this is unnecessary.

## 2. Write the skeleton

Create `myloop.loop.yaml`. Every key is a plain English word doing one job.

```yaml
loop: support_triage
runs: per_ticket

goal:
  resolution_time:
    keep: below 4 hours

beliefs:
  ticket_severity:
    question: "How badly is this customer blocked?"
    from: [ticket_text]
    how: judgement

observes:
  ticket_text:
    informs: ticket_severity
    origin: outside
    how: reported          # the customer's account, not a measurement

actions:
  escalate_to_engineer:
    moves: resolution_time
    can_undo: yes

when:
  - if: "ticket_severity is high"
    do: escalate_to_engineer

people:
  support_lead:
    human: yes
    loses_if_wrong: "the customer relationship"
    sees: [ticket_severity]
```

Two things there are worth pausing on, because they are the parts people skip:

- **`origin` and `how` are separate on purpose.** `origin` asks *did something outside cause
  this data to exist?* `how` asks *was the value measured, claimed, or derived?* A customer's
  ticket is `outside` and `reported` — it comes from beyond your system **and** it is a claim
  by someone with interests. Collapsing these into one field loses the case that matters most:
  `origin: ourselves` + `how: reported` is an agent grading its own homework.
- **`question:` is optional and worth writing.** It is the line a human reads first, and the
  one that exposes a belief nobody can actually state.

## 3. Lint it

```bash
python3 tools/loop.py myloop.loop.yaml --lint
```

You will get findings immediately. **That is normal and is the point** — the reference
examples published by framework authors average five each. A first draft with findings is a
first draft that told you something.

The spec above produces **six**. Three you can act on straight away:

| finding | what to do |
|---|---|
| `belief_never_checked` | add `checked_by:` naming what scores the belief against outcomes — **or accept it, knowingly** |
| `unbounded_loop` | add `spends:` with a ceiling, even a generous one |
| `regulator_without_model` | add `explains:` to the belief that accounts for your goal |

And three that are worth reading before you touch anything:

| finding | what it is telling you |
|---|---|
| `unmeasured_estimand` | `resolution_time` is the goal and **nothing observes it**. The loop steers toward a number it never sees. This is a real hole in the spec above, left in deliberately — it is the most common thing a first draft gets wrong |
| `no_escalation_path` | a human is declared and there is no condition under which the loop stops and asks them |
| `consequence_without_authority` | `support_lead` carries the customer relationship and approves nothing |

### The output is ranked, and two of the checks are deliberately not findings

Findings are ordered by how **unusual** they are, measured against a reference corpus:

- **SPECIFIC TO THIS LOOP** — rare. Most loops do not have these. Read these first.
- **COMMON** — seen in a fair number of loops. Still worth deciding about.
- **UNIVERSAL** — context, not a finding. `regulator_without_model` fires on **21 of 21**
  specs in the corpus, including every framework's own best-practice example. A check that
  fires on everything carries **zero bits** about *your* loop, so it is reported as background
  rather than printed first in the same typeface as something rare.

Both things are true at once: *"100% of published loops lack calibration"* is the strongest
claim this project has **about the field**, and useless **as a lint on your spec**.

### Recording a decision — `consider:`

**You do not have to fix everything.** A finding you have read and decided against is a
different thing from one you never saw, and the format has somewhere to put that:

```yaml
consider:
  orphan_signal/crm_stage:
    because: "read only to detect drift; it feeds no belief on purpose"
    revisit: "if we ever move stages automatically rather than proposing them"
  belief_never_checked:
    because: "no outcome arrives until a deal closes, which is 6-18 months"
    revisit: "when the first cohort of proposed deals has resolved"
```

This **does not suppress the finding.** It moves to a `CONSIDERED` section with your reason
attached, so a reviewer sees the decision rather than a silence. And if the spec changes so the
finding no longer fires, the linter says so — *a stale justification is worse than none*.

## 4. Fix the two that matter

```yaml
beliefs:
  ticket_severity:
    question: "How badly is this customer blocked?"
    from: [ticket_text]
    how: judgement
    explains: resolution_time                  # ← the model
    checked_by: weekly_severity_review         # ← what scores it
    settled_by: "the ticket closed without re-opening"

spends:
  engineer_hours:
    limit: "8 per week"
    spent_by: [escalate_to_engineer]
```

`checked_by` is the one people leave out, and leaving it out is the single most common defect
in this entire corpus — **10 of 10 published reference examples, and 4 of 4 of the eval
harnesses built to catch exactly this.**

### Fixing one thing reveals the next, and that is working correctly

Re-lint and the three are gone — but a new one has appeared:

> **`ceiling_without_correction`** — `engineer_hours` has a limit of `8 per week` and no
> decision rule reads how much is left. The loop runs at full rate until it hits the wall and
> stops.

That is not the linter being difficult. **A ceiling is a stop, not a correction:** it truncates
the loop rather than regulating it, and the halt is indistinguishable from failure. To
regulate, a rule in `when:` has to read `engineer_hours` and do something different when it
runs low — triage harder, batch, or escalate.

The spec still trips `unmeasured_estimand`, because `resolution_time` is genuinely unobserved.
**This tutorial does not end at zero findings, and no honest one would.** The goal is a spec
whose remaining findings you have read and decided about.

## 5. Draw it

```bash
python3 tools/diagram.py myloop.loop.yaml --md > myloop.md
```

Mermaid, renders in GitHub. Four bands in the order a loop runs — **observed → believed →
decided → accountable** — and **defects are drawn, not appended**. A hexagon with no flag
pointing at it is a target nothing can move; you can see it without reading a word.

Layout is derived: the format carries no coordinates, so a diagram cannot be drawn to flatter
its spec.

## 6. Compare it to published loops

```bash
python3 tools/compare.py myloop.loop.yaml research/published_study/encodings/*.loop.yaml
```

This is the part that tends to change people's minds. Your loop next to LangGraph's reflection
tutorial and CrewAI's self-evaluation flow, on the columns that matter. **You cannot diff two
blog posts. You can diff two specs.**

## 7. Compile it

There is no compiler, deliberately. Hand the spec to any LLM:

> Here is a loop spec. Emit a working implementation for **LangGraph**.
> Report anything the target cannot express rather than dropping it: end with a section
> `## did not survive`.

Fidelity is flat from 8B models to frontier ones — the format does not need a clever reader.
**If your target is newer than the model, paste one page of its API alongside**: Flue went from
18% to 100% correct-API output on that alone.

Then check what was lost:

```bash
python3 tools/verify.py myloop.loop.yaml ./generated/
```

This exists because the most-dropped element in a 43-compilation study was **the irreversible
act with no approval gate** — and two of those drops went unreported by the model that made
them. A compiler that silently drops the dangerous act is worse than no compiler.

## Where to go next

| | |
|---|---|
| [`../REFERENCE.md`](../REFERENCE.md) | every key, generated from the grammar |
| [`CHECKS.md`](CHECKS.md) | every check: felt symptom, what it looked at, how to fix |
| [`COOKBOOK.md`](COOKBOOK.md) | the shape you are probably reaching for, and what it costs |
| [`LINTING-EXISTING.md`](LINTING-EXISTING.md) | you already have a running agent and no spec |
| [`../NOTATION.md`](../NOTATION.md) | the diagram language, independent of any renderer |
| [`../ATTENTION.md`](../ATTENTION.md) · [`../CALIBRATION.md`](../CALIBRATION.md) | the two ideas the whole thing is for |
| `../examples/field/` | four real systems, including the Ralph loop |

## A note on what this is not

It will not tell you whether your agent works. It tells you whether your loop **can find out
whether it works** — which is a smaller claim and a different one.

Nothing here replaces evals. Evals measure outcomes and need the failure to have already
happened; this reads structure before it runs. Use both.
