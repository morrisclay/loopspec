# Write your first loop spec

Ten minutes. You will end up with a file you can lint, draw, compare against published loops,
and hand to any LLM to compile.

**Requirements:** Python 3.11 or newer. For a clean local command, run
`python3 -m venv .venv`, then `.venv/bin/pip install .`; the command is `.venv/bin/loopspec`.
You can also work directly from the repository with `python3 tools/loopspec.py`. The spec remains
the artifact: installation only supplies the command and its PyYAML dependency.

---

## 1. Start with four questions that matter

Before any syntax. Most loops are badly built because nobody wrote these down, not because
anyone lacked the skill.

> **What quantity is this loop trying to move?**
> **What does it believe that it cannot see directly?**
> **Who drew the system boundary, and for what purpose?**
> **Through what process does an action become a later observation?**

If you cannot answer the first, you have a script, not a loop. If you cannot answer the
second, you have a thermostat — which is fine, and means most of this is unnecessary.

## 2. Write the skeleton

Create `myloop.loop.yaml`. Every key is a plain English word doing one job.

```yaml
loop: support_triage
runs: per_ticket

boundary:
  drawn_by: support_lead
  purpose: route urgent support work without losing customer trust
  inside: [triage policy, support queue, engineering escalation]
  outside: [customer situation, product behavior]

goal:
  resolution_time:
    keep: below 4 hours

beliefs:
  ticket_severity:
    question: "How badly is this customer blocked?"
    how: judgement

observes:
  ticket_text:
    informs: ticket_severity
    origin: outside
    how: reported          # the customer's account, not a measurement

processes:
  support_workflow:
    location: inside
    observed_as: []        # incomplete until ticket outcomes are added below

actions:
  escalate_to_engineer:
    moves: resolution_time
    through: support_workflow
    effect: decrease
    can_undo: yes

when:
  - if: "ticket_severity is high"
    reads: [ticket_severity]
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
- **`boundary:` records a perspective, not objective truth.** `drawn_by` and `purpose` make
  clear whose distinctions define “inside,” “outside,” and success. `processes:` then records
  the world/system leg that later carries an action's effect back as an observation.

## 3. Lint it

```bash
python3 tools/loopspec.py check myloop.loop.yaml
```

You will get findings immediately. **That is normal and is the point** — the reference
examples published by framework authors average five each. A first draft with findings is a
first draft that told you something.

The spec above intentionally produces several findings. Three you can act on straight away:

| finding | what to do |
|---|---|
| `belief_never_checked` | add `checked_by:` naming what scores the belief against outcomes — **or accept it, knowingly** |
| `unbounded_loop` | add `spends:` with a ceiling, even a generous one |
| `no_explicit_process_model` | add `explains:` when the loop depends on an explicit account of what generates the goal quantity |

And four that are worth reading before you touch anything:

| finding | what it is telling you |
|---|---|
| `unmeasured_estimand` | `resolution_time` is the goal and **nothing observes it**. The loop steers toward a number it never sees. This is a real hole in the spec above, left in deliberately — it is the most common thing a first draft gets wrong |
| `no_escalation_path` | a human is declared and there is no condition under which the loop stops and asks them |
| `consequence_without_authority` | `support_lead` carries the customer relationship and approves nothing |
| `reference_not_used` | `resolution_time` has a target, but no rule declares that it compares the observed value with that target |

### The output is ranked, and universal patterns are deliberately context

Findings are ordered by how **unusual** they are, measured against a reference corpus:

- **SPECIFIC TO THIS LOOP** — rare. Most loops do not have these. Read these first.
- **COMMON** — seen in a fair number of loops. Still worth deciding about.
- **UNIVERSAL** — context, not a finding. `no_explicit_process_model` fires on **22 of 23**
  specs in the corpus, including every framework's own best-practice example. A check that
  fires on everything carries **zero bits** about *your* loop, so it is reported as background
  rather than printed first in the same typeface as something rare.

Both things are true at once: a universal pattern can matter **about the corpus** and carry
almost no information **about your spec**. Also note the assurance boundary: this finding says
no explicit `explains` relation was encoded; it does not establish a Good Regulator theorem
violation.

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
    how: judgement
    explains: resolution_time
    checked_by: weekly_severity_review
    checked_against: ticket_outcome
    scoring_rule: severity classification error
    window: 100 resolved tickets
    adjusts: trust
    every: weekly
    settled_by: "the ticket closed without re-opening"

observes:
  ticket_outcome:
    informs: [ticket_severity, resolution_time]
    origin: outside
    how: measured

processes:
  support_workflow:
    location: inside
    observed_as: [ticket_outcome]
    description: routing and engineering work that produce the resolved-ticket outcome

when:
  - if: "ticket_severity is high"
    reads: [ticket_severity]
    do: escalate_to_engineer
  - if: "resolution_time exceeds 4 hours"
    reads: [resolution_time]
    against: [resolution_time]
    do: escalate_to_engineer

spends:
  engineer_hours:
    limit: "8 per week"
    spent_by: [escalate_to_engineer]

asks_human_when: ["severity evidence conflicts"]
asks_human: support_lead
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

## 5. Review what changed

Keep the previous spec and compare it with the revision by meaning rather than text:

```bash
python3 tools/loopspec.py diff before.loop.yaml myloop.loop.yaml
```

The result is computed from both validated IR documents. It reports changed node fields,
relations, loop membership, exclusions, recorded decisions, and findings; reordering YAML maps
produces no semantic change. Use `--json` for review automation and `--fail-on-change` when a
pipeline should return status 3 on any semantic delta.

This is different from a line diff. Changing `effect: decrease` to `effect: increase` is shown
as an intervention-direction change; removing `against:` is shown as a lost reference edge and
the newly introduced `reference_not_used` finding.

## 6. Draw it

```bash
python3 tools/loopspec.py diagram myloop.loop.yaml --markdown > myloop.md
python3 tools/loopspec.py diagram myloop.loop.yaml --control --markdown > control.md
```

Both are Mermaid and render in GitHub. The dependency/governance view shows the boundary,
process, observed, believed, decided, and accountable structures. The control projection shows
the feedback ring and leaves the process leg visibly broken when it was not declared.

Layout is derived: the format carries no coordinates, so a diagram cannot be drawn to flatter
its spec.

## 7. Compare it to published loops

```bash
python3 tools/compare.py myloop.loop.yaml research/published_study/encodings/*.loop.yaml
```

This is the part that tends to change people's minds. Your loop next to LangGraph's reflection
tutorial and CrewAI's self-evaluation flow, on the columns that matter. **You cannot diff two
blog posts. You can diff two specs.**

## 8. Compile it

Compilation is experimental and is not part of the v1.1 release claim. If you use an LLM as an
adapter, give it the spec and the target's actual API:

> Here is a loop spec. Emit a working implementation for **LangGraph**.
> Report anything the target cannot express rather than dropping it: end with a section
> `## did not survive`.

In a one-spec study, element-preservation scores ranged from 0.898 for 8B models to 0.993 for
frontier models. That grader did not establish executable or semantically correct target code.
Target knowledge was the actual bottleneck: Flue correct-API use was 18% without documentation
and 100% across six scored outputs when a one-page API reference travelled with the spec.

Then run the heuristic loss scan:

```bash
python3 tools/verify.py myloop.loop.yaml ./generated/
```

This exists because the most-dropped element in a 43-compilation archive was **the irreversible
act with no approval gate** — and two drops went unreported by the model that made them. The
scanner is text-based and cannot prove semantic preservation; treat a clean result as review
support, not certification. [`../research/llm_as_compiler.md`](../research/llm_as_compiler.md)
contains the complete correction and limits.

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
