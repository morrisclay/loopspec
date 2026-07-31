<!-- model: openai/gpt-5.6-sol  tier: strong  target: langgraph  finish: stop -->

Below is a runnable LangGraph implementation. It executes one acquisition-loop tick per invocation, pauses for founder approval when required, checks the runway invariant, and records delayed actions in an outbox for an external scheduler.

Install:

```bash
pip install langgraph
```

```python
# customer_acquisition_graph.py
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


# ---------------------------------------------------------------------------
# Declarative metadata retained from the loop specification
# ---------------------------------------------------------------------------

LOOP_SPEC: dict[str, Any] = {
    "name": "customer_acquisition",
    "every": "weekly",
    "regulates": {
        "cac": {
            "target": "< 400",
            "computed_from": ["ad_spend", "new_customers"],
        },
        "payback_months": {
            "target": "< 12",
        },
    },
    "estimates": {
        "product_market_fit": {
            "from": ["customer_interviews", "stripe"],
            "method": "bayesian",
            "explains": "cac",
            "settled_by": "a cohort retains above 80% at month 6",
            "calibrated_by": None,
        },
        "channel_saturation": {
            "from": ["ad_platform"],
            "method": "judgement",
        },
    },
    "observes": {
        "stripe": {
            "measures": "cac",
            "every": "daily",
        },
        "ad_platform": {
            "measures": "channel_saturation",
            "every": "daily",
        },
        "customer_interviews": {
            "measures": "product_market_fit",
            "every": "weekly",
            "cost": "high",
        },
        "board_sentiment": {
            "every": "monthly",
            "asserted_by": "investor",
        },
    },
    "actions": {
        "increase_budget": {
            "moves": "cac",
            "reversibility": "reversible",
            "delay": "2w",
            "consumes": ["runway"],
        },
        "change_pricing": {
            "moves": "payback_months",
            "reversibility": "costly",
            "delay": "4w",
            "approval": "founder",
        },
        "exit_channel": {
            "reversibility": "irreversible",
        },
    },
    "parties": {
        "founder": {
            "human": True,
            "bears": "the company",
            "sees": ["cac", "product_market_fit"],
        },
        "growth_agent": {
            "agent": True,
            "bears": "nothing",
        },
        "investor": {
            "human": True,
            "bears": "a position in the fund",
        },
    },
    "never": ["spend exceeds committed runway"],
    "ignoring": ["competitor_response", "seasonality"],
}


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class AcquisitionState(TypedDict, total=False):
    # Invocation input
    now: str
    raw_data: dict[str, Any]

    # Inputs needed to make increase_budget concrete and enforceable
    committed_runway: float
    spend_to_date: float
    proposed_budget_increase: float

    # Normalized observations and metrics
    observations: dict[str, Any]
    metrics: dict[str, float | None]
    estimates: dict[str, Any]

    # Control-flow state
    pending_actions: list[dict[str, Any]]
    scheduled_actions: list[dict[str, Any]]
    action_log: list[dict[str, Any]]
    escalations: list[dict[str, Any]]
    constraint_violations: list[dict[str, Any]]
    warnings: list[str]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def state_time(state: AcquisitionState) -> datetime:
    value = state.get("now")
    if not value:
        return utc_now()

    # Accept both ISO 8601 "Z" and "+00:00".
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def delayed_time(state: AcquisitionState, weeks: int) -> str:
    return (state_time(state) + timedelta(weeks=weeks)).isoformat()


def copy_list(state: AcquisitionState, key: str) -> list[Any]:
    return list(state.get(key, []))  # type: ignore[literal-required]


# ---------------------------------------------------------------------------
# Observation and estimation
# ---------------------------------------------------------------------------

def observe(state: AcquisitionState) -> dict[str, Any]:
    """
    Normalize payloads supplied by external Stripe, advertising, interview,
    and board-sentiment integrations.

    Expected raw_data shape, with all fields optional:

    {
        "stripe": {
            "ad_spend": 30000,
            "new_customers": 100,
            "payback_months": 9,
            "month_6_retained": 85,
            "month_6_cohort_size": 100
        },
        "customer_interviews": {
            "positive": 8,
            "total": 10
        },
        "ad_platform": {
            "channel_saturation": 0.3
        },
        "board_sentiment": {
            "value": "positive"
        }
    }
    """
    raw = state.get("raw_data", {})
    stripe = dict(raw.get("stripe", {}))
    ad_platform = dict(raw.get("ad_platform", {}))
    interviews = dict(raw.get("customer_interviews", {}))
    board_sentiment = dict(raw.get("board_sentiment", {}))

    previous_metrics = dict(state.get("metrics", {}))

    ad_spend = stripe.get("ad_spend")
    new_customers = stripe.get("new_customers")

    cac: float | None = previous_metrics.get("cac")
    if ad_spend is not None and new_customers is not None:
        if float(new_customers) > 0:
            cac = float(ad_spend) / float(new_customers)
        else:
            cac = None

    payback = stripe.get(
        "payback_months",
        previous_metrics.get("payback_months"),
    )

    observations = {
        "stripe": stripe,
        "ad_platform": ad_platform,
        "customer_interviews": interviews,
        "board_sentiment": {
            **board_sentiment,
            "asserted_by": "investor",
        },
        "observed_at": state_time(state).isoformat(),
    }

    return {
        "observations": observations,
        "metrics": {
            **previous_metrics,
            "ad_spend": (
                float(ad_spend) if ad_spend is not None else None
            ),
            "new_customers": (
                float(new_customers) if new_customers is not None else None
            ),
            "cac": cac,
            "payback_months": (
                float(payback) if payback is not None else None
            ),
        },
    }


def estimate(state: AcquisitionState) -> dict[str, Any]:
    """
    Use a simple Beta-Bernoulli posterior for product-market fit.

    Beta(1, 1) is used as the prior. Positive interview outcomes and retained
    customers count as successes; negative interviews and churned customers
    count as failures.
    """
    observations = state.get("observations", {})
    interviews = observations.get("customer_interviews", {})
    stripe = observations.get("stripe", {})

    positive_interviews = int(interviews.get("positive", 0) or 0)
    total_interviews = int(interviews.get("total", 0) or 0)
    positive_interviews = max(0, min(positive_interviews, total_interviews))
    negative_interviews = total_interviews - positive_interviews

    retained = int(stripe.get("month_6_retained", 0) or 0)
    cohort_size = int(stripe.get("month_6_cohort_size", 0) or 0)
    retained = max(0, min(retained, cohort_size))
    churned = cohort_size - retained

    alpha = 1 + positive_interviews + retained
    beta = 1 + negative_interviews + churned
    pmf_probability = alpha / (alpha + beta)

    retention_rate: float | None = None
    if cohort_size > 0:
        retention_rate = retained / cohort_size

    pmf_settled = retention_rate is not None and retention_rate > 0.80

    ad_platform = observations.get("ad_platform", {})
    prior_estimates = state.get("estimates", {})
    saturation = ad_platform.get(
        "channel_saturation",
        prior_estimates.get("channel_saturation", {}).get("value"),
    )

    warnings = copy_list(state, "warnings")
    warning = (
        "product_market_fit uses method=bayesian but has no calibrated_by."
    )
    if warning not in warnings:
        warnings.append(warning)

    return {
        "estimates": {
            "product_market_fit": {
                "value": pmf_probability,
                "method": "bayesian",
                "posterior": {
                    "distribution": "Beta",
                    "alpha": alpha,
                    "beta": beta,
                },
                "explains": "cac",
                "settled": pmf_settled,
                "settled_by": (
                    "a cohort retains above 80% at month 6"
                ),
                "month_6_retention": retention_rate,
                "calibrated_by": None,
            },
            "channel_saturation": {
                "value": (
                    float(saturation) if saturation is not None else None
                ),
                "method": "judgement",
            },
        },
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Policy evaluation
# ---------------------------------------------------------------------------

def plan(state: AcquisitionState) -> dict[str, Any]:
    metrics = state.get("metrics", {})
    estimates = state.get("estimates", {})

    cac = metrics.get("cac")
    payback = metrics.get("payback_months")
    pmf = estimates.get("product_market_fit", {}).get("value")

    actions: list[dict[str, Any]] = []
    escalations = copy_list(state, "escalations")

    if cac is not None and pmf is not None and cac < 400 and pmf > 0.6:
        actions.append({
            "name": "increase_budget",
            "reason": "cac < 400 and product_market_fit > 0.6",
        })

    if payback is not None and payback > 12:
        actions.append({
            "name": "change_pricing",
            "reason": "payback_months > 12",
        })

    if pmf is not None and pmf < 0.4:
        escalations.append({
            "to": "founder",
            "reason": "product_market_fit < 0.4",
            "created_at": state_time(state).isoformat(),
            "status": "open",
        })

    return {
        "pending_actions": actions,
        "escalations": escalations,
    }


# ---------------------------------------------------------------------------
# Action processing
# ---------------------------------------------------------------------------

def route_next_action(state: AcquisitionState) -> str:
    pending = state.get("pending_actions", [])
    if not pending:
        return "finish"

    name = pending[0]["name"]
    if name in {"increase_budget", "change_pricing", "exit_channel"}:
        return name

    return "unknown_action"


def increase_budget(state: AcquisitionState) -> dict[str, Any]:
    pending = copy_list(state, "pending_actions")
    current = pending.pop(0)

    scheduled = copy_list(state, "scheduled_actions")
    action_log = copy_list(state, "action_log")
    violations = copy_list(state, "constraint_violations")
    escalations = copy_list(state, "escalations")

    committed_runway = state.get("committed_runway")
    spend_to_date = state.get("spend_to_date")
    increase = state.get("proposed_budget_increase")

    # Fail closed because this action consumes runway.
    if (
        committed_runway is None
        or spend_to_date is None
        or increase is None
    ):
        reason = (
            "increase_budget blocked: committed_runway, spend_to_date, and "
            "proposed_budget_increase are required to enforce the runway "
            "constraint"
        )
        violations.append({
            "constraint": "spend must not exceed committed runway",
            "reason": reason,
            "created_at": state_time(state).isoformat(),
        })
        escalations.append({
            "to": "founder",
            "reason": reason,
            "created_at": state_time(state).isoformat(),
            "status": "open",
        })
        action_log.append({
            **current,
            "status": "blocked",
            "reason": reason,
        })
    elif float(spend_to_date) + float(increase) > float(committed_runway):
        reason = (
            f"increase_budget blocked: {spend_to_date} + {increase} exceeds "
            f"committed runway {committed_runway}"
        )
        violations.append({
            "constraint": "spend must not exceed committed runway",
            "reason": reason,
            "created_at": state_time(state).isoformat(),
        })
        action_log.append({
            **current,
            "status": "blocked",
            "reason": reason,
        })
    else:
        scheduled_action = {
            **current,
            "status": "scheduled",
            "scheduled_for": delayed_time(state, weeks=2),
            "reversibility": "reversible",
            "moves": "cac",
            "consumes": ["runway"],
            "parameters": {
                "budget_increase": float(increase),
            },
        }
        scheduled.append(scheduled_action)
        action_log.append(scheduled_action)

    return {
        "pending_actions": pending,
        "scheduled_actions": scheduled,
        "action_log": action_log,
        "constraint_violations": violations,
        "escalations": escalations,
    }


def change_pricing(state: AcquisitionState) -> dict[str, Any]:
    pending = copy_list(state, "pending_actions")
    current = pending[0]

    decision = interrupt({
        "kind": "approval_required",
        "approval_by": "founder",
        "action": "change_pricing",
        "reason": current.get("reason"),
        "moves": "payback_months",
        "reversibility": "costly",
        "delay": "4w",
        "visible_context": {
            # Enforces the declared founder view in the approval payload.
            "cac": state.get("metrics", {}).get("cac"),
            "product_market_fit": (
                state.get("estimates", {})
                .get("product_market_fit", {})
                .get("value")
            ),
        },
        "resume_with": {
            "approved": True,
            "comment": "optional comment",
        },
    })

    if isinstance(decision, dict):
        approved = bool(decision.get("approved", False))
        comment = decision.get("comment")
    else:
        approved = bool(decision)
        comment = None

    # Only remove the action after the interrupt has been resumed.
    pending.pop(0)
    scheduled = copy_list(state, "scheduled_actions")
    action_log = copy_list(state, "action_log")

    if approved:
        result = {
            **current,
            "status": "scheduled",
            "approved_by": "founder",
            "approval_comment": comment,
            "scheduled_for": delayed_time(state, weeks=4),
            "reversibility": "costly",
            "moves": "payback_months",
        }
        scheduled.append(result)
    else:
        result = {
            **current,
            "status": "rejected",
            "rejected_by": "founder",
            "approval_comment": comment,
        }

    action_log.append(result)

    return {
        "pending_actions": pending,
        "scheduled_actions": scheduled,
        "action_log": action_log,
    }


def exit_channel(state: AcquisitionState) -> dict[str, Any]:
    """
    Implemented for completeness, although no rule in the source spec invokes
    this irreversible action.
    """
    pending = copy_list(state, "pending_actions")
    current = pending.pop(0)

    action_log = copy_list(state, "action_log")
    action_log.append({
        **current,
        "status": "recorded",
        "reversibility": "irreversible",
        "created_at": state_time(state).isoformat(),
    })

    return {
        "pending_actions": pending,
        "action_log": action_log,
    }


def unknown_action(state: AcquisitionState) -> dict[str, Any]:
    pending = copy_list(state, "pending_actions")
    current = pending.pop(0)

    action_log = copy_list(state, "action_log")
    action_log.append({
        **current,
        "status": "failed",
        "reason": "unknown action",
    })

    return {
        "pending_actions": pending,
        "action_log": action_log,
    }


def finish(_: AcquisitionState) -> dict[str, Any]:
    return {}


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def build_graph():
    builder = StateGraph(AcquisitionState)

    builder.add_node("observe", observe)
    builder.add_node("estimate", estimate)
    builder.add_node("plan", plan)

    # Empty routing node; conditional edges inspect pending_actions.
    builder.add_node("route_actions", lambda state: {})

    builder.add_node("increase_budget", increase_budget)
    builder.add_node("change_pricing", change_pricing)
    builder.add_node("exit_channel", exit_channel)
    builder.add_node("unknown_action", unknown_action)
    builder.add_node("finish", finish)

    builder.add_edge(START, "observe")
    builder.add_edge("observe", "estimate")
    builder.add_edge("estimate", "plan")
    builder.add_edge("plan", "route_actions")

    builder.add_conditional_edges(
        "route_actions",
        route_next_action,
        {
            "increase_budget": "increase_budget",
            "change_pricing": "change_pricing",
            "exit_channel": "exit_channel",
            "unknown_action": "unknown_action",
            "finish": "finish",
        },
    )

    builder.add_edge("increase_budget", "route_actions")
    builder.add_edge("change_pricing", "route_actions")
    builder.add_edge("exit_channel", "route_actions")
    builder.add_edge("unknown_action", "route_actions")
    builder.add_edge("finish", END)

    # Required so an approval interrupt can be resumed.
    return builder.compile(checkpointer=MemorySaver())


app = build_graph()


# ---------------------------------------------------------------------------
# Example execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    config = {
        "configurable": {
            # Reuse this thread_id when resuming an approval.
            "thread_id": "customer-acquisition-2025-W10",
        }
    }

    initial_state: AcquisitionState = {
        "now": "2025-03-03T09:00:00+00:00",
        "raw_data": {
            "stripe": {
                "ad_spend": 30_000,
                "new_customers": 100,
                "payback_months": 13,
                "month_6_retained": 85,
                "month_6_cohort_size": 100,
            },
            "customer_interviews": {
                "positive": 8,
                "total": 10,
            },
            "ad_platform": {
                "channel_saturation": 0.35,
            },
            "board_sentiment": {
                "value": "cautiously positive",
            },
        },
        "committed_runway": 1_000_000,
        "spend_to_date": 700_000,
        "proposed_budget_increase": 50_000,
        "scheduled_actions": [],
        "action_log": [],
        "escalations": [],
        "constraint_violations": [],
        "warnings": [],
    }

    result = app.invoke(initial_state, config=config)
    print(json.dumps(result, indent=2, default=str))

    if result.get("__interrupt__"):
        # In a real service, return the interrupt payload to the founder.
        # Resume after receiving their decision:
        resumed = app.invoke(
            Command(
                resume={
                    "approved": True,
                    "comment": "Approved for the next pricing experiment.",
                }
            ),
            config=config,
        )
        print("\nResumed result:")
        print(json.dumps(resumed, indent=2, default=str))
```

