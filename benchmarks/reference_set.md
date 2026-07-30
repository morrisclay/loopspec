# The Reference Set

Real systems used to steer the ontology, replacing an invented generic "startup". Named by
the project owner; the pattern across them was not.

| System | What it is | Why it is in the set |
|---|---|---|
| **Toyota** | TPS, automotive manufacturing | Designed adaptive organisation. Settles the loci question. Supplies A3. |
| **SpaceX** | Launch vehicles | Buys information by destroying hardware. Moves its own boundary inward. |
| **Hop Aero** | Hypersonic cargo rockets, YC S26, ~6 people, $1.25M USAF contract, tethered prototype flown | Catastrophically expensive evidence + a government customer that is also partly the goal-setter |
| **Lodestar** | Space operations, London, 2023. ~$2.8M equity, ~$3.6M government grants/contracts (UK Space Agency, ESA, UK MoD) | More money from grants than equity — two funding regimes, two goal-setters |
| **Supabase** | Open-source Postgres backend platform | Community as a distributed sensor with no locus |
| **ElectricSQL** | Local-first Postgres sync | Correctness is provable; adoption is not. Two radically different estimand types in one company. |
| **xorq** | Multi-engine ML pipeline framework on Ibis / DataFusion / Arrow | Deliberately engine-independent — a structural analogue of URAS's own goal |
| **Lumi Science** | Probably lab automation: camera-based experiment capture and analysis (see caveat) | A company whose *product* is reducing the cost of scientific evidence |

**Caveat on Lumi Science:** several unrelated companies use "Lumi". The lab-automation one
(visual intelligence for experiment capture) is the best fit for the name, but this is a
guess and should be corrected. Nothing below depends on it.

---

## The axis the corpus was missing

The named set spans one dimension almost perfectly, and it is a dimension the charter's
coverage axes did not contain: **what it costs to acquire one piece of evidence, and
whether acquiring it is reversible.**

```
evidence nearly free                                    evidence catastrophic
continuous, reversible                                  rare, irreversible
├─────────────┬──────────────┬─────────────┬────────────────┬──────────────┤
Supabase      xorq        ElectricSQL     Toyota        Lodestar      Hop Aero
xorq          issues      adoption     (free BY        (expensive     SpaceX
GitHub/Discord            signals       DESIGN)        + gated)    (destroy vehicle)
```

This matters more than the axes already recorded, because for a company it determines
whether iteration is possible at all. Everything else about how these organisations are run
follows from where they sit on it.

Three consequences:

**1. Cheap evidence is an achievement, not a property of the domain.** Toyota manufactures
physical cars — it belongs on the expensive end by rights. Instead it engineered its way
left: the andon cord, the kanban card and go-and-see doctrine exist to make evidence cheap,
immediate and local in a domain where it naturally is not. That reframes the axis from a
constraint you inherit to a variable you can act on, which makes it a legitimate target of
intervention rather than background.

**2. Irreversibility is separate from cost and behaves differently.** A destroyed rocket is
expensive *and* irreversible. A slow ESA procurement decision is cheap to observe but the
outcome is irreversible and externally timed. A GitHub issue is cheap and fully reversible.
Cost and irreversibility come apart, and conflating them loses the distinction between
"we can afford to find out" and "we only get one attempt."

**3. Lumi Science is a system whose purpose is moving other systems along this axis.** If
the representation cannot express "this intervention reduces the cost of future evidence,"
it cannot describe the company at all — and it cannot describe Toyota's andon cord either,
which is the same move.

### Ontology consequence

`Evidence` gains `cost` and `reversibility` attributes, and the corpus gains an
`evidence_cost` coverage axis. Both are fields on an existing primitive, so the budget is
untouched.

**Prediction to check:** systems on the expensive end will spend heavily on `Estimator`
quality, because they cannot compensate with volume. Systems on the cheap end will run weak
estimators over many observations. If encodings do not show this, either the axis is wrong
or the encodings are not capturing what these organisations actually do.

---

## The second missing pattern: the goal-setter is often outside

The thermostat seed noted that the householder at the dial sits outside the boundary, and
warned that a representation forcing a goal-holder inside every system would lie about it. I
filed that as a quirk of a trivial system.

It is not. It recurs across the set, at company scale:

- **Hop Aero** — a $1.25M USAF contract for delivery to contested environments. The
  customer specifies the requirement, and is also partly the funder, and is also the
  regulator's neighbour. It sits outside the company and holds the dial.
