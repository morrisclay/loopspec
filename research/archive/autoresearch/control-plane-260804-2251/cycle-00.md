# Cycle 00 — freeze before syntax

The three holdouts were cloned before any candidate authoring keys were added. Exact revisions
and source slices are recorded in `research/control_plane/source_packets.json`.

The gold mechanism set is source-cited in `research/control_plane/gold.yaml`. It contains only
the control-plane distinctions relevant to the hypothesis. Goals, beliefs, environmental
processes, and general linter findings are deliberately outside the acceptance metric.

Baseline expressibility is zero for the two proposed node classes because v1.1 has no typed
place for controller operations or outputs. Conditional authority can only be flattened into
an unconditional action gate, and generic action properties can only be omitted. The
experiment must improve expressibility without converting unknown into safe.

## Preregistration correction

Before any independent encoding, the Aider and AgentLab gold profiles were amended to mark an
explicit unknown default. The initial frozen file named the conditional profiles but failed to
represent unmatched requests, contradicting the already-frozen predicate that late-bound
properties remain unknown until bound. `gold.yaml` records this as version 1.1. The correction
adds no favourable system behavior and makes the acceptance set stricter by requiring two more
profile fingerprints.

After the blind outputs were frozen, the OpenAI Agents SDK output fingerprint was corrected
from `approval_request/none` to `approval_request/run`. Both encoders drew the boundary around
one `Runner.run()` invocation; the source returns on interruption and resumes through a later
invocation. The independent encoder exposed an inconsistency in the primary/gold reading.
`gold.yaml` records this source-adjudicated correction as version 1.2. The raw independent
output was not edited.
