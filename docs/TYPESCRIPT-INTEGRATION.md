# TypeScript integration without a second semantic core

LoopSpec's runtime integrations should be native to their host ecosystem. Flue adapters,
OpenTelemetry projection, channel ingress, application evidence helpers, and eval harnesses are
therefore TypeScript. Expansion, canonical validation, structural findings, and semantic diffing
remain one canonical engine for now.

## Decision

Do not rewrite the Python semantic core wholesale yet. Expose it through CLI protocol version 1
and place a typed TypeScript client in front of that protocol.

```text
Flue channels and observations (TypeScript)
                   |
                   v
        typed LoopEvent / episode layer
                   |
                   v
      LoopSpecEngine TypeScript interface
                   |
          CLI JSON protocol v1
                   |
                   v
 expansion + validation + findings + diff (Python, canonical)
```

This separation is about semantics, not language preference. The current expansion, validation,
and finding implementation is several thousand lines with a large conformance suite. Translating
it line by line would introduce two places where a valid document, finding, or semantic hash could
mean something different.

The TypeScript client provides `check`, `expand`, and `diff` as typed asynchronous methods. Its
default executable is the installed `loopspec` command. Development examples may instead launch
`python3 tools/loopspec.py`. A protocol-version mismatch fails closed.

The CLI transport is for Node processes and CI. Do not bundle `child_process` into a Cloudflare
Worker. A Worker-hosted Flue agent can emit privacy-minimised episode evidence to application
storage while a Node CI job, MCP server, or analysis service invokes the canonical engine. A
genuine requirement for in-isolate semantic analysis would satisfy the deployment trigger for a
native TypeScript port described below.

## What belongs in TypeScript now

- Flue event and channel adapters;
- privacy and identity projection;
- application and human-assessment event helpers;
- episode assembly and proposal policy;
- `vitest-evals` harnesses;
- the `LoopSpecEngine` interface and CLI transport;
- GitHub Action presentation and annotations.

## What remains canonical in Python

- authoring-format expansion into graph IR;
- IR validation against the ontology;
- structural finding derivation and assurance metadata;
- canonical semantic hashing;
- semantic diffing;
- the conformance corpus and research analysis.

## Conditions for a TypeScript semantic port

A port becomes warranted when at least one real deployment requires in-process browser, edge, or
single-binary Node execution where a Python command is not acceptable. Before implementing it:

1. freeze a cross-language fixture corpus containing valid, partial, and invalid specifications;
2. record canonical IR, finding sets, semantic hashes, and diffs from protocol v1;
3. require exact parity on that corpus in CI;
4. generate types and validators from the existing schema and ontology where possible;
5. switch the default engine only after a measured compatibility release.

Until then, the typed engine interface preserves the option to add a native TypeScript,
WebAssembly, MCP, or remote implementation without changing Flue integration code.
