# LoopSpec

**A simple YAML for designing and arguing about agent loops: structural feedback, authority,
resources, attention, and calibration in one checkable artifact.**

Agent frameworks build the **operating** loop — observe, believe, decide, act. Their examples
rarely specify the meta-control loops *about* observing and believing:

- **Attention** — *am I looking at the right things, at what cost?* The input side.
- **Calibration** — *does what I believe turn out to be true?* The output side.

They are duals. Calibration helps determine whether attention was well spent; attention
determines what can be calibrated against. A notation makes both reviewable before runtime.

**Status:** authoring language **v1.1** and canonical IR **v2.1** are a locally verified
structural release candidate. `python3 tools/loopspec.py doctor` is the release gate. The tool does
not claim dynamic stability or proven field usefulness; the external-author protocol is
preregistered in
[`research/external_validation/PREREGISTRATION.md`](research/external_validation/PREREGISTRATION.md),
has no observed outcomes, and must pass before the claim advances beyond structural
specification and review.

> **Renamed 2026-08-03.** LoopSpec was previously called URAS. The authoring and IR versions
> did not change meaning during the rename. The old `uras` command remains a deprecated alias
> throughout LoopSpec 2.x; see [`COMPATIBILITY.md`](COMPATIBILITY.md).

```yaml
loop: customer_acquisition
runs: weekly

boundary:
  drawn_by: founder
  purpose: regulate paid acquisition without spending the company past viability
  inside: [growth policy, acquisition channel, company budget]
  outside: [prospective customers, advertising market]

goal:
  cost_per_customer: { keep: below 400 }

beliefs:
  product_market_fit:
    question: "If we keep buying customers like this month's, will they stay?"
    how: bayesian
    checked_by: quarterly_cohort_review
    checked_against: six_month_retention
    scoring_rule: Brier score
    window: 200 cohorts
    adjusts: trust

observes:
  billing_events:      { informs: cost_per_customer, origin: outside, how: measured, source: Stripe }
  customer_interviews: { informs: product_market_fit, origin: outside, how: reported, cost: high }
  six_month_retention: { informs: product_market_fit, origin: outside, how: calculated, every: monthly }

processes:
  acquisition_channel:
    location: interface
    observed_as: [billing_events]
    description: market response that turns spend decisions into customers and cost

actions:
  increase_budget: { moves: cost_per_customer, through: acquisition_channel,
                     effect: unknown, can_undo: yes }
  exit_channel:    { moves: cost_per_customer, through: acquisition_channel,
                     effect: decrease, can_undo: no, needs_approval: founder }

when:
  - if: "cost_per_customer above 400 and product_market_fit below 0.6"
    reads: [cost_per_customer, product_market_fit]
    against: [cost_per_customer]
    do: exit_channel

asks_human_when:
  - "product_market_fit falls below 0.4"
asks_human: founder

people:
  founder: { human: yes, loses_if_wrong: "the company", sees: [cost_per_customer] }
```

**[`ATTENTION.md`](ATTENTION.md)** works out the three levels attention operates at — the
author's (a field is a place you have to look), the loop's (what it observes, at what cost —
and the finding that *nothing had ever scored a signal*), and the humans' (who must look, and
who pays when it is wrong).

**[`CALIBRATION.md`](CALIBRATION.md)** is the other half: verification asks *is this output
good?*; calibration asks *has this thing's confidence historically tracked reality?* Agent
frameworks commonly expose the first; the measured reference corpus does not make the second
a first-class loop contract.

**What was found by looking:** across 10 reference examples written by framework authors to
demonstrate best practice, **10/10 form a belief nothing scores** and **10/10 encode no explicit
process explanation for what they steer** — both robust to independent encoding. The second is
a structural absence, not a Good Regulator theorem violation. The eval harnesses built to catch
quality problems trip the calibration check **4 of 4.** Half the published loops have a ceiling
nothing reads.

**You cannot diff two blog posts. You can diff two specs.** `loopspec diff` compares validated
canonical meaning and findings rather than YAML text; `tools/compare.py` puts a larger corpus
side by side. Reflection and reflexion differ in exactly one column, and that column is the
whole argument between them.

### Where to start

