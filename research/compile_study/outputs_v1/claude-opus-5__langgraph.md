<!-- model: anthropic/claude-opus-5  tier: strong  target: langgraph  finish: length -->

# `customer_acquisition` — LangGraph implementation

Three files' worth of code, given as one module for portability. Tested shape: `langgraph>=0.2.60`, `langchain-core`, `pyyaml`.

The spec is embedded verbatim as YAML and parsed at import, so the spec — not a hand-copy of it — is what drives the lint, the thresholds, the visibility filters and the audit record.

```python
"""
customer_acquisition.py — LangGraph runtime for the v1 loop spec.

Design notes:
  * One graph invocation == one weekly tick (`runs: weekly`). Scheduling is external
    (cron / LangGraph Platform cron / Airflow). See `run_week()`.
  * State is carried between ticks by the checkpointer on a single thread_id, because
    several spec clauses are inherently multi-tick ("stays above 600 for 14 days",
    `effect_after`, bayesian posteriors).
  * Every clause the graph cannot *enforce* is still carried as machine-readable
    metadata and surfaced at the point of decision, so it shows up in the audit log
    instead of evaporating.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Annotated, Any, Callable, Optional, TypedDict

import yaml
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

# ---------------------------------------------------------------------------
# 1. THE SPEC (single source of truth)
# ---------------------------------------------------------------------------

SPEC_YAML = r"""
loop: customer_acquisition
runs: weekly

goal:
  cost_per_customer:
    keep: below 400
    unit: USD
    from: [ad_spend, new_customers]
  payback_months:
    keep: below 12

beliefs:
  product_market_fit:
    question: "If we keep buying customers like this month's, will they stay?"
    from: [customer_interviews, stripe]
    how: bayesian
    explains: cost_per_customer
    settled_by: "a cohort retains above 80% at month 6"
    known_bias: "reads high when volume is low — interviews only reach people who reply"

  channel_saturation:
    question: "Can this channel absorb more money before cost climbs?"
    from: [ad_platform]
    how: judgement
    checked_by: monthly_spend_vs_cost_review

observes:
  stripe:
    informs: cost_per_customer
    every: daily
    origin: outside
    how: measured

  ad_platform:
    informs: channel_saturation
    every: daily
    origin: ourselves
    how: measured

  customer_interviews:
    informs: product_market_fit
    every: weekly
    cost: high
    origin: outside
    how: reported
    reported_by: customers

  board_sentiment:
    every: monthly
    origin: outside
    how: reported
    reported_by: investor

actions:
  increase_budget:
    moves: cost_per_customer
    can_undo: yes
    effect_after: 2w
    consumes: [runway]

  change_pricing:
    moves: payback_months
    can_undo: costly
    effect_after: 4w
    needs_approval: founder

  exit_channel:
    moves: cost_per_customer
    can_undo: no

when:
  - if: "cost_per_customer below 400 and product_market_fit above 0.6"
    do: increase_budget
  - if: "payback_months above 12"
    do: change_pricing

asks_human_when:
  - "product_market_fit falls below 0.4"
  - "cost_per_customer stays above 600 for 14 days"
  - "any action whose can_undo is no becomes the chosen move"

people:
  founder:
    human: yes
    loses_if_wrong: "the company — runway, and 18-month survival odds"
    sees: [cost_per_customer, product_market_fit]
    may_decide: pricing, and anything that cannot be undone
  growth_agent:
    agent: yes
    loses_if_wrong: nothing
    sees: [cost_per_customer, product_market_fit, channel_saturation]
  investor:
    human: yes
    loses_if_wrong: "a position in the fund"

never:
  - "spend exceeds committed runway"

not_modelling:
  - competitor_response
  - seasonality
"""

SPEC: dict[str, Any] = yaml.safe_load(SPEC_YAML)

# YAML turns `can_undo: yes|no` into booleans; the spec's vocabulary is yes/costly/no.
for _name, _a in SPEC["actions"].items():
    if isinstance(_a.get("can_undo"), bool):
        _a["can_undo"] = "yes" if _a["can_undo"] else "no"

GOALS = SPEC["goal"]
BELIEFS = SPEC["beliefs"]
OBSERVES = SPEC["observes"]
ACTIONS = SPEC["actions"]
PEOPLE = SPEC["people"]
NEVER = SPEC["never"]
NOT_MODELLING = SPEC["not_modelling"]

STALENESS_GRACE = {"daily": 2, "weekly": 9, "monthly": 35}  # days before a source is stale
DUR = {"1w": 7, "2w": 14, "4w": 28}


# ---------------------------------------------------------------------------
# 2. LINTER — the spec's deliberate gaps must be *loud*, not silent
# ---------------------------------------------------------------------------

def lint(spec: dict = SPEC) -> list[str]:
    out: list[str] = []
    for name, b in spec["beliefs"].items():
        if not b.get("checked_by"):
            out.append(
                f"LINT belief.{name}: no `checked_by`. how={b.get('how')} and it "
                f"explains={b.get('explains')} — an unchecked belief is steering a goal."
            )
        if b.get("known_bias") and not b.get("checked_by"):
            out.append(
                f"LINT belief.{name}: declares known_bias with no check that would catch it "
                f"({b['known_bias']!r})."
            )
    for name, o in spec["observes"].items():
        if not o.get("informs"):
            out.append(
                f"LINT observes.{name}: informs nothing. Collected every {o.get('every')} "
                f"from {o.get('reported_by', o.get('origin'))} with no stated use."
            )
    for name, a in spec["actions"].items():
        if a.get("can_undo") == "no" and not a.get("needs_approval"):
            out.append(
                f"LINT actions.{name}: can_undo=no and no needs_approval. "
                f"Runtime falls back to people.founder.may_decide "
                f"('anything that cannot be undone')."
            )
        if a.get("can_undo") in ("no", "costly") and not a.get("effect_after"):
            out.append(f"LINT actions.{name}: irreversible-ish and no effect_after — "
                       f"cannot embargo re-firing or attribution.")
    for name, g in spec["goal"].items():
        if not g.get("from"):
            out.append(f"LINT goal.{name}: no `from`. Runtime must accept it as an "
                       f"unattributed external number.")
    for name, p in spec["people"].items():
        if not p.get("sees") and p.get("human"):
            out.append(f"LINT people.{name}: loses_if_wrong={p.get('loses_if_wrong')!r} "
                       f"but sees nothing. Accountable and blind.")
    triggered = {r["do"] for r in spec["when"]}
    for name in spec["actions"]:
        if name not in triggered:
            out.append(f"LINT actions.{name}: no `when` rule proposes it; reachable only "
                       f"by human override.")
    return out


# ---------------------------------------------------------------------------
# 3. Tiny condition language for `when` (no eval)
# ---------------------------------------------------------------------------

_TERM = re.compile(r"^\s*(?P<lhs>[a-z_][a-z0-9_]*)\s+(?P<op>above|below)\s+(?P<rhs>-?[\d.]+)\s*$")


def eval_condition(expr: str, ns: dict[str, Optional[float]]) -> Optional[bool]:
    """Returns None if any referenced quantity is unknown (fail-closed, never guesses)."""
    if " or " in expr and " and " in expr:
        raise ValueError(f"unsupported mixed precedence in condition: {expr!r}")
    join, parts = ("and", expr.split(" and ")) if " and " in expr else \
                  ("or", expr.split(" or ")) if " or " in expr else ("and", [expr])
    results = []
    for part in parts:
        m = _TERM.match(part)
        if not m:
            raise ValueError(f"cannot parse condition term: {part!r}")
        lhs, op, rhs = m["lhs"], m["op"], float(m["rhs"])
        val = ns.get(lhs)
        if val is None:
            return None
        results.append(val > rhs if op == "above" else val < rhs)
    return all(results) if join == "and" else any(results)


def parse_keep(keep: str) -> tuple[str, float]:
    m = _TERM.match("x " + keep)
    if not m:
        raise ValueError(f"cannot parse keep: {keep!r}")
    return m["op"], float(m["rhs"])


# ---------------------------------------------------------------------------
# 4. State
# ---------------------------------------------------------------------------

def merge_dict(old: dict | None, new: dict | None) -> dict:
    return {**(old or {}), **(new or {})}


def merge_readings(old: list | None, new: list | None) -> list:
    by = {r["date"]: dict(r) for r in (old or [])}
    for r in new or []:
        by[r["date"]] = {**by.get(r["date"], {}), **r}
    return [by[k] for k in sorted(by)][-120:]


def append_trim(old: list | None, new: list | None) -> list:
    return ((old or []) + (new or []))[-500:]


class LoopState(TypedDict, total=False):
    tick: int
    now: str                                        # ISO date of this weekly tick
    observations: Annotated[dict, merge_dict]       # per-source latest + freshness + provenance
    readings: Annotated[list, merge_readings]       # daily goal-metric history
    goals: dict                                     # {metric: {value, keep, ok, sources_stale}}
    beliefs: Annotated[dict, merge_dict]            # {name: {value, ...posterior, flags}}
    proposals: list                                 # candidate moves this tick
    approvals: dict
    escalations: list
    blocked: list
    executed: list
    pending_effects: list                           # actions inside their effect_after window
    runway: dict
    lint: list
    audit: Annotated[list, append_trim]
    views: dict
    operator_proposals: list                        # human-injected moves (e.g. exit_channel)


# ---------------------------------------------------------------------------
# 5. Adapters — everything outside the loop
# ---------------------------------------------------------------------------

@dataclass
class Adapters:
    stripe: Callable[[date], dict]                     # daily new_customers, payback_months, cohorts
    ad_platform: Callable[[date], dict]                # daily ad_spend, cost curve
    customer_interviews: Callable[[date], dict]        # weekly coded interview responses
    board_sentiment: Callable[[date], dict]            # monthly; informs nothing (see lint)
    runway: Callable[[date], dict]                     # available_usd, committed_usd
    cohort_retention_m6: Callable[[date], Optional[float]]      # for `settled_by`
    monthly_spend_vs_cost_review: Callable[[date], Optional[dict]]  # `checked_by`
    judge_channel_saturation: Callable[[dict], dict]   # growth_agent judgement -> {value, why}
    propose_params: Callable[[str, dict], dict]        # growth_agent sizes the move
    execute: Callable[[str, dict], dict]               # side effects


def A(config) -> Adapters:
    return config["configurable"]["adapters"]


# ---------------------------------------------------------------------------
# 6. Nodes
# ---------------------------------------------------------------------------

def tick(state: LoopState, config) -> dict:
    now = date.fromisoformat(state["now"])
    still_pending = [p for p in state.get("pending_effects", [])
                     if date.fromisoformat(p["visible_from"]) > now]
    matured = [p for p in state.get("pending_effects", [])
               if date.fromisoformat(p["visible_from"]) <= now]
    return {
        "tick": state.get("tick", 0) + 1,
        "proposals": [], "approvals": {}, "escalations": [], "blocked": [],
        "executed": [], "views": {},
        "pending_effects": still_pending,
        "lint": lint(),
        "audit": [f"[{state['now']}] tick {state.get('tick', 0) + 1} start; "
                  f"effect windows open={[p['action'] for p in still_pending]}, "
                  f"matured={[p['action'] for p in matured]}"],
    }


def _obs(source: str, now: date, at: date, payload: dict) -> dict:
    meta = OBSERVES[source]
    grace = STALENESS_GRACE[meta["every"]]
    stale = (now - at).days > grace
    return {source: {
        "at": at.isoformat(), "stale": stale, "payload": payload,
        # provenance carried verbatim so downstream readers know how much to trust it
        "informs": meta.get("informs"), "every": meta["every"],
        "origin": meta["origin"], "how": meta["how"],
        "reported_by": meta.get("reported_by"), "cost": meta.get("cost"),
    }}


def observe_stripe(state: LoopState, config) -> dict:
    now = date.fromisoformat(state["now"])
    d = A(config).stripe(now)
    return {"observations": _obs("stripe", now, date.fromisoformat(d["as_of"]), d),
            "audit": [f"[{state['now']}] observed stripe (measured, outside): "
                      f"{len(d['daily'])} daily rows"]}


def observe_ad_platform(state: LoopState, config) -> dict:
    now = date.fromisoformat(state["now"])
    d = A(config).ad_platform(now)
    return {"observations": _obs("ad_platform", now, date.fromisoformat(d["as_of"]), d),
            "audit": [f"[{state['now']}] observed ad_platform (measured, ourselves — "
                      f"we caused this spend to exist)"]}


def observe_customer_interviews(state: LoopState, config) -> dict:
    now = date.fromisoformat(state["now"])
    d = A(config).customer_interviews(now)
    return {"observations": _obs("customer_interviews", now, date.fromisoformat(d["as_of"]), d),
            "audit": [f"[{state['now']}] observed customer_interviews "
                      f"(cost=high, reported_by=customers — self-selected): "
                      f"n={d['responses']}"]}


def observe_board_sentiment(state: LoopState, config) -> dict:
    """Collected because the spec says to collect it. `informs: null` -> it may not
    enter any belief, goal or rule. It is recorded and shown to nobody automatically."""
    now = date.fromisoformat(state["now"])
    d = A(config).board_sentiment(now)
    return {"observations": _obs("board_sentiment", now, date.fromisoformat(d["as_of"]), d),
            "audit": [f"[{state['now']}] observed board_sentiment (reported_by=investor); "
                      f"informs nothing — quarantined from all inference (see LINT)"]}


def compute_goals(state: LoopState, config) -> dict:
    """cost_per_customer = ad_spend / new_customers, joined on day.
    payback_months arrives with no declared `from` — taken as given, flagged."""
    obs = state["observations"]
    stripe, adp = obs["stripe"], obs["ad_platform"]
    new_by_day = {r["date"]: r for r in stripe["payload"]["daily"]}
    spend_by_day = {r["date"]: r for r in adp["payload"]["daily"]}
    rows = []
    for day in sorted(set(new_by_day) & set(spend_by_day)):
        nc = new_by_day[day]["new_customers"]
        spend = spend_by_day[day]["ad_spend"]
        rows.append({
            "date": day, "ad_spend": spend, "new_customers": nc,
            "cost_per_customer": (spend / nc) if nc else None,
            "payback_months": new_by_day[day].get("payback_months"),
        })
    readings = merge_readings(state.get("readings"), rows)

    goals = {}
    for metric, g in GOALS.items():
        op, thr = parse_keep(g["keep"])
        latest = next((r[metric] for r in reversed(readings) if r.get(metric) is not None), None)
        needed = {"cost_per_customer": ["stripe", "ad_platform"],
                  "payback_months": ["stripe"]}[metric]
        stale = [s for s in needed if obs.get(s, {}).get("stale", True)]
        goals[metric] = {
            "value": latest, "keep": g["keep"], "unit": g.get("unit"),
            "ok": None if latest is None else (latest < thr if op == "below" else latest > thr),
            "sources_stale": stale,
            "from_declared": g.get("from"),
            "unattributed": not g.get("from"),
        }
    return {"readings": rows, "goals": goals,
            "audit": [f"[{state['now']}] goals: " + ", ".join(
                f"{k}={v['value']} (keep {v['keep']}) ok={v['ok']}"
                f"{' STALE:' + ','.join(v['sources_stale']) if v['sources_stale'] else ''}"
                for k, v in goals.items())]}


def update_beliefs(state: LoopState, config) -> dict:
    """product_market_fit: bayesian (Beta–Binomial).
       channel_saturation: judgement, delegated to growth_agent."""
    obs, now = state["observations"], date.fromisoformat(state["now"])
    prev = state.get("beliefs", {})
    audit, out = [], {}

    # --- product_market_fit -------------------------------------------------
    spec = BELIEFS["product_market_fit"]
    pmf_prev = prev.get("product_market_fit", {"alpha": 2.0, "beta": 2.0, "settled": False})
    settled_value = A(config).cohort_retention_m6(now)
    if pmf_prev.get("settled"):
        pmf = dict(pmf_prev)
        audit.append(f"[{state['now']}] product_market_fit is settled_by "
                     f"{spec['settled_by']!r}; frozen, no further updating")
    else:
        a, b = pmf_prev["alpha"], pmf_prev["beta"]
        # measured evidence: stripe cohort retention (full weight)
        for c in obs["stripe"]["payload"].get("cohorts", []):
            a += c["retained"]
            b += c["size"] - c["retained"]
        # reported evidence: interviews are self-selected -> half weight
        iv = obs["customer_interviews"]["payload"]
        n = iv["responses"]
        a += 0.5 * iv["would_stay"]
        b += 0.5 * (n - iv["would_stay"])
        value = a / (a + b)
        bias_active = n < 10
        pmf = {
            "value": round(value, 4), "alpha": a, "beta": b,
            "n_interviews": n, "how": spec["how"], "explains": spec["explains"],
            "question": spec["question"],
            "known_bias": spec["known_bias"],
            "bias_active": bias_active,
            "checked_by": spec.get("checked_by"),      # None — see LINT
            "unchecked": not spec.get("checked_by"),
            "settled_by": spec["settled_by"],
            "settled": settled_value is not None and settled_value > 0.80,
            "settle_evidence": settled_value,
            "updated": state["now"],
        }
        if bias_active:
            audit.append(f"[{state['now']}] product_market_fit={pmf['value']} with n={n} — "
                         f"known_bias ACTIVE: {spec['known_bias']}")
