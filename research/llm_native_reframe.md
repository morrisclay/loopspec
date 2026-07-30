# Is This the Right Attempt?

A challenge to the project's direction, recorded because it may be correct and because the
evidence for it has been accumulating in this repository for some time without being read
that way.

**The challenge:** URAS should leverage an LLM's reasoning power and embrace it, not limit
it. What has been built limits it.

---

## 1. The charge, stated fairly against myself

I built a **compiler-era artifact**. A closed relation vocabulary. A hard primitive budget.
Fifteen enforced invariants. Determinacy as a top-line term in the score, weighted equally
with everything else.

Then the evidence said the relation vocabulary *cannot be closed* — thirteen further roles
already demanded by the corpus, an open English-verb list with no typing discipline. My
response was **to close it harder**, via typed slots on primitives.

That is the tell. The world reported that it is open and rich, and I treated the report as a
defect to engineer away.

**Determinacy became the goal because it was measurable, not because it was right.** SQL and
LLVM IR need determinacy because their consumer is a machine that cannot reason. Their
canonical forms exist so a *parser* can proceed. If the consumer can reason, insisting on one
canonical encoding discards precisely the capability that makes it worth building for.

## 2. The evidence was already here

Nothing below is new measurement. It is this repository's own record, re-read.

| Finding | What I concluded | What it may actually mean |
|---|---|---|
| `U = 0.042` after 20 attempts | need better queries | the structure is not where the value is |
| Adjudicator: derivation "does not produce better claims than writing them by hand" | write better queries | writing by hand *is competitive*, and hand-writing is what a model does natively |
| Diagnosis: **"typed paraphrase"** | encodings need to derive more | putting prose into typed slots added nothing, because the slots were not the constraint |
| Both genuine claims were trivial absences (*nothing measures X*) | the queries work | a careful reader finds those without any graph |
| Estimand agreement 0.07–0.17 on frontier systems | a determinacy defect to fix | rich systems may have no canonical decomposition, and demanding one is the error |
| 0 genuine claims where the source was already structured | write multi-hop queries | structure over structure adds nothing |
| Numeric `confidence: 0.42` | permit it, mark it | the startup seed already said this is theatre; a *sentence* about why founders disagree is more precise and a model uses it directly |

Seven independent results, all pointing the same way. I read each as a local problem and
never as a pattern.

## 3. Where structure still earns its place — the honest counter

The reframe is not "delete the structure."

- The validator caught **real defects in third-party output**: `on:` parsed as a boolean,
  phantom keys from unquoted commas, loops naming an `Estimand` where a `Signal` belongs.
  Those are machine-checkable and were invisible to every reader.
- The charter's goal is compiling to **executable systems**. You cannot compile prose. The
  Flue mapping is real: `Loop → Agent`, `Intervention → Action`, and an idempotency
  requirement with a documented platform justification.
- Drift detection, versioning, and comparison across time all need something stable to
  compare.

So the question is not structure versus no structure. It is **which structure is
load-bearing**, and the answer is: far less than nineteen primitives and fifteen relations.

## 4. The reframe

**Structure only where a machine must act on it. Language everywhere else.**

| Keep structured | Because |
|---|---|
| Loops: what is observed, what is decided, on what cadence | compiles to an executing agent |
| Who bears which consequence, who holds which authority | mechanically checkable, and the asymmetry is the substance |
| Declared invariants and their subjects | violation must be detectable |
| Excluded variables | the frontier for revision |
| Idempotency basis | a correctness requirement under at-least-once execution |

| Return to language | Because |
|---|---|
| Why a party holds the estimate it holds | a sentence is more precise than a token |
| What a hinge actually means and what would settle it | already free text pretending to be a field |
| The relation between two things | thirteen missing verbs is the vocabulary telling us it is open |
| Uncertainty | ordinal and qualitative language beats invented numbers |
| Everything currently in `note:` | it is there because the schema had no room for the truth |

### Three consequences that follow

**Determinacy should be semantic, not syntactic.** The current `D` asks *did two encoders
produce the same file*. The right question is **do two encodings support the same
conclusions** — which a model can judge and a diff cannot. Two descriptions using different
words that yield identical answers to hard questions are equivalent, and the current metric
scores them as divergent. That is not a refinement of `D`; it replaces it.

