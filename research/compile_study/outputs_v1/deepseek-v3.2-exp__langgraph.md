<!-- model: deepseek/deepseek-v3.2-exp  tier: mid  target: langgraph  finish: stop -->

```python
from typing import Literal, TypedDict, Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import json
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, SystemMessage
import asyncio

# ==================== Type Definitions ====================

class LoopState(TypedDict):
    """State for the customer acquisition loop"""
    # Goals
    cost_per_customer: float  # USD
    payback_months: float
    
    # Beliefs
    product_market_fit: float  # 0.0 to 1.0
    channel_saturation: float  # 0.0 to 1.0
    
    # Observations (latest values)
    stripe_data: Optional[Dict]
    ad_platform_data: Optional[Dict]
    customer_interviews: Optional[List[Dict]]
    board_sentiment: Optional[str]
    
    # Action tracking
    last_budget_change: Optional[datetime]
    last_pricing_change: Optional[datetime]
    last_channel_exit: Optional[datetime]
    
    # Decision tracking
    pending_human_decision: Optional[str]
    human_decision_result: Optional[Dict]
    
    # Run context
    current_week: int
    total_spend: float
    runway_remaining: float  # months
    messages: List[Any]

# ==================== Observation Nodes ====================

async def observe_stripe(state: LoopState) -> LoopState:
    """Daily observation from Stripe"""
    # In reality, this would fetch from Stripe API
    # Simulating measured data
    new_customers = 25  # Example
    ad_spend = 8500     # Example
    
    state["stripe_data"] = {
        "timestamp": datetime.now(),
        "new_customers": new_customers,
        "ad_spend": ad_spend,
        "revenue": 12500  # Example
    }
    
    # Update cost_per_customer
    if new_customers > 0:
        state["cost_per_customer"] = ad_spend / new_customers
    
    return state

async def observe_ad_platform(state: LoopState) -> LoopState:
    """Daily observation from ad platform"""
    # Simulating measured data
    state["ad_platform_data"] = {
        "timestamp": datetime.now(),
        "daily_spend": 1200,
        "ctr": 0.032,
        "cpc": 4.85,
        "impressions": 25000
    }
    
    # Simple saturation calculation (example)
    spend_trend = 1.2  # Example trend
    state["channel_saturation"] = min(0.95, spend_trend * 0.15)
    
    return state

async def observe_customer_interviews(state: LoopState) -> LoopState:
    """Weekly customer interviews"""
    # Simulating reported data from customers
    interviews = [
        {"satisfaction": 8, "would_recommend": True, "feedback": "Great product"},
        {"satisfaction": 6, "would_recommend": False, "feedback": "Needs feature X"},
    ]
    
    state["customer_interviews"] = interviews
    
    # Bayesian update for product_market_fit (simplified)
    avg_satisfaction = sum(i["satisfaction"] for i in interviews) / len(interviews)
    state["product_market_fit"] = avg_satisfaction / 10  # Scale 0-10 to 0-1
    
    return state

async def observe_board_sentiment(state: LoopState) -> LoopState:
    """Monthly board sentiment"""
    # Collected without informing anything specific
    state["board_sentiment"] = "cautiously optimistic"
    return state

# ==================== Belief Nodes ====================

async def update_product_market_fit(state: LoopState) -> LoopState:
    """Bayesian belief update for product-market fit"""
    # Already updated in observe_customer_interviews
    # Additional Bayesian logic would go here
    return state

async def update_channel_saturation(state: LoopState) -> LoopState:
    """Judgement-based belief update for channel saturation"""
    # Checked by monthly_spend_vs_cost_review
    # This is a placeholder for human judgement
    return state

# ==================== Action Nodes ====================

async def increase_budget(state: LoopState) -> LoopState:
    """Increase advertising budget"""
    if state["runway_remaining"] < 3:
        state["pending_human_decision"] = "increase_budget_requires_runway_check"
        return state
    
    # Increase spend by 20%
    current_spend = state.get("total_spend", 10000)
    state["total_spend"] = current_spend * 1.2
    state["last_budget_change"] = datetime.now()
    
    # Effect after 2 weeks - we track but don't apply immediately
    state["messages"].append({
        "type": "action_taken",
        "action": "increase_budget",
        "timestamp": datetime.now(),
        "effect_after": datetime.now() + timedelta(days=14)
    })
    
    return state

async def change_pricing(state: LoopState) -> LoopState:
    """Change pricing strategy"""
    # Needs founder approval
    state["pending_human_decision"] = "change_pricing_needs_approval"
    return state

async def exit_channel(state: LoopState) -> LoopState:
    """Exit advertising channel (cannot be undone)"""
    state["pending_human_decision"] = "exit_channel_cannot_undo"
    return state

# ==================== Decision Nodes ====================

async def evaluate_conditions(state: LoopState) -> LoopState:
    """Evaluate when conditions and human intervention triggers"""
    triggers = []
    
    # Rule-based triggers
    if (state["cost_per_customer"] < 400 and 
        state["product_market_fit"] > 0.6):
        triggers.append("increase_budget")
    
    if state["payback_months"] > 12:
        triggers.append("change_pricing")
    
    # Human intervention triggers
    if state["product_market_fit"] < 0.4:
        state["pending_human_decision"] = "product_market_fit_below_0.4"
    
    # Track cost_per_customer above 600 for 14 days
    # This would require historical tracking - simplified
    if state["cost_per_customer"] > 600:
        state["pending_human_decision"] = "cost_per_customer_high_14days"
    
    # Store triggers for next step
    state["messages"].append({
        "type": "triggers",
        "triggers": triggers,
        "timestamp": datetime.now()
    })
    
    return state

async def select_action(state: LoopState) -> LoopState:
    """Select action based on triggers and human decisions"""
    
    # Check for pending human decisions first
    if state.get("pending_human_decision"):
        # Wait for human input
        return state
    
    # Check triggers from previous step
    triggers = None
    for msg in reversed(state["messages"]):
        if msg.get("type") == "triggers":
            triggers = msg.get("triggers", [])
            break
    
    if triggers:
        # Execute first triggered action
        if "increase_budget" in triggers:
            return await increase_budget(state)
        elif "change_pricing" in triggers:
            return await change_pricing(state)
    
    return state

async def human_decision_node(state: LoopState) -> LoopState:
    """Node for human decision input"""
    # In LangGraph, this would typically pause for human input
    # For this implementation, we'll simulate it
    if state.get("pending_human_decision"):
        # Simulate human approval for demonstration
        if state["pending_human_decision"] == "change_pricing_needs_approval":
            state["human_decision_result"] = {
                "decision": "approved",
                "by": "founder",
                "timestamp": datetime.now()
            }
            state["pending_human_decision"] = None
            # Actually execute the pricing change
            state["last_pricing_change"] = datetime.now()
            state["messages"].append({
                "type": "action_taken",
                "action": "change_pricing",
                "timestamp": datetime.now(),
                "approved_by": "founder"
            })
    
    return state

# ==================== Safety Checks ====================

async def safety_checks(state: LoopState) -> LoopState:
    """Apply never conditions and safety checks"""
    # Never spend exceeds committed runway
    committed_runway = 24  # months, example
    if state["total_spend"] / 10000 > committed_runway:  # Simplified
        state["pending_human_decision"] = "spend_exceeds_runway"
    
    return state

# ==================== Graph Construction ====================

def create_customer_acquisition_graph():
    """Create the LangGraph for customer acquisition loop"""
    
    builder = StateGraph(LoopState)
    
    # Add observation nodes
    builder.add_node("observe_stripe", observe_stripe)
    builder.add_node("observe_ad_platform", observe_ad_platform)
    builder.add_node("observe_customer_interviews", observe_customer_interviews)
    builder.add_node("observe_board_sentiment", observe_board_sentiment)
    
    # Add belief nodes
    builder.add_node("update_product_market_fit", update_product_market_fit)
    builder.add_node("update_channel_saturation", update_channel_saturation)
    
    # Add decision and action nodes
    builder.add_node("evaluate_conditions", evaluate_conditions)
    builder.add_node("select_action", select_action)
    builder.add_node("human_decision", human_decision_node)
    
    # Add safety node
    builder.add_node("safety_checks", safety_checks)
    
    # Define the flow
    builder.set_entry_point("observe_stripe")
    
    # Weekly flow (simplified)
    builder.add_edge("observe_stripe", "observe_ad_platform")
    builder.add_edge("observe_ad_platform", "update_channel_saturation")
    
    # Branch for weekly interviews
    builder.add_conditional_edges(
        "update_channel_saturation",
        lambda state: "observe_customer_interviews" if state["current_week"] % 7 == 0 else "evaluate_conditions",
        {
            "observe_customer_interviews": "observe_customer_interviews",
            "evaluate_conditions": "evaluate_conditions"
        }
    )
    
    builder.add_edge("observe_customer_interviews", "update_product_market_fit")
    builder.add_edge("update_product_market_fit", "evaluate_conditions")
    
    # Monthly board sentiment
    builder.add_conditional_edges(
        "evaluate_conditions",
        lambda state: "observe_board_sentiment" if state["current_week"] % 30 == 0 else "safety_checks",
        {
            "observe_board_sentiment": "observe_board_sentiment",
            "safety_checks": "safety_checks"
        }
    )
    
    builder.add_edge("observe_board_sentiment", "safety_checks")
    builder.add_edge("safety_checks", "select_action")
    
    # Handle human decisions
    builder.add_conditional_edges(
        "select_action",
        lambda state: "human_decision" if state.get("pending_human_decision") else END,
        {
            "human_decision": "human_decision",
            END: END
        }
    )
    
    builder.add_edge("human_decision", END)
    
    # Add memory for checkpoints
    memory = MemorySaver()
    graph = builder.compile(checkpointer=memory)
    
    return graph

# ==================== Initial State ====================

INITIAL_STATE = {
    "cost_per_customer": 350.0,
    "payback_months": 10.0,
    "product_market_fit": 0.7,
    "channel_saturation": 0.3,
    "stripe_data": None,
    "ad_platform_data": None,
    "customer_interviews": None,
    "board_sentiment": None,
    "last_budget_change": None,
    "last_pricing_change": None,
    "last_channel_exit": None,
    "pending_human_decision": None,
    "human_decision_result": None,
    "current_week": 0,
    "total_spend": 10000.0,
    "runway_remaining": 18.0,
    "messages": []
}

# ==================== Example Usage ====================

async def main():
    """Example of running the loop"""
    graph = create_customer_acquisition_graph()
    
    # Run for 4 weeks
    config = {"configurable": {"thread_id": "customer_acquisition_1"}}
    
    current_state = INITIAL_STATE.copy()
    
    for week in range(4):
        print(f"\n=== Week {week + 1} ===")
        current_state["current_week"] = week
        
        # Run the graph for this week
        result = await graph.ainvoke(current_state, config)
        current_state.update(result)
        
        # Print summary
        print(f"Cost per customer: ${current_state['cost_per_customer']:.2f}")
        print(f"Product-market fit: {current_state['product_market_fit']:.2%}")
        print(f"Channel saturation: {current_state['channel_saturation']:.2%}")
        
        # Check for pending decisions
        if current_state.get("pending_human_decision"):
            print(f"Pending human decision: {current_state['pending_human_decision']}")

if __name__ == "__main__":
    asyncio.run(main())
```

