# Blind syntax test — where the vocabulary came from

The v0 key names were mine. The complaint was that they were unintuitive, which is not a
thing I can adjudicate about my own design. So: **a blind test.**

Three strong models — claude-opus-5, gemini-2.5-pro, grok-4.5 — plus codex were given the
requirements in `BRIEF.md` and asked to design the syntax from scratch. **None saw v0.** The
brief listed what must be expressible, in plain language, with one instruction that mattered:
*no jargon from cybernetics or control theory in the key names*.

Where independent designers converge is what a reader expects. Where they unanimously differ
from v0 is where v0 was jargon.

## They rejected almost every word I chose

| concept | opus | gemini | grok | v0 | v1 |
|---|---|---|---|---|---|
| what it steers | `goal` | `goal` | `steers` | `regulates` | **`goal`** |
| what it believes | `beliefs` | `beliefs` | `believes` | `estimates` | **`beliefs`** |
| what scores the belief | `checked_by` | `how_checked` | `checked_by` | `calibrated_by` | **`checked_by`** |
| signal → belief | `informs` | `informs` | `informs` | `measures` | **`informs`** |
| the levers | `actions` | `actions` | `actions` | `acts` | **`actions`** |
| who is exposed | — | — | `people` | `parties` | **`people`** |
| what they lose | — | — | `loses_if_wrong` | `bears` | **`loses_if_wrong`** |
| out of scope | — | — | `not_modelling` | `ignoring` | **`not_modelling`** |
| undo-ability | — | `reversibility` | `can_undo` | `reversibility` | **`can_undo`** |
| lag | — | `effect_shows_in` | `effect_shows_after` | `delay` | **`effect_after`** |

**3/3 rejected every borrowed word.** They independently confirmed exactly two v0 choices:
`moves` and `sees`.

## Three things the blind designers contributed that I did not have

**1. `asks_human_when` as a top-level list (grok).** v0 buried escalation inside
`when[].escalate`. Grok pulled it out as its own block. That is right for a reason beyond
taste: escalation is the property a reader scans for to find out whether the thing can run
away, and burying it inside the decision rule is how it goes missing.

**2. Provenance is two-dimensional (codex).** Everyone else — grok, gemini, and me — collapsed
it. Grok's `comes_from: ourselves | reported | outside` is intuitive and *cannot express the
Ralph shape*, because "our own agent's self-assessment" is both ours and a report. Codex kept
two axes:

```yaml
origin: outside | ourselves      # did something outside cause this data to exist?
how:    measured | reported | calculated   # was the value measured, claimed, or derived?
```

`origin: ourselves` + `how: reported` is an agent grading its own homework, and one axis
cannot say it. Adopted, flattened to two plain keys rather than codex's nested blocks.

**3. `question:` on a belief (opus/grok).** A plain-language statement of what the belief
actually is — *"If we keep buying customers like this month's, will they stay?"* Optional, and
it does real work: it is the line a human reads first, and it exposes a belief nobody can
state.

## What I kept against the majority, and why

**`when` stays structured.** Grok wrote the policy as prose:

> `chooses_actions: > While cost_per_customer is above target, prefer lower_ad_spend unless…`

It reads beautifully and **cannot be linted at all**. The linter is the product. Grok's own
`by: up to +20% of current daily` has the same problem.

**Codex's design was rejected as a whole**, despite being the most rigorous: nested
`origin:`/`obtained_as:`/`arrives:`/`read:` blocks with inline SQL. It expresses more than
anything else here and fails the 30-second test outright. Its one distinction was worth more
than its structure.

## Did the rename actually help? — the compile test, rerun

Blind convergence is evidence about *reading*. Compilation fidelity is evidence about
*machine* legibility, and it is the number that could have refuted the rename.

| tier | v0 | v1 |
|---|---|---|
| very weak (8B) | 0.898 | **0.815** |
| weak (24B) | 0.981 | **1.000** |
| mid | 0.981 | **1.000** |
| strong | 0.993 | **1.000** |
| approval gate preserved | 20/20 | 21/21 |

**v1 is perfect from 24B upward and worse at 8B.** The 8B regression is almost entirely
llama-3.1-8b, which dropped the orphan signal and the people block. Reported rather than
explained away: it is a real cost, on the weakest tier, and the plain-English rename did not
help the smallest models.

**The number that matters most improved.** The irreversible ungated act — the single most
dangerous line in the spec — was silently dropped in:

> **v0: 4 of 20.  v1: 1 of 21.**

`can_undo: no` survives compilation where `reversibility: irreversible` did not. That is the
strongest argument for the rename and it was not the argument I expected to be making: plain
words are not merely nicer to read, they are **harder to lose**.

## Honest limits

- n = 1 spec, and it is the spec I wrote to exercise the format.
- The grader tests element presence, not semantics or execution.
- v0 and v1 encode the same loop but are not literally identical documents (v1 adds
  `question:`, `origin:`, `how:`, `asks_human_when:`), so this is not a controlled A/B on
  naming alone. The `exit_channel` result is the cleanest comparison, since that entry differs
  only in how undo-ability is spelled.
- Four blind designers is not a user study. It measures what capable writers reach for, which
  is a proxy for what readers expect, not the thing itself.