**The query layer should be reasoning, not traversal.** `tools/derive.py` runs eight
hardcoded structural queries. That is a rounding error against unbounded reasoning over the
same material. The queries should be *prompts*, and the structure's job is to make that
reasoning better-founded — not to pre-empt it.

**The relation vocabulary should stop being closed.** Thirteen missing roles is not a backlog.
It is a measurement result saying this is an open class. A closed vocabulary buys parser
determinism that nothing in this stack needs.

## 5. The experiment that decides it

None of the above is worth adopting on argument. The decisive test:

> Give one model **the prose**, another **the encoding**, another **both**. Ask the same hard
> questions — predict a failure, diagnose a cause, identify a disagreement that evidence
> cannot settle, name the measurement that would make things worse. Grade blind.

Three systems where both artifacts exist: hospital, Toyota, Hop Aero. Questions deliberately
require reasoning rather than lookup, because a structure that only helps with lookup is a
filing system.

**What each outcome means:**

- **Encoding ≥ prose** — the structure is load-bearing; continue, and the current direction is
  vindicated against this challenge.
- **Encoding ≈ prose, both > either** — the structure is a useful *supplement* and should be
  much thinner: keep the executable core, return the rest to language.
- **Prose ≥ encoding** — the structure is costing more than it returns. Collapse to the
  executable minimum and rebuild around reasoning.

I have never run this, which is the most surprising thing about the last two days of work. The
project's entire premise is that the representation makes systems more tractable, and that
premise has never been tested against the obvious baseline: **not encoding them at all.**

---

## 6. Result

Run on three systems, four reasoning questions each, answers graded blind by a model that did
not know which arm produced which set.

| arm | mean score /20 | systems won |
|---|---|---|
| prose only | 10.7 | 0 / 3 |
| **encoding only** | **12.0** | **2 / 3** |
| **both** | **13.3** | 1 / 3 |

**The structure helps.** Encoding-only beat prose-only on the mean and won two of three
systems; prose won none. That is evidence against the strongest form of the challenge, and it
was not the result I expected while writing sections 1 to 4.

**But `both` scored highest, and that is the finding that matters.** The pair beats either
alone. The structure is a **supplement, not a substitute** — which is exactly the middle
outcome predicted above, and it changes what the artifact is.

### What this actually changes

I have been building the encoding as though it *replaces* the description. It does not. The
product is the **pair**: a rich description, plus a structural index over it that makes
specific things checkable and computable.

That reframes several standing decisions:

- **Prose is not scaffolding to be discarded after encoding.** It ships. Every encoding
  should reference and travel with its source description, permanently.
- **The compression term in `C` is wrong.** It rewards encodings for being shorter than their
  prose, which pressures exactly the wrong direction — toward replacement rather than
  supplement.
- **`U` was measuring the wrong comparison.** It asked whether the encoding surfaces something
  the prose lacks. The right question is whether the *pair* supports better reasoning than the
  prose alone, which is what this experiment measured directly.

### Honest weaknesses of this result

- **n = 3 systems, one answering model, one judge.** The margins (10.7 / 12.0 / 13.3 out of
  20) are not large relative to that sample. This is suggestive, not settled.
- **`hop_aero` collapsed across all three arms** — 6, 2 and 5 out of 20 — which is an item or
  question-fit defect rather than a representation result, and it drags every mean. Excluding
  it widens the gap in the structure's favour, which is precisely why I am not excluding it.
- The judge noted the encoding arm's characteristic failure: answers "lost ground when they
  substituted plausible but unsupported exact details." **Structure invites confident
  fabrication** — it makes an answer look grounded whether or not it is.

### What survives from sections 1 to 4

The critique was right about the *direction of error* even though the experiment did not
support its strongest claim:

- Determinacy was over-weighted, and the response to "the vocabulary cannot be closed" should
  not have been to close it harder.
- Semantic agreement is the right notion, not syntactic agreement.
- The relation vocabulary should be open, because thirteen demanded roles is a measurement,
  not a backlog.
- Reasoning is the right query layer; eight hardcoded traversals are not.

What does *not* survive is the conclusion that the structure should collapse to an executable
minimum. It earns its place. It simply is not the whole artifact, and I had been treating it
as though it were.
