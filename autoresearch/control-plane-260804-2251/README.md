# Autoresearch: control-plane semantics

Mode: **classic**
Started: **2026-08-04 22:51 Europe/Berlin**
Iteration ceiling: **8**
Publication: **disabled**

## Goal

Test whether LoopSpec should distinguish control of an agent loop from interventions the
agent makes in the world.

## Frozen acceptance predicate

Keep and promote the candidate only when all conditions hold:

1. Aider, AgentLab, and OpenAI Agents SDK are pinned to exact Git revisions before the
   candidate syntax is implemented.
2. The canonical graph can distinguish controller operations, outward outputs, and world
   interventions without encoding one as another.
3. Conditional approval is represented without claiming that every instance of a generic
   action is gated.
4. Deployment- or request-resolved action properties remain explicitly unknown until bound.
5. An independent, tool-disabled encoder reaches micro-F1 >= 0.80 on the frozen,
   source-cited control-plane mechanism set. Matching uses typed semantic fingerprints, not
   raw YAML names or finding counts.
6. Existing v1.1 authoring documents remain accepted without edits.
7. Repository doctor, real-loop corpus, and Astro documentation gates pass.

Failure of conditions 2–5 discards the normative candidate and preserves the experiment as
a negative result. No raw finding-count target is used.

## Iteration ledger

| cycle | candidate | signal | decision |
|---|---|---|---|
| 00 | frozen source and metric | source packets fixed | baseline |
| 01 | typed operations, outputs, action profiles | blind micro-F1 0.495 | reject promotion; refine individuation |
| 02 | prose individuation rules; smolagents + Skyvern holdouts | blind micro-F1 0.343 | reject promotion; make canonical identity enforceable |
| 03 | machine-checked canonical identity; Pydantic AI + Stagehand | raw documents invalid; repaired diagnostic micro-F1 0.817 | reject promotion; remove deterministic syntax friction |
| 04 | qualified-reference normalization; PocketFlow + Notte | one raw document invalid; repaired diagnostic micro-F1 0.919 | reject promotion; make `against` imply its read |
| 05 | nonredundant comparators; Codex + Goose | raw valid; frozen-primary micro-F1 0.444; source-corrected diagnostic 0.961 | reject promotion; clarify terminal and suspension boundaries |
| 06 | clarified terminal/suspension boundary; SWE-agent + Browser Use | raw valid; frozen-primary micro-F1 0.542; source-adjudicated 1.000 | reject frozen score; replicate corrected gold independently |
| 07 | different-model replication against adjudicated SWE-agent + Browser Use gold | raw valid; micro-F1 0.467 | reject promotion |
| 08 | tighten start/status/profile/authority/interrupt scope | residual ambiguity isolated; no adapted holdout | stop at ceiling; candidate remains experimental |
