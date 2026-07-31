<!-- model: x-ai/grok-4.5  tier: strong  target: langgraph  finish: stop -->

Implementing the customer-acquisition loop as a LangGraph graph, preserving spec semantics where the framework allows.

```python
"""
customer_acquisition loop — LangGraph (Python) implementation
Derived from the v1 loop vocabulary spec.
"""

from __future__ import annotations

import operator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Annotated, Any, Literal, Optional, Sequence, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command


# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------

class Origin(str, Enum):
    OUTSIDE = "outside"
    OURSELVES = "ourselves"


class HowObserved(str, Enum):
    MEASURED = "measured"
    REPORTED = "reported"


class BeliefHow(str, Enum):
    BAYESIAN = "bayesian"
    JUDGEMENT = "judgement"


class UndoKind(str, Enum):
    YES = "yes"
    COSTLY = "costly"
    NO = "no"


@dataclass
class GoalMetric:
    name: str
    keep: str  # e.g. "below 400"
    threshold: float
    direction: Literal["below", "above"]
    unit: Optional[str] = None
    derived_from: list[str] = field(default_factory=list)

    def satisfied(self, value: Optional[float]) -> bool:
        if value is None:
            return False
        if self.direction == "below":
            return value < self.threshold
        return value > self.threshold


GOALS = {
    "cost_per_customer": GoalMetric(
        name="cost_per_customer",
        keep="below 400",
        threshold=400.0,
        direction="below",
        unit="USD",
        derived_from=["ad_spend", "new_customers"],
    ),
    "payback_months": GoalMetric(
        name="payback_months",
        keep="below 12",
        threshold=12.0,
        direction="below",
    ),
}


@dataclass
class BeliefSpec:
    name: str
    question: str
    sources: list[str]
    how: BeliefHow
    explains: Optional[str] = None
    settled_by: Optional[str] = None
    known_bias: Optional[str] = None
    checked_by: Optional[str] = None  # None = intentionally unchecked (linter point)


BELIEFS = {
    "product_market_fit": BeliefSpec(
        name="product_market_fit",
        question="If we keep buying customers like this month's, will they stay?",
        sources=["customer_interviews", "stripe"],
        how=BeliefHow.BAYESIAN,
        explains="cost_per_customer",
        settled_by="a cohort retains above 80% at month 6",
        known_bias="reads high when volume is low — interviews only reach people who reply",
        checked_by=None,  # intentional: no checked_by
    ),
    "channel_saturation": BeliefSpec(
        name="channel_saturation",
        question="Can this channel absorb more money before cost climbs?",
        sources=["ad_platform"],
        how=BeliefHow.JUDGEMENT,
        checked_by="monthly_spend_vs_cost_review",
    ),
}


@dataclass
class ObserveSpec:
    name: str
    every: str
    origin: Origin
    how: HowObserved
    informs: Optional[str] = None
    cost: Optional[str] = None
    reported_by: Optional[str] = None


OBSERVES = {
    "stripe": ObserveSpec(
        name="stripe",
        informs="cost_per_customer",
        every="daily",
        origin=Origin.OUTSIDE,
        how=HowObserved.MEASURED,
    ),
    "ad_platform": ObserveSpec(
        name="ad_platform",
        informs="channel_saturation",
        every="daily",
        origin=Origin.OURSELVES,
        how=HowObserved.MEASURED,
    ),
    "customer_interviews": ObserveSpec(
        name="customer_interviews",
        informs="product_market_fit",
        every="weekly",
        cost="high",
        origin=Origin.OUTSIDE,
        how=HowObserved.REPORTED,
        reported_by="customers",
    ),
    "board_sentiment": ObserveSpec(
        name="board_sentiment",
        informs=None,  # collected without saying what it tells you
        every="monthly",
        origin=Origin.OUTSIDE,
        how=HowObserved.REPORTED,
        reported_by="investor",
    ),
}


@dataclass
class ActionSpec:
    name: str
    moves: str
    can_undo: UndoKind
    effect_after: timedelta
    consumes: list[str] = field(default_factory=list)
    needs_approval: Optional[str] = None


ACTIONS = {
    "increase_budget": ActionSpec(
        name="increase_budget",
        moves="cost_per_customer",
        can_undo=UndoKind.YES,
        effect_after=timedelta(weeks=2),
        consumes=["runway"],
    ),
    "change_pricing": ActionSpec(
        name="change_pricing",
        moves="payback_months",
        can_undo=UndoKind.COSTLY,
        effect_after=timedelta(weeks=4),
        needs_approval="founder",
    ),
    "exit_channel": ActionSpec(
        name="exit_channel",
        moves="cost_per_customer",
        can_undo=UndoKind.NO,
        effect_after=timedelta(0),
        # no needs_approval — intentional (linter point)
    ),
}


@dataclass
class PersonSpec:
    name: str
    is_human: bool
    loses_if_wrong: str
    sees: list[str] = field(default_factory=list)
    may_decide: list[str] = field(default_factory=list)


PEOPLE = {
    "founder": PersonSpec(
        name="founder",
        is_human=True,
        loses_if_wrong="the company — runway, and 18-month survival odds",
        sees=["cost_per_customer", "product_market_fit"],
        may_decide=["pricing", "anything_that_cannot_be_undone"],
    ),
    "growth_agent": PersonSpec(
        name="growth_agent",
        is_human=False,
        loses_if_wrong="nothing",
        sees=["cost_per_customer", "product_market_fit", "channel_saturation"],
    ),
    "investor": PersonSpec(
        name="investor",
        is_human=True,
        loses_if_wrong="a position in the fund",
        sees=[],  # accountable and blind
    ),
}


NEVER = ["spend exceeds committed runway"]
NOT_MODELLING = ["competitor_response", "seasonality"]

LOOP_NAME = "customer_acquisition"
RUNS = "weekly"

# Hard guards / human-ask thresholds from spec
CPC_TARGET = 400.0
CPC_ESCALATE = 600.0
CPC_ESCALATE_DAYS = 14
PMF_INCREASE_BUDGET = 0.6
PMF_ASK_HUMAN = 0.4
PAYBACK_TARGET = 12.0


# ---------------------------------------------------------------------------
# Graph state
# ---------------------------------------------------------------------------

class Observation(TypedDict, total=False):
    source: str
    at: str
    payload: dict[str, Any]


class BeliefState(TypedDict, total=False):
    value: float          # 0..1 for PMF; heuristic score for saturation
    uncertainty: float
    last_updated: str
    notes: str


class PendingAction(TypedDict, total=False):
    name: str
    chosen_at: str
    effect_after: str     # ISO datetime when effect lands
    approved: Optional[bool]
    consumptions: dict[str, float]


class HumanAsk(TypedDict, total=False):
    reason: str
    context: dict[str, Any]


def _merge_dicts(a: dict, b: dict) -> dict:
    out = dict(a or {})
    out.update(b or {})
    return out


class LoopState(TypedDict, total=False):
    # clock / cadence
    now: str                          # ISO datetime
    week_index: int

    # raw / derived metrics
    ad_spend: float
    new_customers: int
    cost_per_customer: float
    payback_months: float
    runway: float                     # remaining committed runway (USD)
    spend_this_period: float

    # streak helpers
    cpc_above_600_since: Optional[str]

    # beliefs
    beliefs: dict[str, BeliefState]   # product_market_fit, channel_saturation

    # observation log (append)
    observations: Annotated[list[Observation], operator.add]

    # board sentiment collected but informs nothing
    board_sentiment: Optional[str]

    # action pipeline
    proposed_actions: list[str]
    pending_actions: list[PendingAction]
    applied_actions: Annotated[list[str], operator.add]

    # human-in-the-loop
    human_asks: list[HumanAsk]
    await_human: bool
    human_decision: Optional[dict[str, Any]]

    # safety
    violated_never: list[str]
    halted: bool

    # audit
    log: Annotated[list[str], operator.add]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_ts(s: str) -> datetime:
    return datetime.fromisoformat(s)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _visibility(person: str, state: LoopState) -> dict[str, Any]:
    """Filter state to what a person is allowed to see."""
    spec = PEOPLE[person]
    view = {}
    metric_map = {
        "cost_per_customer": state.get("cost_per_customer"),
        "product_market_fit": (state.get("beliefs") or {}).get("product_market_fit"),
        "channel_saturation": (state.get("beliefs") or {}).get("channel_saturation"),
    }
    for key in spec.sees:
        view[key] = metric_map.get(key)
    return view


def _cpc(ad_spend: float, new_customers: int) -> float:
    if new_customers <= 0:
        return float("inf")
    return ad_spend / new_customers


def _would_exceed_runway(state: LoopState, extra_spend: float) -> bool:
    return (state.get("spend_this_period", 0.0) + extra_spend) > state.get("runway", 0.0)


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

def tick(state: LoopState) -> dict:
    """Advance the weekly loop clock."""
    now = _parse_ts(state["now"]) if state.get("now") else datetime.utcnow()
    # weekly cadence
    if state.get("week_index") is None:
        week = 0
    else:
        week = state["week_index"] + 1
        now = now + timedelta(weeks=1)
    return {
        "now": _iso(now),
        "week_index": week,
        "spend_this_period": 0.0,
        "proposed_actions": [],
        "human_asks": [],
        "await_human": False,
        "log": [f"tick: week={week} now={_iso(now)}"],
    }


def observe(state: LoopState) -> dict:
    """
    Ingest observations per OBSERVES specs.
    External connectors would replace the 'simulator' payloads below.
    Cadence is enforced softly: daily sources may be polled every weekly run
    with latest snapshot; weekly/monthly gated by week_index.
    """
    now = state["now"]
    week = state.get("week_index", 0)
    obs: list[Observation] = []
    updates: dict[str, Any] = {}
    log = []

    # --- stripe (daily, measured, outside) → cost_per_customer ---
    stripe_payload = state.get("_sim_stripe") or {
        "ad_spend_attributed": state.get("ad_spend", 0.0),
        "new_customers": state.get("new_customers", 0),
    }
    # Real system: fetch from Stripe API. Here we recompute CPC from state.
    ad_spend = float(state.get("ad_spend", 0.0))
    new_customers = int(state.get("new_customers", 0))
    cpc = _cpc(ad_spend, new_customers)
    obs.append({"source": "stripe", "at": now, "payload": {"cpc_inputs": True}})
    updates["cost_per_customer"] = cpc
    log.append(f"observe.stripe: cpc={cpc:.2f}")

    # CPC > 600 streak tracking
    if cpc > CPC_ESCALATE:
        if not state.get("cpc_above_600_since"):
            updates["cpc_above_600_since"] = now
    else:
        updates["cpc_above_600_since"] = None

    # --- ad_platform (daily, measured, ourselves) → channel_saturation ---
    ad_payload = state.get("_sim_ad_platform") or {
        "spend": ad_spend,
        "marginal_cpc_trend": state.get("marginal_cpc_trend", 0.0),
    }
    obs.append({"source": "ad_platform", "at": now, "payload": ad_payload})
    log.append("observe.ad_platform: snapshot")

    # --- customer_interviews (weekly, reported, outside, cost=high) ---
    interview_payload = state.get("_sim_interviews") or {
        "n": 0,
        "intent_to_stay": None,
        "reported_by": "customers",
    }
    obs.append({
        "source": "customer_interviews",
        "at": now,
        "payload": {**interview_payload, "cost": "high", "how": "reported"},
    })
    log.append("observe.customer_interviews: weekly (high cost, reported by customers)")

    # --- board_sentiment (monthly, reported by investor, informs nothing) ---
    if week % 4 == 0:
        sentiment = state.get("_sim_board_sentiment", state.get("board_sentiment", "neutral"))
        obs.append({
            "source": "board_sentiment",
            "at": now,
            "payload": {"sentiment": sentiment, "reported_by": "investor"},
        })
        updates["board_sentiment"] = sentiment
        log.append("observe.board_sentiment: collected (informs nothing)")

    updates["observations"] = obs
    updates["log"] = log
    return updates


def update_beliefs(state: LoopState) -> dict:
    """
    product_market_fit: bayesian (no checked_by).
    channel_saturation: judgement, checked_by monthly_spend_vs_cost_review.
    """
    now = state["now"]
    beliefs = dict(state.get("beliefs") or {})
    log = []

    # ----- product_market_fit (bayesian over interviews + stripe) -----
    prior = beliefs.get("product_market_fit") or {
        "value": 0.5,
        "uncertainty": 1.0,
        "last_updated": now,
        "notes": "",
    }
    # Soft evidence from interviews (reported — customers choose what to tell us)
    interview_obs = None
    for o in reversed(state.get("observations") or []):
        if o.get("source") == "customer_interviews":
            interview_obs = o.get("payload") or {}
            break
    intent = None
    n = 0
    if interview_obs:
        intent = interview_obs.get("intent_to_stay")  # 0..1 or None
        n = int(interview_obs.get("n") or 0)

    # known_bias: reads high when volume is low
    bias_note = BELIEFS["product_market_fit"].known_bias
    pmf = float(prior.get("value", 0.5))
    unc = float(prior.get("uncertainty", 1.0))
    if intent is not None and n > 0:
        # simple bayesian-ish shrink toward evidence; stronger shrink when n larger
        strength = min(1.0, n / 30.0)  # saturates ~30 interviews
        # correct for low-volume high-read bias: pull down when n small
        biased_intent = intent
        if n < 10:
            biased_intent = intent * (0.7 + 0.3 * (n / 10.0))
        pmf = (1 - strength) * pmf + strength * float(biased_intent)
        unc = max(0.05, unc * (1 - 0.5 * strength))
    # stripe retention proxy could refine; settled_by is month-6 cohort >80%
    # We do not auto-settle here; mark note if external settlement flag present.
    notes = prior.get("notes") or ""
    if state.get("_cohort_m6_retention") is not None:
        if state["_cohort_m6_retention"] > 0.80:
            notes = (notes + " | SETTLED: cohort m6 retention >80%").strip(" |")
            unc = min(unc, 0.1)

    beliefs["product_market_fit"] = {
        "value": pmf,
        "uncertainty": unc,
        "last_updated": now,
        "notes": notes or bias_note or "",
    }
    log.append(f"belief.product_market_fit: value={pmf:.3f} unc={unc:.3f} (bayesian, no checked_by)")

    # ----- channel_saturation (judgement) -----
    sat_prior = beliefs.get("channel_saturation") or {
        "value": 0.3,
        "uncertainty": 0.5,
        "last_updated": now,
        "notes": "",
    }
    # judgement from ad_platform marginal trend; checked monthly
    trend = 0.0
    for o in reversed(state.get("observations") or []):
        if o.get("source") == "ad_platform":
            trend = float((o.get("payload") or {}).get("marginal_cpc_trend") or 0.0)
            break
    # higher trend → more saturated
    sat = min(1.0, max(0.0, 0.5 * float(sat_prior.get("value", 0.3)) + 0.5 * (trend / 10.0 if trend else float(sat_prior.get("value", 0.3)))))
    sat_notes = sat_prior.get("notes") or ""
    week = state.get("week_index", 0)
    if week % 4 == 0:
        # checked_by: monthly_spend_vs_cost_review
        sat_notes = f"checked_by monthly_spend_vs_cost_review at week={week}"
        log.append("belief.channel_saturation: monthly check ran")

    beliefs["channel_saturation"] = {
        "value": sat,
        "uncertainty": float(sat_prior.get("uncertainty", 0.5)),
        "last_updated": now,
        "notes": sat_notes,
    }
    log.append(f"belief.channel_saturation: value={sat:.3f} (judgement)")

    return {"beliefs": beliefs, "log": log}


def evaluate_goals_and_policies(state: LoopState) -> dict:
    """
    when:
      - if CPC below 400 and PMF above 0.6 → increase_budget
      - if payback_months above 12 → change_pricing
    Also surface exit_channel as a candidate only via human / other logic;
    spec does not auto-bind it to a when-clause.
    """
    cpc = state.get("cost_per_customer")
    payback = state.get("payback_months")
    pmf = ((state.get("beliefs") or {}).get("product_market_fit") or {}).get("value")
    proposed: list[str] = []
    log = []

    if cpc is not None and pmf is not None:
        if cpc < CPC_TARGET and pmf > PMF_INCREASE_BUDGET:
            proposed.append("increase_budget")
            log.append("policy: increase_budget (cpc<400 and pmf>0.6)")

    if payback is not None and payback > PAYBACK_TARGET:
        proposed.append("change_pricing")
        log.append("policy: change_pricing (payback_months>12)")

    return {"proposed_actions": proposed, "log": log or ["policy: no automatic action"]}


def check_human_gates(state: LoopState) -> dict:
    """
    asks_human_when:
      - pmf < 0.4
      - cpc stays above 600 for 14 days
      - any action whose can_undo is no becomes the chosen move
    + needs_approval on change_pricing → founder
    """
    asks: list[HumanAsk] = []
    now = _parse_ts(state["now"])
    pmf = ((state.get("beliefs") or {}).get("product_market_fit") or {}).get("value")
    cpc = state.get("cost_per_customer")

    if pmf is not None and pmf < PMF_ASK_HUMAN:
        asks.append({
            "reason": "product_market_fit falls below 0.4",
            "context": {"pmf": pmf, "visible_to": _visibility("founder", state)},
        })

    since = state.get("cpc_above_600_since")
    if since and cpc is not None and cpc > CPC_ESCALATE:
        days = (now - _parse_ts(since)).days
        if days >= CPC_ESCALATE_DAYS:
            asks.append({
                "reason": "cost_per_customer stays above 600 for 14 days",
                "context": {"cpc": cpc, "days": days},
            })

    for name in state.get("proposed_actions") or []:
        spec = ACTIONS[name]
        if spec.can_undo == UndoKind.NO:
            asks.append({
                "reason": "any action whose can_undo is no becomes the chosen move",
                "context": {"action": name},
            })
        if spec.needs_approval:
            asks.append({
                "reason": f"needs_approval: {spec.needs_approval}",
                "context": {
                    "action": name,
                    "approver": spec.needs_approval,
                    "may_decide": PEOPLE[spec.needs_approval].may_decide,
                    "visible_to": _visibility(spec.needs_approval, state),
                },
            })

    # If exit_channel were proposed, it has can_undo=no and no needs_approval
    # — still caught by the can_undo gate above.

    await_human = len(asks) > 0
    return {
        "human_asks": asks,
        "await_human": await_human,
        "log": [f"human_gates: {len(asks)} ask(s), await={await_human}"],
    }


def human_gate(state: LoopState) -> dict:
    """
    Block for founder (and record investor blindness) when required.
    Uses LangGraph interrupt so a human can resume with a decision payload:
      { "approve": [action_name, ...], "reject": [...], "force": [...] }
    """
    if not state.get("await_human"):
        return {"log": ["human_gate: skip"]}

    payload = {
        "loop": LOOP_NAME,
        "asks": state.get("human_asks") or [],
        "proposed": state.get("proposed_actions") or [],
        "founder_view": _visibility("founder", state),
        "growth_agent_view": _visibility("growth_agent", state),
        "investor_view": _visibility("investor", state),  # intentionally empty
        "people": {
            k: {
                "human": p.is_human,
                "loses_if_wrong": p.loses_if_wrong,
                "may_decide": p.may_decide,
            }
            for k, p in PEOPLE.items()
        },
    }
    decision = interrupt(payload)
    # decision expected as dict when resumed
    return {
        "human_decision": decision if isinstance(decision, dict) else {"raw": decision},
        "await_human": False,
        "log": ["human_gate: decision received"],
    }


def authorize_actions(state: LoopState) -> dict:
    """Apply human decision + policy proposals → pending_actions (not yet effecting)."""
    now = _parse_ts(state["now"])
    proposed = list(state.get("proposed_actions") or [])
    decision = state.get("human_decision") or {}
    approve = set(decision.get("approve") or [])
    reject = set(decision.get("reject") or [])
    force = list(decision.get("force") or [])

    # start from proposed, remove rejects; if there were human asks involving approval,
    # require explicit approve for needs_approval / can_undo=no actions
    chosen = []
    for name in proposed + force:
        if name in reject:
            continue
        spec = ACTIONS[name]
        needs_explicit = (
            spec.needs_approval is not None
            or spec.can_undo == UndoKind.NO
            or state.get("human_asks")
        )
        # If we interrupted, require approve list for gated actions
        if state.get("human_decision") is not None and (
            spec.needs_approval or spec.can_undo == UndoKind.NO
        ):
            if name not in approve and name not in force:
                continue
        elif needs_explicit and state.get("human_asks") and not state.get("human_decision"):
            # safety: shouldn't happen if graph routes correctly
            continue
        if name not in chosen:
            chosen.append(name)

    pending: list[PendingAction] = []
    for name in chosen:
        spec = ACTIONS[name]
        pending.append({
            "name": name,
            "chosen_at": _iso(now),
            "effect_after": _iso(now + spec.effect_after),
            "approved": True,
            "consumptions": {},
        })

    return {
        "pending_actions": pending,
        "log": [f"authorize: pending={[p['name'] for p in pending]}"],
    }


def guard_never(state: LoopState) -> dict:
    """never: spend exceeds committed runway."""
    violations = []
    # Estimate spend impact of pending increase_budget
    extra = 0.0
    for p in state.get("pending_actions") or []:
        if p["name"] == "increase_budget":
            # default bump; real system would carry amount
            bump = float((state.get("human_decision") or {}).get("budget_delta") or state.get("default_budget_delta", 1000.0))
            extra += bump
            p.setdefault("consumptions", {})["runway"] = bump

    if _would_exceed_runway(state, extra):
        violations.append("spend exceeds committed runway")

    if violations:
        # drop spend-consuming actions
        safe_pending = [
            p for p in (state.get("pending_actions") or [])
            if p["name"] != "increase_budget"
        ]
        return {
            "violated_never": violations,
            "pending_actions": safe_pending,
            "halted": False,  # halt spend, not whole company loop
            "log": [f"NEVER violated: {violations}; stripped increase_budget"],
        }
    return {"violated_never": [], "log": ["never: ok"]}


def apply_due_effects(state: LoopState) -> dict:
    """
    Materialize actions whose effect_after has elapsed.
    increase_budget → consumes runway, moves cost_per_customer (after 2w)
    change_pricing → moves payback_months (after 4w), costly undo
    exit_channel → moves cost_per_customer, irreversible
    """
    now = _parse_ts(state["now"])
    still_pending: list[PendingAction] = []
    applied = []
    log = []
    updates: dict[str, Any] = {}
    runway = float(state.get("runway", 0.0))
    spend_this = float(state.get("spend_this_period", 0.0))
    ad_spend = float(state.get("ad_spend", 0.0))
    payback = state.get("payback_months")
    cpc = state.get("cost_per_customer")

    for p in state.get("pending_actions") or []:
        if _parse_ts(p["effect_after"]) > now:
            still_pending.append(p)
            continue
        name = p["name"]
        spec = ACTIONS[name]
        if name == "increase_budget":
            bump = float((p.get("consumptions") or {}).get("runway") or state.get("default_budget_delta", 1000.0))
            if spend_this + bump > runway:
                log.append("apply: increase_budget blocked at effect time by runway")
                continue
            runway -= bump
            spend_this += bump
            ad_spend += bump
            # CPC movement unknown until observe; optimistic bookkeeping only
            applied.append(name)
            log.append(f"apply: increase_budget +{bump} (undo={spec.can_undo.value}, effect_after=2w done)")
        elif name == "change_pricing":
            # foundational: pricing change aims to reduce payback; model not fully specified
            if payback is not None:
                payback = max(0.0, float(payback) * 0.85)
                updates["payback_months"] = payback
            applied.append(name)
            log.append("apply: change_pricing (undo=costly, effect_after=4w done)")
        elif name == "exit_channel":
            # irreversible; stop spend on channel — CPC dynamics left to observe
            applied.append(name)
            log.append("apply: exit_channel (undo=no)")
        else:
            log.append(f"apply: unknown action {name}")

    updates.update({
        "pending_actions": still_pending,
        "applied_actions": applied,
        "runway": runway,
        "spend_this_period": spend_this,
        "ad_spend": ad_spend,
        "log": log or ["apply: nothing due"],
    })
    return updates


def agent_perspective(state: LoopState) -> dict:
    """
    growth_agent (non-human) may annotate with what it sees.
    founder / investor stakes logged for audit SOT.
    """
    ga_view = _visibility("growth_agent", state)
    return {
        "log": [
            f"growth_agent sees: {list(ga_view.keys())}",
            f"founder stakes: {PEOPLE['founder'].loses_if_wrong}",
            f"investor stakes: {PEOPLE['investor'].loses_if_wrong} (sees nothing)",
            f"not_modelling: {NOT_MODELLING}",
        ]
    }


def route_after_gates(state: LoopState) -> str:
    if state.get("await_human"):
        return "human_gate"
    return "authorize_actions"


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------

def build_graph():
    g = StateGraph(LoopState)

    g.add_node("tick", tick)
    g.add_node("observe", observe)
    g.add_node("update_beliefs", update_beliefs)
    g.add_node("evaluate_goals_and_policies", evaluate_goals_and_policies)
    g.add_node("check_human_gates", check_human_gates)
    g.add_node("human_gate", human_gate)
    g.add_node("authorize_actions", authorize_actions)
    g.add_node("guard_never", guard_never)
    g.add_node("apply_due_effects", apply_due_effects)
    g.add_node("agent_perspective", agent_perspective)

    g.add_edge(START, "tick")
    g.add_edge("tick", "observe")
    g.add_edge("observe", "update_beliefs")
    g.add_edge("update_beliefs", "evaluate_goals_and_policies")
    g.add_edge("evaluate_goals_and_policies", "check_human_gates")
    g.add_conditional_edges(
        "check_human_gates",
        route_after_gates,
        {"human_gate": "human_gate", "authorize_actions": "authorize_actions"},
    )
    g.add_edge("human_gate", "authorize_actions")
    g.add_edge("authorize_actions", "guard_never")
    g.add_edge("guard_never", "apply_due_effects")
    g.add_edge("apply_due_effects", "agent_perspective")
    g.add_edge("agent_perspective", END)

    memory = MemorySaver()
    return g.compile(checkpointer=memory)


# ---------------------------------------------------------------------------
# Demo driver (optional)
# ---------------------------------------------------------------------------

def initial_state(**overrides) -> LoopState:
    base: LoopState = {
        "now": datetime.utcnow().isoformat(),
        "week_index": -1,  # tick will move to 0
        "ad_spend": 8000.0,
        "new_customers": 25,
        "cost_per_customer": 320.0,
        "payback_months": 10.0,
        "runway": 50_000.0,
        "spend_this_period": 0.0,
        "cpc_above_600_since": None,
        "beliefs": {
            "product_market_fit": {
                "value": 0.55,
                "uncertainty": 0.4,
                "last_updated": datetime.utcnow().isoformat(),
                "notes": BELIEFS["product_market_fit"].known_bias or "",
            },
            "channel_saturation": {
                "value": 0.3,
                "uncertainty": 0.5,
                "last_updated": datetime.utcnow().isoformat(),
                "notes": "",
            },
        },
        "observations": [],
        "board_sentiment": None,
        "proposed_actions": [],
        "pending_actions": [],
        "applied_actions": [],
        "human_asks": [],
        "await_human": False,
        "human_decision": None,
        "violated_never": [],
        "halted": False,
        "log": [],
        "default_budget_delta": 1000.0,
        # simulation hooks (replace with real connectors)
        "_sim_interviews": {"n": 8, "intent_to_stay": 0.75, "reported_by": "customers"},
        "_sim_ad_platform": {"spend": 8000.0, "marginal_cpc_trend": 2.0},
        "_sim_board_sentiment": "cautiously optimistic",
    }
    base.update(overrides)
    return base


if __name__ == "__main__":
    graph = build_graph()
    config = {"configurable": {"thread_id": "customer_acquisition-1"}}

    # weekly run
    result = graph.invoke(initial_state(), config=config)

    # If interrupted for human, resume like:
    # graph.invoke(Command(resume={"approve": ["change_pricing"], "reject": [], "force": []}), config=config)

    print("=== logs ===")
    for line in result.get("log", []):
        print(line)
    print("=== metrics ===")
    print("cpc", result.get("cost_per_customer"), "payback", result.get("payback_months"))
    print("beliefs", result.get("beliefs"))
    print("pending", result.get("pending_actions"))
    print("human_asks", result.get("human_asks"))
```