| | |
|---|---|
| **[`docs/GETTING-STARTED.md`](docs/GETTING-STARTED.md)** | **write your first spec — ten minutes with a lightweight local command** |
| [`docs/COOKBOOK.md`](docs/COOKBOOK.md) | the common loop shapes — reflection, judge, RAG, tree search, verifier — and **what each one structurally costs** |
| [`docs/LINTING-EXISTING.md`](docs/LINTING-EXISTING.md) | the brownfield path: lint a system you did not spec, including the three times it gave me a wrong answer |
| [`docs/CHECKS.md`](docs/CHECKS.md) | every check: felt symptom, what it looked at, how to fix, with a real example |
| **[`SYNTHESIS.md`](SYNTHESIS.md)** | where the field is, what this contributes, **and what it cannot claim** |
| **[`ATTENTION.md`](ATTENTION.md)** | half one — a notation is an attention device |
| **[`CALIBRATION.md`](CALIBRATION.md)** | half two — and why it is hard rather than neglected |
| [`CYBERNETICS.md`](CYBERNETICS.md) | how cybernetic this actually is — including what is still missing |
| [`REFERENCE.md`](REFERENCE.md) | every key — generated from `schema/loop.keys.yaml` |
| [`COMPATIBILITY.md`](COMPATIBILITY.md) | authoring v1.1 / IR v2.1 promises and migrations |
| [`schema/semantic-map.yaml`](schema/semantic-map.yaml) | traceability from every accepted key to its semantic effect |
| [`NOTATION.md`](NOTATION.md) | the diagram language, independent of any renderer |
| [`REFERENCES.md`](REFERENCES.md) | every external source and the decision it shaped |
| [`RULESET.md`](RULESET.md) | the checks, assurance levels, and theorem boundaries |
| [`research/real_loops/`](research/real_loops/) | source-pinned Codex, Goose, OpenHands, AI Scientist, SWE-agent, Browser Use, autoresearch, and Ralph evidence |
| `examples/field/` | earlier field cases; `research/published_study/` two pre-registered studies |

The complete searchable Astro manual lives in [`website/`](website/). Run `npm install` and
`npm run dev` there for the local documentation experience; `npm run check` rebuilds the site,
refreshes its canonical source pages, and validates routes and anchors.

### The toolset

One primary command, with focused scripts behind it. Nothing here is a framework — the spec is
the artifact and every projection reads the same validated IR.

For a clean local install:

```bash
python3 -m venv .venv
.venv/bin/pip install .
.venv/bin/loopspec doctor
```

Use `.venv/bin/pip install -e .` instead when developing LoopSpec itself. The repository-local
form below is equivalent and remains useful without installation.

```bash
python3 tools/loopspec.py check   spec.loop.yaml       # validate + findings + assurance
python3 tools/loopspec.py expand  spec.loop.yaml       # canonical typed IR v2.1
python3 tools/loopspec.py diff    before.loop.yaml after.loop.yaml
python3 tools/loopspec.py diagram spec.loop.yaml --markdown
python3 tools/loopspec.py diagram spec.loop.yaml --control --markdown
python3 tools/loopspec.py doctor                        # tests + generated-artifact gates

python3 tools/compare.py  specs/*.loop.yaml       # argue about loops side by side
python3 tools/verify.py   spec.loop.yaml build/   # did compilation drop the approval gate?
```

**Compilation is not part of the release claim.** In an exploratory one-spec study, models
from 8B to frontier preserved 0.898–0.993 of mechanically checked source elements, but that
grader did not establish executable or semantically correct target code. Real Flue API use was
18% without target documentation and 100% (6/6 scored outputs) with a one-page API reference.
[`research/llm_as_compiler.md`](research/llm_as_compiler.md) keeps the full correction and
limits; `tools/compile_flue.py` remains a reference mapping, and `tools/verify.py` checks for
declared elements silently lost by a generated implementation.

---

### Historical record

LoopSpec began as **URAS**, a proposed universal representation for adaptive systems. The corpus did not
support that scope, so the project narrowed to agent control loops. The
[`research/ORIGINAL-CHARTER.md`](research/ORIGINAL-CHARTER.md) preserves the original premise;
[`FORK.md`](FORK.md) records the narrowing, and [`CONVERGENCE.md`](CONVERGENCE.md) records the
current evidence gates. Those files are research history, not promises made by v1.1.