- **Lodestar** — more money from UK Space Agency, ESA and MoD than from equity investors.
  Two funding regimes with different clocks, different reporting, and different objectives,
  neither fully internal.
- **Supabase and xorq** — goals set internally but *validated* by a diffuse open-source
  community with no locus at all. Nobody in particular holds the dial; adoption either
  happens or does not. Structurally this is the immune system, not the thermostat: not a
  goal-holder outside the boundary, but no goal-holder anywhere in the sensing apparatus.
- **Toyota** — the exception, and instructive for it. Goals are formed internally at every
  level and negotiated between them. The most sophisticated organisation in the set is the
  one that internalised goal formation.

So there are **three distinct arrangements**, and the seeds already contained all three
without my noticing they formed a set:

| Arrangement | Seed exemplar | Reference exemplar |
|---|---|---|
| Goal-holder outside the boundary | Thermostat | Hop Aero, Lodestar |
| No goal-holder anywhere | Immune system | Supabase, xorq |
| Plural goal-holders inside, negotiating | (none) | Toyota |

The third had no seed exemplar, which is exactly why the seed derivation produced evidence
against the loci hypothesis. **A gap in the corpus produced a wrong finding about the
ontology** — the clearest argument available for why the corpus has to come first and has to
be chosen for structural spread rather than for variety.

---

## What this changes

1. **`Evidence` gains `cost` and `reversibility`.** No budget impact.
2. **`DesiredCondition` held externally is the normal case, not an edge case.** Two of eight
   real companies here are substantially steered from outside. The representation must not
   require an internal goal-holder, and this is now a hard requirement rather than a note on
   a toy.
3. **`Revision` needs a regime attribute** — routine-incremental (kaizen) versus
   episodic-discontinuous (a pivot). Both exist, and treating them alike loses whether the
   prior condition was refuted or abandoned.
4. **A comprehensibility ceiling is justified by prior art.** Toyota's A3 has sixty years of
   evidence behind a hard size limit on problem representation. Feeds the `C` term in
   `ontology/score.md` as a bound rather than a preference.
5. **Two coverage axes added:** `evidence_cost` and `goal_locus`.
6. **xorq is worth watching as a structural analogue.** It exists to let one pipeline
   definition run across Snowflake, Spark, DuckDB and BigQuery — the same
   separate-specification-from-execution claim URAS makes, in a domain where it has already
   been tried. Whether xorq's abstraction leaks, and where, is direct evidence about
   whether URAS's will. This is a better prior-art reference than most of the academic list.

---

## Still to encode from this set

Toyota is written. Priority order for the rest, by what each attacks rather than by
availability:

1. **Hop Aero** — expensive irreversible evidence, external goal-setter. Strongest attack on
   the ontology's assumption that observation is cheap and repeatable.
2. **SpaceX** — boundary as a strategic choice. Vertical integration is deliberately pulling
   the boundary inward to shorten feedback loops, which is the strongest case yet for
   boundary-as-relation. Currently deferred; this may force it.
3. **Supabase** — sensing with no locus, at organisational rather than cellular scale.
4. **ElectricSQL** — two estimand kinds in one company: correctness, which is provable, and
   adoption, which is not. Tests whether one `Estimand` primitive covers both.
5. **Lodestar** — two funding regimes, two clocks.
6. **xorq** — as prior art as much as benchmark.
7. **Lumi Science** — pending identification.

---

## Sources

- [xorq documentation](https://docs.xorq.dev/overview) · [xorq multi-engine data stack](https://xorq.dev/blog/multi-engine-data-stack-ibis/) · [Hussain Sultan interview](https://materializedview.io/p/dataframes-multi-engine-queries-and)
- [Hop Aero on Y Combinator](https://www.ycombinator.com/companies/hop-aero) · [Rook hypersonic cargo rocket](https://digg.com/tech/juifgi73) · [Hop Aero company profile](https://pitchbook.com/profiles/company/740595-70)
- [Lodestar on Crunchbase](https://www.crunchbase.com/organization/lodestar-e2b9) · [Lodestar on Forbes](https://www.forbes.com/profile/lodestar/) · [Lodestar on Tracxn](https://tracxn.com/d/companies/lodestar/__10qJ2yronBwsHKzLzIk14FXLKHuGtwwYrpoVhA-4Y9M)
- [Lumi (lab automation)](https://startups.co.uk/startups-100/2025/lumi/) — identification uncertain