## did not survive

- **Native `runs: weekly` scheduler** — LangGraph has no built-in cron/cadence; weekly ticking is a software `tick` node + external runner, not a platform schedule.
- **`goal.cost_per_customer.from: [ad_spend, new_customers]` as a declared derivation graph** — CPC is computed in code; there is no first-class “goal formula” object the graph engine type-checks.
- **`beliefs.*.explains`** (PMF explains CPC) — recorded in `BeliefSpec` only; no causal/explanatory edge type in LangGraph affecting inference or policy.
- **`settled_by: "a cohort retains above 80% at month 6"`** — represented as an optional external flag (`_cohort_m6_retention`) and a note, not a timed cohort ledger with automatic settlement semantics.
- **`known_bias` as a structured, enforced prior** — used as a text note plus a small-n heuristic pull-down; not a formal bias model the runtime guarantees.
- **Absence of `checked_by` on PMF (linter intentional hole)** — preserved as `checked_by=None` in data, but LangGraph cannot encode “linter asserts this field must be missing.”
- **`how: bayesian` / `how: judgement`** — approximate update functions only; not a real Bayesian engine or audited judgement protocol.
- **`observes.*.every: daily|weekly|monthly`** against a weekly loop — daily sources are snapshotted on weekly run; true daily polling needs an outer scheduler not in the graph.
- **`origin: outside | ourselves` and `how: measured | reported`** — metadata on specs/logs; LangGraph does not type provenance or treat “reported” as adversarial/optional truth.
- **`cost: high` on customer_interviews** — logged, not budgeted or rate-limited by the graph.
- **`reported_by: customers | investor`** — metadata only.
- **`board_sentiment` informs nothing** — stored and deliberately unused; cannot express “forbidden to bind later” as a hard language constraint.
- **`can_undo: yes | costly | no`** — gates human approval for `no` and notes `costly`; no undo ledger, reverse actions, or cost-of-undo accounting.
- **`effect_after: 2w / 4w`** — pending queue with timestamps; requires unbroken weekly invokes/checkpointer to mature—no real-time clock service.
- **`consumes: [runway]`** — simple numeric decrement; not a multi-resource consumption model.
- **`needs_approval: founder` vs exit_channel’s intentional lack of `needs_approval`** — behavior mirrored in gates; linter “must omit field” rule cannot live in LangGraph.
- **`people.*.loses_if_wrong`** — audit strings only; no skin-in-the-game mechanism.
- **`investor` accountable and blind** — empty `sees` filter; cannot enforce that no future node leaks metrics to them.
- **`founder.may_decide: pricing, and anything that cannot be undone`** — checked loosely via action flags; natural-language scope not a formal capability calculus.
- **`never: spend exceeds committed runway`** — enforced for `increase_budget` path only with a default delta; not a global constraint language over all side effects.
- **`not_modelling: competitor_response, seasonality`** — logged as explicit omissions; runtime cannot guarantee these factors stay out of connectors/models.
- **Dual v0/v1 vocabulary / back-compat test role of the file** — single implementation; no paired v0 adapter or format-negotiation layer.
- **Growth agent as autonomous LangGraph agent with tools** — agent is a perspective/log node, not a separate ReAct agent with independent memory beyond shared state.