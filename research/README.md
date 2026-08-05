# Research archive

This directory contains the evidence behind LoopSpec, including negative results. It is not a
second product manual. Start with the repository [`README`](../README.md) to use the language,
and with [`SYNTHESIS.md`](SYNTHESIS.md) for the bounded field-level argument.

> [!WARNING]
> LoopSpec is an early research candidate. A study directory records what was tested under a
> particular protocol; its presence does not mean the hypothesis passed or the result generalized.

## Current evidence paths

| Directory | Question |
|---|---|
| [`real_loops/`](real_loops/) | Can the language encode identifiable mechanisms in real agent loops at pinned upstream revisions? |
| [`control_plane/`](control_plane/) | Do independent encoders converge on actions, controller operations, outputs, and conditional safety? |
| [`external_validation/`](external_validation/) | Can independent authors use LoopSpec, and does it improve their review of a loop? |
| [`published_study/`](published_study/) | Which structural patterns appear in framework-authored examples and evaluation loops? |

The control-plane study stopped below its preregistered threshold. The external-author protocol
has no observed outcomes yet. These are explicit limits, not missing footnotes.

## Supporting and historical studies

| Directory or document | Role |
|---|---|
| [`syntax_study/`](syntax_study/) | Blind syntax and authoring-surface experiments |
| [`does_structure_help/`](does_structure_help/) | Tests of whether structured encodings improve derived claims |
| [`compile_study/`](compile_study/) | Exploratory LLM-as-compiler results and API-conditioning correction |
| [`cases/`](cases/) | Case-specific source and analysis material |
| [`strata/`](strata/) | Structural comparison artifacts |
| [`CONVERGENCE.md`](CONVERGENCE.md) | Current evidence gates and unresolved research questions |
| [`ORIGINAL-CHARTER.md`](ORIGINAL-CHARTER.md) | Superseded universal-representation premise |
| [`agent_loop_pivot.md`](agent_loop_pivot.md) | Rationale for narrowing to agentic loops |
| [`prior_art_gate.md`](prior_art_gate.md) | Prior-art and reduction constraints |

Superseded charters, scorecards, theses, and field instruments are grouped under
[`archive/`](archive/). They are retained for provenance and should not be read as the current
language or product contract.

## Evidence-preservation conventions

- Raw model output stays beside normalized or repaired output when the distinction affects the
  reported result. Identical files may therefore be intentional provenance, not accidental copies.
- Source revisions and source packets are retained when they define a frozen evaluation set.
- Completed autonomous-run ledgers remain in `archive/autoresearch/`; deleting rejected trials
  would make the apparent research trajectory misleading.
- Generated implementation output belongs under ignored `build/`, not in version control.
- Scripts that call model APIs require separately supplied environment variables and may incur
  cost. The standard `doctor` and corpus-validation gates do not call external model APIs.

## Reproduce the local gates

```bash
python3 tools/loopspec.py doctor
python3 research/real_loops/validate_corpus.py

cd website
npm ci
npm run check
```

The first two commands are local and deterministic. The website check rebuilds the static Astro
manual. Individual research protocols may have additional frozen inputs and requirements; read
their local README or preregistration before running them.
