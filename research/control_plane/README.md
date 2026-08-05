# Control-plane language experiment

This experiment asks whether LoopSpec needs a typed distinction between:

- a **world intervention**, which acts through a controlled process;
- a **controller operation**, which changes execution of the loop itself; and
- an **output**, which leaves the loop without being an intervention on the controlled process.

It also tests whether a generic action family can carry conditional, late-bound profiles
without pretending that runtime capability is deployment policy.

The test is preregistered in
`autoresearch/control-plane-260804-2251/README.md`. Sources and expected mechanisms were frozen
before candidate syntax was implemented. Independent outputs do not receive `gold.yaml`.

## Holdouts

| system | role | revision |
|---|---|---|
| Aider | interactive coding loop | `5dc9490bb35f9729ef2c95d00a19ccd30c26339c` |
| AgentLab | browser experiment loop | `cbc35a9bc0facaf731bc858c5825edbe757c719f` |
| OpenAI Agents SDK | conditional approval and resumable runner | `19e364c17344905ce6d17f41ea4fe084cba20388` |
| smolagents | tool-using agent run | `e3a5b8994b301983b91c0325546e9dc82eab8cf0` |
| Skyvern | browser automation agent | `6442cdc49dbe031c7d9462c140d9035fd2d6f0cd` |
| Pydantic AI | resumable typed agent graph | `c8bcbb17fd7b490c541ccbb45822c1b25edf2717` |
| Stagehand | streaming browser agent | `7566804ed4b97649706782bccdcab5d80f6fe588` |
| PocketFlow | node flow and browser cookbook | `f74d023f93607b8c3268133339a5e532a949898c` |
| Notte | browser agent with completion validation | `10e0fd35316565cc84bdbe9905d2645972f8b77c` |
| OpenAI Codex | coding turn with approval, compaction, and interruption | `2a16af823456712e3dbb030ecf29fb727c2cde66` |
| Goose | streamed coding turn with hooks and permission inspection | `7f62ce53e70c49e634ed9ba16a1ef8e02a2d239c` |
| SWE-agent | bounded model requery and patch submission | `3ea751c087f32b16e039a2233dd6eefecef325d5` |
| Browser Use | browser control with pause, stop, and stall detection | `c561b1f514f1e197580e0c4b75a5bfbc3f1e61f2` |

The metric compares typed semantic fingerprints after expansion. Encoder-chosen identifiers
and prose are ignored. This avoids rewarding shared naming while still requiring agreement
about operation kind, output termination scope, action-profile binding stage, reversibility,
authority, and the typed edges among them.

## Result

The candidate proved mechanically expressible and exposed useful distinctions, but it did not
converge under the preregistered independent-encoding metric. The final different-model
replication scored **0.467 micro-F1** against the **0.80** threshold. The implementation remains
experimental; the raw outputs, normalization records, source-adjudication notes, and all rejected
cycles are retained so the negative result is reproducible rather than summarized away.
