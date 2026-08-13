# Autoresearch run: typed logs to LoopSpec design revisions

- Mode: `orchestrator`
- Archetype: `explore`
- Terminal choice: stop at verified local result
- Started: 2026-08-13
- Scope: test whether blinded typed occurrence logs can produce small, valid LoopSpec revisions
  that improve paired synthetic future episodes
- Safety: no push, publish, deploy, production mutation, or fabricated human outcome

## Success predicate

```sh
python3 research/episode_accounting/design_evolution.py --check-gates
```

Expected: `PASS` with all seven frozen holdout gates satisfied.

## Iteration record

1. Froze the input separation, development/holdout split, inference thresholds, future replay,
   score, and seven promotion gates.
2. Development passed: `+0.030` over unchanged and `+0.022` over shuffled placebo.
3. First holdout replay passed all outcome gates but failed G6 because generated `people.sees`
   entries named observations, which the grammar rejects. No inference or outcome parameter was
   changed.
4. Corrected that materialization error; the complete gate passed.
5. Tightened the common candidate baseline to resolve attention-budget and independent-crosscheck
   findings. The frozen scores were unchanged; all 40 designs then had zero active findings.

## Verdict

`CONVERGED` inside the synthetic laboratory. The result supports an evidence-linked proposal and
prospective testing workflow. It does not support autonomous application of revisions or make the
simulated policy effects real-world causal evidence.
