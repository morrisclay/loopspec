# Batch Results — 19 companies, and the two-case reading does not survive

Predictions were committed before any archive was opened. Scored against the rule fixed in
advance. **Four of five predictions failed, including the decisive one.**

## Usable sample

19 queried, **9 valid**. Ten discarded, and the discards matter because most were the *wrong
company*, not merely thin data:

| discarded | why |
|---|---|
| supabase | baseline is "Portal Home — Supamaan Pte Ltd" |
| emm | latest is an **automotive supplies firm**, not menstrual tech |
| axiom_tx | latest is "Axiom Systems", a different company |
| lace | latest is Cardano's Lace wallet |
| oshen | fetch returned archive boilerplate |
| neon, tabular, databricks, callosum, lumai | one endpoint had no usable body |

**53% unusable against a predicted 30%** — P4 failed by underestimating how hard this is.

## The nine valid cases

| company | sector | early | late | call |
|---|---|---|---|---|
| deepset | software | "Cutting-edge NLP Solutions" | "Custom AI Solutions" | **BROADENED** |
| zama | software | "homomorphic ML inference solution" | "Open Source Cryptography" | **BROADENED** |
| edgeless | software | "The future is secure" | "Confidential Computing & Runtime Encryption" | NARROWED |
| motherduck | software | "Data Infrastructure and Analytics" | "Data Warehouse based on DuckDB" | NARROWED |
| bruin | software | "Unified Analytics Platform" | "Your Last Data Platform… works with your stack" | STABLE + incremental |
| proxima fusion | hardware | "Designing stellarator power plants" | "Building stellarators to power the future" | STABLE |
| positron | hardware | "Transforming the cost of ML" | "Generative AI Acceleration" | NARROWED |
| fractile | hardware | "run the world's largest LLMs" | "Radically Accelerate Frontier Model Inference" | STABLE |
| ncodin | hardware | "Light down to the core" | "Our vision: an **optical interposer**" | NARROWED |

## Scoring

```
software narrowing   2/5 = 40%
hardware narrowing   2/4 = 50%
```

- **P1 — a majority of software cases narrow. FAILED.** 40% is not a majority, and two software
  cases *broadened*.
- **P2 — narrowing markedly less common in hardware. FAILED DECISIVELY.** Hardware narrowed at
  a **higher** rate than software.
- **P4 — ~30% unusable. FAILED.** 53%.
- **P5 — agent language in a third of software cases. FAILED.** Near-absent across the sample.

## What this does to the earlier conclusion

The two-case reading was:

> An ambitious general abstraction lost to a narrow, concrete primitive with an incremental
> adoption path — and this indicts URAS's shape.

**P2's failure kills that.** Narrowing occurs at the same or higher rate in hardware companies
that have **no abstraction layer to narrow at all**. Proxima Fusion cannot abandon an
abstraction; Ncodin narrowed from "photonic computing" to "an optical interposer" because it
picked a product, not because an abstraction failed.

So the pattern, where it appears, is **ordinary company maturation** — going from a vision
statement to a specific product — and not evidence about abstractions. **The xorq and
ElectricSQL cases were over-fitted.** Two data points that happened to share a direction were
read as a mechanism.

**Retracted:** "URAS's shape is indicted by market evidence." It is not. The evidence does not
distinguish URAS's generality from ordinary early-stage vagueness.

**Also weakened in the other direction:** P5's failure undercuts the counter-explanation that
xorq's move was agent-market timing. Agent language is near-absent across nineteen companies
in 2025–26, so xorq's pivot looks idiosyncratic rather than market-driven. Neither the
original reading nor its main rival survives this sample.

## What stands

- The **xorq case itself** remains valid as a single documented instance: an explicit "define
  once, run anywhere" thesis, abandoned. That is one company's outcome, and should be cited as
  one.
- **ElectricSQL's incremental-adoption language** — "one route at a time", "greenfield and
  brownfield" — is real and appears again in Bruin's "works with your existing stack". Two
  instances is a hypothesis worth holding, not a finding.
- The question it raised for URAS — *what is the smallest adoptable unit?* — is a **good design
  question on its own merits**, and does not need this evidence to justify it.

## Method notes for the next batch

Three harvest attempts were needed. Each exposed a different contamination: prior domain
owners at the earliest snapshot; a company-name filter defeated by parked pages displaying the
domain; and archive rate-limiting producing silent fetch failures. The fix that worked was a
per-company founding-year floor on the CDX query.

**The classification calls above are mine and are contestable.** The before/after text is
included so each can be checked, which is the point of printing it rather than only the verdict.
