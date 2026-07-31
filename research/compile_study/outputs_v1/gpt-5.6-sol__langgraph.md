<!-- model: openai/gpt-5.6-sol  tier: strong  target: langgraph  finish: stop -->

Below is a runnable LangGraph implementation. It preserves the source specification as metadata, computes the two metrics, updates beliefs, selects actions, enforces the `never` rule, and uses LangGraph interrupts for human escalation and approval.

Install:

```bash
pip install langgraph
```

```python
# customer_acquisition_graph.py

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Literal, TypedDict
from uuid import uuid4

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


# ---------------------------------------------------------------------------
# Source specification, retained as runtime metadata.
# ---------------------------------------------------------------------------

LOOP_SPEC: dict[str, Any] = {
    "loop": "customer_acquisition",
    "runs": "weekly",
    "goal": {
        "cost_per_customer": {
            "keep": "below 400",
            "unit": "USD",
            "from": ["ad_spend", "new_customers"],
        },
        "payback_months": {
            "keep": "below 12",
        },
    },
    "beliefs": {
        "product_market_fit": {
            "question": (
                "If we keep buying customers like this month's, will they stay?"
            ),
            "from": ["customer_interviews", "stripe"],
            "how": "bayesian",
            "explains": "cost_per_customer",
            "settled_by": "a cohort retains above 80% at month 6",
            "known_bias": (
                "reads high when volume is low — interviews only reach people "
                "who reply"
            ),
        },
        "channel_saturation": {
            "question": (
                "Can this channel absorb more money before cost climbs?"
            ),
            "from": ["ad_platform"],
            "how": "judgement",
            "checked_by": "monthly_spend_vs_cost_review",
        },
    },
    "observes": {
        "stripe": {
            "informs": "cost_per_customer",
            "every": "daily",
            "origin": "outside",
            "how": "measured",
        },
        "ad_platform": {
            "informs": "channel_saturation",
            "every": "daily",
            "origin": "ourselves",
            "how": "measured",
        },
        "customer_interviews": {
            "informs": "product_market_fit",
            "every": "weekly",
            "cost": "high",
            "origin": "outside",
            "how": "reported",
            "reported_by": "customers",
        },
        "board_sentiment": {
            "every": "monthly",
            "origin": "outside",
            "how": "reported",
            "reported_by": "investor",
        },
    },
    "actions": {
        "increase_budget": {
            "moves": "cost_per_customer",
            "can_undo": "yes",
            "effect_after": "2w",
            "consumes": ["runway"],
        },
        "change_pricing": {
            "moves": "payback_months",
            "can_undo": "costly",
            "effect_after": "4w",
            "needs_approval": "founder",
        },
        "exit_channel": {
            "moves": "cost_per_customer",
            "can_undo": "no",
        },
    },
    "when": [
        {
            "if": (
                "cost_per_customer below 400 and "
                "product_market_fit above 0.6"
            ),
            "do": "increase_budget",
        },
        {
            "if": "payback_months above 12",
            "do": "change_pricing",
        },
    ],
    "asks_human_when": [
        "product_market_fit falls below 0.4",
        "cost_per_customer stays above 600 for 14 days",
        "any action whose can_undo is no becomes the chosen move",
    ],
    "people": {
        "founder": {
            "human": "yes",
            "loses_if_wrong": (
                "the company — runway, and 18-month survival odds"
            ),
            "sees": [
                "cost_per_customer",
                "product_market_fit",
            ],
            "may_decide": "pricing, and anything that cannot be undone",
        },
        "growth_agent": {
            "agent": "yes",
            "loses_if_wrong": "nothing",
            "sees": [
                "cost_per_customer",
                "product_market_fit",
                "channel_saturation",
            ],
        },
        "investor": {
            "human": "yes",
            "loses_if_wrong": "a position in the fund",
        },
    },
    "never": [
        "spend exceeds committed runway",
    ],
    "not_modelling": [
        "competitor_response",
        "seasonality",
    ],
}


ActionName = Literal[
    "increase_budget",
    "change_pricing",
    "exit_channel",
]


class LoopState(TypedDict, total=False):
    # Invocation inputs
    as_of: str
    observations: dict[str, Any]
    requested_action: ActionName | None

    # Persistent Bayesian state
    pmf_alpha: float
    pmf_beta: float

    # Derived metrics and beliefs
    cost_per_customer: float | None
    payback_months: float | None
    product_market_fit: float
    channel_saturation: float | None

    # Persistence used by the 14-day escalation
    cpc_above_600_since: str | None

    # Decision state
    chosen_action: ActionName | None
    decision_reason: str | None
    review_reasons: list[str]
    human_review: dict[str, Any] | None

    # Guard and output state
    policy_violations: list[str]
    action_plan: dict[str, Any] | None
    status: str
    warnings: list[str]


def parse_time(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)

    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def to_iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

def ingest_observations(state: LoopState) -> dict[str, Any]:
    observations = state.get("observations", {})
    as_of = parse_time(state.get("as_of"))

    warnings: list[str] = []

    ad_spend = observations.get("ad_spend")
    new_customers = observations.get("new_customers")

    if ad_spend is None or new_customers is None:
        cost_per_customer = None
        warnings.append(
            "cost_per_customer was not computed because ad_spend or "
            "new_customers was absent"
        )
    elif float(new_customers) <= 0:
        cost_per_customer = None
        warnings.append(
            "cost_per_customer was not computed because new_customers "
            "was not positive"
        )
    else:
        cost_per_customer = float(ad_spend) / float(new_customers)

    payback = observations.get("payback_months")
    payback_months = float(payback) if payback is not None else None

    # Track the beginning of a continuously observed CPC > 600 period.
    # A caller may provide daily_cost_per_customer to establish the streak
    # from daily measurements. Otherwise the graph tracks it across runs.
    above_since = state.get("cpc_above_600_since")
    daily_samples = observations.get("daily_cost_per_customer", [])

    if daily_samples:
        sorted_samples = sorted(
            daily_samples,
            key=lambda sample: parse_time(sample["at"]),
        )

        current_streak_start: datetime | None = None
        for sample in sorted_samples:
            sample_time = parse_time(sample["at"])
            value = float(sample["value"])

            if value > 600:
                if current_streak_start is None:
                    current_streak_start = sample_time
            else:
                current_streak_start = None

        above_since = (
            to_iso(current_streak_start)
            if current_streak_start is not None
            else None
        )
    elif cost_per_customer is not None:
        if cost_per_customer > 600:
            above_since = above_since or to_iso(as_of)
        else:
            above_since = None

    return {
        "as_of": to_iso(as_of),
        "cost_per_customer": cost_per_customer,
        "payback_months": payback_months,
        "cpc_above_600_since": above_since,
        "warnings": warnings,
        "status": "observations_ingested",
    }


def update_beliefs(state: LoopState) -> dict[str, Any]:
    """
    Implements product_market_fit as a Beta-Bernoulli posterior.

    Optional observation fields:
      retained_at_month_6: count of retained customers
      cohort_size_at_month_6: total count in the cohort
      supportive_interviews: count of supportive interviews
      total_interviews: total interview count
      channel_saturation: caller-provided judgement in [0, 1]

    The posterior begins with Beta(1, 1) unless persisted in the checkpoint.
    """
    observations = state.get("observations", {})

    alpha = float(state.get("pmf_alpha", 1.0))
    beta = float(state.get("pmf_beta", 1.0))

    retained = int(observations.get("retained_at_month_6", 0))
    cohort_size = int(observations.get("cohort_size_at_month_6", 0))

    if retained < 0 or cohort_size < 0 or retained > cohort_size:
        raise ValueError(
            "retained_at_month_6 must be between 0 and "
            "cohort_size_at_month_6"
        )

    supportive = int(observations.get("supportive_interviews", 0))
    interviews = int(observations.get("total_interviews", 0))

    if supportive < 0 or interviews < 0 or supportive > interviews:
        raise ValueError(
            "supportive_interviews must be between 0 and total_interviews"
        )

    # Both measured retention and reported interviews contribute evidence.
    # This is an explicit implementation choice because the source specifies
    # "bayesian" but does not define a likelihood model.
    successes = retained + supportive
    failures = (cohort_size - retained) + (interviews - supportive)

    alpha += successes
    beta += failures
    product_market_fit = alpha / (alpha + beta)

    channel_value = observations.get("channel_saturation")
    channel_saturation = (
        min(1.0, max(0.0, float(channel_value)))
        if channel_value is not None
        else state.get("channel_saturation")
    )

    return {
        "pmf_alpha": alpha,
        "pmf_beta": beta,
        "product_market_fit": product_market_fit,
        "channel_saturation": channel_saturation,
        "status": "beliefs_updated",
    }


def choose_action(state: LoopState) -> dict[str, Any]:
    requested = state.get("requested_action")
    if requested is not None:
        if requested not in LOOP_SPEC["actions"]:
            raise ValueError(f"Unknown requested action: {requested}")
        return {
            "chosen_action": requested,
            "decision_reason": "Action explicitly requested by caller",
            "status": "action_selected",
        }

    cpc = state.get("cost_per_customer")
    pmf = state.get("product_market_fit")
    payback = state.get("payback_months")

    # The YAML lists increase_budget first, so it has precedence if both
    # conditions are true.
    if cpc is not None and pmf is not None and cpc < 400 and pmf > 0.6:
        return {
            "chosen_action": "increase_budget",
            "decision_reason": (
                "cost_per_customer is below 400 and "
                "product_market_fit is above 0.6"
            ),
            "status": "action_selected",
        }

    if payback is not None and payback > 12:
        return {
            "chosen_action": "change_pricing",
            "decision_reason": "payback_months is above 12",
            "status": "action_selected",
        }

    return {
        "chosen_action": None,
        "decision_reason": "No action condition matched",
        "status": "no_action_selected",
    }


def evaluate_policy(state: LoopState) -> dict[str, Any]:
    reasons: list[str] = []
    violations: list[str] = []

    action = state.get("chosen_action")
    pmf = state.get("product_market_fit")
    as_of = parse_time(state.get("as_of"))

    if pmf is not None and pmf < 0.4:
        reasons.append("product_market_fit fell below 0.4")

    above_since_raw = state.get("cpc_above_600_since")
    if above_since_raw:
        above_since = parse_time(above_since_raw)
        if as_of - above_since >= timedelta(days=14):
            reasons.append(
                "cost_per_customer has stayed above 600 for at least 14 days"
            )

    if action:
        action_spec = LOOP_SPEC["actions"][action]

        if action_spec.get("can_undo") == "no":
            reasons.append(
                f"{action} cannot be undone and requires human review"
            )

        approval = action_spec.get("needs_approval")
        if approval:
            reasons.append(f"{action} requires approval from {approval}")

    violation = runway_violation(state, action)
    if violation:
        violations.append(violation)

    # A `never` constraint is not human-overridable.
    chosen_action = None if violations else action

    return {
        "chosen_action": chosen_action,
        "review_reasons": unique(reasons),
        "policy_violations": unique(violations),
        "status": (
            "blocked_by_policy"
            if violations
            else "human_review_required"
            if reasons
            else "policy_passed"
        ),
    }


def runway_violation(
    state: LoopState,
    action: ActionName | None,
) -> str | None:
    observations = state.get("observations", {})

    committed_runway = observations.get("committed_runway")
    spend_to_date = observations.get("spend_to_date", 0)
    incremental_spend = observations.get("proposed_incremental_spend", 0)

    if committed_runway is None:
        return None

    projected_spend = float(spend_to_date)

    if action == "increase_budget":
        projected_spend += float(incremental_spend)

    if projected_spend > float(committed_runway):
        return (
            "Blocked by never-rule: projected spend "
            f"{projected_spend:.2f} exceeds committed runway "
            f"{float(committed_runway):.2f}"
        )

    return None


def route_after_policy(
    state: LoopState,
) -> Literal["human_review", "final_guard"]:
    if state.get("review_reasons"):
        return "human_review"
    return "final_guard"


def human_review(state: LoopState) -> dict[str, Any]:
    proposed_action = state.get("chosen_action")

    response = interrupt(
        {
            "type": "customer_acquisition_human_review",
            "reviewer": "founder",
            "reasons": state.get("review_reasons", []),
            "proposed_action": proposed_action,
            "decision_reason": state.get("decision_reason"),
            "visible_context": {
                "cost_per_customer": state.get("cost_per_customer"),
                "product_market_fit": state.get("product_market_fit"),
                "payback_months": state.get("payback_months"),
            },
            "instructions": {
                "approved": "Boolean approval decision",
                "action": (
                    "Optional replacement action: increase_budget, "
                    "change_pricing, exit_channel, or null"
                ),
                "note": "Optional human explanation",
            },
        }
    )

    if not isinstance(response, dict):
        raise ValueError("Human review response must be a dictionary")

    approved = bool(response.get("approved", False))
    reviewed_action = response.get("action", proposed_action)

    if reviewed_action is not None and reviewed_action not in LOOP_SPEC["actions"]:
        raise ValueError(f"Human selected unknown action: {reviewed_action}")

    return {
        "chosen_action": reviewed_action if approved else None,
        "human_review": {
            "reviewer": "founder",
            "approved": approved,
            "selected_action": reviewed_action,
            "note": response.get("note"),
            "reviewed_at": to_iso(datetime.now(timezone.utc)),
        },
        "status": "human_approved" if approved else "human_declined",
    }


def final_guard(state: LoopState) -> dict[str, Any]:
    """
    Re-check the non-overridable rule after human review, because the human
    may have selected a different action.
    """
    action = state.get("chosen_action")
    violation = runway_violation(state, action)

    if violation:
        return {
            "chosen_action": None,
            "policy_violations": unique(
                [*state.get("policy_violations", []), violation]
            ),
            "status": "blocked_by_policy",
        }

    return {"status": state.get("status", "ready")}


def create_action_plan(state: LoopState) -> dict[str, Any]:
    action = state.get("chosen_action")

    if action is None:
        return {
            "action_plan": None,
            "status": (
                "blocked_by_policy"
                if state.get("policy_violations")
                else "completed_without_action"
            ),
        }

    action_spec = LOOP_SPEC["actions"][action]
    as_of = parse_time(state.get("as_of"))

    effect_weeks = {
        "increase_budget": 2,
        "change_pricing": 4,
        "exit_channel": 0,
    }[action]

    plan = {
        "action": action,
        "moves": action_spec["moves"],
        "can_undo": action_spec["can_undo"],
        "consumes": action_spec.get("consumes", []),
        "approved_by": (
            state.get("human_review", {}).get("reviewer")
            if state.get("human_review")
            and state["human_review"].get("approved")
            else None
        ),
        "planned_at": to_iso(as_of),
        "expected_effect_at": to_iso(
            as_of + timedelta(weeks=effect_weeks)
        ),
        "reason": state.get("decision_reason"),
    }

    return {
        "action_plan": plan,
        "status": "action_planned",
    }


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def build_graph():
    builder = StateGraph(LoopState)

    builder.add_node("ingest_observations", ingest_observations)
    builder.add_node("update_beliefs", update_beliefs)
    builder.add_node("choose_action", choose_action)
    builder.add_node("evaluate_policy", evaluate_policy)
    builder.add_node("human_review", human_review)
    builder.add_node("final_guard", final_guard)
    builder.add_node("create_action_plan", create_action_plan)

    builder.add_edge(START, "ingest_observations")
    builder.add_edge("ingest_observations", "update_beliefs")
    builder.add_edge("update_beliefs", "choose_action")
    builder.add_edge("choose_action", "evaluate_policy")

    builder.add_conditional_edges(
        "evaluate_policy",
        route_after_policy,
        {
            "human_review": "human_review",
            "final_guard": "final_guard",
        },
    )

    builder.add_edge("human_review", "final_guard")
    builder.add_edge("final_guard", "create_action_plan")
    builder.add_edge("create_action_plan", END)

    # A checkpointer is required for interrupt/resume and also persists the
    # Bayesian prior and 14-day streak between invocations for a thread.
    return builder.compile(checkpointer=MemorySaver())


graph = build_graph()


# ---------------------------------------------------------------------------
# Optional linter for the intentionally incomplete parts of the source spec.
# ---------------------------------------------------------------------------

def lint_spec() -> list[str]:
    findings: list[str] = []

    for name, belief in LOOP_SPEC["beliefs"].items():
        if "checked_by" not in belief:
            findings.append(f"belief {name!r} has no checked_by")

    for name, observation in LOOP_SPEC["observes"].items():
        if "informs" not in observation:
            findings.append(f"observation {name!r} informs nothing")

    for name, action in LOOP_SPEC["actions"].items():
        if (
            action.get("can_undo") == "no"
            and "needs_approval" not in action
        ):
            findings.append(
                f"irreversible action {name!r} has no needs_approval"
            )

    for name, person in LOOP_SPEC["people"].items():
        if "loses_if_wrong" in person and not person.get("sees"):
            findings.append(
                f"accountable person {name!r} has no declared visibility"
            )

    return findings


# ---------------------------------------------------------------------------
# Example
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    config = {
        "configurable": {
            # Reuse this ID across weekly runs to retain belief state.
            "thread_id": f"customer-acquisition-{uuid4()}",
        }
    }

    result = graph.invoke(
        {
            "as_of": "2025-03-01T12:00:00Z",
            "observations": {
                "ad_spend": 30_000,
                "new_customers": 100,
                "payback_months": 10,
                "retained_at_month_6": 85,
                "cohort_size_at_month_6": 100,
                "supportive_interviews": 8,
                "total_interviews": 10,
                "channel_saturation": 0.35,
                "committed_runway": 1_000_000,
                "spend_to_date": 400_000,
                "proposed_incremental_spend": 50_000,
            },
        },
        config=config,
    )

    print("Initial result:")
    print(result)
    print("Lint findings:", lint_spec())

    # If the result contains __interrupt__, resume it like this:
    #
    # result = graph.invoke(
    #     Command(
    #         resume={
    #             "approved": True,
    #             "action": "change_pricing",
    #             "note": "Founder approved the pricing test.",
    #         }
    #     ),
    #     config=config,
    # )
    # print("Resumed result:")
    # print(result)
```

