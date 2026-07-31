# Case Results — ElectricSQL and Lodestar

Predictions were committed before any archive was opened. Scored against the rule fixed in
advance: a prediction counts only if the archive shows **the specific shift named**, not merely
that something changed.

---

## ElectricSQL — Prediction A CORRECT

Predicted (~55%): *"narrows from a broad local-first/offline platform toward a specific,
concrete capability… the 'local-first' ideology recedes; the sync primitive stays."*

| | positioning |
|---|---|
| **Oct 2022** | "ElectricSQL · **Local-first. Electrified.**" — you develop local-first apps, we provide the cloud sync. Embedded SQLite, **conflict-free active-active replication**, offline, privacy-respecting, reactive queries. |
| **May 2025** | "**Electric is a Postgres sync engine.**" Adopt sync **incrementally, one route at a time**, into **greenfield and brownfield** applications. Latency and memory benchmarks. Customer logos. |

Gone from the headline: local-first as an ideology, embedded SQLite, CRDTs, offline-first,
privacy. Retained: the sync primitive.

The prediction named the mechanism correctly — **application paradigm → plumbing.**

## Lodestar Space — UNVERIFIABLE

Predicted (~50%) a shift toward defence and sovereign-capability framing.

The endpoint is unambiguously defence-framed: *"DEFENDING THE ULTIMATE. Fully-autonomous AI
fighter-pilots for space. US and allied assets."* — bodyguard satellites, in-orbit threat
detection, national security.

**But there is no baseline.** `lodestar.space` was a **parked domain** in Feb 2023, and the
first substantive snapshot is January 2026. The Jan 2026 and Mar 2026 captures are identical.

So the archive shows a defence-framed *endpoint* and no observable *shift*. Under the
pre-registered scoring rule this does **not** count as correct. It is undetermined, and the
cross-case prediction that depended on it is untestable.

Recorded as a miss on testability rather than quietly reinterpreted as a win.

---

## The revised cross-case finding

The xorq case concluded **"provenance, not portability."** Two cases show that reading was
too specific.

| company | from | to |
|---|---|---|
| xorq | run anywhere across engines | expressions with identity and lineage |
| ElectricSQL | local-first apps, CRDTs, offline | a Postgres sync engine, one route at a time |

The shared pattern is not portability→provenance. It is:

> **An ambitious general abstraction lost to a narrow, concrete primitive with an incremental
> adoption path.**

Provenance was simply what xorq's concrete primitive happened to be. ElectricSQL's was a sync
engine. The direction is the same; the destination is domain-specific.

### This is worse for URAS than the xorq reading was

The xorq conclusion suggested a fix: reweight toward provenance. The two-case reading does not,
because it indicts the **shape**, not the emphasis:

| pattern | URAS |
|---|---|
| abandoned maximal generality | "universal", all domains, 20 primitives |
| abandoned wholesale adoption | you encode an entire system or nothing |
| adopted incremental entry | **no partial-adoption path exists at all** |

"Adopt incrementally, one route at a time" and "greenfield **and brownfield**" is the specific
mechanism both converged on. URAS has no equivalent. There is no way to use one primitive, or
encode one loop, and get value — which is the thing both companies discovered they needed.

### The concrete consequence

The next design question is not which primitives are right. It is: **what is the smallest
useful unit of URAS that someone can adopt without encoding a whole system?**

On present evidence the candidate is a **single loop** with its signal, its intervention and
its declared refutation condition — roughly one screen, no ontology commitment, no
completeness requirement. That is testable: encode one loop from a real system, and ask
whether it is useful without the other nineteen primitives ever appearing.

## Limits

- **n = 2 usable cases**, both developer-infrastructure companies. The pattern may be specific
  to that market rather than to abstractions generally — which is exactly what Lodestar was
  supposed to test and could not.
- ElectricSQL's page carries a testimonial about streaming **agent** updates. Agents appear as
  a customer use case, not a repositioning — mild support for the counter-explanation that
  xorq's v3 reflects agent-market timing rather than a durable truth about abstractions.
- Archive snapshots show what changed, never why. Both companies may have repositioned for
  funding or competitive reasons unrelated to the merits of the abstraction.
