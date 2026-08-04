# Held-out verification

Accepted independently of the working assertion set.

- Nine product specs were expanded twice with every named-map section reversed. Their
  canonical semantic signatures and findings were identical.
- Eight legacy held-out IR encodings remained readable without synthesizing v2.1 semantics.
- Adversarial mutations of safety fields, references, types, aliases, and graph identifiers
  all failed closed.
- Analysis and semantic-diff JSON plus generated-artifact checks were identical under hash
  seeds 1 and 777.
- All nine product fixtures matched their pinned normalized semantic and complete finding-set
  hashes; the complete fixture remained a zero-finding negative.
- All 38 authoring checks fired on an executable positive fixture, while none of the 12
  compatibility-only checks leaked into the authoring fixture bank.
- Twenty-three historical independent encodings were screened: nineteen completed the new
  path, four were rejected as specification errors, and none crashed unexpectedly.
- A forced analysis-query exception propagated through the fail-closed analysis API.
- The full source gate passed in isolated runtimes across Python 3.11–3.14.

Verdict: **stable for the local v1.1 / IR v2.1 release-candidate milestone**. Historical
research artifacts are not rewritten to make the gate green. External usefulness remains a
separate, pre-registered empirical gate.
