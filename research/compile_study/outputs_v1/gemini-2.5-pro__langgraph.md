<!-- model: google/gemini-2.5-pro  tier: strong  target: langgraph  finish: stop -->

This Python script implements the `customer_acquisition` loop using LangGraph.

The implementation models the state, observations, beliefs, and actions as described in the specification. It uses a central `router` node to implement the `when`, `never`, and `asks_human_when` logic, directing the flow of control. Human-in-the-loop interruptions are handled for actions that require approval, are irreversible, or when key metrics cross critical thresholds.

```python
import os
import random
import uuid
import json
from datetime import datetime, timedelta
from typing import TypedDict, List, Optional, Literal

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

# --- Helper for Human-in-the-Loop ---
# In a real application, you would replace this with a proper human interaction service.
def wait_for_human_approval(run_id: str, is_dangerous_action: bool = False, is_state_escalation: bool = False):
    """
    A placeholder function to simulate waiting for a human to review and approve.
    In a real system, this would involve a UI, a ticketing system, or a chat interface.
    """
    print("\n" + "="*50)
    print("🚦 HUMAN INTERVENTION REQUIRED 🚦")
    print(f"Run ID: {run_id}")
    if is_state_escalation:
        print("Reason: A key metric has crossed a critical threshold, requiring human review.")
    elif is_dangerous_action:
        print("Reason: The recommended action is irreversible or requires specific approval.")
    
    print("\nInspect the current state above to make a decision.")
    print("To approve and continue, run the following command in your terminal:")
    print(f'python <your_script_name>.py --resume "{run_id}" --approve')
    print("\nTo stop the process, run:")
    print(f'python <your_script_name>.py --resume "{run_id}" --deny')
    print("="*50 + "\n")


# --- State Definition ---
# The state holds all metrics, beliefs, observations, and control flow variables.
class CustomerAcquisitionState(TypedDict):
    # Core Goals
    cost_per_customer: Optional[float]
    payback_months: Optional[float]

    # Beliefs
    product_market_fit: Optional[float]
    channel_saturation: Optional[float]

    # Observations (raw data)
    ad_spend: float
    new_customers: int
    customer_interview_summary: str
    interview_retention_signal: float # A float derived from interviews
    stripe_retention_signal: float # A float derived from stripe data
    board_sentiment_summary: str
    
    # Resources
    runway_usd: float

    # History & Control Flow
    cost_per_customer_history: List[tuple[str, float]]
    recommended_action: Optional[str]
    action_log: List[str]
    escalation_reason: Optional[str]
    
    # Internal router state
    next_node: Optional[Literal["execute_action", "human_review", "__end__"]]


# --- Mock Data Sources and Actions ---
# These functions simulate fetching data and executing business actions.

def get_stripe_data() -> dict:
    """Observes: stripe. Informs a part of product_market_fit belief."""
    # Simulates getting new customer count and a retention signal
    new_customers = random.randint(45, 65)
    retention_signal = random.uniform(0.78, 0.92) # "a cohort retains above 80% at month 6"
    print(f"OBSERVE(stripe): Got {new_customers} new customers. Retention signal: {retention_signal:.2f}")
    return {"new_customers": new_customers, "stripe_retention_signal": retention_signal}

def get_ad_platform_data() -> dict:
    """Observes: ad_platform. Informs channel_saturation belief."""
    ad_spend = random.uniform(20000, 28000)
    print(f"OBSERVE(ad_platform): Spend this period is ${ad_spend:,.2f}.")
    return {"ad_spend": ad_spend}

def get_customer_interviews() -> dict:
    """Observes: customer_interviews. Informs product_market_fit belief."""
    # Known bias: "reads high when volume is low"
    summary = "Customers are happy with the core feature but wish for better integration options."
    retention_signal = random.uniform(0.5, 0.75) # Usually more pessimistic than Stripe
    print(f"OBSERVE(customer_interviews): Signal: {retention_signal:.2f}. Summary: '{summary}'")
    return {"customer_interview_summary": summary, "interview_retention_signal": retention_signal}

def get_board_sentiment() -> dict:
    """Observes: board_sentiment. Informs nothing, just collected."""
    sentiments = ["cautiously optimistic", "concerned about burn rate", "bullish on growth"]
    summary = random.choice(sentiments)
    print(f"OBSERVE(board_sentiment): Investor sentiment is '{summary}'.")
    return {"board_sentiment_summary": summary}
    
# Action implementations
def increase_budget(state: CustomerAcquisitionState) -> dict:
    """Action: increase_budget. Consumes runway."""
    increase_amount = state["ad_spend"] * 0.20 # Increase by 20%
    print(f"ACTION: Increasing budget by ${increase_amount:,.2f}.")
    return {"runway_usd": state["runway_usd"] - increase_amount, "action_log": [f"Increased budget by {increase_amount}"]}

def change_pricing(state: CustomerAcquisitionState) -> dict:
    """Action: change_pricing."""
    print("ACTION: Initiating process to change pricing. This is a significant project.")
    return {"action_log": ["Initiated pricing change project"]}

def exit_channel(state: CustomerAcquisitionState) -> dict:
    """Action: exit_channel."""
    print("ACTION: Exiting current ad channel. This cannot be easily undone.")
    return {"action_log": ["Exited ad channel"]}


ACTION_IMPLS = {
    "increase_budget": increase_budget,
    "change_pricing": change_pricing,
    "exit_channel": exit_channel,
}

ACTION_METADATA = {
    "increase_budget": {"can_undo": "yes", "needs_approval": None},
    "change_pricing": {"can_undo": "costly", "needs_approval": "founder"},
    "exit_channel": {"can_undo": "no", "needs_approval": None},
}


# --- Graph Nodes ---
def observe_node(state: CustomerAcquisitionState) -> dict:
    """Gathers all new observations from external sources."""
    print("\n--- 1. OBSERVING ---")
    updates = {}
    updates.update(get_stripe_data())
    updates.update(get_ad_platform_data())
    updates.update(get_customer_interviews())
    updates.update(get_board_sentiment())
    return updates

def calculate_metrics_node(state: CustomerAcquisitionState) -> dict:
    """Calculates goals and updates beliefs based on new observations."""
    print("\n--- 2. UPDATING METRICS & BELIEFS ---")
    
    # Calculate Goal: cost_per_customer
    cpc = state["ad_spend"] / state["new_customers"] if state["new_customers"] > 0 else 0
    print(f"GOAL(cost_per_customer): ${cpc:,.2f} (Target: < $400)")
    
    # Maintain history for trend-based checks
    history = state.get("cost_per_customer_history", [])
    history.append((datetime.utcnow().isoformat(), cpc))
    # Keep history for the last ~3 weeks (for the 14-day rule)
    history = history[-21:]

    # Calculate Goal: payback_months (using a mock value)
    payback = random.uniform(8, 14)
    print(f"GOAL(payback_months): {payback:.1f} months (Target: < 12)")
    
    # Update Belief: product_market_fit (Bayesian - simulated)
    # Weights Stripe data higher than interview data
    pmf = (state["stripe_retention_signal"] * 0.7) + (state["interview_retention_signal"] * 0.3)
    print(f"BELIEF(product_market_fit): Updated to {pmf:.3f}")

    # Update Belief: channel_saturation (Judgement - simulated)
    # If spend is high but CPC is also high, channel might be saturated
    saturation = 0.0
    if state["ad_spend"] > 24000 and cpc > 450:
        saturation = random.uniform(0.7, 0.9)
    elif state["ad_spend"] > 22000:
        saturation = random.uniform(0.4, 0.6)
    else:
        saturation = random.uniform(0.1, 0.3)
    print(f"BELIEF(channel_saturation): Judged to be {saturation:.3f}")
    
    return {
        "cost_per_customer": cpc,
        "payback_months": payback,
        "product_market_fit": pmf,
        "channel_saturation": saturation,
        "cost_per_customer_history": history,
    }

def router_node(state: CustomerAcquisitionState) -> dict:
    """
    The core logic node. It checks for escalations and decides the next action.
    This combines the `when`, `asks_human_when`, and `never` clauses.
    """
    print("\n--- 3. ROUTING & DECISION ---")
    
    # 1. Check "never" hard constraints
    # Spec: "spend exceeds committed runway"
    # This check happens implicitly if an action consumes runway. We add an explicit one.
    if state['ad_spend'] > state['runway_usd']:
        print("HALT: Ad spend would exceed total committed runway.")
        return {"next_node": "__end__", "escalation_reason": "Spend exceeds committed runway."}

    # 2. Check "asks_human_when" for state-based escalations
    if state["product_market_fit"] < 0.4:
        reason = f"product_market_fit ({state['product_market_fit']:.2f}) fell below 0.4 threshold."
        print(f"ROUTER: Escalating to human. Reason: {reason}")
        return {"next_node": "human_review", "escalation_reason": reason}

    cpc_history = state["cost_per_customer_history"]
    if len(cpc_history) >= 14: # Assuming one entry per day for this rule
        recent_14_days = cpc_history[-14:]
        if all(cpc > 600 for _, cpc in recent_14_days):
            reason = "cost_per_customer has stayed above 600 for 14 days."
            print(f"ROUTER: Escalating to human. Reason: {reason}")
            return {"next_node": "human_review", "escalation_reason": reason}

    # 3. If no state escalation, apply "when" rules to decide an action
    recommended_action = None
    if state["payback_months"] > 12:
        recommended_action = "change_pricing"
    elif state["cost_per_customer"] < 400 and state["product_market_fit"] > 0.6:
        recommended_action = "increase_budget"
    
    if not recommended_action:
        print("ROUTER: No action criteria met. Ending cycle.")
        return {"next_node": "__end__"}

    print(f"ROUTER: Recommended action is '{recommended_action}'.")
    
    # 4. Check "asks_human_when" for action-based escalations
    action_meta = ACTION_METADATA.get(recommended_action, {})
    needs_approval = action_meta.get("needs_approval") is not None
    is_irreversible = action_meta.get("can_undo") == "no"

    if needs_approval or is_irreversible:
        reason = f"Action '{recommended_action}' requires human review (needs_approval={needs_approval}, is_irreversible={is_irreversible})."
        print(f"ROUTER: Escalating to human. Reason: {reason}")
        return {"recommended_action": recommended_action, "next_node": "human_review", "escalation_reason": reason}

    # 5. If no escalations, proceed to execution
    print("ROUTER: Action is safe to execute automatically.")
    return {"recommended_action": recommended_action, "next_node": "execute_action"}

def execute_action_node(state: CustomerAcquisitionState) -> dict:
    """Executes the recommended action."""
    print("\n--- 4. EXECUTING ACTION ---")
    action_name = state.get("recommended_action")
    if not action_name:
        print("EXECUTE: No action to execute.")
        return {"action_log": ["No action taken."]}

    action_func = ACTION_IMPLS.get(action_name)
    if not action_func:
        raise ValueError(f"Unknown action: {action_name}")

    # The action function returns the state changes
    return action_func(state)

def human_review_node(state: CustomerAcquisitionState) -> dict:
    """A placeholder node that we interrupt before executing."""
    print("\n--- PAUSED FOR HUMAN REVIEW ---")
    # This node's main purpose is to be a target for interruption.
    # Logic to proceed will be handled by the external resume call.
    return {}


# --- Graph Construction ---
workflow = StateGraph(CustomerAcquisitionState)

workflow.add_node("observe", observe_node)
workflow.add_node("calculate_metrics", calculate_metrics_node)
workflow.add_node("router", router_node)
workflow.add_node("execute_action", execute_action_node)
workflow.add_node("human_review", human_review_node)

workflow.set_entry_point("observe")

workflow.add_edge("observe", "calculate_metrics")
workflow.add_edge("calculate_metrics", "router")

# Conditional routing based on the router's decision
workflow.add_conditional_edges(
    "router",
    lambda x: x["next_node"],
    {
        "execute_action": "execute_action",
        "human_review": "human_review",
        "__end__": END,
    },
)

# After execution or review, the process ends for this cycle
workflow.add_edge("execute_action", END)
workflow.add_edge("human_review", END) # The graph ends here, awaiting external resume.

# We will interrupt the graph *before* it executes the human_review_node
app = workflow.compile(
    checkpointer=SqliteSaver.from_conn_string(":memory:"),
    interrupt_before=["human_review"],
)

# --- Graph Execution Example ---

def run_scenario(run_id, initial_state, approve=False, deny=False):
    config = {"configurable": {"thread_id": run_id}}
    
    # If we are not resuming, start a new run
    if not (approve or deny):
        print("\n\n" + "*"*80)
        print(f"🚀 STARTING NEW RUN: {run_id}")
        print("*"*80)
        final_state = app.invoke(initial_state, config)
    # If we are resuming, load the state and continue
    else:
        print("\n\n" + "*"*80)
        print(f"▶️ RESUMING RUN: {run_id} (Approved: {approve})")
        print("*"*80)
        if deny:
            print("🛑 Run denied by human. No action will be taken.")
            # We don't need to call the graph again. The run is just over.
            return
        
        # To resume, we get the interrupted state
        snapshot = app.get_state(config)
        # The next node to execute is the one we were interrupted before
        next_node = snapshot.next[0]
        # We invoke the graph starting from that node
        final_state = app.invoke(None, config, input=snapshot.values,
                                 start_at=next_node)
    
    # Check if the graph was interrupted
    if final_state.next:
        wait_for_human_approval(run_id, 
            is_dangerous_action="action" in final_state.values.get("escalation_reason", ""),
            is_state_escalation="threshold" in final_state.values.get("escalation_reason", "")
        )
    else:
        print("\n" + "*"*80)
        print(f"✅ RUN COMPLETE: {run_id}")
        print("*"*80)
        print("\nFinal State:")
        print(json.dumps(final_state.values, indent=2))


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", type=str, help="Run ID to resume")
    parser.add_argument("--approve", action="store_true", help="Approve the pending action")
    parser.add_argument("--deny", action="store_true", help="Deny the pending action")
    args = parser.parse_args()

    # Define initial states for different scenarios
    initial_state_auto = {
        "runway_usd": 1_000_000,
        "action_log": [],
        "cost_per_customer_history": [],
    }
    
    initial_state_human_approval = {
        "runway_usd": 1_000_000,
        "action_log": [],
        "cost_per_customer_history": [],
        # Force a high payback to trigger the 'change_pricing' action, which needs approval
        "payback_months": 13,
    }
    
    if args.resume:
        # This part simulates the external system resuming the graph
        run_scenario(args.resume, {}, approve=args.approve, deny=args.deny)
    else:
        # Scenario 1: Everything is fine, should run automatically.
        # We mock a favorable PMF to ensure it passes the checks.
        with unittest.mock.patch('__main__.random.uniform', side_effect=[0.7, 0.8, 10.0, 0.2]):
             run_scenario(f"auto-run-{uuid.uuid4()}", initial_state_auto)


        # Scenario 2: Action requires human approval
        # We mock a high payback months value to trigger 'change_pricing'
        with unittest.mock.patch('__main__.random.uniform', side_effect=[0.8, 0.9, 13.0, 0.3]):
             run_scenario(f"approval-run-{uuid.uuid4()}", initial_state_auto)
```

