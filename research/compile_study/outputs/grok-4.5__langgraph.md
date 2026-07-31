<!-- model: x-ai/grok-4.5  tier: strong  target: langgraph  finish: stop -->

```python
"""
customer_acquisition loop — LangGraph implementation
Weekly venture customer-acquisition control loop.
"""

from __future__ import annotations

import operator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Annotated, Any, Literal, Optional, Sequence, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver


# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------

class Reversibility(str, Enum):
    REVERSIBLE = "reversible"
    COSTLY = "costly"
    IRREVERSIBLE = "irreversible"


class PartyKind(str, Enum):
    HUMAN = "human"
    AGENT = "agent"


@dataclass
class Party:
    name: str
    kind: PartyKind
    bears: str
    sees: list[str] = field(default_factory=list)


PARTIES = {
    "founder": Party("founder", PartyKind.HUMAN, bears="the company",
                     sees=["cac", "product_market_fit"]),
    "growth_agent": Party("growth_agent", PartyKind.AGENT, bears="nothing"),
    "investor": Party("investor", PartyKind.HUMAN, bears="a position in the fund"),
}


# ---------------------------------------------------------------------------
# Graph state
# ---------------------------------------------------------------------------

class Observation(TypedDict, total=False):
    source: str
    value: float
    at: str
    asserted_by: str


class Estimate(TypedDict, total=False):
    name: str
    value: float
    method: str
    from_sources: list[str]
    settled: bool
    settled_by: str


class ActionRecord(TypedDict, total=False):
    name: str
    at: str
    delay_weeks: int
    reversibility: str
    approval: Optional[str]
    approved: bool
    consumes: list[str]


class LoopState(TypedDict):
    # regulated variables
    cac: float
    payback_months: float
    ad_spend: float
    new_customers: int
    runway: float  # weeks of runway remaining

    # estimates
    product_market_fit: float  # 0..1
    channel_saturation: float  # 0..1
    pmf_settled: bool

    # targets / guards
    cac_target: float
    payback_target: float
    never_violations: Annotated[list[str], operator.add]
    escalations: Annotated[list[str], operator.add]
    pending_approvals: Annotated[list[str], operator.add]
    actions_taken: Annotated[list[ActionRecord], operator.add]
    observations: Annotated[list[Observation], operator.add]
    log: Annotated[list[str], operator.add]

    # scheduling
    tick: int  # week number
    halted: bool


# ---------------------------------------------------------------------------
# Observation nodes (sensors)
# ---------------------------------------------------------------------------

def observe_stripe(state: LoopState) -> dict:
    """Daily sensor — measures CAC from ad_spend / new_customers."""
    spend = state["ad_spend"]
    customers = max(state["new_customers"], 1)
    cac = spend / customers
    obs: Observation = {
        "source": "stripe",
        "value": cac,
        "at": f"week-{state['tick']}",
    }
    return {
        "cac": cac,
        "observations": [obs],
        "log": [f"[stripe] cac={cac:.1f}"],
    }


def observe_ad_platform(state: LoopState) -> dict:
    """Daily sensor — channel saturation (stub: passthrough/judgement)."""
    sat = state["channel_saturation"]
    obs: Observation = {
        "source": "ad_platform",
        "value": sat,
        "at": f"week-{state['tick']}",
    }
    return {
        "observations": [obs],
        "log": [f"[ad_platform] channel_saturation={sat:.2f}"],
    }


def observe_customer_interviews(state: LoopState) -> dict:
    """Weekly, high-cost sensor — feeds PMF estimate."""
    # In a real system this would schedule/cost interviews.
    pmf = state["product_market_fit"]
    obs: Observation = {
        "source": "customer_interviews",
        "value": pmf,
        "at": f"week-{state['tick']}",
    }
    return {
        "observations": [obs],
        "log": [f"[customer_interviews] (cost=high) pmf_signal={pmf:.2f}"],
    }


def observe_board_sentiment(state: LoopState) -> dict:
    """Monthly — asserted by investor (only fires every ~4 ticks)."""
    if state["tick"] % 4 != 0:
        return {"log": ["[board_sentiment] skipped (not monthly boundary)"]}
    obs: Observation = {
        "source": "board_sentiment",
        "value": 0.0,  # qualitative; placeholder numeric
        "at": f"week-{state['tick']}",
        "asserted_by": "investor",
    }
    return {
        "observations": [obs],
        "log": ["[board_sentiment] asserted_by=investor"],
    }


# ---------------------------------------------------------------------------
# Estimation nodes
# ---------------------------------------------------------------------------

def estimate_product_market_fit(state: LoopState) -> dict:
    """
    Bayesian estimate from customer_interviews + stripe.
    Explains CAC. Settled when a cohort retains >80% at month 6.
    (No calibrated_by in the spec — left uncalibrated.)
    """
    # Stub bayesian update: blend prior with interview signal & inverse-CAC quality.
    prior = state["product_market_fit"]
    # proxy quality from CAC (lower CAC → higher implied PMF contribution)
    cac = max(state["cac"], 1.0)
    cac_signal = max(0.0, min(1.0, 1.0 - (cac / 800.0)))
    interview_signal = prior  # already holding last interview posterior
    posterior = 0.5 * interview_signal + 0.5 * cac_signal

    settled = state["pmf_settled"]  # external truth; set by cohort retention
    return {
        "product_market_fit": posterior,
        "log": [
            f"[estimate:pmf] method=bayesian value={posterior:.2f} "
            f"settled={settled} (settled_by='cohort retains >80% at month 6')"
        ],
    }


def estimate_channel_saturation(state: LoopState) -> dict:
    """Judgement estimate from ad_platform."""
    sat = state["channel_saturation"]
    return {
        "log": [f"[estimate:channel_saturation] method=judgement value={sat:.2f}"],
    }


# ---------------------------------------------------------------------------
# Regulation / guard checks
# ---------------------------------------------------------------------------

def check_regulators_and_invariants(state: LoopState) -> dict:
    """Evaluate regulated targets and the `never` invariant."""
    logs: list[str] = []
    violations: list[str] = []
    escalations: list[str] = []

    cac = state["cac"]
    payback = state["payback_months"]

    if cac >= state["cac_target"]:
        logs.append(f"[regulate:cac] BREACH cac={cac:.1f} target=< {state['cac_target']}")
    else:
        logs.append(f"[regulate:cac] ok cac={cac:.1f}")

    if payback >= state["payback_target"]:
        logs.append(
            f"[regulate:payback_months] BREACH payback={payback:.1f} "
            f"target=< {state['payback_target']}"
        )
    else:
        logs.append(f"[regulate:payback_months] ok payback={payback:.1f}")

    # never: spend exceeds committed runway
    # interpret runway as remaining budget-weeks; ad_spend weekly must not exceed it
    if state["ad_spend"] > state["runway"]:
        msg = "spend exceeds committed runway"
        violations.append(msg)
        logs.append(f"[never] VIOLATION: {msg}")
        # hard stop
        return {
            "never_violations": violations,
            "halted": True,
            "log": logs,
        }

    return {
        "never_violations": violations,
        "escalations": escalations,
        "log": logs,
    }


# ---------------------------------------------------------------------------
# Policy (when-clauses) → action selection
# ---------------------------------------------------------------------------

def policy(state: LoopState) -> dict:
    """
    when:
      - cac < 400 and pmf > 0.6  → increase_budget
      - payback_months > 12      → change_pricing
      - pmf < 0.4                → escalate founder
    """
    if state.get("halted"):
        return {"log": ["[policy] halted — no actions"]}

    logs: list[str] = []
    actions: list[ActionRecord] = []
    escalations: list[str] = []
    pending: list[str] = []

    cac = state["cac"]
    pmf = state["product_market_fit"]
    payback = state["payback_months"]
    now = f"week-{state['tick']}"

    # escalate has priority visibility
    if pmf < 0.4:
        escalations.append("founder")
        logs.append(f"[policy] escalate → founder (pmf={pmf:.2f} < 0.4)")

    if cac < 400 and pmf > 0.6:
        actions.append({
            "name": "increase_budget",
            "at": now,
            "delay_weeks": 2,
            "reversibility": Reversibility.REVERSIBLE.value,
            "approval": None,
            "approved": True,
            "consumes": ["runway"],
        })
        logs.append("[policy] do increase_budget (cac<400 ∧ pmf>0.6)")

    if payback > 12:
        # requires founder approval
        actions.append({
            "name": "change_pricing",
            "at": now,
            "delay_weeks": 4,
            "reversibility": Reversibility.COSTLY.value,
            "approval": "founder",
            "approved": False,
            "consumes": [],
        })
        pending.append("change_pricing")
        logs.append("[policy] do change_pricing (payback>12) — pending founder approval")

    # exit_channel is declared but has no `when` trigger in the spec;
    # available as a manual/terminal act, not auto-selected here.

    return {
        "actions_taken": actions,
        "escalations": escalations,
        "pending_approvals": pending,
        "log": logs,
    }


# ---------------------------------------------------------------------------
# Actuators
# ---------------------------------------------------------------------------

def apply_actions(state: LoopState) -> dict:
    """Apply approved actions, respecting delay annotations (modeled as staged effect)."""
    if state.get("halted"):
        return {"log": ["[act] halted — no side effects"]}

    logs: list[str] = []
    new_spend = state["ad_spend"]
    new_runway = state["runway"]
    new_payback = state["payback_months"]
    approvals_still_pending: list[str] = []

    for action in state["actions_taken"]:
        # only act on actions minted this tick
        if action.get("at") != f"week-{state['tick']}":
            continue

        name = action["name"]
        needs = action.get("approval")
        approved = action.get("approved", True)

        if needs and not approved:
            # Human-in-the-loop gate (founder). In production wire langgraph interrupt.
            logs.append(f"[act:{name}] waiting approval from {needs}")
            approvals_still_pending.append(name)
            continue

        if name == "increase_budget":
            # delay 2w — we stage the spend bump; full effect after delay ticks
            bump = 1000.0
            if new_runway - bump < 0:
                logs.append("[act:increase_budget] blocked — would breach runway")
                continue
            new_spend += bump
            new_runway -= bump
            logs.append(
                f"[act:increase_budget] staged +{bump:.0f} spend "
                f"(delay=2w, reversibility=reversible, consumes=runway)"
            )

        elif name == "change_pricing":
            # delay 4w, costly reverse; stub: improve payback by 20%
            new_payback = max(1.0, new_payback * 0.8)
            logs.append(
                f"[act:change_pricing] staged payback→{new_payback:.1f} "
                f"(delay=4w, reversibility=costly, approval=founder)"
            )

        elif name == "exit_channel":
            logs.append("[act:exit_channel] irreversible exit executed")

    return {
        "ad_spend": new_spend,
        "runway": new_runway,
        "payback_months": new_payback,
        "pending_approvals": approvals_still_pending,
        "log": logs,
    }


def founder_approval_gate(state: LoopState) -> dict:
    """
    Party: founder (human). Sees cac, product_market_fit.
    Auto-approve stub — replace with interrupt / human channel.
    """
    if not state.get("pending_approvals"):
        return {"log": ["[founder] no pending approvals"]}

    logs = []
    revised: list[ActionRecord] = []
    # Re-emit approved actions for this tick
    for action in state["actions_taken"]:
        if action["name"] in state["pending_approvals"] and not action.get("approved"):
            approved_action = dict(action)
            approved_action["approved"] = True
            revised.append(approved_action)  # type: ignore[arg-type]
            logs.append(
                f"[founder] approved {action['name']} "
                f"(sees cac={state['cac']:.1f}, pmf={state['product_market_fit']:.2f})"
            )
    return {
        "actions_taken": revised,
        "pending_approvals": [],
        "log": logs,
    }


def advance_tick(state: LoopState) -> dict:
    return {
        "tick": state["tick"] + 1,
        "log": [f"[clock] → week-{state['tick'] + 1}"],
    }


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

def route_after_guards(state: LoopState) -> Literal["policy", "__end__"]:
    if state.get("halted") or state.get("never_violations"):
        return "__end__"
    return "policy"


def route_approvals(state: LoopState) -> Literal["founder_approval", "apply_actions"]:
    if state.get("pending_approvals"):
        return "founder_approval"
    return "apply_actions"


# ---------------------------------------------------------------------------
# Build graph
# ---------------------------------------------------------------------------

def build_customer_acquisition_loop() -> Any:
    g = StateGraph(LoopState)

    # sensors
    g.add_node("observe_stripe", observe_stripe)
    g.add_node("observe_ad_platform", observe_ad_platform)
    g.add_node("observe_customer_interviews", observe_customer_interviews)
    g.add_node("observe_board_sentiment", observe_board_sentiment)

    # estimates
    g.add_node("estimate_pmf", estimate_product_market_fit)
    g.add_node("estimate_saturation", estimate_channel_saturation)

    # regulate + policy + act
    g.add_node("guards", check_regulators_and_invariants)
    g.add_node("policy", policy)
    g.add_node("founder_approval", founder_approval_gate)
    g.add_node("apply_actions", apply_actions)
    g.add_node("advance_tick", advance_tick)

    # weekly body: fan-out observations → estimates → guards → policy → acts
    g.add_edge(START, "observe_stripe")
    g.add_edge("observe_stripe", "observe_ad_platform")
    g.add_edge("observe_ad_platform", "observe_customer_interviews")
    g.add_edge("observe_customer_interviews", "observe_board_sentiment")
    g.add_edge("observe_board_sentiment", "estimate_pmf")
    g.add_edge("estimate_pmf", "estimate_saturation")
    g.add_edge("estimate_saturation", "guards")

    g.add_conditional_edges("guards", route_after_guards, {
        "policy": "policy",
        "__end__": END,
    })

    g.add_conditional_edges("policy", route_approvals, {
        "founder_approval": "founder_approval",
        "apply_actions": "apply_actions",
    })
    g.add_edge("founder_approval", "apply_actions")
    g.add_edge("apply_actions", "advance_tick")
    g.add_edge("advance_tick", END)

    return g.compile(checkpointer=MemorySaver())


# ---------------------------------------------------------------------------
# Demo driver — one weekly tick
# ---------------------------------------------------------------------------

def initial_state(**overrides: Any) -> LoopState:
    base: LoopState = {
        "cac": 350.0,
        "payback_months": 14.0,
        "ad_spend": 3500.0,
        "new_customers": 10,
        "runway": 50_000.0,
        "product_market_fit": 0.65,
        "channel_saturation": 0.3,
        "pmf_settled": False,
        "cac_target": 400.0,
        "payback_target": 12.0,
        "never_violations": [],
        "escalations": [],
        "pending_approvals": [],
        "actions_taken": [],
        "observations": [],
        "log": [],
        "tick": 1,
        "halted": False,
    }
    base.update(overrides)  # type: ignore[typeddict-item]
    return base


if __name__ == "__main__":
    graph = build_customer_acquisition_loop()
    config = {"configurable": {"thread_id": "customer_acquisition-1"}}

    # Run a few weekly ticks
    state = initial_state()
    for week in range(3):
        print(f"\n===== WEEK {state['tick']} =====")
        result = graph.invoke(state, config=config)
        for line in result["log"]:
            print(line)
        if result.get("escalations"):
            print("ESCALATIONS:", result["escalations"])
        if result.get("never_violations"):
            print("NEVER:", result["never_violations"])
            break
        # carry forward mutable footprint for next invoke
        state = result  # type: ignore[assignment]
```

