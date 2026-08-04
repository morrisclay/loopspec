# Four real loops, in the format

Not written to exercise the format — these are re-encodings of systems that exist and run:
three from the t-minus specs, one from a widely-copied public technique. They were previously
encoded as flat graphs; this is the same content on the authoring surface, which is the
surface anyone would actually use.

| loop | what it is | findings |
|---|---|---|
| `ralph` | ghuntley's `while true` agent loop | 11 |
| `deal_steward` | proposes deal stage moves, never writes them | 9 |
| `conviction_termination` | when does the `/complicate` engine stop? | 9 |
| `meeseeks_sourcing` | searches channels for candidates, retires dead ones | 13 |

## What the re-encoding changed, honestly

Reformatting was not lossless, and two of the differences were the *format catching the
encoding*, not the reverse.

**Ralph's headline finding was wrong, and the format found it.** Encoded as a graph, Ralph
tripped `no_exogenous_grounding` — nothing outside the loop reaches it. That is not true.
Ralph reads test results, which are exogenous. The old firing was an artifact of the graph's
loop record naming only one of Ralph's two signals; the loop format records them all, so it
correctly stopped firing.

The real property is narrower and more useful, and is now a check of its own:

> **`single_point_of_grounding`** — Loop `ralph` reads 2 observations and exactly one of
> them, `test_results`, comes from outside itself. Everything else it looks at, it produced.
> `test_results` is therefore the only thing that can fail in a way this loop did not intend,
> and the loop is exactly as trustworthy as that one input.

That is what `THESIS.md` claimed from intuition — *"Ralph is grounded only through the test
signal"* — now **derived from the spec's shape** rather than asserted. It is also what
practitioners report, which the wrong version was not.

**A decision rule reading a quantity that does not exist.** The conviction engine's stop rule
guards on `avg_confidence`, which is declared nowhere in the system — not a goal, not a
belief, nothing observes it and nothing computes it. Caught by a new check,
`policy_reads_undeclared`, which exists because the loop format distinguishes *declared but
unmeasured* from *never declared at all*. The graph shape could not tell those apart.

This surfaced only after fixing a bug it was hiding: the expander tokenised the condition
string naively and put the word **"above"** in the policy's inputs, so the check was
comparing against noise. Inputs are now the intersection with declared names.

**`estimand_never_estimated` no longer fires from the authoring path.** Every `beliefs:` entry
gets an estimator by construction, so it is unreachable — but the case it covered is caught,
by `target_without_actuator` and `unmeasured_estimand` together. Verified with a spec declaring
a goal nothing tracks. It remains live for hand-written graph encodings.

## The one that is not a defect

`meeseeks_sourcing` is the only loop here with a `checked_by`, and it checks something unusual:

```yaml
checked_by: viability_review     # retires a channel that finds nothing
```

It scores the **source**, not the output — asking whether this channel was worth searching
rather than whether a candidate was good. Every other loop in this corpus, if it scores
anything, scores its own judgements. Worth noticing as the shape to copy.

## Reproduce

```
python3 tools/loop.py examples/field/ralph.loop.yaml --lint
python3 tools/diagram.py examples/field/ralph.loop.yaml --md
```
