# Cycle 03 — canonical identity candidate

## Frozen holdouts

- Pydantic AI at `c8bcbb17fd7b490c541ccbb45822c1b25edf2717`;
- Stagehand at `7566804ed4b97649706782bccdcab5d80f6fe588`.

The exact source ranges are frozen in `research/control_plane/source_packets.json` before the
cycle-03 language and validation changes. Neither system appeared in cycles 01 or 02.

## Preregistered refinement

The 0.80 micro-F1 threshold and counter-based typed fingerprints remain unchanged. This cycle
adds machine-checked canonical identity rather than changing the score:

- one outward role per `(output kind, terminating scope)` tuple;
- one controller transition per `(operation kind, invocation authority, emitted role set)` tuple;
- `authorized_by` means authority to invoke, never the component that merely executes a branch;
- terminal sentinels are classified by semantic effect even when routed through tool/action code;
- public stream events are non-terminal outputs, and a resumable return at the declared run
  boundary is a pause plus a non-terminal output.

Candidate promotion still requires all original acceptance conditions.

## Blind result

Both first-pass independent documents were invalid. Stagehand used natural qualified local
references such as `goal.browser_task`, which strict name resolution did not accept. Pydantic AI
mixed base action safety fields with profiles and declared a produced observation as external.
Those are language-usage failures, so this cycle cannot promote regardless of repaired agreement.

For diagnosis only, mechanical comparison copies removed known prefixes, moved the Pydantic AI
fallback safety value into its profile partition, and corrected the contradictory provenance.
Source adjudication then corrected two primary encodings: Stagehand's caller is a system rather
than a human, while Pydantic AI separates the run caller from the human approver and exposes its
external-submission, suspended-turn, and interrupted-batch behavior.

| case | precision | recall | F1 |
|---|---:|---:|---:|
| Pydantic AI | 0.850 | 0.739 | 0.791 |
| Stagehand | 0.750 | 1.000 | 0.857 |
| **diagnostic micro** | **0.806** | **0.829** | **0.817** |

The micro row is 29 shared fingerprints, 35 primary fingerprints, and 36 replication
fingerprints. It shows that canonical identity resolved the semantic disagreement, but only
after invalid inputs were repaired.

## Decision

Reject promotion. Cycle 04 keeps the canonical identity rules, accepts known section-qualified
local references through deterministic normalization, and makes the two remaining fail-closed
rules explicit in the encoder instructions. First-pass validity remains mandatory.
