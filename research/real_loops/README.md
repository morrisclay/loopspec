# Real-loop corpus

This corpus tests LoopSpec against agent loops people can inspect and run. It is not a
showcase. A case belongs here because its control path is visible in source, not because it
is likely to make LoopSpec look useful.

The existing published-example study is the seed set. This directory adds source-pinned
runtime systems whose loops can mutate code, spend money or compute, operate browsers, route
among agents, or optimize an external metric.

## The question

For each system, separate four things that are easy to conflate:

1. **System property** — the source really has or lacks the represented mechanism.
2. **Encoding decision** — a boundary, provenance, or consequence had to be interpreted.
3. **Language gap** — the source states something important that LoopSpec cannot express.
4. **Check behavior** — the linter reports, misses, or overstates a consequence of the shape.

No defect-rate claim is made from an encoding until another encoder can reproduce the
relevant structure. Findings are hypotheses for author review, not facts about the project.

## Inclusion rule

A case must have all of the following:

- a repeated observe/decide/act path, rather than a one-shot chain;
- public source or primary documentation;
- an exact revision for Git sources, or a dated retrieval for a web-only source;
- evidence anchors for the loop, stop condition, and material resource or authority boundary;
- an encoding of what the source states, with omissions left visible.

Framework runtimes and deployed applications are different strata. A generic runtime can
prove that a mechanism is representable, but it cannot establish the reversibility,
consequence, or success criterion of an application built on it.

## Sampling matrix

The target is at least 30 loops across five deliberately different strata:

| stratum | examples | why it matters |
|---|---|---|
| autonomous coding | Ralph, SWE-agent, Codex, OpenHands, Goose | long horizon, repository mutation, tests as feedback |
| autonomous research | autoresearch, AI Scientist, GPT Researcher, PaperQA | metric selection, search, evaluator regress |
| browser/computer use | Browser Use, AgentLab, OSWorld agents | environmental change, weak reversibility, human consequence |
| framework runtimes | OpenAI Agents SDK, AutoGen/MAF, smolagents, Pydantic AI | stop, handoff, approval, and budget mechanisms |
| evaluation/optimization | DeepEval, Braintrust, Ragas, DSPy | who evaluates the evaluator and what changes afterward |

Selection and current status live in `corpus.yaml`. `candidate` means discovered, not yet
encoded. `excluded` cases stay in the registry with a reason so selection cannot silently
drift toward flattering examples.

## Reproduce

From the repository root:

```sh
python3 research/real_loops/validate_corpus.py
python3 tools/loopspec.py check research/real_loops/encodings/autoresearch.loop.yaml
python3 tools/loopspec.py diagram research/real_loops/encodings/browser_use.loop.yaml --control --markdown
python3 research/real_loops/compare_findings.py \
  research/real_loops/encodings/browser_use.loop.yaml \
  research/real_loops/independent_encodings/browser_use.loop.yaml
```

The validation command checks every seed and new encoding, verifies source metadata, and
prints corpus and finding counts. It does not decide whether findings are true; adjudication
is a separate human or independent-encoder step.

`independent_packets.json` and `independent_encode.py` reproduce the blinded source-to-spec
test. Raw model outputs stay in `drafts/`; held-out outputs and run metadata stay in
`independent_encodings/`. The Browser Use raw output is preserved separately because it used
qualified references that required a namespace-only normalization before validation.
That exact transform is recorded in
`independent_encodings/browser_use.normalization.json`; the normalized artifact contains no
semantic edits.

## Expansion protocol

For every new tranche:

1. Freeze the candidate IDs before reading their findings.
2. Pin the source revision and record the exact files and line spans used.
3. Encode once without looking at linter output.
4. Run the checker and label each result `system`, `encoding`, `language`, or `check`.
5. Independently encode a held-out sample.
6. Keep a language/check change only if it improves agreement or catches a source-cited
   consequence without adding false certainty to the holdout.

The convergence metric is not “more findings.” It is **more source-cited, author-confirmed
consequential insight per minute, with less encoder variance**.
