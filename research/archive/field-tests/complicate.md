# Field Test — one loop of your conviction engine

> [!NOTE]
> **Historical field instrument.** This is preserved research material, not evidence that the
> current LoopSpec candidate has passed external usefulness validation. See
> the current [`external-validation preregistration`](../../external_validation/PREREGISTRATION.md).

I encoded a single loop of `/complicate` — the INVESTIGATE cycle, nothing else. 63 lines, one
screen, no commitment to the rest of the ontology. Below is what the structure says about it.

**Two questions per item. Four minutes.**

**(a) Did you already know this?** `yes, obviously` / `yes, but never stated` / `no`
**(b) Would it change anything?** `no` / `a conversation` / `an actual decision`

Answer honestly rather than generously. A row of "yes, obviously" is a real and useful result.

---

### 1. Nothing scores whether your past resolutions were right

Hypotheses move `draft → queued → investigating → resolved`. Evidence updates them. But there
is no step anywhere that later asks **whether a hypothesis resolved the right way**.

So the engine's confidence in its own resolution process is unearned — not wrong, just never
checked. Every other quantity in the loop gets revisited; the resolver never does.

(a) ______ (b) ______

### 2. "Conviction" is a decision, not a measurement

Every other quantity in the loop has something that would settle it: a hypothesis resolves,
evidence arrives, a scenario is refuted. **Conviction has no such thing.** No observation
settles it. It is an aggregate you compute over hypothesis states and then treat as a reading.

That makes conviction structurally identical to a hospital calling a patient "ready for
discharge" — five people assess five different things and the aggregate is a *negotiated
output*, not a quantity anyone measured. Reaching a conviction threshold is a decision to stop,
wearing the clothes of a measurement that says you may.

(a) ______ (b) ______

### 3. The loop generates its own evidence

`investigate` is the intervention **and** the thing that produces the signal. The loop's input
is manufactured by its own output — there is no exogenous evidence channel in the cycle.

A loop like that can converge on high confidence purely from evidence it chose to go and find.
Your `balance_rule` — every investigated hypothesis needs at least one *supporting* and one
*challenging* item — is the only structural guard against it. That rule is doing far more work
than its one line suggests, and it is the single thing standing between the engine and
confident self-confirmation.

(a) ______ (b) ______

### 4. The three things that would most distort conviction are the three you don't record

The encoding forced me to declare what is knowingly left out. These came out:

- whether a hypothesis was dropped because it **resolved** or because it got **tiring**
- which evidence was **sought** versus which merely **arrived**
- how much of a conviction score is actually the **deadline**

Each of those changes what conviction means, none is captured anywhere, and all three are
knowable at the time.

(a) ______ (b) ______

---

### The question that matters most

> If you kept this model of your own process current, what would you use it for — and what
> would make you stop opening it?

---

## How this gets scored

Strictly, because the failure mode is hearing what I want to hear.

- **`no` + `an actual decision`** — a genuine result. The project has never had one from a human.
- **`yes, but never stated` + `a conversation`** — partial credit. Making tacit things explicit
  has value but is weaker than discovery.
- **`yes, obviously`** — a restatement, whatever else the answer says.

If all four are `yes, obviously`, that settles it: the representation reorganises what you
already hold, and the right move is to write up the research and stop building. That is a clean
answer and worth more than another artifact nothing can evaluate.

Only item 1 came from the automated query. Items 2–4 came from **encoding forcing choices** —
which quantity is an estimand, which is an aggregate, what gets declared as excluded. If those
three land and item 1 doesn't, the value is in the act of encoding rather than in anything
computed afterward, and the tooling should shrink accordingly.