## did not survive

- **`every: weekly` (loop-level cadence) / sensor cadences (`daily`, `weekly`, `monthly`)** — LangGraph has no native cron/cadence scheduler. Cadence is approximated by a discrete `tick` counter and simple modulo checks (e.g. board_sentiment monthly); real wall-clock scheduling and per-edge `every` must live outside the graph (orchestrator / ops).
- **`computed_from: [ad_spend, new_customers]` on `cac`** — expressed procedurally in `observe_stripe`, not as a declarative regulated-variable formula the runtime enforces.
- **`estimates.*.explains` (PMF explains CAC)** — no first-class causal/explanation edge in LangGraph; noted only in log text.
- **`settled_by: "a cohort retains above 80% at month 6"`** — settlement criterion is documentation + a boolean flag (`pmf_settled`); no cohort-retention subprocess or evidence binder.
- **`method: bayesian` / `method: judgement`** — cannot be declared as estimate methods; only stubbed in node bodies. No calibrated posterior / judgement protocol object.
- **Missing `calibrated_by` (linter warning)** — LangGraph has no spec linter; the absence is not reified as a compile-time diagnostic.
- **`cost: high` on customer_interviews** — no resource/cost model for observations; mentioned in logs only.
- **`asserted_by: investor` on board_sentiment** — recorded as a field on the observation, not as an authority/attestation capability tied to the investor party.
- **`acts.*.moves` (increase_budget moves cac, change_pricing moves payback_months)** — effect direction is hard-coded in actuators, not a declarative `moves` relation the graph engine understands.
- **`delay: 2w` / `4w`** — delays are annotations + log text; no real deferred-effect / wallet scheduler (effects apply immediately in the stub).
- **`reversibility: reversible | costly | irreversible`** — stored on action records but not enforced (no undo ledger, cost-of-reverse, or irreversible commit semantics).
- **`consumes: [runway]`** — partially modeled as a numeric decrement + never-guard; not a general resource-consumption algebra.
- **`exit_channel` (irreversible, no `when`)** — declared as a possible act but unreachable by policy (no trigger in `when`); no separate manual-act API.
- **`parties.*.bears` / `sees`** — party metadata is static data; `sees` is not enforced as an information-partition (founder approval node peeks only at declared fields by convention). `growth_agent` is never wired as an actor node.
- **`approval: founder` human gate** — stub auto-approves; not a true LangGraph `interrupt()` / human-in-the-loop channel.
- **`escalate: founder`** — appends to an `escalations` list; no escalation protocol, notification, or transfer of control.
- **`never: "spend exceeds committed runway"`** — implemented as a halt guard, but natural-language never-rules have no general interpreter; only this one concrete check.
- **`ignoring: [competitor_response, seasonality]`** — cannot be expressed; LangGraph has no “deliberately unmodeled factors” collider. Omission is silent.
- **`regulates.*.target` as declarative constraints** — targets are state fields checked imperatively, not regulator objects the runtime continuously enforces.
- **Loop expansion semantics (`python3 tools/loop.py` flat-graph expand)** — this is a hand-built graph, not the product of the loop macro/expander toolchain.