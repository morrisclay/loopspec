# Practitioner Test

**Purpose:** the only thing currently capping this project is whether the representation tells
a real operator something they did not already know. A model can catch restatement — and does,
reproducibly — but it cannot judge news. This is the instrument for that.

**How to use it:** send the section below to a founder or operator. Do not explain URAS, do not
explain the score, do not say what you are hoping to hear. It takes about four minutes.

---

## The instrument — send from here down

We took an ordinary description of how a company is run — the goal, what gets measured, what
decisions get made and when — and turned it into a structured model. Then we asked a program to
look for structural gaps: places where the decision-making machinery refers to something the
company does not actually collect.

Below are the gaps it found. For each one, please answer just two things:

**(a) Did you already know this?**  `yes, obviously` / `yes, but not stated` / `no`
**(b) Would it change anything?**  `no` / `a conversation` / `an actual decision`

---

### 1

> The decision rule for whether to narrow the customer profile, change pricing, or stop
> pursuing the market reads three quantities: willingness to pay, sales cycle, and
> implementation cost. Only willingness to pay has anything collecting it. The other two are
> inputs to a decision that nothing measures.

(a) ____________  (b) ____________

### 2

> There is an invariant — product velocity must stay above a minimum viable rate — and nothing
> in the system observes product velocity. If it were violated, nothing would detect it.

(a) ____________  (b) ____________

### 3

> The runway calculation is arithmetic over two measured numbers, so it carries no uncertainty
> of its own. The genuinely uncertain quantity — whether a budget owner exists at all — is the
> one the company's survival turns on, and it is the one with the least measurement pointed at
> it.

(a) ____________  (b) ____________

### 4

> The stated goal is 18 months of runway and the policy fires at 12. That six-month gap is a
> deadband: it exists so the company does not thrash on small fluctuations. It is structurally
> identical to the band in a domestic thermostat that stops the boiler short-cycling. Nobody
> wrote it down as a design decision.

(a) ____________  (b) ____________

---

**Last question, and the most important one:**

> If you had this model of your own company, kept current, what would you actually use it for —
> and what would make you stop opening it?

---

## How to read the answers

This is scored strictly, because the failure mode is hearing what we want to hear.

- **`no` + `an actual decision`** — a genuine claim. This is what the project needs and has
  never yet had from a human.
- **`yes, but not stated` + `a conversation`** — partial credit. Making tacit things explicit
  has value, but it is a weaker claim than discovery.
- **`yes, obviously`** — a restatement, whatever else the answer says. Four of the first six
  claims this project produced died here under model adjudication, and a human saying it is
  worth more than a model saying it.
- **Any answer to the last question that amounts to "nothing"** — the most useful result
  available, and the one to actively look for rather than explain away.

## What happens to the answers

They set `audited: true` and a verdict on each claim in `adjudication/`, which is what `U` in
`ontology/score.md` reads. One `genuine` from a practitioner is worth more than any number of
model-adjudicated ones, because model adjudication is a necessary condition and this is the
actual bar.

If all four come back `yes, obviously`, that is a real result and should be recorded as one.
It would mean the representation is currently reorganising what operators already hold in their
heads — which is the thing the project has been claiming to avoid, and would be the strongest
argument yet for changing direction rather than continuing.