## did not survive

- **Native weekly/daily/monthly scheduling:** LangGraph executes graph runs but is not itself a calendar scheduler. The loop’s weekly cadence and observation cadences remain metadata; an external cron job, workflow service, or LangGraph deployment scheduler must invoke them.
- **Delayed action execution:** The `2w` and `4w` delays are represented as dated outbox entries. LangGraph does not automatically execute those external business actions at the future time; an external worker must consume them.
- **Real data-source behavior:** The spec names Stripe, an ad platform, interviews, and board sentiment but provides no API contracts. The graph therefore accepts normalized payloads rather than calling real integrations.
- **Exact Bayesian model:** “Bayesian” does not specify priors, likelihoods, or how interviews and retention should be weighted. The implementation uses a documented Beta-Bernoulli model, which is an interpretation rather than an exact preservation.
- **Judgement implementation:** No judge, rubric, or model is specified for channel saturation. The graph records the supplied judgement value without independently deriving it.
- **Action effect sizes:** `moves` identifies affected variables but not direction, magnitude, or execution parameters. Actions are scheduled as intents; only the separately supplied budget increase is made concrete.
- **Field-level party access control:** The founder’s declared `sees` fields are enforced in the approval payload, but LangGraph state itself does not provide field-level ACLs. Party liability (`bears`) remains metadata.
- **`exit_channel` trigger:** The action is implemented and retained, but no `when` rule invokes it, so it is unreachable under the supplied policy.
- **Ignored factors:** Competitor response and seasonality remain explicitly recorded as ignored metadata and do not affect computation, as required by the source spec.