## did not survive

This section lists parts of the YAML specification that could not be literally or declaratively represented in the LangGraph implementation and explains why.

*   **`runs: weekly` and `every: daily/weekly/monthly`**: LangGraph executes a state machine; it does not include a scheduler. The `weekly` loop execution and the `daily`/`weekly` data observation frequencies would be managed by an external system, such as a cron job or an orchestration platform (e.g., Airflow, Dagster), which would trigger the LangGraph run.

*   **`effect_after: 2w` / `4w`**: Modeling time delays for action effects is beyond the scope of a single, synchronous graph execution. A real-world system would require a more complex architecture, likely involving:
    1.  Storing the timestamp and details of an executed action.
    2.  A separate monitoring process that checks if the `effect_after` duration has passed.
    3.  Feeding this information back into the `observe` node of a future run to correlate actions with observed changes.
    This implementation executes an action and then finishes, it does not wait for 2-4 weeks.

*   **Declarative Metadata**: Several keys in the spec are descriptive metadata for human understanding, not executable logic. While they inform the implementation, they don't exist as first-class objects in the code.
    *   `unit: USD`: Captured in comments and print statements, but not as a typed attribute in the state.
    *   `from`, `informs`, `explains`: These causal/dependency links are implemented procedurally (e.g., the `calculate_metrics_node` *uses* `ad_spend` to produce `cost_per_customer`). They are not stored as declarative metadata on the graph itself.
    *   `how: bayesian`, `how: judgement`, `how: measured`, `how: reported`: These describe the *method* of a calculation or observation. The code *implements* these methods (e.g., simulating a Bayesian update), but the "how" keyword itself is not a LangGraph primitive.
    *   `known_bias`, `settled_by`, `loses_if_wrong`, `cost`, `origin`: These are all forms of documentation for the humans operating or building the loop. They are extremely valuable but are represented as code comments or external documentation, not as part of the graph's structure.

*   **`people` and `sees: [...]` (Access Control)**: The `people` block defines roles and responsibilities. The `sees` key specifies role-based access control (RBAC) on data. LangGraph's state is a single, unified object within a given run; the entire graph has access to the entire state. Implementing RBAC to show only `cost_per_customer` to a `founder` would require a separate layer or application built on top of the graph execution engine. The graph itself is not aware of the different "people" viewing its state.

*   **`checked_by: monthly_spend_vs_cost_review`**: This refers to a separate, related business process. It's an important contextual link but is not part of the `customer_acquisition` loop being modeled here.