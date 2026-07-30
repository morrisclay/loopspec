# Corpus Scope

**Target domain: frontier technology ventures.** Frontier software, new compute, new space,
new energy, new materials, new science.

The corpus was originally built from the charter's list, which predates that target. This
document records the retargeting and — more importantly — why several off-domain systems are
deliberately retained.

---

## The measurement that decided this

The question raised was whether the hospital is out of scope and whether it was dragging the
score down. Both halves were tested rather than argued.

**It does drag determinacy.** Removing it raises `D` by +0.067 — the intuition was right.

**And removing it takes the total score to zero.**

```
WITH hospital     S 0.875  E 0.936  D 0.789  U 0.113  C 0.560  ->  0.527
WITHOUT hospital  S 0.875  E 0.972  D 0.856  U 0.000  C 0.559  ->  0.000
```

Both genuine claims the project has ever produced came from the hospital encoding. The
thermostat produced none across five vendors. So the hospital is simultaneously the worst
benchmark for determinacy and the only source of demonstrated usefulness.

**Those are the same property.** It is the only system in the corpus complex enough that the
representation found something in it that was not already in the prose.

### The principle this establishes

**Easy benchmarks produce no insight.** A corpus narrowed to systems that encode cleanly
drives `U` to zero, and `U` is the binding term. Retaining hard cases is not tolerance of a
bad score; it is the only thing generating a score at all.

---

## What each benchmark is for

### On-domain — frontier tech ventures

| System | Segment | What it stresses |
|---|---|---|
| **Hop Aero** | new space | Catastrophic irreversible evidence; externally held goal (USAF contract); non-tradeable constraints |
| **SpaceX** | new space | Boundary as strategic choice; interventions targeting own structure to change evidence economics |
| **AI frontier lab** | frontier software / new compute | Authority decoupled from information; incommensurable safety-capability; reflexive measurement |
| **Fusion venture** | new energy | Decade horizon; objective is a physical threshold no party holds; simulation treated as observation; no intermediate market |
| **Materials discovery** | new materials | The only system NOT bottlenecked on evidence cost — search allocation over a vast space; multi-threshold objective; portfolio rather than loop |

### Off-domain, deliberately retained

| System | Why it stays |
|---|---|
| **Hospital** | The only source of genuine claims to date. Multi-party conflicting estimates, authority/information inversion, and metis — all of which recur in AI labs and critical infrastructure. Removing it zeroes the score. |
| **Thermostat** | The reduction floor. Must degrade to a classical control loop, confirmed independently by five vendors. Also the only benchmark where all five agree perfectly, which makes it the calibration point. |
| **Toyota** | The only system in the corpus that does adaptation *well*. Its absence caused a wrong finding: with only badly-adapting organisations in the corpus, the loci-of-goal-formation hypothesis appeared refuted. It is the control against which pathology is legible. |
| **Immune system** | The only system with no goal-holder anywhere. Guards against a representation that requires one. |
| **Startup (generic)** | Endogenous goal revision and state-space revision. Superseded in specificity by the named ventures but retains the pivot case. |

### Negative control

**Quicksort** must remain unencodable. If it ever encodes cleanly, the primitives have become
so general they distinguish nothing.

---

## The transfer question, and how it gets settled

The open question is whether the hospital's difficulty is *representative* of frontier
ventures or an artifact of healthcare specifically.

It is settled by measurement, not assertion: **encode the AI frontier lab and compare.**

- If it encodes like the hospital — low determinacy, insight-rich — the difficulty is general
  and the hospital earns its place as the stress case.
- If it encodes like the thermostat — clean and insight-free — the hospital is an outlier and
  should be scoped out.

The AI lab was written specifically to answer this. Its structural features were chosen to
mirror the hospital's: conflicting estimates over one quantity, authority sitting apart from
information, incommensurable objectives, and heavy unwritten knowledge — arrived at from the
domain rather than imported from the hospital.

## Held out — still sealed

`ecosystem`, `family`, `factory`, `llm_agent_system`. Not opened. One-shot, and only
meaningful against a frozen ontology.

Note that `llm_agent_system` is on-domain and sealed, which makes it the strongest available
generalization test once the ontology freezes.