A completed result includes an `action_plan` rather than directly changing an ad platform or billing system. For repeated weekly runs, reuse the same `thread_id` so the Bayesian posterior and CPC streak remain checkpointed.

## did not survive

- **Native weekly scheduling:** LangGraph defines execution and persistence, but does not itself provide a weekly scheduler. Invoke the graph from cron, Celery, Airflow, Temporal, or a hosted scheduler.
- **Actual external action execution:** The spec does not define APIs, credentials, budget amounts, pricing changes, or channel identifiers. The graph therefore emits an approved `action_plan` instead of mutating external systems.
- **Exact Bayesian semantics:** The spec says `how: bayesian` but supplies no prior, likelihood, weighting, or treatment of interview bias. The implementation uses a `Beta(1,1)` prior and treats retention and interview responses as Bernoulli evidence.
- **Exact “stays above 600 for 14 days” proof from weekly runs:** A weekly invocation alone cannot prove the value stayed above the threshold between runs. The implementation can use supplied daily samples; otherwise it approximates continuity from persisted weekly observations.
- **Automatic effect verification after 2w/4w:** LangGraph can record `expected_effect_at`, but the spec does not define the follow-up measurement or success criterion needed to verify each action’s effect.
- **Operational semantics for `not_modelling`:** `competitor_response` and `seasonality` are retained as metadata, but intentionally do not affect decisions.