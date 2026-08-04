# Autoresearch cycle: semantic pipeline and cybernetic closure

This is the reproducibility ledger for the first convergence milestone.

- Archetype: `build-feature`
- Mode: orchestration loop
- Terminal choice: stop at independently verified local changes
- Working predicate: `PYTHONDONTWRITEBYTECODE=1 python3 tools/uras.py doctor`
- Acceptance: exit zero; semantic tests, grammar, semantic map, check catalog, and generated
  artifacts all pass; the installed wheel also passes an out-of-checkout smoke test
- Holdout: reverse every authoring map, retain eight legacy IR fixtures, run safety mutations,
  and compare output under two hash seeds

The installed autoresearch bundle lacks its documented `scripts/orchestrate.sh`, so routing
and state updates are recorded here manually without weakening the safety boundaries.

Cycle 3 retains the locally verified release candidate and adds canonical semantic diff,
per-authoring-check positive coverage, a normative conformance manifest, and a clean-tree
external freeze gate. Independent implementation agreement and the pre-registered
external-author study remain evidence gates.
