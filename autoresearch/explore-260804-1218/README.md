# Autoresearch run: real agent loops

- Mode: `orchestrator`
- Archetype: `explore`
- Terminal choice: stop at verified local result
- Started: 2026-08-04
- Scope: build a source-backed real-loop corpus and use it to test LoopSpec's current
  language and checks
- Safety: no push, publish, deploy, destructive reset, or external write

## Success predicate

```sh
python3 research/real_loops/validate_corpus.py
```

Expected: exit 0 with at least 21 valid encodings, three full-revision source-pinned cases,
and 12 frozen live candidates.

## Verdict

`CONVERGED` for tranche 1. The predicate passes with 21 encodings, three pinned cases, and
16 candidates. Full repository tests and documentation build are the independent verification
gate recorded in `handoff.json`.
