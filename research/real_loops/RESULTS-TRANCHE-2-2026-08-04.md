# Real-loop tranche 2 — results

Date: **2026-08-04**  
Scope frozen before linting: independent re-encoding of SWE-agent and Browser Use, then
source-pinned encodings of Codex, Goose, OpenHands SDK, and AI Scientist v2.

## Outcome

The corpus gate now validates **25 unique encodings**, including **7 cases pinned to full
upstream commit hashes**. Twelve named candidates remain. The four new adjudicated encodings
add 18 findings, bringing the mechanical total to 274 unadjudicated finding instances.

The total is not a defect count. The independent test rejected that interpretation.

| case | findings | source-adjudicated reading |
|---|---:|---|
| Codex | 3 | the turn loop has steering, interruption, compaction, conditional sandbox approval, and tool-result feedback; concrete tool reversibility remains deployment-bound |
| Goose | 4 | the runtime has permission inspection, bounded turns, goal nudges, retry logic, and stop hooks; provider completion remains endogenous |
| OpenHands SDK | 6 | the richest explicit controller: confirmation policies, pause/interrupt, stuck detection, limits, stop hooks, and optional critic refinement; critic and risk judgements are not cross-run calibrated |
| AI Scientist v2 | 5 | executable experiments and metrics genuinely settle candidate questions, but stage progression and best-node selection remain inside the research loop and later paper review does not revise them |

## Independent encoding result

The held-out encoder received only the language reference and source ranges, with tools and
session persistence disabled. It did not see primary encodings or findings.

| case | shared exact categories | Jaccard | primary-category recall |
|---|---|---:|---:|
| SWE-agent | `consequence_without_authority`, `reversibility_unspecified` | 0.167 | 0.333 |
| Browser Use | `belief_never_checked`, `consequence_without_authority`, `reversibility_unspecified` | 0.333 | 1.000 |

SWE-agent fails a reasonable exact-category agreement threshold. Both encoders saw the same
source-level omissions—external grading is outside the run, concrete shell reversibility is
unbound, and no human escalation is evidenced—but projected them into different graph nodes
and therefore different checks. See `INDEPENDENT-ENCODING-2026-08-04.md` for the full audit.

**Decision:** no corpus defect rates, and no product metric based on raw finding count.

## What mature runtimes already do well

The new systems refute a simplistic “agents have no feedback or governance” story:

- Codex supports pending user steering, active-turn interruption, context-pressure correction,
  stop hooks, sandbox policy, and conditional approval.
- Goose supports pending steers, permission inspection, approval requests, cancellation,
  maximum turns, bounded empty-response retries, goal nudges, and stop-hook denial.
- OpenHands supports pause and interrupt, confirmation policies driven by security risk,
  iteration and spend ceilings, corrective nudges, stuck termination, stop hooks, and optional
  critic-driven refinement.
- AI Scientist v2 executes candidate experiments, parses metrics, distinguishes buggy and good
  nodes, carries best nodes across stages, and performs multi-seed evaluation.

LoopSpec is useful here because those mechanisms are distributed across runtime, policy,
configuration, hooks, and downstream evaluation. A single reviewable control contract can show
which mechanisms are merely offered by a runtime and which a deployment actually binds.

## What the test changed

### 1. Causal provenance is not epistemic novelty

AI Scientist causes its own experiments, so `experiment_result` correctly has
`origin: ourselves`. Those measurements can still surprise the agent because they pass through
an outside experimental process. The previous grounding check inferred that a self-produced
signal could not surprise the loop. That was false. The check now reports only the absence or
concentration of a causally independent observation path.

This leaves a language research question: should provenance separately represent who caused a
signal, where it was measured, and who asserted it? `origin` plus `how` is useful, but not yet a
complete epistemic account of active experimentation.

### 2. Conditional authority is not an action constant

Codex, Goose, and OpenHands decide approval per request from policy, sandbox, risk, or permission
inspection. Writing `needs_approval: operator` on a generic tool action falsely makes every call
gated; omitting it makes `consequence_without_authority` ignore real conditional gates.

The next representation must bind authority to a predicate or action profile without pretending
that runtime capability equals deployment configuration.

### 3. Controller operations are not world interventions

Compaction, pause, interrupt, retry, stop-hook denial, max-turn exit, `done`, patch submission,
and final responses repeatedly forced encoders into the `actions` section or into prose. Treating
them as world interventions creates false reversibility and process-path findings. Omitting them
loses essential loop control.

Both held-out encodings reproduced this pressure. It is the strongest candidate for the next
language increment.

### 4. Generic actions have bound and unbound properties

“Execute a tool call” cannot truthfully have one reversibility or consequence value. A read-only
search, local patch, payment, and deployment are instances of the same runtime action family with
different profiles. Unknown remains the correct v1 encoding; a future binding mechanism must not
turn unknown into safe.

## Usefulness, usability, desirability

**Useful now:** source-cited design review, comparison, diagrams, and exposing missing bindings.
It successfully distinguishes local result settlement from longitudinal calibration and makes
distributed safeguards reviewable together.

**Usable with friction:** a separate model could encode both held-outs, but one raw result used
qualified references (`beliefs.behavioral_loop`) rejected by the grammar. Encoders also varied on
boundaries, terminal nodes, and whether controller operations count as actions. The brownfield
workflow needs a source-packet helper, namespace-tolerant diagnostics, and root-cause grouping.

**Desirable for agentic loop engineers if positioned narrowly:** an executable control contract
between runtime code, deployment policy, evaluation, and human ownership is differentiated from
another orchestration or tracing framework. A generic “AI linter” with inflated defect counts is
not.

## Convergence gates

1. Add no new normative field from prevalence alone.
2. Prototype controller operations and terminal outputs in a non-normative branch.
3. Re-encode one held-out coding loop and one browser loop; retain the prototype only if exact
   graph/finding agreement improves without hiding a source-cited consequence.
4. Prototype conditional authority and deployment-bound profiles against Codex, Goose, and
   OpenHands; require all three to encode without unconditional claims.
5. Group diagnostics by causal root before using review time or action rate as a product metric.
6. Run the preregistered external-author study. Until its thresholds pass, claim a structural
   specification and review tool—not proven field usefulness or better production outcomes.