## did not survive

1. **Bayesian belief updating mechanics**: The spec mentions `how: bayesian` for `product_market_fit` but doesn't specify the Bayesian model structure, priors, or update rules. Implemented a simplified satisfaction-based update instead.

2. **Judgement-based belief with monthly review**: `channel_saturation` uses `how: judgement` with `checked_by: monthly_spend_vs_cost_review`. The actual judgement process and review mechanics aren't specified, so implemented a placeholder.

3. **Effect timing with delays**: Actions have `effect_after: 2w` and `effect_after: 4w` properties, but the spec doesn't define how delayed effects should be modeled in a weekly loop. Implemented tracking of effect timing but no delayed state changes.

4. **Costly undo semantics**: `can_undo: costly` for pricing changes isn't operationalized. Implemented as needing approval but no cost modeling.

5. **14-day continuous condition checking**: The trigger `"cost_per_customer stays above 600 for 14 days"` requires historical state tracking across runs, which isn't fully implemented.

6. **Runway commitment modeling**: `"spend exceeds committed runway"` uses `committed runway` which isn't defined in the state. Implemented a simplified check.

7. **Investor accountability without visibility**: The investor `sees nothing` but is `accountable and blind` - this paradoxical accountability can't be operationalized in an automated system.

8. **Non-modelling declarations**: `not_modelling: competitor_response, seasonality` are acknowledged but don't affect implementation since they're explicitly excluded.

9. **Belief bias handling**: `known_bias: "reads high when volume is low"` for product_market_fit isn't incorporated into the belief update logic.

10. **Origin distinctions**: `origin: ourselves` vs `origin: outside` distinctions don't affect the observation logic in the current implementation.

11. **Reported vs measured data handling**: The distinction between `how: reported` and `how: measured` isn't implemented in data quality or processing differences.