---
title: "Diagram notation"
description: "The stable visual vocabulary behind LoopSpec dependency and control-loop diagrams."
---

> This page is generated from `NOTATION.md` during every site build. Edit the canonical source, not this copy.

A projection is not a notation. `tools/diagram.py` emitted Mermaid with shape choices buried
in a dict, which means the diagram was readable only by someone who had read the emitter. This
is the notation stated independently of the tool: what each shape means, what each arrow
means, and how a defect is drawn.

**The test of a notation is that a person can draw one by hand and another person can read
it.** Mermaid is one rendering of it, not the thing itself.

---

## 1. Five bands, in reading order

Every diagram lays out left to right in the order a control loop actually runs. The bands are
not decorative — a node's band is determined by its kind, so two people drawing the same spec
put the same node in the same place.

```
 world/boundary → observed → believed → decided → accountable
 where the path    what arrives   what it thinks   what it does   who is exposed
```

A loop that is missing a band is missing a stage of regulation, and that is visible before
reading a single label. **A diagram with an empty `believed` band is a flowchart with a model
in it, not a regulator** — which is the distinction the whole project rests on.

## 2. Shapes — the noun vocabulary

| shape | primitive | reads as |
|---|---|---|
| `[[ boundary ]]` | Boundary | an observer-relative inside/outside distinction |
| `[( process )]` | System with `role: controlled_process` | the world/system path through which action becomes observation |
| `(  rounded  )` | Estimand | a quantity |
| `[/ slanted /]` | Signal | data arriving |
| `[  box  ]` | Estimator | a computation |
| `[\ inverted \]` | Calibration | scoring the past |
| `(  oval  )` | Explanation | a model of why |
| `{{ hexagon }}` | DesiredCondition | a target |
| `{ diamond }` | Policy | a decision |
| `> flag ]` | Intervention | an act on the world |
| `(( circle ))` | Party | a person or an agent |
| `[( cylinder )]` | Consequence, Resource | a stock — what is held or lost |

Two marks ride on shapes rather than taking their own:

- **`⚠` on an act** — `reversibility: irreversible`. **`!`** — `costly`.
- **`🧑` on a party** — a human. Its absence in a diagram full of circles is the fastest way
  to see a system with no person in it.

## 3. Arrows — the verb vocabulary

The relation vocabulary is closed, so the arrow set is closed too.

| arrow | relation | reads as |
|---|---|---|
| `──measures──▶` | measures | this tells you about that |
| `──estimates──▶` | estimates | this computes a belief about that |
| `──selects──▶` | authorizes | this chooses that act |
| `──scores──▶` | revises | this grades that estimator's past |
| `──bears──▶` | bears | this party carries that cost |
| `──asserts──▶` | asserts | this party *claims* it — not a measurement |
| `──after──▶` | delays | the effect arrives later |
| `──consumes──▶` | consumes | draws down a finite stock |
| `──reads──▶` | reads | this decision rule semantically reads that quantity or resource |
| `──uses reference──▶` | uses_reference | this ordered rule compares against that desired condition |
| `──outcome──▶` | compares | this calibration contract joins to that later outcome |
| `──through──▶` | causes | this action operates through that controlled process |
| `──emits──▶` | produces | this process produces that observation |
| `╌╌frames╌▶` | frames | this party chose that boundary for a purpose |
| `╌╌bounds╌▶` | bounds | this boundary applies to that controller |
| `╌╌targets╌▶` | targets | aims at, without guaranteeing reach |
| `╌╌sees╌▶` | holds | information reaches this party |
| `╌╌explains╌▶` | explains | claims a mechanism |
| `╌╌forbids╌▶` | constrains | must never |

**Solid arrows carry something; dashed arrows carry a claim.** `targets`, `sees`, `explains`
and `forbids` are all assertions about the system that may be false — which is exactly why the
linter checks them and the solid ones largely check themselves.

## 4. Defects are drawn, not appended

The design constraint, adopted from Briefing §5:

> **Every validator invariant needs a visual failure mode. If it cannot be drawn wrong, it
> probably should not be an invariant.**

A defect appears as a red note attached to the node it is about, and that node is redrawn with
a dashed red border. The finding text is the linter's own, so the diagram cannot drift from
the linter — `diagram.py` runs `derive.py` rather than reimplementing it.

The shapes of the common failures, readable without the labels:

| what you see | what it means |
|---|---|
| a slanted box with **no outgoing arrow** | `orphan_signal` — collected, tells you nothing |
| a rounded box with **nothing coming in** | `unmeasured_estimand` — believed, never observed |
| a box with **no return arrow into it** | `uncalibrated_estimator` — never scored |
| a hexagon with **no flag pointing at it** | `target_without_actuator` — a declared target with no declared lever |
| a circle with `bears` but **no `sees`** | `accountable_but_blind` — oversight in name only |
| a `⚠` flag with **no circle attached** | `irreversible_without_approval` |
| an **empty model relation** | `no_explicit_process_model` — no generative explanation is encoded |
| a red **unrepresented process** between act and observation | `process_path_not_declared` — the world leg is implicit |
| a missing boundary note | `boundary_not_declared` — inside/outside and observer purpose are unstated |
| an action whose effect sign is absent | `effect_direction_unspecified` — a later view must not invent polarity |
| a target with no policy arrow using it | `reference_not_used` — target and value coexist without a comparator |
| **no dashed arrow leaving the diagram** | `no_exogenous_grounding` — nothing can surprise it |

That last one is the group failure and it is the one people recognise instantly once drawn:
a diagram where every arrow originates inside the diagram.

## 5. Layout is derived, never authored

The format carries **no coordinates, no ordering hints, no styling**. Band assignment follows
from node kind; everything else is left to the renderer.

This is not a limitation, it is the guarantee. **A diagram that cannot be hand-positioned
cannot be drawn to flatter its spec.** If a diagram looks incomplete, the spec is incomplete —
there is no layout in which a missing calibration edge looks present.

## 6. Rendering

`python3 tools/loopspec.py diagram <spec.loop.yaml> --markdown` emits the dependency/governance
projection. Add `--control` for the feedback-ring projection. Both emit Mermaid, which renders
in GitHub, most editors, and this notation's own documentation.

Mermaid was chosen for reach rather than fit: it has no native concept of a band, so bands are
subgraphs, and its shape set is a near-miss for several primitives. A dedicated renderer would
draw all of §2 exactly. The notation above is what such a renderer would target, and is
deliberately written so that it does not depend on Mermaid surviving.
