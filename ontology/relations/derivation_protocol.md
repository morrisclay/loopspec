# Task: derive the relation vocabulary from evidence

## The problem

This ontology has 19 primitives (node kinds) that went through a rigorous derivation: written
from seed systems, stressed against adversarial ones, and finally tested against four held-out
systems the catalog was never designed against. They survived that.

The **relation vocabulary did not go through any of it.** Twelve relations were declared in one
sitting by the author while writing the canonical shape. Three more (`asserts`, `replenishes`,
`produces`) were added reactively last night from a single encoder's proposals — and are
**orphans with zero uses across all 23 encodings**. That is the same defect that got a
primitive called `Evidence` retired hours earlier: declared but never instantiated.

The relations were **declared, not derived**. Your job is to derive them.

## Inputs — PRE-COMPUTED, do not parse YAML with jq

- `ALL_EDGES.json` — every edge in the corpus, already resolved: file, domain, rel, from/to
  ids, **from_kind/to_kind**, and the full attributes of both endpoint nodes. This is the
  evidence. Query it with python3, not jq.
- `ASSERTS_CANDIDATES.json` — pre-filtered: Party->Signal edges, and all edges into Signals.
  Use this for question 3.

## Other inputs
- `encodings/` — 23 real encodings across 9 domains. This is the evidence.
- `OBSERVED_USAGE.md` — every relation, its usage count, and the node-kind pairs it connects.
- `primitives.yaml` — the 19 primitives.
- `uras.graph.md` — the canonical shape, including the current relation list.

## Questions, in priority order

**1. Are the twelve in-use relations the right twelve?**
Look at the observed node-kind pairs. Any relation used for structurally different things is
doing two jobs and should split. Any two relations connecting the same kinds for the same
reason should merge. Be specific: cite the pairs.

**2. Should `asserts`, `replenishes`, `produces` exist at all?**
They were justified by held-out systems and then never used. For each, either:
  (a) identify **specific existing edges in `encodings/` that should be re-typed to it** —
      give file, from, to, and the relation currently used; or
  (b) say it should be dropped.
An untestable justification is not a justification.

**3. The author made a claim that was never tested.** They wrote that `asserts` — a party
generating a datum rather than measuring one — "is not confined to the system that demanded
it", and predicted it recurs wherever a reported number is produced by someone with an
incentive. Test that against the corpus. Is it true? Where exactly?

**4. What relations are MISSING?**
Not from theory — from these encodings. Where did an encoder have to force something through
an ill-fitting relation, or express in a `note` what should have been an edge?

**5. Is there a principled basis for the relation set, or is it ad hoc?**
The primitives have a derivation story. Do the relations admit one — a small closed algebra,
a typing discipline over node kinds, something? Or are they an open-ended list that will grow
forever? Say honestly which, because it determines whether this vocabulary can ever be frozen.

## Output

Write `proposal.md`:

```markdown
## Verdict on the current 15
| relation | keep / merge / split / drop | evidence |

## Re-typings required
file | from | to | currently | should be | why

## Missing relations
name | from-kind -> to-kind | evidence in the corpus | how many encodings need it

## Principled basis
Is the relation set closable? Argue from the data.

## Harshest observation
The most important thing wrong with this vocabulary.
```

Be adversarial and concrete. Cite files and edges. A vocabulary you cannot justify from the
encodings is one that should shrink.
