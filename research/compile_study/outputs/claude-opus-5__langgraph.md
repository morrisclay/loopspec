<!-- model: anthropic/claude-opus-5  tier: strong  target: langgraph  finish: length -->

Below is a runnable LangGraph implementation. The spec is transcribed as data first (so every clause is visible and checkable), then compiled into a graph. Anything the spec states but LangGraph/Python cannot enforce is surfaced by the linter at build time and re-listed at the end.

```python
# customer_acquisition.py
#
# LangGraph implementation of the loop spec `customer_acquisition`.
#
# Layout:
#   §0  spec transcribed as data (no invention)
#   §1  linter (what the spec says but cannot enforce)
#   §2  condition compiler for `when:` expressions
#   §3  estimator math (bayesian / judgement)
#   §4  world adapter (stand-in for the real sensors + effects)
#   §5  graph nodes
#   §6  graph wiring
#   §7  demo driver
#
# Anything marked `OUT-OF-SPEC` is an assumption I had to add to make the loop
# execute; each one is repeated in the "did not survive" report.

from __future__ import annotations

import math
import operator
import random
import re
from dataclasses import dataclass, field
from typing import Annotated, Any, Callable, Optional, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command, interrupt

# ============================================================================
# §0 — THE SPEC, TRANSCRIBED
# ============================================================================

LOOP_NAME = "customer_acquisition"
LOOP_EVERY = "weekly"
TICK_DAYS = 7  # one graph invocation == one weekly tick

CADENCE_DAYS = {"daily": 1, "weekly": 7, "monthly": 28}


@dataclass(frozen=True)
class Regulated:
    name: str
    target: str                              # e.g. "< 400"
    computed_from: tuple[str, ...] = ()

    def compiled_target(self) -> Callable[[float], bool]:
        m = re.fullmatch(r"\s*(<=|>=|<|>|==)\s*(-?\d+(?:\.\d+)?)\s*", self.target)
        if not m:
            raise ValueError(f"unparseable target on {self.name}: {self.target!r}")
        op, val = m.group(1), float(m.group(2))
        fn = {"<": operator.lt, ">": operator.gt, "<=": operator.le,
              ">=": operator.ge, "==": operator.eq}[op]
        return lambda x: fn(x, val)


@dataclass(frozen=True)
class Estimated:
    name: str
    sources: tuple[str, ...]
    method: str                              # "bayesian" | "judgement"
    explains: Optional[str] = None
    settled_by: Optional[str] = None         # prose
    calibrated_by: Optional[str] = None      # absent for product_market_fit


@dataclass(frozen=True)
class Observer:
    name: str
    measures: Optional[str] = None
    every: str = "weekly"
    cost: Optional[str] = None               # "high" — unquantified
    asserted_by: Optional[str] = None


@dataclass(frozen=True)
class Act:
    name: str
    moves: Optional[str] = None
    reversibility: str = "reversible"
    delay: Optional[str] = None              # "2w"
    consumes: tuple[str, ...] = ()
    approval: Optional[str] = None

    @property
    def delay_ticks(self) -> int:
        if not self.delay:
            return 0
        m = re.fullmatch(r"(\d+)([dwm])", self.delay)
        if not m:
            raise ValueError(f"unparseable delay on {self.name}: {self.delay!r}")
        n, unit = int(m.group(1)), m.group(2)
        days = n * {"d": 1, "w": 7, "m": 28}[unit]
        return max(1, round(days / TICK_DAYS))


@dataclass(frozen=True)
class Rule:
    cond: str
    do: Optional[str] = None
    escalate: Optional[str] = None


@dataclass(frozen=True)
class Party:
    name: str
    human: bool = False
    agent: bool = False
    bears: Optional[str] = None
    sees: Optional[tuple[str, ...]] = None   # None == undeclared


REGULATES = {
    "cac": Regulated("cac", "< 400", ("ad_spend", "new_customers")),
    "payback_months": Regulated("payback_months", "< 12"),
}

ESTIMATES = {
    "product_market_fit": Estimated(
        "product_market_fit",
        sources=("customer_interviews", "stripe"),
        method="bayesian",
        explains="cac",
        settled_by="a cohort retains above 80% at month 6",
        calibrated_by=None,                                  # linter flags this
    ),
    "channel_saturation": Estimated(
        "channel_saturation",
        sources=("ad_platform",),
        method="judgement",
    ),
}

OBSERVES = {
    "stripe": Observer("stripe", measures="cac", every="daily"),
    "ad_platform": Observer("ad_platform", measures="channel_saturation", every="daily"),
    "customer_interviews": Observer("customer_interviews", measures="product_market_fit",
                                    every="weekly", cost="high"),
    "board_sentiment": Observer("board_sentiment", every="monthly", asserted_by="investor"),
}

ACTS = {
    "increase_budget": Act("increase_budget", moves="cac", reversibility="reversible",
                           delay="2w", consumes=("runway",)),
    "change_pricing": Act("change_pricing", moves="payback_months", reversibility="costly",
                          delay="4w", approval="founder"),
    "exit_channel": Act("exit_channel", reversibility="irreversible"),
}

WHEN = [
    Rule(cond="cac < 400 and product_market_fit above 0.6", do="increase_budget"),
    Rule(cond="payback_months > 12", do="change_pricing"),
    Rule(cond="product_market_fit below 0.4", escalate="founder"),
]

PARTIES = {
    "founder": Party("founder", human=True, bears="the company",
                     sees=("cac", "product_market_fit")),
    "growth_agent": Party("growth_agent", agent=True, bears="nothing", sees=None),
    "investor": Party("investor", human=True, bears="a position in the fund", sees=None),
}

NEVER = ["spend exceeds committed runway"]

IGNORING = ["competitor_response", "seasonality"]

# ---- OUT-OF-SPEC constants required to make the above executable ------------

CREDIBLE_MASS = 0.80          # what `above`/`below` on an estimate must clear
PMF_PRIOR = (2.0, 3.0)        # Beta prior for product_market_fit
JUDGEMENT_SPREAD = 0.15       # width given to a `judgement` estimate
COMMITTED_RUNWAY = 900_000.0  # the number `never:` compares against
SETTLE_THRESHOLD = 0.80       # "retains above 80%"
SETTLE_MONTH = 6              # "at month 6"
EXPLAINS_MIN_TICKS = 8        # before we complain that `explains:` is unsupported
EXPLAINS_MIN_R = 0.20

# `moves:` names a variable, not a direction or a magnitude. The loop cannot be
# executed without both, so they are declared here, out of spec, and logged.
EFFECT_MODEL: dict[str, dict[str, Any]] = {
    "increase_budget": {"var": "cac", "direction": +1, "magnitude": 0.08, "spend": 25_000.0},
    "change_pricing":  {"var": "payback_months", "direction": -1, "magnitude": 0.20, "spend": 0.0},
    "exit_channel":    {"var": None, "direction": 0, "magnitude": 0.0, "spend": 0.0},
}


# ============================================================================
# §1 — LINTER
# ============================================================================

def lint() -> list[str]:
    out: list[str] = []

    for e in ESTIMATES.values():
        if e.calibrated_by is None:
            out.append(f"E001 estimate `{e.name}` has no `calibrated_by`: nothing in the loop "
                       f"ever checks whether this estimate is any good.")
        if e.settled_by:
            out.append(f"E002 estimate `{e.name}`.settled_by is prose "
                       f"({e.settled_by!r}); executable proxy hand-written, may not match intent.")
        if e.method == "judgement":
            judges = [p.name for p in PARTIES.values() if p.agent or p.human]
            out.append(f"E003 estimate `{e.name}` uses method `judgement` but no party is named "
                       f"as the judge; assigned to `growth_agent` (candidates: {judges}).")
        if e.explains and e.explains not in REGULATES:
            out.append(f"E004 estimate `{e.name}` claims to explain unknown variable "
                       f"`{e.explains}`.")

    referenced = " ".join(r.cond for r in WHEN)
    for e in ESTIMATES.values():
        if e.name not in referenced and not e.explains:
            out.append(f"E005 estimate `{e.name}` is referenced by no `when:` rule and explains "
                       f"nothing: it is computed and discarded.")

    for r in REGULATES.values():
        if not r.computed_from:
            out.append(f"R001 regulated variable `{r.name}` has no `computed_from`: its value is "
                       f"taken verbatim from a sensor payload, unverified.")
        for src in r.computed_from:
            if src not in OBSERVES and src not in ESTIMATES:
                out.append(f"R002 `{r.name}.computed_from` names `{src}`, which is neither an "
                           f"observer nor an estimate; wired to a raw field of `stripe`.")
    if REGULATES["cac"].computed_from and OBSERVES["stripe"].measures == "cac":
        out.append("R003 `cac` is both `computed_from: [ad_spend, new_customers]` and `measured` "
                   "by stripe. Two definitions; the computed one is used.")

    for o in OBSERVES.values():
        if o.measures is None:
            out.append(f"O001 observer `{o.name}` measures nothing and feeds no estimate: its "
                       f"readings are logged and otherwise inert.")
        if o.measures and o.measures not in REGULATES and o.measures not in ESTIMATES:
            out.append(f"O002 observer `{o.name}` measures unknown `{o.measures}`.")
        if o.cost:
            out.append(f"O003 observer `{o.name}` has cost `{o.cost}` with no unit and no budget: "
                       f"cannot be traded off, only logged (and skipped once settled).")
        if o.asserted_by:
            out.append(f"O004 observer `{o.name}` is asserted_by `{o.asserted_by}` on a "
                       f"`{o.every}` cadence: nothing in the graph can make a human assert on "
                       f"schedule; missing assertions are recorded as gaps.")

    fired = {r.do for r in WHEN if r.do}
    for a in ACTS.values():
        if a.name not in fired:
            out.append(f"A001 act `{a.name}` is unreachable: no `when:` rule fires it.")
        if a.moves is None:
            out.append(f"A002 act `{a.name}` declares no `moves:`: its effect on the regulated "
                       f"variables is unstated.")
        if a.moves and a.moves not in REGULATES:
            out.append(f"A003 act `{a.name}` moves unknown `{a.moves}`.")
        out.append(f"A004 act `{a.name}` says `moves: {a.moves}` but gives no direction or "
                   f"magnitude; supplied out of spec in EFFECT_MODEL.")
        if a.reversibility == "irreversible" and not a.approval:
            out.append(f"A005 act `{a.name}` is irreversible and requires no approval; the guard "
                       f"blocks it (policy added out of spec).")
        for res in a.consumes:
            out.append(f"A006 act `{a.name}` consumes `{res}`, which is declared nowhere: "
                       f"initial stock supplied out of spec (COMMITTED_RUNWAY).")

    for r in WHEN:
        if r.do and r.do not in ACTS:
            out.append(f"W001 rule {r.cond!r} fires unknown act `{r.do}`.")
        if r.escalate and r.escalate not in PARTIES:
            out.append(f"W002 rule {r.cond!r} escalates to unknown party `{r.escalate}`.")
    out.append("W003 `when:` gives no ordering, no mutual exclusion, and no rate limit; rules are "
               "evaluated top-to-bottom and may all fire in the same tick.")
    out.append("W004 `above`/`below` on an estimate vs `<`/`>` on a measurement is a distinction "
               f"the spec makes but does not define; read as P(theta) >= {CREDIBLE_MASS}.")

    for p in PARTIES.values():
        if p.sees is None:
            out.append(f"P001 party `{p.name}` has no `sees:`; defaulting to see nothing, which "
                       f"is a guess.")
        if p.bears in (None, "nothing"):
            out.append(f"P002 party `{p.name}` bears nothing; the loop can still route work to "
                       f"it, and consequences land elsewhere. Not enforceable.")
        if p.bears and p.bears not in ("nothing",):
            out.append(f"P003 party `{p.name}` bears {p.bears!r}: prose, no runtime meaning.")

    for n in NEVER:
        out.append(f"N001 never-clause {n!r} is prose; hand-compiled to "
                   f"`cumulative_spend + committed_spend > COMMITTED_RUNWAY`.")
    for i in IGNORING:
        out.append(f"I001 `ignoring: {i}` recorded as metadata only. Nothing detects the moment "
                   f"{i} starts mattering.")
    out.append(f"L001 `every: {LOOP_EVERY}` cannot be honoured inside LangGraph: the graph has no "
               f"clock. An external driver must invoke it once per week.")
    return out


# ============================================================================
# §2 — CONDITION COMPILER
# ============================================================================

CLAUSE = re.compile(
    r"^\s*(?P<lhs>[A-Za-z_][A-Za-z0-9_]*)\s*"
    r"(?P<op><=|>=|==|<|>|above|below)\s*"
    r"(?P<rhs>-?\d+(?:\.\d+)?)\s*$"
)


def compile_condition(expr: str) -> Callable[[dict], tuple[bool, list[str]]]:
    """`and`/`or` over simple clauses. Returns (value, trace)."""
    or_parts = re.split(r"\bor\b", expr)
    parsed: list[list[tuple[str, str, float]]] = []
    for op_ in or_parts:
        and_parts = re.split(r"\band\b", op_)
        group = []
        for c in and_parts:
            m = CLAUSE.match(c)
            if not m:
                raise ValueError(f"unparseable clause {c!r} in {expr!r}")
            group.append((m.group("lhs"), m.group("op"), float(m.group("rhs"))))
        parsed.append(group)

    def run(ctx: dict) -> tuple[bool, list[str]]:
        trace: list[str] = []
        any_true = False
        for group in parsed:
            all_true = True
            for name, op, val in group:
                ok, note = eval_clause(ctx, name, op, val)
                trace.append(note)
                all_true = all_true and ok
            any_true = any_true or all_true
        return any_true, trace

    return run


def eval_clause(ctx: dict, name: str, op: str, val: float) -> tuple[bool, str]:
    if name in ctx["regulated"]:
        x = ctx["regulated"][name]
        if x is None:
            return False, f"{name} unavailable -> false"
        if op in ("above", "below"):
            ok = x > val if op == "above" else x < val
            return ok, (f"{name}={x:.3f} {op} {val} -> {ok} "
                        f"(NOTE: `{op}` used on a measurement, read as a bare comparison)")
        fn = {"<": operator.lt, ">": operator.gt, "<=": operator.le,
              ">=": operator.ge, "==": operator.eq}[op]
        ok = fn(x, val)
        return ok, f"{name}={x:.3f} {op} {val} -> {ok}"

    if name in ctx["estimates"]:
        post = ctx["estimates"][name]
        if post is None:
            return False, f"{name} not yet estimated -> false"
        mass = prob_above(post, val) if op in ("above", ">", ">=") else prob_below(post, val)
        if op in ("above", "below"):
            ok = mass >= CREDIBLE_MASS
            return ok, (f"P({name} {op} {val})={mass:.2f} >= {CREDIBLE_MASS} -> {ok}")
        m = point(post)
        fn = {"<": operator.lt, ">": operator.gt, "<=": operator.le,
              ">=": operator.ge, "==": operator.eq}[op]
        ok = fn(m, val)
        return ok, (f"E[{name}]={m:.3f} {op} {val} -> {ok} "
                    f"(NOTE: sharp comparison on an uncertain estimate; uncertainty discarded)")

    return False, f"unknown symbol `{name}` -> false"


# ============================================================================
# §3 — ESTIMATOR MATH
# ============================================================================

def beta_pdf(a: float, b: float, x: float) -> float:
    if x <= 0 or x >= 1:
        return 0.0
    lg = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    return math.exp(lg + (a - 1) * math.log(x) + (b - 1) * math.log(1 - x))


def prob_above(post: dict, t: float, n: int = 2001) -> float:
    if post["kind"] == "beta":
        a, b = post["a"], post["b"]
        tot = hi = 0.0
        for i in range(1, n):
            x = i / n
            d = beta_pdf(a, b, x)
            tot += d
            if x > t:
                hi += d
        return hi / tot if tot else 0.0
    lo, hi_ = post["value"] - post["spread"], post["value"] + post["spread"]
    if t <= lo:
        return 1.0
    if t >= hi_:
        return 0.0
    return (hi_ - t) / (hi_ - lo)


def prob_below(post: dict, t: float) -> float:
    return 1.0 - prob_above(post, t)


def point(post: dict) -> float:
    return post["a"] / (post["a"] + post["b"]) if post["kind"] == "beta" else post["value"]


def beta_update(post: dict, successes: float, failures: float) -> dict:
    return {"kind": "beta", "a": post["a"] + successes, "b": post["b"] + failures}


def pearson(xs: list[float], ys: list[