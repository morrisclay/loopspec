# How cybernetic is this, actually?

Asked directly, and the honest answer as of this writing is: **cybernetic in its checks, and
until recently not in its object.**

The checks cite Conant & Ashby, Kalman, Forrester. But the thing being drawn was a *dependency
graph*, and a control engineer looking at it would ask the first question they always ask —
**where is the error signal?** — and there was no answer. The word "setpoint" appeared in this
project only inside a prose docstring. There was no comparator, no error, no gain.

That is worth saying plainly because it is the difference between a field's vocabulary and its
method.

---

## What was genuinely cybernetic

| claim | from |
|---|---|
| a loop steering something it has no model of is a **reflex, not a regulator** | Conant & Ashby 1970 |
| a quantity nothing observes cannot be regulated | Kalman observability |
| a target nothing can drive is a wish | Kalman controllability |
| a loop with no balancing path diverges | Forrester / Sterman polarity |
| **a ceiling is a stop, not a correction** — a stop absorbs no disturbance | Ashby |
| attention and calibration are *second-order* loops — loops about the loop | second-order cybernetics |

Those are necessary conditions from proved results, not style opinions, and they are what lets
the linter say *"your loop violates the Good Regulator theorem, and here is the line"* rather
than *"here are some things I noticed."*

## What was missing, and is now there

### 1. The error signal — `tools/control.py`

The central object of any control loop is **the difference between what you want and what you
believe**. Nothing named it.

The control projection draws the canonical ring per regulated quantity:

```
setpoint ─┐
          ▼
      (Σ error) ──▶ decide ──▶ ⟨action⟩ ──delay──▶ ((the world))
          ▲                                              │
          └──── feedback ──── believed ◀── /signal/ ◀─────┘
                                              ▲
                                        ⟨disturbance⟩
```

**Nothing new is asked of the author.** The comparator is *derived*: a goal targets a
quantity, something estimates that quantity, so the error exists and follows. Drawing it is
what makes a loop legible **as a loop** — and it immediately produces readings the dependency
graph could not:

> `payback_months` — the ring is open: nothing measures it, so **the comparator has no second
> input and there is no error to act on**.

That is the same fact `unmeasured_estimand` reports, stated in control terms, and it is
sharper. "A quantity has no signal" is a schema complaint. "The comparator has no second
input" tells you the loop cannot function.

### 2. Requisite variety — and it was never actually blocked

`insufficient_variety` sat listed as *blocked on a missing `Disturbance` primitive* for most of
this project, with the core budget full at 18. That was wrong. **`not_modelling:` is the
disturbance list.**

> The things you have declared you are not modelling are precisely the disturbances you are not
> regulating against.

No new primitive, no budget fight. The check compares distinguishable actions to named
unmodelled disturbances:

> The loop declares **1** action — `send_winback_email` — and **4** things it is knowingly not
> modelling: a support outage, competitor pricing, seasonality, the product getting worse.
> Only variety can destroy variety.

**Honest about the proxy:** counting names is a crude reading of variety. Ashby's is a measure
over *states*, not a headcount, and a spec that names no disturbances scores well by saying
nothing. It fires only when the gap is stark. It is a prompt to think, not a proof.

## Is it a loop design tool?

**It is becoming one.** The honest state, split:

**Design-tool behaviour it has.** You can write a loop before building it, see the ring, and
find that it does not close. `tools/control.py` will show you an open ring before any code
exists. The cookbook says what each common shape structurally costs. `consider:` records the
decisions you made and why.

**Design-tool behaviour it does not have yet, and these are real gaps:**

1. **No dynamics.** `effect_after` and `damping` are recorded and nothing reasons about them.
   Nyquist says gain plus delay oscillates; this cannot tell you whether *your* loop will
   thrash, only that it has a delay and no declared damping. `delay_without_damping` remains
   unimplemented.
2. **No gain.** How hard does the action push per unit of error? Unrepresentable. Without it,
   stability is not analysable even in principle.
3. **No cascade or hierarchy.** Real control systems nest — an inner fast loop inside an outer
   slow one. Groups share nodes, but nothing expresses *this loop's setpoint is that loop's
   output*, which is the standard cascade and very common in agent systems.
4. **Variety is counted, not measured.**

## The honest summary

It is a **cybernetically-grounded notation with a control projection**, not a control-systems
analysis tool. It will tell you your loop is structurally not a regulator. It will not tell you
whether your regulator is stable — and it should stop implying otherwise anywhere it does.

The next thing that would move it furthest is **cascade**: `goal.<q>.set_by: <other_loop>`.
That is one field, it is the standard shape of every real hierarchy of control, and it is how
agent systems actually fail — an outer loop's target quietly becoming an inner loop's
unexamined constant.
